from django.db import models

from .prenda import Prenda
from .renta import Renta


class Devolucion(models.Model):
    class Estatus(models.TextChoices):
        REVISAR_SALIDA = "revisar_salida", "Revisar si salió"
        AFUERA = "afuera", "Afuera"
        RETRASADO = "retrasado", "Retrasado"
        REGRESADO = "regresado", "Regresado"

    renta = models.ForeignKey(
        Renta,
        on_delete=models.CASCADE,
        related_name="devoluciones",
    )
    cliente = models.CharField(max_length=200)
    prenda = models.ForeignKey(
        Prenda,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="devoluciones",
    )
    prenda_nombre = models.CharField(max_length=200)
    cantidad = models.PositiveIntegerField(default=1)
    estatus = models.CharField(max_length=24, choices=Estatus.choices)
    fecha_limite = models.DateField()
    penalizacion = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    multa_perdonada = models.BooleanField(default=False)
    cargo_danos = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    nota_danos = models.TextField(blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["fecha_limite", "-id"]
        verbose_name = "devolución"
        verbose_name_plural = "devoluciones"

    def __str__(self) -> str:
        return f"Devolución {self.cliente} — {self.prenda_nombre}"
