"""Modelos de cuentas: perfil, preferencias y relaciones de amistad.

El Usuario del modelo de dominio se implementa con el modelo User de Django,
extendido con un Perfil en relación 1 a 1. El Administrador del dominio se
representa con User.is_staff y el nivel de acceso del perfil.
"""

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from apps.catalog.models import Genero


class Perfil(models.Model):
    """Datos de personalización del usuario."""

    class Estado(models.TextChoices):
        ACTIVO = "ACTIVO", "Activo"
        INACTIVO = "INACTIVO", "Inactivo"
        SUSPENDIDO = "SUSPENDIDO", "Suspendido"

    class NivelAcceso(models.TextChoices):
        MODERADOR = "MODERADOR", "Moderador"
        SUPERADMIN = "SUPERADMIN", "Superadministrador"

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="perfil",
        verbose_name="usuario",
    )
    alias = models.CharField("alias", max_length=50, unique=True)
    avatar_url = models.URLField("URL del avatar", blank=True)
    biografia = models.TextField("biografía", blank=True)
    estado = models.CharField(
        "estado", max_length=12, choices=Estado.choices, default=Estado.ACTIVO
    )
    nivel_acceso = models.CharField(
        "nivel de acceso",
        max_length=12,
        choices=NivelAcceso.choices,
        blank=True,
        help_text="Solo aplica a los administradores.",
    )
    generos = models.ManyToManyField(
        Genero,
        through="Preferencia",
        related_name="perfiles",
        verbose_name="géneros preferidos",
    )

    class Meta:
        verbose_name = "perfil"
        verbose_name_plural = "perfiles"

    def __str__(self):
        return f"@{self.alias}"

    @property
    def iniciales(self):
        nombre = (self.usuario.get_full_name() or self.usuario.username).strip()
        partes = [p for p in nombre.split() if p]
        if not partes:
            return "?"
        if len(partes) == 1:
            return partes[0][:2].upper()
        return (partes[0][0] + partes[-1][0]).upper()

    @property
    def puede_iniciar_sesion(self):
        """FE-02 del CU-02: solo las cuentas activas pueden acceder."""
        return self.estado == self.Estado.ACTIVO


class Preferencia(models.Model):
    """Asociación entre un perfil y un género, con su peso de interés."""

    perfil = models.ForeignKey(
        Perfil, on_delete=models.CASCADE, related_name="preferencias", verbose_name="perfil"
    )
    genero = models.ForeignKey(
        Genero, on_delete=models.CASCADE, related_name="preferencias", verbose_name="género"
    )
    nivel_interes = models.PositiveSmallIntegerField(
        "nivel de interés",
        default=3,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="RN-04: pondera el algoritmo de recomendación (1 a 5).",
    )

    class Meta:
        verbose_name = "preferencia"
        verbose_name_plural = "preferencias"
        constraints = [
            models.UniqueConstraint(
                fields=["perfil", "genero"], name="preferencia_unica_por_perfil_y_genero"
            )
        ]

    def __str__(self):
        return f"{self.perfil} → {self.genero} ({self.nivel_interes})"


class AmistadQuerySet(models.QuerySet):
    def aceptadas(self):
        return self.filter(estado=Amistad.Estado.ACEPTADA)

    def de_usuario(self, usuario):
        return self.filter(models.Q(solicitante=usuario) | models.Q(destinatario=usuario))


class Amistad(models.Model):
    """Relación social entre dos usuarios."""

    class Estado(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        ACEPTADA = "ACEPTADA", "Aceptada"
        RECHAZADA = "RECHAZADA", "Rechazada"
        BLOQUEADA = "BLOQUEADA", "Bloqueada"

    solicitante = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="amistades_enviadas",
        verbose_name="solicitante",
    )
    destinatario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="amistades_recibidas",
        verbose_name="destinatario",
    )
    estado = models.CharField(
        "estado", max_length=10, choices=Estado.choices, default=Estado.PENDIENTE
    )
    fecha_solicitud = models.DateTimeField("fecha de solicitud", auto_now_add=True)
    fecha_aceptacion = models.DateTimeField("fecha de aceptación", null=True, blank=True)

    objects = AmistadQuerySet.as_manager()

    class Meta:
        verbose_name = "amistad"
        verbose_name_plural = "amistades"
        constraints = [
            # RN-09: una amistad es única entre dos usuarios.
            models.UniqueConstraint(
                fields=["solicitante", "destinatario"], name="amistad_unica_entre_usuarios"
            ),
            models.CheckConstraint(
                condition=~models.Q(solicitante=models.F("destinatario")),
                name="amistad_sin_auto_referencia",
            ),
        ]

    def __str__(self):
        return f"{self.solicitante} → {self.destinatario} ({self.get_estado_display()})"

    def aceptar(self):
        self.estado = self.Estado.ACEPTADA
        self.fecha_aceptacion = timezone.now()
        self.save(update_fields=["estado", "fecha_aceptacion"])

    def rechazar(self):
        self.estado = self.Estado.RECHAZADA
        self.save(update_fields=["estado"])

    def otro_usuario(self, usuario):
        """Devuelve el extremo de la amistad que no es el usuario dado."""
        return self.destinatario if self.solicitante_id == usuario.id else self.solicitante
