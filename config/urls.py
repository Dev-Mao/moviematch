"""Enrutado principal de MovieMatch."""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("", include("apps.recommendations.urls")),
    path("", include("apps.accounts.urls")),
    path("", include("apps.catalog.urls")),
    path("", include("apps.ratings.urls")),
    path("", include("apps.lists.urls")),
    path("", include("apps.analytics.urls")),
]
