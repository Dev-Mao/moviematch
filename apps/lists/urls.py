from django.urls import path

from . import views

app_name = "lists"

urlpatterns = [
    path("listas/", views.mis_listas, name="mis_listas"),
    path("listas/nueva/", views.crear_lista, name="crear_lista"),
    path("listas/<int:lista_id>/", views.detalle_lista, name="detalle_lista"),
    path("listas/<int:lista_id>/agregar/", views.agregar_contenido, name="agregar_contenido"),
    path(
        "listas/<int:lista_id>/quitar/<int:contenido_id>/",
        views.quitar_contenido,
        name="quitar_contenido",
    ),
    path("listas/<int:lista_id>/eliminar/", views.eliminar_lista, name="eliminar_lista"),
]
