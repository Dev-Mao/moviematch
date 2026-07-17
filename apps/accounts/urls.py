from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("registro/", views.registro, name="registro"),
    path("acceder/", views.AccesoView.as_view(), name="login"),
    path("salir/", views.SalidaView.as_view(), name="logout"),
    path("perfil/", views.perfil, name="perfil"),
    path("amigos/", views.amigos, name="amigos"),
    path("amigos/solicitar/<int:usuario_id>/", views.enviar_solicitud, name="enviar_solicitud"),
    path(
        "amigos/responder/<int:amistad_id>/<str:accion>/",
        views.responder_solicitud,
        name="responder_solicitud",
    ),
    path("amigos/eliminar/<int:usuario_id>/", views.eliminar_amistad, name="eliminar_amistad"),
    path("gestion/usuarios/", views.admin_usuarios, name="admin_usuarios"),
    path(
        "gestion/usuarios/<int:perfil_id>/estado/<str:estado>/",
        views.admin_cambiar_estado,
        name="admin_cambiar_estado",
    ),
]
