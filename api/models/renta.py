from django.db import models

from .common import celda_vacia
from .linea_negocio import LineaNegocio
from .metodo_pago import MetodoPago
from .pieza import Pieza


class Renta(models.Model):
    class TipoEntrega(models.TextChoices):
        RECOGER = "recoger", "Recoger"
        PREMIER = "premier", "Premier"

    class EstatusCelda(models.TextChoices):
        NORMAL = "normal", "Normal"
        ARRUGADO = "arrugado", "Arrugado"
        LISTO_EMPACAR = "listo_empacar", "Listo para empacar"
        SUCIO = "sucio", "Sucio"
        SALIO = "salio", "Fuera / Salió"
        MOJADO = "mojado", "Mojado"
        LISTO = "listo_para_entregar", "Listo para entregar"
        EN_AJUSTES = "en_ajustes", "Ajustes"
        OTRA_SITUACION = "otra_situacion", "Otra situación"
        ENTREGADO = "entregado", "Entregado"
        VENTA = "venta", "Venta (texto azul)"
        PREMIER = "premier", "Premier (texto morado)"
        SESION_FOTOS = "sesion_fotos", "Sesión de fotos"
        PATROCINIO = "patrocinio", "Patrocinio"

    class CategoriaVestido(models.TextChoices):
        NOCHE = "noche", "Noche"
        QUINCE = "quince", "XV / Quinceañera"
        BODA = "boda", "Novia"

    class TipoOperacion(models.TextChoices):
        RENTA = "renta", "Renta"
        VENTA = "venta", "Venta"
        PREMIER = "premier", "Premier"
        SESION_FOTOS = "sesion_fotos", "Sesión de fotos"
        PATROCINIO = "patrocinio", "Patrocinio"

    color = models.JSONField(default=celda_vacia)
    saco = models.JSONField(default=celda_vacia)
    chaleco = models.JSONField(default=celda_vacia)
    pantalon = models.JSONField(default=celda_vacia)
    camisa = models.JSONField(default=celda_vacia)
    corbata_mono = models.JSONField(default=celda_vacia)
    cinto = models.JSONField(default=celda_vacia)
    accesorio = models.JSONField(default=celda_vacia)
    tipo_entrega = models.CharField(
        max_length=10,
        choices=TipoEntrega.choices,
        default=TipoEntrega.RECOGER,
    )
    empleado = models.JSONField(default=celda_vacia)
    cliente = models.JSONField(default=celda_vacia)
    telefono = models.CharField(max_length=30, blank=True)
    direccion = models.CharField(max_length=255, blank=True)
    fecha_cita = models.JSONField(default=celda_vacia)
    horario = models.JSONField(default=celda_vacia)
    detalles = models.JSONField(default=celda_vacia)
    ajustes = models.CharField(max_length=255, blank=True)
    marca = models.CharField(max_length=120, blank=True)
    color_chaleco = models.CharField(max_length=120, blank=True)
    color_pantalon = models.CharField(max_length=120, blank=True)
    marca_chaleco = models.CharField(max_length=120, blank=True)
    marca_pantalon = models.CharField(max_length=120, blank=True)
    detalles_saco = models.CharField(max_length=255, blank=True, help_text="Nombre/descripción del saco (ej: TRAJE AZUL INDIGO)")
    detalles_chaleco = models.CharField(max_length=255, blank=True, help_text="Nombre/descripción del chaleco")
    detalles_pantalon = models.CharField(max_length=255, blank=True, help_text="Nombre/descripción del pantalón")
    estatus_fila = models.CharField(
        max_length=24,
        choices=EstatusCelda.choices,
        blank=True,
    )
    semana_inicio = models.DateField()
    fecha_salida = models.CharField(max_length=32)
    fecha_regreso = models.CharField(max_length=32)
    fecha_salio_real = models.DateField(
        null=True,
        blank=True,
        help_text="Fecha en que el cliente recogió el traje (al marcar salió en rentas).",
    )
    pieza_saco = models.ForeignKey(
        Pieza,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="rentas_saco",
    )
    pieza_chaleco = models.ForeignKey(
        Pieza,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="rentas_chaleco",
    )
    pieza_pantalon = models.ForeignKey(
        Pieza,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="rentas_pantalon",
    )
    fondo = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    anticipo = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    multa = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    metodo_pago = models.CharField(
        max_length=20,
        choices=MetodoPago.choices,
        default=MetodoPago.PESOS,
    )
    pago_efectivo_mxn = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Efectivo recibido en pesos (pago mixto o contado).",
    )
    pago_efectivo_usd = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Efectivo recibido en dólares.",
    )
    feria_mxn = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Cambio entregado al cliente en pesos.",
    )
    linea_negocio = models.CharField(
        max_length=20,
        choices=LineaNegocio.choices,
        default=LineaNegocio.TRAJES,
        db_index=True,
    )
    categoria_vestido = models.CharField(
        max_length=12,
        choices=CategoriaVestido.choices,
        blank=True,
        db_index=True,
        help_text="Solo vestidos: noche, quince o novia",
    )
    cancelada = models.BooleanField(default=False, db_index=True)
    tipo_operacion = models.CharField(
        max_length=15,
        choices=TipoOperacion.choices,
        default=TipoOperacion.RENTA,
        db_index=True,
    )
    deposito_reembolsable = models.CharField(
        max_length=100,
        blank=True,
        help_text="Depósito reembolsable (texto descriptivo, ej: $500)",
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-semana_inicio", "-id"]
        verbose_name = "renta"
        verbose_name_plural = "rentas"

    def __str__(self) -> str:
        cliente = self.cliente.get("valor", "") if isinstance(self.cliente, dict) else ""
        return f"Renta #{self.pk} — {cliente or 'Sin cliente'}"
