"""Crea los datos de demostración: usuarios, preferencias, amistades y valoraciones.

Es idempotente y determinista (usa una semilla fija), así que puede ejecutarse
varias veces sin duplicar información y siempre produce el mismo resultado.

Uso:
    python manage.py seed_demo
"""

import random

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import Amistad, Perfil, Preferencia
from apps.catalog.models import ContenidoAudiovisual, Genero
from apps.lists.models import ListaDeRecomendaciones
from apps.ratings.models import Valoracion

SEMILLA = 2026
PASSWORD_DEMO = "moviematch2026"

# El primer usuario es la cuenta principal de demostración.
USUARIOS = [
    ("mariana", "Mariana", "Agudelo", "mariana@moviematch.co", "marianaa",
     "Cinéfila de hueso colorado. Amante del sci-fi y los dramas de autor."),
    ("ana", "Ana", "García", "ana@moviematch.co", "anag",
     "Del cine de autor a los blockbusters, todo cabe."),
    ("luis", "Luis", "Rojas", "luis@moviematch.co", "luisr",
     "Thrillers y policiacas, entre más giros mejor."),
    ("sofia", "Sofía", "Mejía", "sofia@moviematch.co", "sofim",
     "La animación también es para adultos."),
    ("diego", "Diego", "Vega", "diego@moviematch.co", "diegov",
     "Acción y ciencia ficción, sin culpa."),
    ("valentina", "Valentina", "Castro", "valentina@moviematch.co", "valen",
     "Documentales y cine histórico."),
    ("nicolas", "Nicolás", "Peña", "nicolas@moviematch.co", "nicop",
     "Comedias para desconectar."),
    ("maria", "María", "Restrepo", "maria@moviematch.co", "mariar",
     "Recién llegada a MovieMatch."),
    ("julian", "Julián", "Torres", "julian@moviematch.co", "juliant",
     "Buscando qué ver esta noche."),
]

# Géneros preferidos por usuario (se emparejan por nombre con el catálogo).
PREFERENCIAS = {
    "mariana": ["Ciencia ficción", "Drama", "Crimen", "Animación"],
    "ana": ["Drama", "Romance", "Aventura"],
    "luis": ["Crimen", "Suspense", "Misterio"],
    "sofia": ["Animación", "Familia", "Fantasía"],
    "diego": ["Acción", "Ciencia ficción", "Aventura"],
    "valentina": ["Documental", "Historia", "Drama"],
    "nicolas": ["Comedia", "Familia"],
    "maria": ["Drama", "Terror"],
    "julian": ["Acción", "Comedia"],
}


class Command(BaseCommand):
    help = "Crea usuarios de demostración con preferencias, amistades y valoraciones."

    @transaction.atomic
    def handle(self, *args, **options):
        aleatorio = random.Random(SEMILLA)

        if not ContenidoAudiovisual.objects.exists():
            self.stdout.write(
                self.style.WARNING(
                    "El catálogo está vacío. Ejecuta primero: "
                    "python manage.py loaddata fixtures/catalogo.json"
                )
            )
            return

        perfiles = self._crear_usuarios()
        self.stdout.write(self.style.SUCCESS(f"  {len(perfiles)} usuarios listos"))

        n_prefs = self._crear_preferencias(perfiles)
        self.stdout.write(self.style.SUCCESS(f"  {n_prefs} preferencias asignadas"))

        n_amistades = self._crear_amistades(perfiles)
        self.stdout.write(self.style.SUCCESS(f"  {n_amistades} amistades creadas"))

        n_valoraciones = self._crear_valoraciones(perfiles, aleatorio)
        self.stdout.write(self.style.SUCCESS(f"  {n_valoraciones} valoraciones registradas"))

        n_listas = self._crear_listas(perfiles, aleatorio)
        self.stdout.write(self.style.SUCCESS(f"  {n_listas} listas creadas"))

        self._crear_administrador()
        self.stdout.write(self.style.SUCCESS("  administrador listo"))

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Datos de demostración creados."))
        self.stdout.write(f"  Usuario principal: mariana / {PASSWORD_DEMO}")
        self.stdout.write(f"  Administrador:     admin / {PASSWORD_DEMO}")

    # -------------------------------------------------------------- Usuarios

    def _crear_usuarios(self):
        perfiles = {}
        for username, nombre, apellido, email, alias, bio in USUARIOS:
            usuario, creado = User.objects.get_or_create(
                username=username,
                defaults={"first_name": nombre, "last_name": apellido, "email": email},
            )
            if creado:
                usuario.set_password(PASSWORD_DEMO)
                usuario.save(update_fields=["password"])
            perfil, _ = Perfil.objects.get_or_create(
                usuario=usuario, defaults={"alias": alias, "biografia": bio}
            )
            perfiles[username] = perfil
        return perfiles

    def _crear_administrador(self):
        admin, creado = User.objects.get_or_create(
            username="admin",
            defaults={
                "first_name": "Administrador",
                "last_name": "MovieMatch",
                "email": "admin@moviematch.co",
                "is_staff": True,
                "is_superuser": True,
            },
        )
        if creado:
            admin.set_password(PASSWORD_DEMO)
            admin.save(update_fields=["password"])
        Perfil.objects.get_or_create(
            usuario=admin,
            defaults={
                "alias": "admin",
                "biografia": "Cuenta de administración del sistema.",
                "nivel_acceso": Perfil.NivelAcceso.SUPERADMIN,
            },
        )

    # ---------------------------------------------------------- Preferencias

    def _crear_preferencias(self, perfiles):
        total = 0
        for username, nombres_genero in PREFERENCIAS.items():
            perfil = perfiles[username]
            for posicion, nombre in enumerate(nombres_genero):
                genero = Genero.objects.filter(nombre=nombre).first()
                if not genero:
                    continue
                # El primer género declarado es el de mayor interés.
                nivel = max(5 - posicion, 2)
                _, creado = Preferencia.objects.get_or_create(
                    perfil=perfil, genero=genero, defaults={"nivel_interes": nivel}
                )
                total += int(creado)
        return total

    # ------------------------------------------------------------ Amistades

    def _crear_amistades(self, perfiles):
        aceptadas = [("mariana", "ana"), ("mariana", "luis"), ("mariana", "sofia"),
                     ("mariana", "diego"), ("mariana", "valentina"), ("mariana", "nicolas"),
                     ("ana", "luis"), ("sofia", "diego"), ("ana", "sofia")]
        pendientes = [("maria", "mariana"), ("julian", "mariana")]

        total = 0
        for origen, destino in aceptadas:
            amistad, creado = Amistad.objects.get_or_create(
                solicitante=perfiles[origen].usuario,
                destinatario=perfiles[destino].usuario,
                defaults={
                    "estado": Amistad.Estado.ACEPTADA,
                    "fecha_aceptacion": timezone.now(),
                },
            )
            total += int(creado)

        for origen, destino in pendientes:
            _, creado = Amistad.objects.get_or_create(
                solicitante=perfiles[origen].usuario,
                destinatario=perfiles[destino].usuario,
                defaults={"estado": Amistad.Estado.PENDIENTE},
            )
            total += int(creado)
        return total

    # ---------------------------------------------------------- Valoraciones

    def _crear_valoraciones(self, perfiles, aleatorio):
        contenidos = list(ContenidoAudiovisual.objects.prefetch_related("generos"))
        total = 0

        for username, perfil in perfiles.items():
            favoritos = set(PREFERENCIAS.get(username, []))
            # Cada usuario valora entre 12 y 22 contenidos.
            muestra = aleatorio.sample(contenidos, aleatorio.randint(12, 22))
            for contenido in muestra:
                generos = {g.nombre for g in contenido.generos.all()}
                # Puntúa más alto lo que coincide con sus géneros preferidos.
                if generos & favoritos:
                    puntuacion = aleatorio.choice([4, 4, 5, 5, 5])
                else:
                    puntuacion = aleatorio.choice([2, 3, 3, 4])
                _, creado = Valoracion.objects.get_or_create(
                    usuario=perfil.usuario,
                    contenido=contenido,
                    defaults={"puntuacion": puntuacion},
                )
                total += int(creado)
        return total

    # ---------------------------------------------------------------- Listas

    def _crear_listas(self, perfiles, aleatorio):
        definiciones = [
            ("mariana", "Para maratón de finde", "Lo que tengo pendiente para el sábado.", True),
            ("mariana", "Sci-fi imperdibles", "Ciencia ficción que hay que ver al menos una vez.", False),
            ("ana", "Dramas que duelen", "Para llorar con ganas.", True),
            ("sofia", "Animación para todas las edades", "No solo para niños.", True),
        ]
        contenidos = list(ContenidoAudiovisual.objects.all())
        total = 0
        for username, nombre, descripcion, publica in definiciones:
            lista, creado = ListaDeRecomendaciones.objects.get_or_create(
                propietario=perfiles[username].usuario,
                nombre=nombre,
                defaults={"descripcion": descripcion, "es_publica": publica},
            )
            if creado:
                lista.contenidos.set(aleatorio.sample(contenidos, aleatorio.randint(5, 12)))
                if not publica:
                    lista.compartida_con.set([perfiles["ana"].usuario, perfiles["luis"].usuario])
                total += 1
        return total
