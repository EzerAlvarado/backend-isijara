from django.db import models


class MetodoPago(models.TextChoices):
    PESOS = "pesos", "Pesos"
    DLLS = "dlls", "DLLS"
    MIXTO = "mixto", "Mixto"
    BBVA = "bbva", "BBVA"
    ZELLE = "zelle", "Zelle"
    TRANSFERENCIA = "transferencia", "Transferencia"
    TARJETA = "tarjeta", "Tarjeta"


PAGOS_DIGITALES = (
    MetodoPago.BBVA,
    MetodoPago.ZELLE,
    MetodoPago.TRANSFERENCIA,
    MetodoPago.TARJETA,
)


def es_pago_digital(pago: str | None) -> bool:
    return (pago or "") in PAGOS_DIGITALES
