from django.db import models

from .linea_negocio import LineaNegocio

PRECIOS_REFERENCIA_TRAJES = [
    {"id": "recoger", "nombre": "Renta recoger en boutique", "precioMxn": 550},
    {"id": "premier", "nombre": "Renta Premier (a domicilio)", "precioMxn": 700},
    {"id": "completa", "nombre": "Traje completo (saco + chaleco + pantalón)", "precioMxn": 620},
    {"id": "camisa", "nombre": "Camisa", "precioMxn": 150},
    {"id": "accesorios", "nombre": "Accesorios (corbata, moño, cinto)", "precioMxn": 80},
]

PRECIOS_REFERENCIA_VESTIDOS = [
    {"id": "recoger", "nombre": "Renta recoger en boutique", "precioMxn": 800},
    {"id": "premier", "nombre": "Renta Premier (a domicilio)", "precioMxn": 950},
    {"id": "noche", "nombre": "Vestido de noche", "precioMxn": 900},
    {"id": "quince", "nombre": "Vestido XV / Quinceañera", "precioMxn": 1200},
    {"id": "boda", "nombre": "Vestido de novia", "precioMxn": 1500},
]

PRECIOS_REFERENCIA_DEFAULT = PRECIOS_REFERENCIA_TRAJES

TIPO_CAMBIO_DEFAULT = "18.50"
MULTA_POR_DIA_DEFAULT = "15.00"
FONDO_FERIA_DEFAULT = "2732.00"


def precios_default_por_linea(linea: str) -> list:
    if linea == LineaNegocio.VESTIDOS:
        return PRECIOS_REFERENCIA_VESTIDOS
    return PRECIOS_REFERENCIA_TRAJES


class ConfiguracionSistema(models.Model):
    """Configuración por línea de negocio (trajes / vestidos)."""

    linea_negocio = models.CharField(
        max_length=20,
        choices=LineaNegocio.choices,
        unique=True,
        default=LineaNegocio.TRAJES,
    )
    tipo_cambio_usd = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=TIPO_CAMBIO_DEFAULT,
        help_text="Pesos mexicanos por 1 USD",
    )
    precios_referencia = models.JSONField(default=list, blank=True)
    multa_por_dia = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=MULTA_POR_DIA_DEFAULT,
        help_text="Multa en MXN por cada día de retraso en devolución",
    )
    fondo_feria = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=FONDO_FERIA_DEFAULT,
        help_text="Fondo de feria (cambio) en caja, en MXN",
    )
    usar_codigos_nuevos_pantalon = models.BooleanField(
        default=False,
        help_text="Si es falso, en pantalones se prefiere código viejo; si es verdadero, código nuevo",
    )
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "configuración del sistema"
        verbose_name_plural = "configuración del sistema"

    def __str__(self) -> str:
        return f"Configuración — {self.get_linea_negocio_display()}"
