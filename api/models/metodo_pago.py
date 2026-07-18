from django.db import models


class MetodoPago(models.TextChoices):
    PESOS = "pesos", "Pesos"
    DLLS = "dlls", "DLLS"
    MIXTO = "mixto", "Mixto"
    BBVA = "bbva", "BBVA"
    ZELLE = "zelle", "Zelle"
