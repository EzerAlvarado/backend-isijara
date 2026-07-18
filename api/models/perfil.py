from django.conf import settings
from django.db import models

from .linea_negocio import LineaNegocio
from .renta import Renta


class PerfilUsuario(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="perfil",
    )
    linea_negocio = models.CharField(
        max_length=20,
        choices=LineaNegocio.choices,
    )
    perfil_vestido = models.CharField(
        max_length=20,
        choices=Renta.CategoriaVestido.choices,
        blank=True,
        null=True,
        help_text="Solo línea vestidos: categoría asignada al usuario.",
    )

    class Meta:
        verbose_name = "perfil de usuario"
        verbose_name_plural = "perfiles de usuario"

    def __str__(self) -> str:
        return f"{self.user.username} ({self.get_linea_negocio_display()})"
