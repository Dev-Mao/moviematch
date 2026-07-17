from django.urls import path

from . import views

app_name = "ratings"

urlpatterns = [
    path("contenido/<int:contenido_id>/valorar/", views.valorar, name="valorar"),
    path("contenido/<int:contenido_id>/valorar/eliminar/", views.eliminar_valoracion, name="eliminar"),
    path("actividad/", views.actividad, name="actividad"),
]
