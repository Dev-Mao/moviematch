"""Modelo de listas de recomendaciones compartibles."""

from django.conf import settings
from django.db import models

from apps.catalog.models import ContenidoAudiovisual


class ListaDeRecomendaciones(models.Model):
    """Colección curada y compartible de contenidos."""

    propietario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="listas",
        verbose_name="propietario",
    )
    nombre = models.CharField("nombre", max_length=120)
    descripcion = models.TextField("descripción", blank=True)
    es_publica = models.BooleanField("es pública", default=False)
    contenidos = models.ManyToManyField(
        ContenidoAudiovisual, related_name="listas", blank=True, verbose_name="contenidos"
    )
    compartida_con = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="listas_compartidas",
        blank=True,
        verbose_name="compartida con",
        help_text="RN-10: una lista privada solo es visible para amigos aceptados.",
    )
    fecha_creacion = models.DateTimeField("fecha de creación", auto_now_add=True)

    class Meta:
        verbose_name = "lista de recomendaciones"
        verbose_name_plural = "listas de recomendaciones"
        ordering = ["-fecha_creacion"]

    def __str__(self):
        return self.nombre

    @property
    def visibilidad(self):
        if self.es_publica:
            return "Pública"
        if self.compartida_con.exists():
            return "Compartida"
        return "Privada"

    def es_visible_para(self, usuario):
        """RN-10: pública para todos; privada solo para el dueño y con quien se comparta."""
        if self.es_publica or self.propietario_id == usuario.id:
            return True
        return self.compartida_con.filter(pk=usuario.pk).exists()
