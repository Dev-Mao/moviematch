"""Vistas de cuentas: registro, acceso, perfil, amigos y gestión de usuarios."""

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView, LogoutView
from django.core.cache import cache
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import LoginForm, PerfilForm, PreferenciasForm, RegistroForm
from .models import Amistad, Perfil


def es_administrador(usuario):
    return usuario.is_authenticated and usuario.is_staff


# --------------------------------------------------------------- CU-01 y CU-02


def registro(request):
    """CU-01: Registrarse."""
    if request.user.is_authenticated:
        return redirect("recommendations:home")

    if request.method == "POST":
        form = RegistroForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            login(request, usuario)
            messages.success(
                request, "Bienvenida a MovieMatch. Elige tus géneros favoritos para empezar."
            )
            return redirect("accounts:perfil")
    else:
        form = RegistroForm()

    return render(request, "accounts/registro.html", {"form": form})


def _clave_intentos(identificador):
    return f"login_intentos:{identificador.lower()}"


class AccesoView(LoginView):
    """CU-02: Iniciar sesión, con bloqueo temporal por intentos fallidos (RN-03)."""

    template_name = "accounts/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        cache.delete(_clave_intentos(self.request.POST.get("username", "")))
        respuesta = super().form_valid(form)
        # Si no marca "Recuérdame", la sesión termina al cerrar el navegador.
        if not self.request.POST.get("recordarme"):
            self.request.session.set_expiry(0)
        return respuesta

    def form_invalid(self, form):
        identificador = self.request.POST.get("username", "")
        if identificador and not form.has_error("__all__", code="cuenta_no_activa"):
            clave = _clave_intentos(identificador)
            intentos = cache.get(clave, 0) + 1
            cache.set(clave, intentos, timeout=settings.LOGIN_LOCKOUT_MINUTES * 60)
            restantes = settings.LOGIN_MAX_ATTEMPTS - intentos
            if 0 < restantes <= 2:
                messages.warning(
                    self.request,
                    f"Te queda{'n' if restantes > 1 else ''} {restantes} "
                    f"intento{'s' if restantes > 1 else ''} antes del bloqueo temporal.",
                )
        return super().form_invalid(form)

    def post(self, request, *args, **kwargs):
        """FE-03: bloquea el acceso tras varios intentos fallidos."""
        identificador = request.POST.get("username", "")
        if identificador:
            intentos = cache.get(_clave_intentos(identificador), 0)
            if intentos >= settings.LOGIN_MAX_ATTEMPTS:
                messages.error(
                    request,
                    "Demasiados intentos fallidos. Tu acceso está bloqueado "
                    f"durante {settings.LOGIN_LOCKOUT_MINUTES} minutos.",
                )
                return redirect("accounts:login")
        return super().post(request, *args, **kwargs)


class SalidaView(LogoutView):
    """Cierre de sesión."""

    next_page = "accounts:login"


# ---------------------------------------------------------------------- CU-03


@login_required
def perfil(request):
    """CU-03: Gestionar perfil y preferencias."""
    perfil_usuario = request.user.perfil

    if request.method == "POST":
        form = PerfilForm(request.POST, instance=perfil_usuario)
        form_preferencias = PreferenciasForm(request.POST, perfil=perfil_usuario)
        if form.is_valid() and form_preferencias.is_valid():
            form.save()
            form_preferencias.save()
            # Paso 5 del CU-03: las recomendaciones quedan marcadas para recálculo.
            request.user.recomendaciones.all().delete()
            messages.success(request, "Tu perfil se actualizó correctamente.")
            return redirect("accounts:perfil")
        messages.error(request, "Revisa los datos del formulario.")
    else:
        form = PerfilForm(instance=perfil_usuario)
        form_preferencias = PreferenciasForm(perfil=perfil_usuario)

    contexto = {
        "seccion": "perfil",
        "form": form,
        "form_preferencias": form_preferencias,
        "perfil": perfil_usuario,
        "total_valoraciones": request.user.valoraciones.count(),
        "total_amigos": Amistad.objects.de_usuario(request.user).aceptadas().count(),
        "total_listas": request.user.listas.count(),
    }
    return render(request, "accounts/perfil.html", contexto)


# ---------------------------------------------------------------------- CU-07


@login_required
def amigos(request):
    """CU-07: Gestionar solicitudes de amistad."""
    busqueda = request.GET.get("q", "").strip()

    amistades = (
        Amistad.objects.de_usuario(request.user)
        .aceptadas()
        .select_related("solicitante__perfil", "destinatario__perfil")
    )
    lista_amigos = [amistad.otro_usuario(request.user) for amistad in amistades]

    pendientes = Amistad.objects.filter(
        destinatario=request.user, estado=Amistad.Estado.PENDIENTE
    ).select_related("solicitante__perfil")

    resultados = []
    if busqueda:
        excluidos = {request.user.id}
        for solicitante_id, destinatario_id in Amistad.objects.de_usuario(
            request.user
        ).values_list("solicitante_id", "destinatario_id"):
            excluidos.update({solicitante_id, destinatario_id})
        resultados = (
            User.objects.filter(
                Q(perfil__alias__icontains=busqueda)
                | Q(first_name__icontains=busqueda)
                | Q(last_name__icontains=busqueda)
            )
            .exclude(id__in=excluidos)
            .exclude(is_staff=True)
            .select_related("perfil")[:10]
        )

    contexto = {
        "seccion": "amigos",
        "amigos": lista_amigos,
        "pendientes": pendientes,
        "busqueda": busqueda,
        "resultados": resultados,
        "conteo_valoraciones": {
            usuario.id: usuario.valoraciones.count() for usuario in lista_amigos
        },
    }
    return render(request, "accounts/amigos.html", contexto)


@login_required
@require_POST
def enviar_solicitud(request, usuario_id):
    """CU-07 paso 2: enviar una solicitud de amistad."""
    destinatario = get_object_or_404(User, pk=usuario_id)

    if destinatario == request.user:
        messages.error(request, "No puedes enviarte una solicitud a ti misma.")
        return redirect("accounts:amigos")

    existente = Amistad.objects.filter(
        Q(solicitante=request.user, destinatario=destinatario)
        | Q(solicitante=destinatario, destinatario=request.user)
    ).first()
    if existente:
        # FE-01: ya existe una amistad o una solicitud entre ambos.
        messages.info(request, f"Ya tienes una solicitud con {destinatario.get_full_name()}.")
        return redirect("accounts:amigos")

    Amistad.objects.create(solicitante=request.user, destinatario=destinatario)
    messages.success(request, f"Solicitud enviada a {destinatario.get_full_name()}.")
    return redirect("accounts:amigos")


@login_required
@require_POST
def responder_solicitud(request, amistad_id, accion):
    """CU-07 pasos 3 y 4: aceptar o rechazar una solicitud recibida."""
    amistad = get_object_or_404(
        Amistad, pk=amistad_id, destinatario=request.user, estado=Amistad.Estado.PENDIENTE
    )

    if accion == "aceptar":
        amistad.aceptar()
        # Las valoraciones del nuevo amigo ya pueden influir en las recomendaciones.
        request.user.recomendaciones.all().delete()
        messages.success(request, f"Ahora eres amiga de {amistad.solicitante.get_full_name()}.")
    else:
        amistad.rechazar()
        messages.info(request, "Solicitud rechazada.")
    return redirect("accounts:amigos")


@login_required
@require_POST
def eliminar_amistad(request, usuario_id):
    """FA-01 del CU-07: eliminar una amistad existente."""
    otro = get_object_or_404(User, pk=usuario_id)
    Amistad.objects.filter(
        Q(solicitante=request.user, destinatario=otro)
        | Q(solicitante=otro, destinatario=request.user)
    ).delete()
    request.user.recomendaciones.all().delete()
    messages.info(request, f"Ya no eres amiga de {otro.get_full_name()}.")
    return redirect("accounts:amigos")


# ---------------------------------------------------------------------- CU-10


@login_required
@user_passes_test(es_administrador)
def admin_usuarios(request):
    """CU-10: Gestionar usuarios."""
    busqueda = request.GET.get("q", "").strip()
    estado = request.GET.get("estado", "").strip()

    usuarios = (
        User.objects.select_related("perfil")
        .annotate(num_valoraciones=Count("valoraciones", distinct=True))
        .order_by("-date_joined")
    )
    if busqueda:
        usuarios = usuarios.filter(
            Q(first_name__icontains=busqueda)
            | Q(last_name__icontains=busqueda)
            | Q(email__icontains=busqueda)
            | Q(perfil__alias__icontains=busqueda)
        )
    if estado:
        usuarios = usuarios.filter(perfil__estado=estado)

    contexto = {
        "seccion": "admin_usuarios",
        "es_admin": True,
        "usuarios": usuarios,
        "busqueda": busqueda,
        "estado": estado,
        "estados": Perfil.Estado.choices,
        "total": User.objects.count(),
    }
    return render(request, "accounts/admin_usuarios.html", contexto)


@login_required
@user_passes_test(es_administrador)
@require_POST
def admin_cambiar_estado(request, perfil_id, estado):
    """CU-10 pasos 3 y 4: suspender o reactivar una cuenta.

    RN-12: solo un superadministrador puede eliminar cuentas; un moderador
    únicamente puede suspender.
    """
    perfil_objetivo = get_object_or_404(Perfil, pk=perfil_id)

    if estado not in Perfil.Estado.values:
        messages.error(request, "Estado no válido.")
        return redirect("accounts:admin_usuarios")

    if perfil_objetivo.usuario == request.user:
        messages.error(request, "No puedes cambiar el estado de tu propia cuenta.")
        return redirect("accounts:admin_usuarios")

    perfil_objetivo.estado = estado
    perfil_objetivo.save(update_fields=["estado"])
    messages.success(
        request,
        f"La cuenta de {perfil_objetivo.usuario.get_full_name()} quedó "
        f"{perfil_objetivo.get_estado_display().lower()}.",
    )
    return redirect("accounts:admin_usuarios")
