from django.db import models


class MetodoPago(models.TextChoices):
    PESOS = "pesos", "Pesos"
    DLLS = "dlls", "DLLS"
    MIXTO = "mixto", "Mixto"
    BBVA = "bbva", "BBVA"
    ZELLE = "zelle", "Zelle"
    TRANSFERENCIA = "transferencia", "Transferencia"


def es_pago_en_usd(pago: str) -> bool:
    return pago in (MetodoPago.DLLS, MetodoPago.ZELLE)


def es_pago_digital_mxn(pago: str) -> bool:
    return pago in (MetodoPago.BBVA, MetodoPago.TRANSFERENCIA)
