from calendar import monthrange
from datetime import datetime
from decimal import Decimal

from django.db.models import Q
from django.utils import timezone

from api.models import LineaNegocio, MetodoPago, Renta, Transaccion
from api.services.finanzas import obtener_tipo_cambio
from api.services.vales import es_gasto_fondo

RUBROS = (
    ("trajes", "Trajes"),
    ("xv", "XV"),
    ("noche", "Noche"),
    ("novia", "Novia"),
)

MESES_ES = (
    "",
    "Enero",
    "Febrero",
    "Marzo",
    "Abril",
    "Mayo",
    "Junio",
    "Julio",
    "Agosto",
    "Septiembre",
    "Octubre",
    "Noviembre",
    "Diciembre",
)


def _inicio_fin_mes(anio: int, mes: int):
    tz = timezone.get_current_timezone()
    inicio = timezone.make_aware(datetime(anio, mes, 1), tz)
    if mes == 12:
        fin = timezone.make_aware(datetime(anio + 1, 1, 1), tz)
    else:
        fin = timezone.make_aware(datetime(anio, mes + 1, 1), tz)
    return inicio, fin


def _monto_mxn(monto: Decimal, pago: str, linea: str, tc_cache: dict[str, Decimal]) -> Decimal:
    if pago == MetodoPago.DLLS:
        if linea not in tc_cache:
            tc_cache[linea] = obtener_tipo_cambio(linea)
        return Decimal(monto) * tc_cache[linea]
    return Decimal(monto)


def _rubro_transaccion(tx: Transaccion) -> str:
    if tx.linea_negocio == LineaNegocio.TRAJES:
        return "trajes"
    cat = (tx.categoria_vestido or "").strip().lower()
    if cat == Renta.CategoriaVestido.QUINCE:
        return "xv"
    if cat == Renta.CategoriaVestido.BODA:
        return "novia"
    return "noche"


def _concepto(referencia: str) -> str:
    ref = (referencia or "").upper()
    if ref.startswith("MR") or ref.startswith("M"):
        return "multa"
    if ref.startswith("D"):
        return "danos"
    if ref.startswith("A"):
        return "abono"
    if ref.startswith("R"):
        return "operacion"
    return "otro"


def _vacio() -> dict:
    return {
        "ingresoMxn": Decimal("0"),
        "hoyMxn": Decimal("0"),
        "movimientos": 0,
        "porConcepto": {
            "operacion": Decimal("0"),
            "abono": Decimal("0"),
            "multa": Decimal("0"),
            "danos": Decimal("0"),
            "otro": Decimal("0"),
        },
    }


def ingresos_mensuales(anio: int, mes: int) -> dict:
    inicio, fin = _inicio_fin_mes(anio, mes)
    ahora = timezone.now()
    hoy_inicio = ahora.replace(hour=0, minute=0, second=0, microsecond=0)
    es_mes_actual = ahora.year == anio and ahora.month == mes

    txs = Transaccion.objects.filter(
        timestamp__gte=inicio,
        timestamp__lt=fin,
        anulada=False,
        monto__gt=0,
    ).exclude(Q(referencia__istartswith="G"))

    acumulado = {clave: _vacio() for clave, _ in RUBROS}
    tc_cache: dict[str, Decimal] = {}

    for tx in txs.iterator():
        rubro = _rubro_transaccion(tx)
        bucket = acumulado[rubro]
        mxn = _monto_mxn(tx.monto, tx.pago, tx.linea_negocio, tc_cache)
        if mxn <= 0:
            continue
        bucket["ingresoMxn"] += mxn
        bucket["movimientos"] += 1
        concepto = _concepto(tx.referencia)
        bucket["porConcepto"][concepto] = bucket["porConcepto"].get(concepto, Decimal("0")) + mxn
        if tx.timestamp >= hoy_inicio:
            bucket["hoyMxn"] += mxn

    def money(valor: Decimal) -> float:
        return float(valor.quantize(Decimal("0.01")))

    rubros = []
    total = Decimal("0")
    hoy = Decimal("0")
    movimientos = 0
    for clave, label in RUBROS:
        b = acumulado[clave]
        total += b["ingresoMxn"]
        hoy += b["hoyMxn"]
        movimientos += b["movimientos"]
        rubros.append(
            {
                "id": clave,
                "label": label,
                "ingresoMxn": money(b["ingresoMxn"]),
                "hoyMxn": money(b["hoyMxn"]),
                "movimientos": b["movimientos"],
                "porConcepto": {k: money(v) for k, v in b["porConcepto"].items()},
            }
        )

    ultimo_dia = monthrange(anio, mes)[1]
    return {
        "anio": anio,
        "mes": mes,
        "mesLabel": f"{MESES_ES[mes]} {anio}",
        "esMesActual": es_mes_actual,
        "desde": inicio.date().isoformat(),
        "hasta": (fin.date().isoformat()),
        "diasDelMes": ultimo_dia,
        "totalMxn": money(total),
        "hoyMxn": money(hoy) if es_mes_actual else 0.0,
        "movimientos": movimientos,
        "rubros": rubros,
    }
