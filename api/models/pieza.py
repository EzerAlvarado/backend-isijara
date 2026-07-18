from django.db import models

from .linea_negocio import LineaNegocio


class Pieza(models.Model):
    class Tipo(models.TextChoices):
        SACO = "saco", "Saco"
        CHALECO = "chaleco", "Chaleco"
        PANTALON = "pantalon", "Pantalón"
        QUINCE = "quince", "XV / Quinceañera"
        BODA = "boda", "Novia"
        NOCHE = "noche", "Noche"
        # Legacy (migración desde inventario anterior)
        VESTIDO = "vestido", "Vestido"
        ACCESORIO = "accesorio", "Accesorio"

    class Estatus(models.TextChoices):
        RENTADO = "rentado", "Rentado"
        DISPONIBLE = "disponible", "Disponible"
        MANTENIMIENTO = "mantenimiento", "Mantenimiento"
        SALIO = "salio", "Fuera / Salió"
        SUCIO = "sucio", "Sucio"
        MOJADO = "mojado", "Mojado"
        EN_AJUSTES = "en_ajustes", "En ajustes"
        LISTO = "listo_para_entregar", "Listo para entregar"

    tipo = models.CharField(max_length=12, choices=Tipo.choices)
    color = models.CharField(
        max_length=120,
        help_text="Color mero (ej. VERDE, ROSA)",
    )
    color_vestido = models.CharField(
        max_length=200,
        blank=True,
        help_text="Descripción del vestido (ej. VERDE SAGE CON BRILLOS)",
    )
    talla = models.CharField(max_length=80)
    marca = models.CharField(max_length=120, blank=True)
    detalles = models.CharField(max_length=255, blank=True)
    codigo_old = models.CharField(max_length=80, blank=True)
    codigo_new = models.CharField(max_length=80, blank=True)
    conjunto = models.CharField(
        max_length=80,
        blank=True,
        help_text="Código de agrupación del traje original",
    )
    estatus = models.CharField(
        max_length=24,
        choices=Estatus.choices,
        default=Estatus.DISPONIBLE,
    )
    precio_renta = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Precio de renta (vestidos)",
    )
    precio_venta = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Precio de venta (vestidos)",
    )
    precio_premier = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Precio de renta Premier / a domicilio (vestidos)",
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
        ordering = ["tipo", "color", "talla"]
        verbose_name = "pieza"
        verbose_name_plural = "piezas"

    def __str__(self) -> str:
        codigo = self.codigo_new or self.codigo_old or f"#{self.pk}"
        return f"{self.get_tipo_display()} {self.color} {self.talla} — {codigo}"
