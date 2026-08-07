from django.contrib import admin

from .models import Devolucion, Pedido, Prenda, Renta, Transaccion


@admin.register(Prenda)
class PrendaAdmin(admin.ModelAdmin):
    list_display = ("codigo_new", "talla", "color", "estatus", "marca")
    list_filter = ("estatus", "talla")
    search_fields = ("codigo_new", "codigo_old", "color", "marca")


@admin.register(Renta)
class RentaAdmin(admin.ModelAdmin):
    list_display = ("id", "semana_inicio", "tipo_entrega", "fecha_salida", "fondo")
    list_filter = ("semana_inicio", "tipo_entrega", "estatus_fila")
    date_hierarchy = "semana_inicio"


@admin.register(Devolucion)
class DevolucionAdmin(admin.ModelAdmin):
    list_display = (
        "cliente",
        "prenda_nombre",
        "estatus",
        "fecha_limite",
        "penalizacion",
        "multa_perdonada",
        "cargo_danos",
    )
    list_filter = ("estatus", "fecha_limite")


@admin.register(Transaccion)
class TransaccionAdmin(admin.ModelAdmin):
    list_display = ("referencia", "cliente", "pago", "monto", "timestamp")
    list_filter = ("pago",)
    search_fields = ("referencia", "cliente")


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "cliente",
        "tipo_pedido",
        "estatus",
        "servicio",
        "fecha_entrega",
        "mes_etiqueta",
    )
    list_filter = ("tipo_pedido", "estatus", "servicio", "mes_etiqueta")
    search_fields = ("cliente", "estilo_piezas", "comentarios")

