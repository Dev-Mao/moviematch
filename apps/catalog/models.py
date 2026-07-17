"""Modelos del catálogo de contenido audiovisual."""

from django.db import models


class Genero(models.Model):
    """Categoría de clasificación del contenido."""

    nombre = models.CharField("nombre", max_length=60, unique=True)
    slug = models.SlugField("slug", max_length=60, unique=True)

    class Meta:
        verbose_name = "género"
        verbose_name_plural = "géneros"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class ContenidoAudiovisual(models.Model):
    """Abstracción de una obra audiovisual (película o serie)."""

    class Estado(models.TextChoices):
        PUBLICADO = "PUBLICADO", "Publicado"
        RETIRADO = "RETIRADO", "Retirado"

    titulo = models.CharField("título", max_length=200)
    sinopsis = models.TextField("sinopsis", blank=True)
    anio_estreno = models.PositiveIntegerField("año de estreno")
    poster_url = models.URLField("URL del póster", blank=True)
    backdrop_url = models.URLField("URL del fondo panorámico", blank=True)
    clasificacion = models.CharField("clasificación", max_length=10, blank=True)
    generos = models.ManyToManyField(Genero, related_name="contenidos", verbose_name="géneros")
    estado = models.CharField(
        "estado", max_length=12, choices=Estado.choices, default=Estado.PUBLICADO
    )
    creado = models.DateTimeField("creado", auto_now_add=True)

    class Meta:
        verbose_name = "contenido audiovisual"
        verbose_name_plural = "contenidos audiovisuales"
        ordering = ["titulo"]

    def __str__(self):
        return f"{self.titulo} ({self.anio_estreno})"

    @property
    def esta_publicado(self):
        """RN-08 y RN-13: solo el contenido publicado se lista y se recomienda."""
        return self.estado == self.Estado.PUBLICADO

    @property
    def tipo(self):
        if hasattr(self, "pelicula"):
            return "Película"
        if hasattr(self, "serie"):
            return "Serie"
        return "Contenido"

    @property
    def promedio_valoraciones(self):
        resultado = self.valoraciones.aggregate(promedio=models.Avg("puntuacion"))
        return round(resultado["promedio"], 1) if resultado["promedio"] else None


class Pelicula(ContenidoAudiovisual):
    """Contenido audiovisual de un solo bloque."""

    duracion_min = models.PositiveIntegerField("duración en minutos")

    class Meta:
        verbose_name = "película"
        verbose_name_plural = "películas"


class Serie(ContenidoAudiovisual):
    """Contenido audiovisual episódico."""

    num_temporadas = models.PositiveIntegerField("número de temporadas", default=1)
    num_episodios = models.PositiveIntegerField("número de episodios", default=1)
    en_emision = models.BooleanField("en emisión", default=False)

    class Meta:
        verbose_name = "serie"
        verbose_name_plural = "series"
