"""Modelo de valoraciones de contenido."""

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.catalog.models import ContenidoAudiovisual


class Valoracion(models.Model):
    """Calificación que un usuario da a un contenido."""

    PUNTUACION_MINIMA = 1
    PUNTUACION_MAXIMA = 5

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="valoraciones",
        verbose_name="usuario",
    )
    contenido = models.ForeignKey(
        ContenidoAudiovisual,
        on_delete=models.CASCADE,
        related_name="valoraciones",
        verbose_name="contenido",
    )
    puntuacion = models.PositiveSmallIntegerField(
        "puntuación",
        validators=[
            MinValueValidator(PUNTUACION_MINIMA),
            MaxValueValidator(PUNTUACION_MAXIMA),
        ],
        help_text="RN-05: la puntuación va de 1 a 5.",
    )
    comentario = models.TextField("comentario", blank=True)
    fecha = models.DateTimeField("fecha", auto_now=True)

    class Meta:
        verbose_name = "valoración"
        verbose_name_plural = "valoraciones"
        ordering = ["-fecha"]
        constraints = [
            # RN-06: una sola valoración vigente por usuario y contenido.
            models.UniqueConstraint(
                fields=["usuario", "contenido"], name="valoracion_unica_por_usuario_y_contenido"
            ),
            models.CheckConstraint(
                condition=models.Q(puntuacion__gte=1) & models.Q(puntuacion__lte=5),
                name="valoracion_puntuacion_entre_1_y_5",
            ),
        ]

    def __str__(self):
        return f"{self.usuario} valoró {self.contenido} con {self.puntuacion}"

    @property
    def estrellas(self):
        """Lista de booleanos para pintar las cinco estrellas en la plantilla."""
        return [i <= self.puntuacion for i in range(1, self.PUNTUACION_MAXIMA + 1)]
