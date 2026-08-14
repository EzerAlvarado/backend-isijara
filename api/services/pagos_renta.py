from decimal import Decimal

from django.db.models import Sum

from api.models import Abono, MetodoPago, Renta
from api.services.finanzas import obtener_tipo_cambio


def monto_en_pesos(monto: Decimal, pago: str, linea_negocio: str) -> Decimal:
    if pago == MetodoPago.DLLS:
        return Decimal(monto) * obtener_tipo_cambio(linea_negocio)
    return Decimal(monto)


def monto_inicial_pagado_mxn(renta: Renta) -> Decimal:
    """Equivalente en MXN del cobro inicial.

    En DLLS/MIXTO se usa el efectivo recibido (pago_efectivo_*) cuando existe,
    para que un pago en dólares con feria no quede “casi pagado” por redondeo
    del anticipo guardado en USD.
    """
    mxn = Decimal(renta.pago_efectivo_mxn or 0)
    usd = Decimal(renta.pago_efectivo_usd or 0)
    if renta.metodo_pago in (MetodoPago.MIXTO, MetodoPago.DLLS) and (mxn > 0 or usd > 0):
        tc = obtener_tipo_cambio(renta.linea_negocio)
        return mxn + usd * tc
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
    # Hasta $1 MXN por redondeo de tipo de cambio (USD ↔ MXN).
    return restante_mxn(renta) <= Decimal("1.00")


def etiqueta_operacion(tipo_operacion: str) -> str:
    return {
        Renta.TipoOperacion.RENTA: "Renta",
        Renta.TipoOperacion.VENTA: "Venta",
        Renta.TipoOperacion.PREMIER: "Premier",
        Renta.TipoOperacion.SESION_FOTOS: "Sesión de fotos",
        Renta.TipoOperacion.PATROCINIO: "Patrocinio",
        Renta.TipoOperacion.PAQUETE_PREMIUM: "Paquete Premium",
    }.get(tipo_operacion, "Renta")
