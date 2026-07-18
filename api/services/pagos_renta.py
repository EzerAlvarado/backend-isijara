from decimal import Decimal

from django.db.models import Sum

from api.models import Abono, MetodoPago, Renta
from api.services.finanzas import obtener_tipo_cambio


def monto_en_pesos(monto: Decimal, pago: str, linea_negocio: str) -> Decimal:
    if pago == MetodoPago.DLLS:
        return Decimal(monto) * obtener_tipo_cambio(linea_negocio)
    return Decimal(monto)


def monto_inicial_pagado_mxn(renta: Renta) -> Decimal:
    if renta.metodo_pago == MetodoPago.MIXTO:
        tc = obtener_tipo_cambio(renta.linea_negocio)
        return Decimal(renta.pago_efectivo_mxn) + Decimal(renta.pago_efectivo_usd) * tc
    if renta.metodo_pago == MetodoPago.DLLS:
        return monto_en_pesos(renta.anticipo, MetodoPago.DLLS, renta.linea_negocio)
    return Decimal(renta.anticipo)


def total_abonado_mxn(renta: Renta) -> Decimal:
    agg = Abono.objects.filter(renta=renta).aggregate(total=Sum("monto_mxn"))
    return Decimal(agg["total"] or 0)


def total_cobrar_mxn(renta: Renta) -> Decimal:
    return Decimal(renta.fondo) + Decimal(renta.multa)


def total_pagado_mxn(renta: Renta) -> Decimal:
    return monto_inicial_pagado_mxn(renta) + total_abonado_mxn(renta)


def restante_mxn(renta: Renta) -> Decimal:
    return max(Decimal("0"), total_cobrar_mxn(renta) - total_pagado_mxn(renta))


def esta_pagada(renta: Renta) -> bool:
    return restante_mxn(renta) <= Decimal("0.01")


def etiqueta_operacion(tipo_operacion: str) -> str:
    return {
        Renta.TipoOperacion.RENTA: "Renta",
        Renta.TipoOperacion.VENTA: "Venta",
        Renta.TipoOperacion.PREMIER: "Premier",
        Renta.TipoOperacion.SESION_FOTOS: "Sesión de fotos",
        Renta.TipoOperacion.PATROCINIO: "Patrocinio",
    }.get(tipo_operacion, "Renta")
