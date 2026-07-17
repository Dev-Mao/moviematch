"""Vistas de valoraciones (CU-04) y actividad de amigos (CU-09)."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.accounts.models import Amistad
from apps.catalog.models import ContenidoAudiovisual

from .models import Valoracion


@login_required
@require_POST
def valorar(request, contenido_id):
    """CU-04: Valorar película o serie."""
    contenido = get_object_or_404(ContenidoAudiovisual, pk=contenido_id)

    # FE-02: no se puede valorar contenido retirado del catálogo.
    if not contenido.esta_publicado:
        messages.error(request, "Este contenido ya no está disponible y no se puede valorar.")
        return redirect("catalog:catalogo")

    try:
        puntuacion = int(request.POST.get("puntuacion", 0))
    except (TypeError, ValueError):
        puntuacion = 0

    # FE-01: la puntuación debe estar entre 1 y 5 (RN-05).
    if not Valoracion.PUNTUACION_MINIMA <= puntuacion <= Valoracion.PUNTUACION_MAXIMA:
        messages.error(request, "La puntuación debe estar entre 1 y 5 estrellas.")
        return redirect("catalog:detalle", contenido_id=contenido.id)

    comentario = request.POST.get("comentario", "").strip()

    # RN-06: una sola valoración vigente por usuario y contenido, así que se
    # actualiza si ya existía (FA-01: editar una valoración previa).
    _, creada = Valoracion.objects.update_or_create(
        usuario=request.user,
        contenido=contenido,
        defaults={"puntuacion": puntuacion, "comentario": comentario},
    )

    # Paso 5 del CU-04: las recomendaciones quedan marcadas para recálculo.
    request.user.recomendaciones.all().delete()

    messages.success(
        request,
        f"Tu valoración de «{contenido.titulo}» se {'registró' if creada else 'actualizó'}.",
    )
    return redirect("catalog:detalle", contenido_id=contenido.id)


@login_required
@require_POST
def eliminar_valoracion(request, contenido_id):
    """FA-02 del CU-04: eliminar la valoración propia."""
    Valoracion.objects.filter(usuario=request.user, contenido_id=contenido_id).delete()
    request.user.recomendaciones.all().delete()
    messages.info(request, "Tu valoración se eliminó.")
    return redirect("catalog:detalle", contenido_id=contenido_id)


@login_required
def actividad(request):
    """CU-09: Ver valoraciones de amigos."""
    ids_amigos = [
        amistad.otro_usuario(request.user).id
        for amistad in Amistad.objects.de_usuario(request.user).aceptadas()
    ]
    filtro_amigo = request.GET.get("amigo", "").strip()

    # RN-07: solo la actividad de las amistades aceptadas.
    valoraciones = (
        Valoracion.objects.filter(usuario_id__in=ids_amigos)
        .select_related("usuario__perfil", "contenido")
        .prefetch_related("contenido__generos")
        .order_by("-fecha")
    )
    if filtro_amigo.isdigit():
        valoraciones = valoraciones.filter(usuario_id=int(filtro_amigo))

    populares = (
        ContenidoAudiovisual.objects.filter(
            valoraciones__usuario_id__in=ids_amigos,
            estado=ContenidoAudiovisual.Estado.PUBLICADO,
        )
        .annotate(cuantos=Count("valoraciones"), promedio=Avg("valoraciones__puntuacion"))
        .order_by("-cuantos", "-promedio")[:5]
    )

    from django.contrib.auth.models import User

    contexto = {
        "seccion": "actividad",
        "valoraciones": valoraciones[:25],
        "populares": populares,
        "amigos": User.objects.filter(id__in=ids_amigos).select_related("perfil"),
        "filtro_amigo": filtro_amigo,
    }
    return render(request, "ratings/actividad.html", contexto)
