"""Modelo de recomendaciones generadas por el motor."""

from django.conf import settings
from django.db import models

from apps.catalog.models import ContenidoAudiovisual


class Recomendacion(models.Model):
    """Sugerencia generada para un usuario sobre un contenido.

    RN-D5: siempre la genera el motor de recomendaciones, nunca se crea a mano.
    """

    class Origen(models.TextChoices):
        PREFERENCIAS = "PREFERENCIAS", "Tus géneros preferidos"
        AMIGOS = "AMIGOS", "Valoraciones de tus amigos"
        HISTORIAL = "HISTORIAL", "Tu historial de valoraciones"
        POPULARIDAD = "POPULARIDAD", "Popular en MovieMatch"

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recomendaciones",
        verbose_name="usuario",
    )
    contenido = models.ForeignKey(
        ContenidoAudiovisual,
        on_delete=models.CASCADE,
        related_name="recomendaciones",
        verbose_name="contenido",
    )
    score = models.FloatField("puntuación", default=0)
    origen = models.CharField(
        "origen", max_length=14, choices=Origen.choices, default=Origen.POPULARIDAD
    )
    motivo = models.CharField("motivo", max_length=200, blank=True)
    fecha_generada = models.DateTimeField("fecha de generación", auto_now_add=True)

    class Meta:
        verbose_name = "recomendación"
        verbose_name_plural = "recomendaciones"
        ordering = ["-score"]
        constraints = [
            models.UniqueConstraint(
                fields=["usuario", "contenido"], name="recomendacion_unica_por_usuario_y_contenido"
            )
        ]

    def __str__(self):
        return f"{self.contenido} para {self.usuario} ({self.score:.2f})"
