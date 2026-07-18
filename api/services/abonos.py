from decimal import Decimal

from django.utils import timezone

from api.models import Abono, MetodoPago, Renta
from api.services.corte import registrar_transaccion_abono
from api.services.finanzas import obtener_tipo_cambio
from api.services.pagos_renta import monto_en_pesos, restante_mxn, esta_pagada


def _resolver_monto_abono(
    renta: Renta,
    *,
    monto: Decimal | None,
    metodo_pago: str,
    pago_pesos: Decimal,
    pago_dlls: Decimal,
) -> tuple[Decimal, str, Decimal, Decimal, Decimal]:
    """Devuelve (monto_tx, metodo_pago, pago_mxn, pago_usd, monto_mxn)."""
    linea = renta.linea_negocio
    tc = obtener_tipo_cambio(linea)

    if metodo_pago in (MetodoPago.PESOS, MetodoPago.DLLS, MetodoPago.MIXTO):
        mxn = Decimal(pago_pesos)
        usd = Decimal(pago_dlls)
        if mxn <= 0 and usd <= 0 and monto is not None:
            monto_mxn = monto_en_pesos(monto, metodo_pago, linea)
            return monto, metodo_pago, Decimal("0"), Decimal("0"), monto_mxn

        recibido_mxn = mxn + usd * tc
        limite = restante_mxn(renta)
        aplicado_mxn = min(recibido_mxn, limite)
        if aplicado_mxn <= 0:
            raise ValueError("El abono debe ser mayor a cero.")

        if metodo_pago == MetodoPago.MIXTO or (mxn > 0 and usd > 0):
            metodo = MetodoPago.MIXTO
            return aplicado_mxn, metodo, mxn, usd, aplicado_mxn

        if usd > 0 and mxn <= 0:
            metodo = MetodoPago.DLLS
            monto_usd = min(usd, aplicado_mxn / tc if tc else usd)
            return monto_usd, metodo, Decimal("0"), monto_usd, aplicado_mxn

        metodo = MetodoPago.PESOS
        return aplicado_mxn, metodo, aplicado_mxn, Decimal("0"), aplicado_mxn

    if monto is None or monto <= 0:
        raise ValueError("El monto debe ser mayor a cero.")
    monto_mxn = monto_en_pesos(monto, metodo_pago, linea)
    limite = restante_mxn(renta)
    if monto_mxn > limite + Decimal("0.01"):
        raise ValueError(f"El abono excede el saldo pendiente (${limite}).")
    return monto, metodo_pago, Decimal("0"), Decimal("0"), monto_mxn


def crear_abono(
    renta: Renta,
    *,
    monto: Decimal | None = None,
    metodo_pago: str = MetodoPago.PESOS,
    pago_pesos: Decimal = Decimal("0"),
    pago_dlls: Decimal = Decimal("0"),
) -> Abono:
    if renta.cancelada:
        raise ValueError("No se pueden registrar abonos en una renta cancelada.")
    if esta_pagada(renta):
        raise ValueError("Esta renta ya está pagada.")

    monto_tx, metodo, pago_mxn, pago_usd, monto_mxn = _resolver_monto_abono(
        renta,
        monto=monto,
        metodo_pago=metodo_pago,
        pago_pesos=pago_pesos,
        pago_dlls=pago_dlls,
    )

    abono = Abono.objects.create(
        renta=renta,
        monto=monto_tx,
        metodo_pago=metodo,
        pago_efectivo_mxn=pago_mxn,
        pago_efectivo_usd=pago_usd,
        monto_mxn=monto_mxn,
        linea_negocio=renta.linea_negocio,
        creado_en=timezone.now(),
    )
    registrar_transaccion_abono(abono)
    return abono
