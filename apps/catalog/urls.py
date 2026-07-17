from django.urls import path

from . import views

app_name = "catalog"

urlpatterns = [
    path("catalogo/", views.catalogo, name="catalogo"),
    path("contenido/<int:contenido_id>/", views.detalle, name="detalle"),
    path("gestion/contenido/", views.admin_contenido, name="admin_contenido"),
    path(
        "gestion/contenido/<int:contenido_id>/estado/",
        views.admin_cambiar_estado,
        name="admin_cambiar_estado",
    ),
]
