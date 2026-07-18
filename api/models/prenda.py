from django.db import models

from .linea_negocio import LineaNegocio


class Prenda(models.Model):
    class Estatus(models.TextChoices):
        RENTADO = "rentado", "Rentado"
        DISPONIBLE = "disponible", "Disponible"
        MANTENIMIENTO = "mantenimiento", "Mantenimiento"

    talla = models.CharField(max_length=10)
    color = models.CharField(max_length=120)
    detalles = models.CharField(max_length=255, blank=True)
    marca = models.CharField(max_length=120, blank=True)
    saco = models.CharField(max_length=80, blank=True)
    chaleco = models.CharField(max_length=80, blank=True)
    pantalon = models.CharField(max_length=80, blank=True)
    codigo_old = models.CharField(max_length=80, blank=True)
    codigo_new = models.CharField(max_length=80, blank=True)
    estatus = models.CharField(
        max_length=20,
        choices=Estatus.choices,
        default=Estatus.DISPONIBLE,
    )
    ubicacion = models.CharField(max_length=120, blank=True)
    linea_negocio = models.CharField(
        max_length=20,
        choices=LineaNegocio.choices,
        default=LineaNegocio.TRAJES,
        db_index=True,
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["codigo_new", "talla", "color"]
        verbose_name = "prenda"
        verbose_name_plural = "prendas"

    def __str__(self) -> str:
        return f"{self.codigo_new or self.codigo_old} — {self.color}"
