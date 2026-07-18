"""Denominaciones y totales del conteo físico de caja."""

from decimal import Decimal

FONDO_FERIA_DEFAULT = Decimal("2732.00")

MXN_BILLETES = [1000, 500, 200, 100, 50, 20]
MXN_MONEDAS = [20, 10, 5, 2, 1, 0.5]
USD_BILLETES = [100, 50, 20, 10, 5, 1]

CONTEO_VACIO = {
    "mxnBilletes": {str(d): 0 for d in MXN_BILLETES},
    "mxnMonedas": {str(d): 0 for d in MXN_MONEDAS},
    "usdBilletes": {str(d): 0 for d in USD_BILLETES},
    "valesMxn": 0,
}


def _sum_denominaciones(conteo: dict, denominaciones: list[int]) -> Decimal:
    total = Decimal("0")
    for d in denominaciones:
        cantidad = int(conteo.get(str(d), 0) or 0)
        if cantidad < 0:
            cantidad = 0
        total += Decimal(str(d)) * cantidad
    return total


def normalizar_conteo(raw: dict | None) -> dict:
    if not isinstance(raw, dict):
        return {**CONTEO_VACIO}

    def norm_bloque(claves: dict, keys: list) -> dict:
        src = raw.get(claves, {})
        if not isinstance(src, dict):
            src = {}
        return {str(k): max(0, int(src.get(str(k), 0) or 0)) for k in keys}

    return {
        "mxnBilletes": norm_bloque("mxnBilletes", MXN_BILLETES),
        "mxnMonedas": norm_bloque("mxnMonedas", MXN_MONEDAS),
        "usdBilletes": norm_bloque("usdBilletes", USD_BILLETES),
        "valesMxn": max(0, int(raw.get("valesMxn", 0) or 0)),
    }


def totales_conteo(conteo: dict | None) -> dict:
    c = normalizar_conteo(conteo)
    mxn_billetes = _sum_denominaciones(c["mxnBilletes"], MXN_BILLETES)
    mxn_monedas = _sum_denominaciones(c["mxnMonedas"], MXN_MONEDAS)
    mxn_vales = Decimal(str(c.get("valesMxn", 0) or 0))
    usd = _sum_denominaciones(c["usdBilletes"], USD_BILLETES)
    mxn_total = mxn_billetes + mxn_monedas + mxn_vales
    return {
        "mxnBilletes": float(mxn_billetes),
        "mxnMonedas": float(mxn_monedas),
        "mxnVales": float(mxn_vales),
        "mxnTotal": float(mxn_total),
        "usdTotal": float(usd),
    }


def conteo_equivalente_mxn(conteo: dict | None, tipo_cambio: Decimal) -> float:
    t = totales_conteo(conteo)
    return float(Decimal(str(t["mxnTotal"])) + Decimal(str(t["usdTotal"])) * tipo_cambio)


def _descontar_centavos_greedy(conteo: dict, centavos: int) -> int:
    """Resta del conteo MXN (billetes y monedas) usando denominaciones grandes primero."""
    if centavos <= 0:
        return 0

    denoms: list[tuple[int, str]] = [(d, "mxnBilletes") for d in MXN_BILLETES]
    denoms.extend((d, "mxnMonedas") for d in MXN_MONEDAS)
    denoms.sort(key=lambda item: item[0], reverse=True)

    restante = centavos
    for valor, bloque in denoms:
        if restante <= 0:
            break
        valor_cent = int(Decimal(str(valor)) * 100)
        if valor_cent <= 0:
            continue
        key = str(valor)
        disponible = int(conteo[bloque].get(key, 0) or 0)
        if disponible <= 0:
            continue
        quitar = min(disponible, restante // valor_cent)
        if quitar <= 0:
            continue
        conteo[bloque][key] = disponible - quitar
        restante -= quitar * valor_cent

    return restante


def aplicar_vale_a_conteo_fondo(conteo: dict | None, monto_mxn: Decimal) -> dict:
    """
    Al crear un vale: resta del desglose físico (greedy) y suma a valesMxn.
    El total del conteo se mantiene si había suficiente efectivo registrado.
    """
    c = normalizar_conteo(conteo)
    monto = max(Decimal("0"), Decimal(monto_mxn))
    centavos = int((monto * 100).to_integral_value())
    if centavos <= 0:
        return c

    _descontar_centavos_greedy(c, centavos)
    c["valesMxn"] = int(c.get("valesMxn", 0) or 0) + int(monto.to_integral_value())
    return c


def _agregar_centavos_greedy(conteo: dict, centavos: int) -> None:
    """Devuelve efectivo al conteo usando monedas/billetes pequeños primero."""
    if centavos <= 0:
        return

    denoms: list[tuple[int, str]] = [(d, "mxnMonedas") for d in MXN_MONEDAS]
    denoms.extend((d, "mxnBilletes") for d in MXN_BILLETES)
    denoms.sort(key=lambda item: item[0])

    restante = centavos
    for valor, bloque in denoms:
        if restante <= 0:
            break
        valor_cent = int(Decimal(str(valor)) * 100)
        if valor_cent <= 0:
            continue
        key = str(valor)
        agregar = restante // valor_cent
        if agregar <= 0:
            continue
        conteo[bloque][key] = int(conteo[bloque].get(key, 0) or 0) + agregar
        restante -= agregar * valor_cent


def reponer_monto_en_conteo_fondo(conteo: dict | None, monto_mxn: Decimal) -> dict:
    """Al reponer un vale: baja valesMxn y regresa monto al desglose físico."""
    c = normalizar_conteo(conteo)
    monto = max(Decimal("0"), Decimal(monto_mxn))
    pesos = int(monto.to_integral_value())
    if pesos <= 0:
        return c
    c["valesMxn"] = max(0, int(c.get("valesMxn", 0) or 0) - pesos)
    _agregar_centavos_greedy(c, pesos * 100)
    return c
