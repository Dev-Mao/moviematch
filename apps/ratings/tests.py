"""Pruebas de las reglas de negocio de las valoraciones (CU-04)."""

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.catalog.models import Pelicula
from apps.ratings.models import Valoracion


class ValoracionTest(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user(username="mariana", password="clave-de-prueba")
        self.otro = User.objects.create_user(username="ana", password="clave-de-prueba")
        self.pelicula = Pelicula.objects.create(
            titulo="Cadena perpetua", anio_estreno=1994, duracion_min=143
        )

    def test_valoracion_unica_por_usuario_y_contenido(self):
        """RN-06: un usuario solo tiene una valoración vigente por contenido."""
        Valoracion.objects.create(usuario=self.usuario, contenido=self.pelicula, puntuacion=5)

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Valoracion.objects.create(
                    usuario=self.usuario, contenido=self.pelicula, puntuacion=3
                )

    def test_usuarios_distintos_pueden_valorar_el_mismo_contenido(self):
        Valoracion.objects.create(usuario=self.usuario, contenido=self.pelicula, puntuacion=5)
        Valoracion.objects.create(usuario=self.otro, contenido=self.pelicula, puntuacion=4)

        self.assertEqual(self.pelicula.valoraciones.count(), 2)

    def test_la_base_de_datos_rechaza_puntuaciones_fuera_de_rango(self):
        """RN-05: la puntuación debe estar entre 1 y 5."""
        for puntuacion in (0, 6):
            with self.subTest(puntuacion=puntuacion):
                with self.assertRaises(IntegrityError):
                    with transaction.atomic():
                        Valoracion.objects.create(
                            usuario=self.usuario, contenido=self.pelicula, puntuacion=puntuacion
                        )

    def test_la_validacion_del_modelo_rechaza_puntuaciones_fuera_de_rango(self):
        """FE-01 del CU-04: el formulario debe rechazar un valor fuera de 1 a 5."""
        valoracion = Valoracion(usuario=self.usuario, contenido=self.pelicula, puntuacion=9)

        with self.assertRaises(ValidationError):
            valoracion.full_clean()

    def test_editar_una_valoracion_no_crea_una_nueva(self):
        """FA-01 del CU-04: editar actualiza la valoración existente."""
        valoracion = Valoracion.objects.create(
            usuario=self.usuario, contenido=self.pelicula, puntuacion=3
        )

        valoracion.puntuacion = 5
        valoracion.save()

        self.assertEqual(Valoracion.objects.filter(usuario=self.usuario).count(), 1)
        self.assertEqual(Valoracion.objects.get(pk=valoracion.pk).puntuacion, 5)

    def test_promedio_de_valoraciones_del_contenido(self):
        Valoracion.objects.create(usuario=self.usuario, contenido=self.pelicula, puntuacion=5)
        Valoracion.objects.create(usuario=self.otro, contenido=self.pelicula, puntuacion=4)

        self.assertEqual(self.pelicula.promedio_valoraciones, 4.5)
