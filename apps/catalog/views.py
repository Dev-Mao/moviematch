"""Vistas del catálogo (CU-06) y de la gestión de contenido (CU-11)."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Avg, Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.accounts.models import Amistad
from apps.accounts.views import es_administrador
from apps.lists.models import ListaDeRecomendaciones
from apps.ratings.models import Valoracion

from .models import ContenidoAudiovisual, Genero


@login_required
def catalogo(request):
    """CU-06: Buscar o explorar el catálogo."""
    busqueda = request.GET.get("q", "").strip()
    genero_slug = request.GET.get("genero", "").strip()
    tipo = request.GET.get("tipo", "").strip()
    orden = request.GET.get("orden", "valoradas")

    # RN-08: solo se lista el contenido publicado.
    contenidos = (
        ContenidoAudiovisual.objects.filter(estado=ContenidoAudiovisual.Estado.PUBLICADO)
        .annotate(promedio=Avg("valoraciones__puntuacion"), num_valoraciones=Count("valoraciones"))
        .prefetch_related("generos")
    )

    if busqueda:
        contenidos = contenidos.filter(
            Q(titulo__icontains=busqueda) | Q(sinopsis__icontains=busqueda)
        )
    if genero_slug:
        contenidos = contenidos.filter(generos__slug=genero_slug)
    if tipo == "pelicula":
        contenidos = contenidos.filter(pelicula__isnull=False)
    elif tipo == "serie":
        contenidos = contenidos.filter(serie__isnull=False)

    if orden == "recientes":
        contenidos = contenidos.order_by("-anio_estreno")
    elif orden == "titulo":
        contenidos = contenidos.order_by("titulo")
    else:
        contenidos = contenidos.order_by("-promedio", "-num_valoraciones")

    paginador = Paginator(contenidos.distinct(), 20)
    pagina = paginador.get_page(request.GET.get("pagina"))

    contexto = {
        "seccion": "buscar",
        "pagina": pagina,
        "busqueda": busqueda,
        "genero_slug": genero_slug,
        "tipo": tipo,
        "orden": orden,
        "generos": Genero.objects.annotate(n=Count("contenidos")).filter(n__gt=0),
        "total": paginador.count,
    }
    return render(request, "catalog/catalogo.html", contexto)


@login_required
def detalle(request, contenido_id):
    """CU-06 pasos 3 y 4: ficha del contenido, desde donde se puede valorar."""
    contenido = get_object_or_404(
        ContenidoAudiovisual.objects.prefetch_related("generos"), pk=contenido_id
    )

    # FE-02 del CU-04: el contenido retirado no admite nuevas valoraciones.
    if not contenido.esta_publicado and not request.user.is_staff:
        messages.warning(request, "Este contenido ya no está disponible en el catálogo.")
        return redirect("catalog:catalogo")

    mi_valoracion = Valoracion.objects.filter(usuario=request.user, contenido=contenido).first()

    ids_amigos = [
        amistad.otro_usuario(request.user).id
        for amistad in Amistad.objects.de_usuario(request.user).aceptadas()
    ]
    # RN-07: solo se muestran las valoraciones de las amistades aceptadas.
    valoraciones_amigos = (
        Valoracion.objects.filter(contenido=contenido, usuario_id__in=ids_amigos)
        .select_related("usuario__perfil")
        .order_by("-fecha")
    )

    resumen = Valoracion.objects.filter(contenido=contenido).aggregate(
        promedio=Avg("puntuacion"), total=Count("id")
    )

    contexto = {
        "seccion": "buscar",
        "contenido": contenido,
        "detalle_tipo": getattr(contenido, "pelicula", None) or getattr(contenido, "serie", None),
        "mi_valoracion": mi_valoracion,
        "valoraciones_amigos": valoraciones_amigos,
        "promedio": round(resumen["promedio"], 1) if resumen["promedio"] else None,
        "total_valoraciones": resumen["total"],
        "rango": range(1, 6),
        "mis_listas": ListaDeRecomendaciones.objects.filter(propietario=request.user),
    }
    return render(request, "catalog/detalle.html", contexto)


# ---------------------------------------------------------------------- CU-11


@login_required
@user_passes_test(es_administrador)
def admin_contenido(request):
    """CU-11: Gestionar contenido."""
    busqueda = request.GET.get("q", "").strip()
    estado = request.GET.get("estado", "").strip()
    tipo = request.GET.get("tipo", "").strip()

    contenidos = (
        ContenidoAudiovisual.objects.annotate(promedio=Avg("valoraciones__puntuacion"))
        .prefetch_related("generos")
        .order_by("titulo")
    )
    if busqueda:
        contenidos = contenidos.filter(titulo__icontains=busqueda)
    if estado:
        contenidos = contenidos.filter(estado=estado)
    if tipo == "pelicula":
        contenidos = contenidos.filter(pelicula__isnull=False)
    elif tipo == "serie":
        contenidos = contenidos.filter(serie__isnull=False)

    paginador = Paginator(contenidos, 15)
    pagina = paginador.get_page(request.GET.get("pagina"))

    contexto = {
        "seccion": "admin_contenido",
        "es_admin": True,
        "pagina": pagina,
        "busqueda": busqueda,
        "estado": estado,
        "tipo": tipo,
        "estados": ContenidoAudiovisual.Estado.choices,
        "total": paginador.count,
    }
    return render(request, "catalog/admin_contenido.html", contexto)


@login_required
@user_passes_test(es_administrador)
@require_POST
def admin_cambiar_estado(request, contenido_id):
    """FA-02 del CU-11: publicar o retirar un contenido.

    RN-13: el contenido retirado desaparece del catálogo y de las
    recomendaciones, pero conserva sus valoraciones históricas.
    """
    contenido = get_object_or_404(ContenidoAudiovisual, pk=contenido_id)
    if contenido.estado == ContenidoAudiovisual.Estado.PUBLICADO:
        contenido.estado = ContenidoAudiovisual.Estado.RETIRADO
        aviso = f"«{contenido.titulo}» se retiró del catálogo."
    else:
        contenido.estado = ContenidoAudiovisual.Estado.PUBLICADO
        aviso = f"«{contenido.titulo}» se publicó de nuevo."
    contenido.save(update_fields=["estado"])
    messages.success(request, aviso)
    return redirect("catalog:admin_contenido")
