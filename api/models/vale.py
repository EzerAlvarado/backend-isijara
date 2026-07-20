from django.db import models

from .linea_negocio import LineaNegocio
from .metodo_pago import MetodoPago
from .renta import Renta
from .transaccion import Transaccion


class Vale(models.Model):
    class Estatus(models.TextChoices):
        PENDIENTE = "pendiente", "Pendiente"
        REPUSTO = "repuesto", "Repuesto"

    fecha = models.DateField()
    concepto = models.CharField(max_length=200)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    pago = models.CharField(max_length=20, choices=MetodoPago.choices, default=MetodoPago.PESOS)
    monto_mxn = models.DecimalField(max_digits=10, decimal_places=2)
    estatus = models.CharField(
        max_length=20,
        choices=Estatus.choices,
        default=Estatus.PENDIENTE,
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
        help_text="Solo vestidos: noche, quince o boda.",
    )
    transaccion = models.OneToOneField(
        Transaccion,
        on_delete=models.CASCADE,
        related_name="vale",
        null=True,
        blank=True,
    )
    repuesto_en = models.DateTimeField(null=True, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha", "-creado_en"]
        verbose_name = "vale"
        verbose_name_plural = "vales"

    def __str__(self) -> str:
        return f"Vale {self.concepto} — ${self.monto_mxn} ({self.estatus})"
