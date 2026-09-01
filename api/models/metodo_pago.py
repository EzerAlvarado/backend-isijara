from django.db import models


class MetodoPago(models.TextChoices):
    PESOS = "pesos", "Pesos"
    DLLS = "dlls", "DLLS"
    MIXTO = "mixto", "Mixto"
    BBVA = "bbva", "BBVA"
    ZELLE = "zelle", "Zelle"
    TRANSFERENCIA = "transferencia", "Transferencia"
    TARJETA = "tarjeta", "Tarjeta"


def es_pago_en_usd(pago: str) -> bool:
    return pago in (MetodoPago.DLLS, MetodoPago.ZELLE)


def es_pago_digital_mxn(pago: str) -> bool:
    return pago in (MetodoPago.BBVA, MetodoPago.TRANSFERENCIA, MetodoPago.TARJETA)


def es_pago_digital(pago: str | None) -> bool:
    metodo = pago or ""
    return es_pago_digital_mxn(metodo) or metodo == MetodoPago.ZELLE
