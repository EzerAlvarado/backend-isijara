from django.db import models


class LineaNegocio(models.TextChoices):
    TRAJES = "trajes", "Trajes"
    VESTIDOS = "vestidos", "Vestidos"
