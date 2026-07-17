"""Pruebas del motor de recomendaciones (CU-05)."""

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from apps.accounts.models import Amistad, Perfil, Preferencia
from apps.catalog.models import ContenidoAudiovisual, Genero, Pelicula
from apps.ratings.models import Valoracion
from apps.recommendations.models import Recomendacion
from apps.recommendations.services import MotorDeRecomendaciones


class MotorDeRecomendacionesTest(TestCase):
    def setUp(self):
        self.drama = Genero.objects.create(nombre="Drama", slug="drama")
        self.terror = Genero.objects.create(nombre="Terror", slug="terror")

        self.usuario = self._crear_usuario("mariana")
        self.amigo = self._crear_usuario("ana")
        self.desconocido = self._crear_usuario("julian")

        self.drama_1 = self._crear_pelicula("Drama uno", self.drama)
        self.drama_2 = self._crear_pelicula("Drama dos", self.drama)
        self.terror_1 = self._crear_pelicula("Terror uno", self.terror)

    # ------------------------------------------------------------- Utilidades

    def _crear_usuario(self, username):
        usuario = User.objects.create_user(username=username, password="clave-de-prueba")
        Perfil.objects.create(usuario=usuario, alias=username)
        return usuario

    def _crear_pelicula(self, titulo, *generos):
        pelicula = Pelicula.objects.create(titulo=titulo, anio_estreno=2020, duracion_min=100)
        pelicula.generos.set(generos)
        return pelicula

    def _hacer_amigos(self, uno, otro):
        return Amistad.objects.create(
            solicitante=uno,
            destinatario=otro,
            estado=Amistad.Estado.ACEPTADA,
            fecha_aceptacion=timezone.now(),
        )

    # ---------------------------------------------------------------- Pruebas

    def test_arranque_en_frio_recomienda_por_popularidad(self):
        """FA-01: sin historial ni preferencias, recomienda lo popular."""
        Valoracion.objects.create(usuario=self.amigo, contenido=self.drama_1, puntuacion=5)
        Valoracion.objects.create(usuario=self.desconocido, contenido=self.drama_1, puntuacion=5)

        recomendaciones = MotorDeRecomendaciones(self.usuario).generar()

        self.assertTrue(recomendaciones)
        # Se compara por identificador: en herencia multi-tabla, una instancia de
        # ContenidoAudiovisual y una de Pelicula con el mismo id no son iguales.
        self.assertEqual(recomendaciones[0].contenido_id, self.drama_1.id)
        self.assertEqual(recomendaciones[0].origen, Recomendacion.Origen.POPULARIDAD)

    def test_no_recomienda_contenido_ya_valorado(self):
        """El usuario no debe recibir lo que ya valoró."""
        Valoracion.objects.create(usuario=self.usuario, contenido=self.drama_1, puntuacion=4)

        recomendaciones = MotorDeRecomendaciones(self.usuario).generar()

        recomendados = {r.contenido_id for r in recomendaciones}
        self.assertNotIn(self.drama_1.id, recomendados)

    def test_no_recomienda_contenido_retirado(self):
        """RN-13: el contenido retirado no aparece en las recomendaciones."""
        Preferencia.objects.create(perfil=self.usuario.perfil, genero=self.drama, nivel_interes=5)
        self.drama_1.estado = ContenidoAudiovisual.Estado.RETIRADO
        self.drama_1.save(update_fields=["estado"])

        recomendaciones = MotorDeRecomendaciones(self.usuario).generar()

        recomendados = {r.contenido_id for r in recomendaciones}
        self.assertNotIn(self.drama_1.id, recomendados)
        self.assertIn(self.drama_2.id, recomendados)

    def test_las_preferencias_priorizan_el_genero_favorito(self):
        """RN-04: el nivel de interés pondera el resultado."""
        Preferencia.objects.create(perfil=self.usuario.perfil, genero=self.drama, nivel_interes=5)

        recomendaciones = MotorDeRecomendaciones(self.usuario).generar()

        self.assertEqual(recomendaciones[0].origen, Recomendacion.Origen.PREFERENCIAS)
        self.assertIn(self.drama, recomendaciones[0].contenido.generos.all())

    def test_solo_influyen_las_amistades_aceptadas(self):
        """RN-07: una solicitud pendiente no debe influir en las recomendaciones."""
        Amistad.objects.create(
            solicitante=self.usuario,
            destinatario=self.desconocido,
            estado=Amistad.Estado.PENDIENTE,
        )
        Valoracion.objects.create(usuario=self.desconocido, contenido=self.terror_1, puntuacion=5)

        recomendaciones = MotorDeRecomendaciones(self.usuario).generar()

        origenes = {r.contenido_id: r.origen for r in recomendaciones}
        self.assertNotEqual(origenes.get(self.terror_1.id), Recomendacion.Origen.AMIGOS)

    def test_las_valoraciones_de_amigos_generan_recomendaciones(self):
        """RN-07: lo que valoran los amigos aceptados sí influye."""
        self._hacer_amigos(self.usuario, self.amigo)
        Valoracion.objects.create(usuario=self.amigo, contenido=self.terror_1, puntuacion=5)

        recomendaciones = MotorDeRecomendaciones(self.usuario).generar()

        por_contenido = {r.contenido_id: r for r in recomendaciones}
        self.assertIn(self.terror_1.id, por_contenido)
        self.assertEqual(por_contenido[self.terror_1.id].origen, Recomendacion.Origen.AMIGOS)
        self.assertIn("amigo", por_contenido[self.terror_1.id].motivo)

    def test_regenerar_reemplaza_las_recomendaciones_anteriores(self):
        """CU-03 paso 5: al cambiar las preferencias se recalculan las recomendaciones."""
        motor = MotorDeRecomendaciones(self.usuario)
        Valoracion.objects.create(usuario=self.amigo, contenido=self.drama_1, puntuacion=5)
        Valoracion.objects.create(usuario=self.desconocido, contenido=self.drama_1, puntuacion=5)
        motor.generar()
        primera_cantidad = Recomendacion.objects.filter(usuario=self.usuario).count()

        motor.generar()

        self.assertEqual(
            Recomendacion.objects.filter(usuario=self.usuario).count(), primera_cantidad
        )

    def test_una_recomendacion_por_usuario_y_contenido(self):
        """No deben duplicarse recomendaciones para el mismo contenido."""
        Preferencia.objects.create(perfil=self.usuario.perfil, genero=self.drama, nivel_interes=5)

        recomendaciones = MotorDeRecomendaciones(self.usuario).generar()

        contenidos = [r.contenido_id for r in recomendaciones]
        self.assertEqual(len(contenidos), len(set(contenidos)))
