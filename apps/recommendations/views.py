"""Vistas de recomendaciones (CU-05)."""

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from apps.accounts.models import Amistad
from apps.ratings.models import Valoracion

from .models import Recomendacion
from .services import MotorDeRecomendaciones


@login_required
def home(request):
    """CU-05: Recibir recomendaciones personalizadas."""
    recomendaciones = list(
        Recomendacion.objects.filter(usuario=request.user)
        .select_related("contenido")
        .prefetch_related("contenido__generos")
    )

    # Si no hay recomendaciones vigentes, el motor las genera al vuelo.
    if not recomendaciones:
        MotorDeRecomendaciones(request.user).generar()
        recomendaciones = list(
            Recomendacion.objects.filter(usuario=request.user)
            .select_related("contenido")
            .prefetch_related("contenido__generos")
        )

    destacada = recomendaciones[0] if recomendaciones else None
    para_ti = [r for r in recomendaciones if r.origen != Recomendacion.Origen.AMIGOS][:5]
    de_amigos = [r for r in recomendaciones if r.origen == Recomendacion.Origen.AMIGOS][:5]

    ids_amigos = [
        amistad.otro_usuario(request.user).id
        for amistad in Amistad.objects.de_usuario(request.user).aceptadas()
    ]
    actividad = (
        Valoracion.objects.filter(usuario_id__in=ids_amigos)
        .select_related("usuario__perfil", "contenido")
        .order_by("-fecha")[:4]
    )

    contexto = {
        "seccion": "inicio",
        "destacada": destacada,
        "para_ti": para_ti,
        "de_amigos": de_amigos,
        "actividad": actividad,
        "sin_datos": not recomendaciones,
    }
    return render(request, "recommendations/home.html", contexto)


@login_required
@require_POST
def actualizar(request):
    """Permite al usuario forzar el recálculo de sus recomendaciones."""
    MotorDeRecomendaciones(request.user).generar()
    return redirect("recommendations:home")
