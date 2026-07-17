from django.urls import path

from . import views

app_name = "analytics"

urlpatterns = [
    path("gestion/metricas/", views.panel, name="panel"),
]
