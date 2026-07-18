from django.db import models

from .linea_negocio import LineaNegocio
from .metodo_pago import MetodoPago


class Transaccion(models.Model):
    timestamp = models.DateTimeField()
    referencia = models.CharField(max_length=80, unique=True)
    cliente = models.CharField(max_length=200)
    pago = models.CharField(max_length=20, choices=MetodoPago.choices)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    linea_negocio = models.CharField(
        max_length=20,
        choices=LineaNegocio.choices,
        default=LineaNegocio.TRAJES,
        db_index=True,
    )
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]
        verbose_name = "transacción"
        verbose_name_plural = "transacciones"

    def __str__(self) -> str:
        return f"{self.referencia} — {self.cliente} (${self.monto})"
