"""Importa el catálogo de películas y series desde la API de TMDB.

Este comando se ejecuta solo en desarrollo para construir los datos de prueba.
El resultado se exporta a un fixture que sí se versiona, de modo que el entorno
de producción nunca necesita la API key ni acceso a internet.

Uso:
    python manage.py import_tmdb --peliculas 45 --series 15
"""

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify

from apps.catalog.models import ContenidoAudiovisual, Genero, Pelicula, Serie

API_BASE = "https://api.themoviedb.org/3"
IMAGE_BASE = "https://image.tmdb.org/t/p/w500"
BACKDROP_BASE = "https://image.tmdb.org/t/p/w1280"
IDIOMA = "es-ES"


def leer_api_key(base_dir):
    """Obtiene la API key del entorno o del archivo .env local."""
    import os

    clave = os.environ.get("TMDB_API_KEY")
    if clave:
        return clave.strip()

    archivo = Path(base_dir) / ".env"
    if archivo.exists():
        for linea in archivo.read_text(encoding="utf-8").splitlines():
            linea = linea.strip()
            if linea.startswith("TMDB_API_KEY="):
                return linea.split("=", 1)[1].strip()
    return None


class Command(BaseCommand):
    help = "Importa películas y series populares desde TMDB al catálogo local."

    def add_arguments(self, parser):
        parser.add_argument("--peliculas", type=int, default=45)
        parser.add_argument("--series", type=int, default=15)

    def handle(self, *args, **options):
        from django.conf import settings

        self.api_key = leer_api_key(settings.BASE_DIR)
        if not self.api_key:
            raise CommandError(
                "No se encontró TMDB_API_KEY. Defínela en el archivo .env de la raíz."
            )

        self.stdout.write("Importando géneros...")
        generos = self._importar_generos()
        self.stdout.write(self.style.SUCCESS(f"  {len(generos)} géneros disponibles"))

        self.stdout.write("Importando películas...")
        n_peliculas = self._importar_peliculas(options["peliculas"], generos)
        self.stdout.write(self.style.SUCCESS(f"  {n_peliculas} películas importadas"))

        self.stdout.write("Importando series...")
        n_series = self._importar_series(options["series"], generos)
        self.stdout.write(self.style.SUCCESS(f"  {n_series} series importadas"))

        total = ContenidoAudiovisual.objects.count()
        self.stdout.write(self.style.SUCCESS(f"Catálogo con {total} contenidos en total."))

    # ------------------------------------------------------------------ API

    def _get(self, ruta, **parametros):
        parametros["api_key"] = self.api_key
        parametros.setdefault("language", IDIOMA)
        url = f"{API_BASE}{ruta}?{urllib.parse.urlencode(parametros)}"
        for intento in range(3):
            try:
                with urllib.request.urlopen(url, timeout=20) as respuesta:
                    return json.loads(respuesta.read().decode("utf-8"))
            except urllib.error.HTTPError as error:
                if error.code == 429:  # límite de peticiones
                    time.sleep(2)
                    continue
                raise CommandError(f"TMDB respondió {error.code} en {ruta}")
            except urllib.error.URLError as error:
                if intento == 2:
                    raise CommandError(f"No se pudo conectar con TMDB: {error.reason}")
                time.sleep(2)
        return {}

    @staticmethod
    def _imagen(detalle, campo, base):
        """Construye la URL absoluta de una imagen de TMDB, si existe."""
        ruta = detalle.get(campo)
        return f"{base}{ruta}" if ruta else ""

    def _sinopsis(self, detalle, ruta):
        """Devuelve la sinopsis en español; si TMDB no la tiene, usa la inglesa."""
        texto = (detalle.get("overview") or "").strip()
        if texto:
            return texto
        alterno = self._get(ruta, language="en-US")
        return (alterno.get("overview") or "").strip()

    # --------------------------------------------------------------- Géneros

    @transaction.atomic
    def _importar_generos(self):
        """Devuelve un diccionario {id_tmdb: Genero} con películas y series."""
        generos = {}
        for ruta in ("/genre/movie/list", "/genre/tv/list"):
            for item in self._get(ruta).get("genres", []):
                objeto, _ = Genero.objects.get_or_create(
                    nombre=item["name"], defaults={"slug": slugify(item["name"])}
                )
                generos[item["id"]] = objeto
        return generos

    # -------------------------------------------------------------- Películas

    def _importar_peliculas(self, cantidad, generos):
        importadas = 0
        pagina = 1
        while importadas < cantidad and pagina <= 10:
            datos = self._get("/movie/top_rated", page=pagina)
            for resumen in datos.get("results", []):
                if importadas >= cantidad:
                    break
                if self._crear_pelicula(resumen["id"], generos):
                    importadas += 1
            pagina += 1
        return importadas

    def _crear_pelicula(self, tmdb_id, generos):
        detalle = self._get(f"/movie/{tmdb_id}", append_to_response="release_dates")
        titulo = (detalle.get("title") or "").strip()
        fecha = detalle.get("release_date") or ""
        if not titulo or not fecha:
            return False

        anio = int(fecha[:4])
        if Pelicula.objects.filter(titulo=titulo, anio_estreno=anio).exists():
            return False

        pelicula = Pelicula.objects.create(
            titulo=titulo,
            sinopsis=self._sinopsis(detalle, f"/movie/{tmdb_id}"),
            anio_estreno=anio,
            poster_url=self._imagen(detalle, "poster_path", IMAGE_BASE),
            backdrop_url=self._imagen(detalle, "backdrop_path", BACKDROP_BASE),
            clasificacion=self._certificacion_pelicula(detalle),
            duracion_min=detalle.get("runtime") or 0,
        )
        pelicula.generos.set(
            [generos[g["id"]] for g in detalle.get("genres", []) if g["id"] in generos]
        )
        return True

    def _certificacion_pelicula(self, detalle):
        resultados = (detalle.get("release_dates") or {}).get("results", [])
        for pais in ("CO", "ES", "US"):
            for entrada in resultados:
                if entrada.get("iso_3166_1") != pais:
                    continue
                for fecha in entrada.get("release_dates", []):
                    certificacion = (fecha.get("certification") or "").strip()
                    if certificacion:
                        return certificacion[:10]
        return ""

    # ----------------------------------------------------------------- Series

    def _importar_series(self, cantidad, generos):
        importadas = 0
        pagina = 1
        while importadas < cantidad and pagina <= 10:
            datos = self._get("/tv/top_rated", page=pagina)
            for resumen in datos.get("results", []):
                if importadas >= cantidad:
                    break
                if self._crear_serie(resumen["id"], generos):
                    importadas += 1
            pagina += 1
        return importadas

    def _crear_serie(self, tmdb_id, generos):
        detalle = self._get(f"/tv/{tmdb_id}", append_to_response="content_ratings")
        titulo = (detalle.get("name") or "").strip()
        fecha = detalle.get("first_air_date") or ""
        if not titulo or not fecha:
            return False

        anio = int(fecha[:4])
        if Serie.objects.filter(titulo=titulo, anio_estreno=anio).exists():
            return False

        serie = Serie.objects.create(
            titulo=titulo,
            sinopsis=self._sinopsis(detalle, f"/tv/{tmdb_id}"),
            anio_estreno=anio,
            poster_url=self._imagen(detalle, "poster_path", IMAGE_BASE),
            backdrop_url=self._imagen(detalle, "backdrop_path", BACKDROP_BASE),
            clasificacion=self._certificacion_serie(detalle),
            num_temporadas=detalle.get("number_of_seasons") or 1,
            num_episodios=detalle.get("number_of_episodes") or 1,
            en_emision=bool(detalle.get("in_production")),
        )
        serie.generos.set(
            [generos[g["id"]] for g in detalle.get("genres", []) if g["id"] in generos]
        )
        return True

    def _certificacion_serie(self, detalle):
        resultados = (detalle.get("content_ratings") or {}).get("results", [])
        for pais in ("CO", "ES", "US"):
            for entrada in resultados:
                if entrada.get("iso_3166_1") == pais:
                    certificacion = (entrada.get("rating") or "").strip()
                    if certificacion:
                        return certificacion[:10]
        return ""
