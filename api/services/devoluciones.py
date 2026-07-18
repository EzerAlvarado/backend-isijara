from datetime import date
from decimal import Decimal

from api.models import Devolucion, LineaNegocio, Renta
from api.services.finanzas import obtener_multa_por_dia


def dias_retraso(fecha_limite: date, hoy: date | None = None) -> int:
    hoy = hoy or date.today()
    if hoy <= fecha_limite:
        return 0
    return (hoy - fecha_limite).days


def calcular_penalizacion(
    fecha_limite: date,
    linea_negocio: str = LineaNegocio.TRAJES,
    hoy: date | None = None,
) -> Decimal:
    dias = dias_retraso(fecha_limite, hoy)
    if dias <= 0:
        return Decimal("0")
    return Decimal(dias) * obtener_multa_por_dia(linea_negocio)


def marcar_devoluciones_retrasadas(linea_negocio: str | None = None) -> int:
    """Pasa a retrasado las que siguen afuera y ya pasó la fecha límite."""
    hoy = date.today()
    qs = Devolucion.objects.filter(
        estatus=Devolucion.Estatus.AFUERA,
        fecha_limite__lt=hoy,
    )
    if linea_negocio:
        qs = qs.filter(renta__linea_negocio=linea_negocio)
    return qs.update(estatus=Devolucion.Estatus.RETRASADO)


def actualizar_penalizaciones_retrasadas(linea_negocio: str | None = None) -> int:
    """Recalcula multa de devoluciones retrasadas según días y tarifa configurada."""
    hoy = date.today()
    actualizadas = 0

    qs = Devolucion.objects.filter(estatus=Devolucion.Estatus.RETRASADO).select_related(
        "renta"
    )
    if linea_negocio:
        qs = qs.filter(renta__linea_negocio=linea_negocio)

    for dev in qs:
        linea = dev.renta.linea_negocio if dev.renta_id else LineaNegocio.TRAJES
        multa_dia = obtener_multa_por_dia(linea)
        dias = dias_retraso(dev.fecha_limite, hoy)
        penalizacion = Decimal(dias) * multa_dia if dias > 0 else Decimal("0")
        if dev.penalizacion != penalizacion:
            dev.penalizacion = penalizacion
            dev.save(update_fields=["penalizacion"])
            actualizadas += 1
        if dev.renta_id and dev.renta.multa != penalizacion:
            Renta.objects.filter(pk=dev.renta_id).update(multa=penalizacion)

    return actualizadas


def sincronizar_estado_devoluciones(linea_negocio: str | None = None) -> None:
    marcar_devoluciones_retrasadas(linea_negocio)
    actualizar_penalizaciones_retrasadas(linea_negocio)
