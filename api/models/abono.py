from django.db import models

from .linea_negocio import LineaNegocio
from .metodo_pago import MetodoPago
from .renta import Renta


class Abono(models.Model):
    renta = models.ForeignKey(
        Renta,
        on_delete=models.CASCADE,
        related_name="abonos",
    )
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    metodo_pago = models.CharField(max_length=20, choices=MetodoPago.choices)
    pago_efectivo_mxn = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    pago_efectivo_usd = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    monto_mxn = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Equivalente en pesos para saldo y corte.",
    )
    linea_negocio = models.CharField(
        max_length=20,
        choices=LineaNegocio.choices,
        default=LineaNegocio.TRAJES,
        db_index=True,
    )
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["creado_en", "id"]
        verbose_name = "abono"
        verbose_name_plural = "abonos"

    def __str__(self) -> str:
        return f"Abono #{self.pk} — Renta #{self.renta_id} (${self.monto_mxn})"
