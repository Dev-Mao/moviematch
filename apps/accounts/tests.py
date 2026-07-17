"""Pruebas de las reglas de negocio de cuentas, preferencias y amistades."""

from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.accounts.models import Amistad, Perfil, Preferencia
from apps.catalog.models import Genero


class PerfilTest(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user(
            username="mariana", password="clave-de-prueba", first_name="Mariana", last_name="Agudelo"
        )
        self.perfil = Perfil.objects.create(usuario=self.usuario, alias="marianaa")

    def test_alias_unico(self):
        otro = User.objects.create_user(username="ana", password="clave-de-prueba")

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Perfil.objects.create(usuario=otro, alias="marianaa")

    def test_iniciales_a_partir_del_nombre(self):
        self.assertEqual(self.perfil.iniciales, "MA")

    def test_solo_las_cuentas_activas_pueden_iniciar_sesion(self):
        """FE-02 del CU-02: una cuenta suspendida no puede acceder."""
        self.assertTrue(self.perfil.puede_iniciar_sesion)

        self.perfil.estado = Perfil.Estado.SUSPENDIDO
        self.assertFalse(self.perfil.puede_iniciar_sesion)


class PreferenciaTest(TestCase):
    def setUp(self):
        usuario = User.objects.create_user(username="mariana", password="clave-de-prueba")
        self.perfil = Perfil.objects.create(usuario=usuario, alias="marianaa")
        self.drama = Genero.objects.create(nombre="Drama", slug="drama")

    def test_preferencia_unica_por_perfil_y_genero(self):
        Preferencia.objects.create(perfil=self.perfil, genero=self.drama, nivel_interes=5)

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Preferencia.objects.create(perfil=self.perfil, genero=self.drama, nivel_interes=3)


class AmistadTest(TestCase):
    def setUp(self):
        self.mariana = User.objects.create_user(username="mariana", password="clave-de-prueba")
        self.ana = User.objects.create_user(username="ana", password="clave-de-prueba")
        self.luis = User.objects.create_user(username="luis", password="clave-de-prueba")

    def test_amistad_unica_entre_dos_usuarios(self):
        """RN-09: no se puede duplicar una solicitud entre los mismos usuarios."""
        Amistad.objects.create(solicitante=self.mariana, destinatario=self.ana)

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Amistad.objects.create(solicitante=self.mariana, destinatario=self.ana)

    def test_no_se_permite_la_amistad_consigo_mismo(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Amistad.objects.create(solicitante=self.mariana, destinatario=self.mariana)

    def test_aceptar_registra_la_fecha(self):
        amistad = Amistad.objects.create(solicitante=self.mariana, destinatario=self.ana)
        self.assertIsNone(amistad.fecha_aceptacion)

        amistad.aceptar()

        amistad.refresh_from_db()
        self.assertEqual(amistad.estado, Amistad.Estado.ACEPTADA)
        self.assertIsNotNone(amistad.fecha_aceptacion)

    def test_rechazar_no_registra_fecha_de_aceptacion(self):
        amistad = Amistad.objects.create(solicitante=self.mariana, destinatario=self.ana)

        amistad.rechazar()

        amistad.refresh_from_db()
        self.assertEqual(amistad.estado, Amistad.Estado.RECHAZADA)
        self.assertIsNone(amistad.fecha_aceptacion)

    def test_otro_usuario_devuelve_el_extremo_contrario(self):
        amistad = Amistad.objects.create(solicitante=self.mariana, destinatario=self.ana)

        self.assertEqual(amistad.otro_usuario(self.mariana), self.ana)
        self.assertEqual(amistad.otro_usuario(self.ana), self.mariana)

    def test_filtro_de_amistades_aceptadas_de_un_usuario(self):
        Amistad.objects.create(
            solicitante=self.mariana, destinatario=self.ana, estado=Amistad.Estado.ACEPTADA
        )
        Amistad.objects.create(
            solicitante=self.luis, destinatario=self.mariana, estado=Amistad.Estado.PENDIENTE
        )

        aceptadas = Amistad.objects.de_usuario(self.mariana).aceptadas()

        self.assertEqual(aceptadas.count(), 1)
        self.assertEqual(aceptadas.first().otro_usuario(self.mariana), self.ana)
