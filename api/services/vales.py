from decimal import Decimal

from django.utils import timezone

from api.models import CorteDia, MetodoPago, Transaccion, Vale


def es_gasto_fondo(referencia: str) -> bool:
    return str(referencia or "").upper().startswith("G")


def vales_pendientes(linea_negocio: str, categoria: str | None = None):
    qs = Vale.objects.filter(
        estatus=Vale.Estatus.PENDIENTE,
        linea_negocio=linea_negocio,
    )
    if categoria:
        qs = qs.filter(categoria_vestido=categoria)
    else:
        qs = qs.filter(categoria_vestido__isnull=True)
    return qs.select_related("transaccion")


def registrar_gasto_fondo(
    corte: CorteDia,
    concepto: str,
    monto: Decimal,
    pago: str,
) -> tuple[Transaccion, Vale]:
    if corte.cerrado:
        raise ValueError("No se pueden registrar gastos en un corte cerrado.")
    if monto <= 0:
        raise ValueError("El monto debe ser mayor a cero.")
    if pago not in (MetodoPago.PESOS, MetodoPago.DLLS):
        pago = MetodoPago.PESOS

    from api.services.conteo_caja import aplicar_vale_a_conteo_fondo
    from api.services.corte import _monto_en_pesos

    monto_mxn = _monto_en_pesos(monto, pago, corte.linea_negocio)
    ref = f"G{timezone.now().strftime('%Y%m%d%H%M%S')}"
    tx = Transaccion.objects.create(
        timestamp=timezone.now(),
        referencia=ref,
        cliente=concepto.upper(),
        pago=pago,
        monto=-abs(monto),
        linea_negocio=corte.linea_negocio,
        categoria_vestido=corte.categoria_vestido,
    )
    corte.conteo_fondo = aplicar_vale_a_conteo_fondo(corte.conteo_fondo, monto_mxn)
    corte.save(update_fields=["conteo_fondo", "actualizado_en"])
    vale = Vale.objects.create(
        fecha=corte.fecha,
        concepto=concepto.upper(),
        monto=abs(monto),
        pago=pago,
        monto_mxn=monto_mxn,
        linea_negocio=corte.linea_negocio,
        categoria_vestido=corte.categoria_vestido,
        transaccion=tx,
    )
    return tx, vale


def reponer_vale(corte: CorteDia, vale: Vale, *, ajustar_fondo: bool = True) -> Vale:
    if corte.cerrado:
        raise ValueError("No se pueden reponer vales en un corte cerrado.")
    if vale.estatus == Vale.Estatus.REPUSTO:
        raise ValueError("Este vale ya fue repuesto.")
    if vale.linea_negocio != corte.linea_negocio:
        raise ValueError("El vale no corresponde a esta línea de negocio.")
    if vale.categoria_vestido != corte.categoria_vestido:
        raise ValueError("El vale no corresponde a esta categoría.")

    from api.services.conteo_caja import reponer_monto_en_conteo_fondo

    if ajustar_fondo:
        corte.conteo_fondo = reponer_monto_en_conteo_fondo(corte.conteo_fondo, vale.monto_mxn)
        corte.save(update_fields=["conteo_fondo", "actualizado_en"])
    vale.estatus = Vale.Estatus.REPUSTO
    vale.repuesto_en = timezone.now()
    vale.save(update_fields=["estatus", "repuesto_en"])
    return vale
