from decimal import Decimal

from django.db import models

from .linea_negocio import LineaNegocio
from .renta import Renta


class TurnoCorte(models.TextChoices):
    MANANA = "manana", "Mañana"
    TARDE = "tarde", "Tarde"


class CorteDia(models.Model):
    fecha = models.DateField()
    turno = models.CharField(
        max_length=10,
        choices=TurnoCorte.choices,
        default=TurnoCorte.MANANA,
        db_index=True,
    )
    linea_negocio = models.CharField(
        max_length=20,
        choices=LineaNegocio.choices,
        default=LineaNegocio.TRAJES,
        db_index=True,
    )
    categoria_vestido = models.CharField(
        max_length=20,
        choices=Renta.CategoriaVestido.choices,
        blank=True,
        null=True,
        db_index=True,
        help_text="Solo vestidos: noche, quince o boda. Null para trajes.",
    )
    fondo_inicial = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("2732.00"),
    )
    conteo_fondo = models.JSONField(default=dict, blank=True)
    conteo_caja = models.JSONField(default=dict, blank=True)
    conteo_fisico = models.JSONField(default=dict, blank=True)
    cerrado = models.BooleanField(default=False)
    cerrado_en = models.DateTimeField(null=True, blank=True)
    empleado_corte = models.CharField(
        max_length=120,
        blank=True,
        default="",
        help_text="Nombre del empleado que realizó el cierre de caja.",
    )
    omitido = models.BooleanField(
        default=False,
        help_text="Turno de mañana cerrado automáticamente al hacer corte de tarde.",
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-fecha"]
        verbose_name = "corte del día"
        verbose_name_plural = "cortes del día"
        constraints = [
            models.UniqueConstraint(
                fields=["fecha", "linea_negocio", "turno", "categoria_vestido"],
                name="unique_corte_fecha_linea_turno_categoria",
            ),
        ]

    def __str__(self) -> str:
        estado = "cerrado" if self.cerrado else "abierto"
        turno = self.get_turno_display()
        return f"Corte {self.fecha} {turno} ({estado})"
