from django.db import models


class Pedido(models.Model):
    class TipoPedido(models.TextChoices):
        TUXEDO = "tuxedo", "Tuxedo"
        NOCHE = "noche", "Noche"
        XV = "xv", "XV"
        NOVIA = "novia", "Novia"

    class Estatus(models.TextChoices):
        PENDIENTE = "pendiente", "Pendiente"
        EN_PROCESO = "en_proceso", "En proceso"
        EN_BOUTIQUE = "en_boutique", "En boutique"
        EN_CAMINO = "en_camino", "En camino"
        CON_KAYLA = "con_kayla", "Con Kayla"
        NO_HAY = "no_hay", "No hay"
        ENTREGADO = "entregado", "Entregado"
        CANCELADO = "cancelado", "Cancelado"

    class Servicio(models.TextChoices):
        VENTA = "venta", "Venta"
        PREMIER = "premier", "Premier"

    cliente = models.CharField(max_length=255)
    tipo_pedido = models.CharField(
        max_length=16,
        choices=TipoPedido.choices,
        default=TipoPedido.TUXEDO,
    )
    estatus = models.CharField(
        max_length=20,
        choices=Estatus.choices,
        default=Estatus.PENDIENTE,
    )
    estilo_piezas = models.TextField(blank=True, default="")
    servicio = models.CharField(
        max_length=16,
        choices=Servicio.choices,
        default=Servicio.VENTA,
    )
    fecha_entrega = models.CharField(max_length=120, blank=True, default="")
    comentarios = models.TextField(blank=True, default="")
    mes_etiqueta = models.CharField(
        max_length=40,
        blank=True,
        default="",
        help_text="Etiqueta de mes para agrupar (ej. JULIO). Vacío = sin grupo.",
    )
    orden = models.PositiveIntegerField(default=0)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["mes_etiqueta", "orden", "-id"]

    def __str__(self) -> str:
        return f"{self.cliente} · {self.get_tipo_pedido_display()}"
