"""Formularios de registro, acceso y perfil."""

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

from apps.catalog.models import Genero

from .models import Perfil, Preferencia


class RegistroForm(UserCreationForm):
    """CU-01: alta de una cuenta nueva."""

    first_name = forms.CharField(label="Nombre", max_length=60)
    last_name = forms.CharField(label="Apellido", max_length=60)
    email = forms.EmailField(label="Correo electrónico")
    alias = forms.CharField(label="Alias", max_length=50, help_text="Así te encontrarán tus amigos.")
    acepta_terminos = forms.BooleanField(
        label="Acepto los Términos y la Política de tratamiento de datos (GDPR)."
    )

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "alias", "password1", "password2"]

    def clean_email(self):
        """RN-01: el correo electrónico es único en el sistema."""
        email = self.cleaned_data["email"].lower().strip()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "Ya existe una cuenta con este correo. ¿Quieres iniciar sesión?"
            )
        return email

    def clean_alias(self):
        alias = self.cleaned_data["alias"].strip()
        if Perfil.objects.filter(alias__iexact=alias).exists():
            raise forms.ValidationError("Este alias ya está en uso, elige otro.")
        return alias

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.email = self.cleaned_data["email"]
        # El nombre de usuario se deriva del alias para no pedir un campo extra.
        usuario.username = self.cleaned_data["alias"]
        usuario.save()
        Perfil.objects.create(usuario=usuario, alias=self.cleaned_data["alias"])
        return usuario


class LoginForm(AuthenticationForm):
    """CU-02: inicio de sesión."""

    username = forms.CharField(label="Alias o correo electrónico")

    error_messages = {
        **AuthenticationForm.error_messages,
        # FE-01: no se revela cuál de los dos campos falló.
        "invalid_login": "Las credenciales no son válidas. Revisa tus datos e inténtalo de nuevo.",
    }

    def clean_username(self):
        """Permite iniciar sesión indistintamente con el alias o con el correo."""
        identificador = self.cleaned_data["username"].strip()
        if "@" in identificador:
            usuario = User.objects.filter(email__iexact=identificador).first()
            if usuario:
                return usuario.username
        return identificador

    def confirm_login_allowed(self, user):
        """FE-02: una cuenta suspendida o inactiva no puede acceder."""
        super().confirm_login_allowed(user)
        perfil = getattr(user, "perfil", None)
        if perfil and not perfil.puede_iniciar_sesion:
            raise forms.ValidationError(
                f"Tu cuenta está {perfil.get_estado_display().lower()}. "
                "Contacta al administrador para más información.",
                code="cuenta_no_activa",
            )


class PerfilForm(forms.ModelForm):
    """CU-03: edición de los datos del perfil."""

    first_name = forms.CharField(label="Nombre", max_length=60)
    last_name = forms.CharField(label="Apellido", max_length=60)

    class Meta:
        model = Perfil
        fields = ["alias", "avatar_url", "biografia"]
        labels = {"avatar_url": "URL del avatar", "biografia": "Biografía"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["first_name"].initial = self.instance.usuario.first_name
            self.fields["last_name"].initial = self.instance.usuario.last_name

    def clean_alias(self):
        alias = self.cleaned_data["alias"].strip()
        existentes = Perfil.objects.filter(alias__iexact=alias)
        if self.instance.pk:
            existentes = existentes.exclude(pk=self.instance.pk)
        if existentes.exists():
            raise forms.ValidationError("Este alias ya está en uso, elige otro.")
        return alias

    def save(self, commit=True):
        perfil = super().save(commit=False)
        usuario = perfil.usuario
        usuario.first_name = self.cleaned_data["first_name"]
        usuario.last_name = self.cleaned_data["last_name"]
        if commit:
            usuario.save(update_fields=["first_name", "last_name"])
            perfil.save()
        return perfil


class PreferenciasForm(forms.Form):
    """CU-03: selección de los géneros favoritos."""

    generos = forms.ModelMultipleChoiceField(
        queryset=Genero.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Géneros favoritos",
    )

    def __init__(self, *args, perfil=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.perfil = perfil
        if perfil and not self.is_bound:
            self.fields["generos"].initial = perfil.generos.all()

    def save(self):
        """Sincroniza las preferencias conservando el nivel de interés existente."""
        seleccionados = self.cleaned_data["generos"]
        actuales = {p.genero_id: p for p in self.perfil.preferencias.all()}

        for genero in seleccionados:
            if genero.id not in actuales:
                Preferencia.objects.create(perfil=self.perfil, genero=genero)

        ids_seleccionados = {g.id for g in seleccionados}
        for genero_id, preferencia in actuales.items():
            if genero_id not in ids_seleccionados:
                preferencia.delete()
        return seleccionados
