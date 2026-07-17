from django.urls import path

from . import views

app_name = "recommendations"

urlpatterns = [
    path("", views.home, name="home"),
    path("actualizar/", views.actualizar, name="actualizar"),
]
