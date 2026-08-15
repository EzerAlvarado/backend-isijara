from collections import defaultdict
from datetime import date, timedelta

from django.utils import timezone

from api.models import LineaNegocio, Renta
from api.services.inventario_renta import parse_fecha_mx

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

TIPOS_CUENTAN = {
    Renta.TipoOperacion.RENTA,
    Renta.TipoOperacion.PREMIER,
    Renta.TipoOperacion.SESION_FOTOS,
    Renta.TipoOperacion.PAQUETE_PREMIUM,
    Renta.TipoOperacion.PATROCINIO,
}

DIAS_ALERTA_DEFAULT = 10
DIAS_PASADO_ALERTA = 30
DIAS_FUTURO_ALERTA = 180


def _rubro_renta(renta: Renta) -> str:
    if renta.linea_negocio == LineaNegocio.TRAJES:
        return "trajes"
    cat = (renta.categoria_vestido or "").strip().lower()
    if cat == Renta.CategoriaVestido.QUINCE:
        return "xv"
    if cat == Renta.CategoriaVestido.BODA:
        return "novia"
    return "noche"


def _fecha_salida(renta: Renta) -> date | None:
    return parse_fecha_mx(renta.fecha_salida) or renta.semana_inicio


def _fecha_regreso(renta: Renta, salida: date | None) -> date | None:
    regreso = parse_fecha_mx(renta.fecha_regreso)
    if regreso:
        return regreso
    if salida:
        return salida + timedelta(days=3)
    return None


def _valor_celda(celda) -> str:
    if isinstance(celda, dict):
        return str(celda.get("valor", "")).strip()
    return str(celda or "").strip()


def _codigo_pieza(pieza) -> str:
    if not pieza:
        return ""
    return (pieza.codigo_new or pieza.codigo_old or "").strip().upper()


def _codigo_renta(renta: Renta) -> str:
    codigo = _codigo_pieza(renta.pieza_saco)
    if codigo:
        return codigo
    return _valor_celda(renta.saco).upper()


def _color_renta(renta: Renta) -> str:
    if renta.pieza_saco and renta.pieza_saco.color:
        return renta.pieza_saco.color.strip()
    return _valor_celda(renta.color)


def _descripcion_renta(renta: Renta) -> str:
    if renta.pieza_saco and renta.pieza_saco.color_vestido:
        return renta.pieza_saco.color_vestido.strip()
    return (renta.detalles_saco or _valor_celda(renta.chaleco)).strip()


def _clave_vestido(renta: Renta) -> str | None:
    if renta.pieza_saco_id:
        return f"p:{renta.pieza_saco_id}"
    codigo = _codigo_renta(renta)
    if codigo and codigo not in {"X", "—", "-", "NO", "N/A"}:
        return f"c:{codigo}"
    return None


def _qs_ocupacion():
    return Renta.objects.filter(
        cancelada=False,
        tipo_operacion__in=TIPOS_CUENTAN,
    ).select_related("pieza_saco")


def conteo_piezas_anio(anio: int) -> dict:
    hoy = timezone.localdate()
    anio_ant = anio - 1
    por_mes = {
        year: {mes: {clave: 0 for clave, _ in RUBROS} for mes in range(1, 13)}
        for year in (anio_ant, anio)
    }

    for renta in _qs_ocupacion().iterator():
        fecha = _fecha_salida(renta)
        if not fecha or fecha.year not in por_mes:
            continue
        por_mes[fecha.year][fecha.month][_rubro_renta(renta)] += 1

    meses = []
    for mes in range(1, 13):
        rubros = []
        total_actual = 0
        total_anterior = 0
        for clave, label in RUBROS:
            actual = por_mes[anio][mes][clave]
            anterior = por_mes[anio_ant][mes][clave]
            total_actual += actual
            total_anterior += anterior
            rubros.append(
                {
                    "id": clave,
                    "label": label,
                    "actual": actual,
                    "anterior": anterior,
                    "diferencia": actual - anterior,
                }
            )
        meses.append(
            {
                "mes": mes,
                "mesLabel": MESES_ES[mes],
                "esMesActual": hoy.year == anio and hoy.month == mes,
                "esFuturo": date(anio, mes, 1) > date(hoy.year, hoy.month, 1),
                "rubros": rubros,
                "totalActual": total_actual,
                "totalAnterior": total_anterior,
                "diferencia": total_actual - total_anterior,
            }
        )

    ocupados = sorted(
        (
            {
                "mes": m["mes"],
                "mesLabel": m["mesLabel"],
                "total": por_mes[anio_ant][m["mes"]][clave] + por_mes[anio][m["mes"]][clave],
                "actual": por_mes[anio][m["mes"]][clave],
                "anterior": por_mes[anio_ant][m["mes"]][clave],
                "rubro": clave,
                "rubroLabel": label,
            }
            for m in meses
            for clave, label in RUBROS
            if por_mes[anio_ant][m["mes"]][clave] or por_mes[anio][m["mes"]][clave]
        ),
        key=lambda item: item["anterior"],
        reverse=True,
    )[:4]

    return {
        "anio": anio,
        "anioAnterior": anio_ant,
        "meses": meses,
        "mesesMasOcupados": ocupados,
        "totales": {
            "actual": sum(m["totalActual"] for m in meses),
            "anterior": sum(m["totalAnterior"] for m in meses),
        },
    }


def _resumen_renta(renta: Renta) -> dict:
    return {
        "rentaId": renta.id,
        "cliente": _valor_celda(renta.cliente),
        "fechaSalida": renta.fecha_salida,
        "fechaRegreso": renta.fecha_regreso,
        "tipoOperacion": renta.tipo_operacion,
    }


def _severidad(traslape: bool, dias_entre: int) -> str:
    if traslape or dias_entre <= 3:
        return "alta"
    if dias_entre <= 7:
        return "media"
    return "baja"


def alertas_reuso_vestido(
    dias_alerta: int = DIAS_ALERTA_DEFAULT,
    categoria: str = Renta.CategoriaVestido.QUINCE,
    hoy: date | None = None,
) -> dict:
    hoy = hoy or timezone.localdate()
    desde = hoy - timedelta(days=DIAS_PASADO_ALERTA)
    hasta = hoy + timedelta(days=DIAS_FUTURO_ALERTA)
    cat = (categoria or "").strip().lower()
    qs = _qs_ocupacion().filter(linea_negocio=LineaNegocio.VESTIDOS)
    if cat and cat != "todas":
        if cat == "xv":
            cat = Renta.CategoriaVestido.QUINCE
        qs = qs.filter(categoria_vestido=cat)

    grupos: dict[str, list[Renta]] = defaultdict(list)
    meta: dict[str, dict] = {}
    for renta in qs.iterator():
        clave = _clave_vestido(renta)
        if not clave:
            continue
        grupos[clave].append(renta)
        if clave not in meta:
            meta[clave] = {
                "codigo": _codigo_renta(renta),
                "color": _color_renta(renta),
                "descripcion": _descripcion_renta(renta),
                "piezaId": renta.pieza_saco_id,
            }

    alertas = []
    mas_rentados = []
    for clave, rentas in grupos.items():
        ordenadas = sorted(
            rentas,
            key=lambda r: (_fecha_salida(r) or date.min, r.id),
        )
        info = meta[clave]
        mas_rentados.append(
            {
                "codigo": info["codigo"],
                "color": info["color"],
                "descripcion": info["descripcion"],
                "piezaId": info["piezaId"],
                "veces": len(ordenadas),
            }
        )
        for prev, nxt in zip(ordenadas, ordenadas[1:]):
            salida_next = _fecha_salida(nxt)
            salida_prev = _fecha_salida(prev)
            if not salida_next or not salida_prev:
                continue
            if salida_next < desde or salida_next > hasta:
                continue
            regreso_prev = _fecha_regreso(prev, salida_prev)
            if not regreso_prev:
                continue
            dias_entre = (salida_next - regreso_prev).days
            traslape = salida_next <= regreso_prev
            if not traslape and dias_entre > dias_alerta:
                continue
            alertas.append(
                {
                    "codigo": info["codigo"],
                    "color": info["color"],
                    "descripcion": info["descripcion"],
                    "piezaId": info["piezaId"],
                    "vecesRentado": len(ordenadas),
                    "diasEntre": dias_entre,
                    "traslape": traslape,
                    "severidad": _severidad(traslape, dias_entre),
                    "anterior": _resumen_renta(prev),
                    "siguiente": _resumen_renta(nxt),
                }
            )

    alertas.sort(
        key=lambda a: (
            0 if a["severidad"] == "alta" else 1 if a["severidad"] == "media" else 2,
            a["diasEntre"],
        )
    )
    mas_rentados.sort(key=lambda item: (-item["veces"], item["codigo"]))

    return {
        "diasAlerta": dias_alerta,
        "categoria": cat or "todas",
        "alertas": alertas,
        "masRentados": mas_rentados[:20],
    }
