"""Modelo de métricas de uso para el panel de administración."""

from django.db import models


class MetricaDeUso(models.Model):
    """Indicador agregado de uso o desempeño.

    RN-14: las métricas se calculan sobre datos anonimizados y agregados.
    """

    class Tipo(models.TextChoices):
        USUARIOS_ACTIVOS = "USUARIOS_ACTIVOS", "Usuarios activos"
        RECOMENDACIONES = "RECOMENDACIONES", "Recomendaciones generadas"
        VALORACIONES = "VALORACIONES", "Valoraciones registradas"
        TIEMPO_RESPUESTA = "TIEMPO_RESPUESTA", "Tiempo de respuesta (s)"
        TASA_ERROR = "TASA_ERROR", "Tasa de error (%)"

    tipo = models.CharField("tipo", max_length=20, choices=Tipo.choices)
    valor = models.FloatField("valor")
    fecha_corte = models.DateField("fecha de corte")

    class Meta:
        verbose_name = "métrica de uso"
        verbose_name_plural = "métricas de uso"
        ordering = ["-fecha_corte", "tipo"]
        constraints = [
            models.UniqueConstraint(
                fields=["tipo", "fecha_corte"], name="metrica_unica_por_tipo_y_fecha"
            )
        ]

    def __str__(self):
        return f"{self.get_tipo_display()} · {self.fecha_corte}: {self.valor}"
