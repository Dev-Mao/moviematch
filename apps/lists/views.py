"""Vistas de listas de recomendaciones (CU-08)."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.accounts.models import Amistad
from apps.catalog.models import ContenidoAudiovisual

from .models import ListaDeRecomendaciones


@login_required
def mis_listas(request):
    """CU-08: consultar las listas propias y las compartidas conmigo."""
    propias = (
        ListaDeRecomendaciones.objects.filter(propietario=request.user)
        .annotate(cuantos=Count("contenidos"))
        .prefetch_related("contenidos", "compartida_con")
    )
    compartidas = (
        ListaDeRecomendaciones.objects.filter(compartida_con=request.user)
        .annotate(cuantos=Count("contenidos"))
        .select_related("propietario__perfil")
    )
    return render(
        request,
        "lists/mis_listas.html",
        {"seccion": "listas", "propias": propias, "compartidas": compartidas},
    )


@login_required
def detalle_lista(request, lista_id):
    """Ficha de una lista, respetando su visibilidad."""
    lista = get_object_or_404(
        ListaDeRecomendaciones.objects.prefetch_related("contenidos", "compartida_con"),
        pk=lista_id,
    )
    # RN-10: una lista privada solo es visible para el dueño y con quien se comparte.
    if not lista.es_visible_para(request.user):
        messages.error(request, "Esta lista es privada.")
        return redirect("lists:mis_listas")

    return render(
        request,
        "lists/detalle_lista.html",
        {"seccion": "listas", "lista": lista, "es_propietario": lista.propietario == request.user},
    )


@login_required
def crear_lista(request):
    """CU-08 pasos 1 a 4: crear una lista y elegir con quién compartirla."""
    amigos = [
        amistad.otro_usuario(request.user)
        for amistad in Amistad.objects.de_usuario(request.user).aceptadas()
    ]

    if request.method == "POST":
        nombre = request.POST.get("nombre", "").strip()
        if not nombre:
            messages.error(request, "La lista necesita un nombre.")
            return redirect("lists:crear_lista")

        lista = ListaDeRecomendaciones.objects.create(
            propietario=request.user,
            nombre=nombre,
            descripcion=request.POST.get("descripcion", "").strip(),
            es_publica=request.POST.get("es_publica") == "on",
        )
        ids_amigos = request.POST.getlist("compartida_con")
        if ids_amigos:
            # FE-02: solo se puede compartir con amistades aceptadas.
            permitidos = [a.id for a in amigos if str(a.id) in ids_amigos]
            lista.compartida_con.set(permitidos)
        messages.success(request, f"La lista «{lista.nombre}» se creó correctamente.")
        return redirect("lists:detalle_lista", lista_id=lista.id)

    return render(request, "lists/crear_lista.html", {"seccion": "listas", "amigos": amigos})


@login_required
@require_POST
def agregar_contenido(request, lista_id):
    """CU-08 paso 2: agregar un contenido a una lista propia."""
    lista = get_object_or_404(ListaDeRecomendaciones, pk=lista_id, propietario=request.user)
    contenido = get_object_or_404(ContenidoAudiovisual, pk=request.POST.get("contenido_id"))
    lista.contenidos.add(contenido)
    messages.success(request, f"«{contenido.titulo}» se agregó a «{lista.nombre}».")
    return redirect("catalog:detalle", contenido_id=contenido.id)


@login_required
@require_POST
def quitar_contenido(request, lista_id, contenido_id):
    lista = get_object_or_404(ListaDeRecomendaciones, pk=lista_id, propietario=request.user)
    lista.contenidos.remove(contenido_id)
    messages.info(request, "Contenido retirado de la lista.")
    return redirect("lists:detalle_lista", lista_id=lista.id)


@login_required
@require_POST
def eliminar_lista(request, lista_id):
    """FA-01 del CU-08: eliminar una lista propia."""
    lista = get_object_or_404(ListaDeRecomendaciones, pk=lista_id, propietario=request.user)
    nombre = lista.nombre
    lista.delete()
    messages.info(request, f"La lista «{nombre}» se eliminó.")
    return redirect("lists:mis_listas")
