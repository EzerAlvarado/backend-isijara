from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from api.models import Abono, CorteDia, Devolucion, LineaNegocio, MetodoPago, Renta, Transaccion, TurnoCorte, Vale
from api.models.metodo_pago import es_pago_digital, es_pago_en_usd
from api.services.conteo_caja import normalizar_conteo, totales_conteo
from api.services.finanzas import obtener_fondo_feria, obtener_tipo_cambio


def _monto_en_pesos(monto: Decimal, pago: str, linea_negocio: str) -> Decimal:
    if es_pago_en_usd(pago):
        return Decimal(monto) * obtener_tipo_cambio(linea_negocio)
    return Decimal(monto)


def _monto_cobro_renta(renta: Renta) -> Decimal:
    """Dinero cobrado al registrar la renta. En BBVA/transferencia/tarjeta es el anticipo."""
    mxn = Decimal(renta.pago_efectivo_mxn or 0)
    usd = Decimal(renta.pago_efectivo_usd or 0)
    metodo = renta.metodo_pago or MetodoPago.PESOS
    anticipo = Decimal(renta.anticipo or 0)
    fondo = Decimal(renta.fondo or 0)

    if es_pago_digital(metodo):
        if anticipo > 0:
            return anticipo
        return fondo if fondo > 0 else Decimal("0")

    if mxn > 0 or usd > 0:
        if es_pago_en_usd(metodo):
            if usd > 0:
                return usd
            return anticipo if anticipo > 0 else Decimal("0")
        if mxn > 0:
            return mxn
        return anticipo if anticipo > 0 else Decimal("0")

    if anticipo > 0:
        return anticipo
    return fondo if fondo > 0 else Decimal("0")


def _inicio_fin_dia(fecha: date) -> tuple[datetime, datetime]:
    tz = timezone.get_current_timezone()
    inicio = timezone.make_aware(datetime.combine(fecha, time.min), tz)
    fin = timezone.make_aware(datetime.combine(fecha, time.max), tz)
    return inicio, fin


def _cliente_renta(renta: Renta) -> str:
    if isinstance(renta.cliente, dict):
        return str(renta.cliente.get("valor", "")).upper()
    return ""


def _tx_anulada(referencia: str, linea: str) -> bool:
    return Transaccion.objects.filter(
        referencia=referencia,
        linea_negocio=linea,
        anulada=True,
    ).exists()


def _qs_multa_renta(renta_pk: int, linea: str):
    """Movimientos de multa de una renta: MR{id} y MR{id}-2, MR{id}-3…"""
    base = f"MR{renta_pk}"
    return Transaccion.objects.filter(linea_negocio=linea).filter(
        Q(referencia=base) | Q(referencia__startswith=f"{base}-")
    )


def _siguiente_ref_multa_renta(renta_pk: int, linea: str) -> str:
    base = f"MR{renta_pk}"
    usadas = set(_qs_multa_renta(renta_pk, linea).values_list("referencia", flat=True))
    if base not in usadas:
        return base
    n = 2
    while f"{base}-{n}" in usadas:
        n += 1
    return f"{base}-{n}"


def registrar_transaccion_renta(renta: Renta) -> None:
    linea = renta.linea_negocio or LineaNegocio.TRAJES
    categoria = renta.categoria_vestido if linea == LineaNegocio.VESTIDOS else None
    referencia = f"R{renta.pk}"

    # Rentas capturadas de papel / anticipo cobrado antes: no entran al corte
    if getattr(renta, "excluir_corte", False):
        if not _tx_anulada(referencia, linea):
            Transaccion.objects.filter(referencia=referencia, linea_negocio=linea).delete()
        return

    monto = _monto_cobro_renta(renta)
    if monto <= 0:
        if not _tx_anulada(referencia, linea):
            Transaccion.objects.filter(referencia=referencia, linea_negocio=linea).delete()
        return

    if _tx_anulada(referencia, linea):
        return

    pago = renta.metodo_pago or MetodoPago.PESOS
    if pago in (MetodoPago.DLLS, MetodoPago.MIXTO) and renta.anticipo <= 0 and renta.fondo > 0:
        pago = MetodoPago.PESOS
    if pago == MetodoPago.MIXTO:
        pago = MetodoPago.PESOS

    Transaccion.objects.update_or_create(
        referencia=referencia,
        linea_negocio=linea,
        defaults={
            "timestamp": renta.creado_en or timezone.now(),
            "cliente": _cliente_renta(renta) or f"RENTA #{renta.pk}",
            "pago": pago,
            "monto": monto,
            "categoria_vestido": categoria,
        },
    )


def _aplicar_defaults_sin_mover_hora(tx: Transaccion, defaults: dict) -> Transaccion:
    """Actualiza monto/cliente/pago sin cambiar la hora (el turno del corte)."""
    campos = []
    for campo, valor in defaults.items():
        if campo == "timestamp":
            continue
        if getattr(tx, campo) != valor:
            setattr(tx, campo, valor)
            campos.append(campo)
    if campos:
        tx.save(update_fields=campos)
    return tx


def _upsert_transaccion_conservando_hora(
    *,
    referencia: str,
    linea: str,
    defaults: dict,
) -> Transaccion | None:
    existing = Transaccion.objects.filter(referencia=referencia, linea_negocio=linea).first()
    if existing:
        if existing.anulada:
            return existing
        return _aplicar_defaults_sin_mover_hora(existing, defaults)
    create_data = {k: v for k, v in defaults.items() if k != "timestamp"}
    return Transaccion.objects.create(
        referencia=referencia,
        linea_negocio=linea,
        timestamp=defaults.get("timestamp") or timezone.now(),
        **create_data,
    )


def registrar_transaccion_multa(devolucion: Devolucion) -> None:
    linea = devolucion.renta.linea_negocio if devolucion.renta_id else LineaNegocio.TRAJES
    categoria = None
    if devolucion.renta_id and linea == LineaNegocio.VESTIDOS:
        categoria = devolucion.renta.categoria_vestido
    referencia = f"M{devolucion.pk}"
    if devolucion.multa_perdonada or devolucion.penalizacion <= 0:
        if not _tx_anulada(referencia, linea):
            Transaccion.objects.filter(referencia=referencia, linea_negocio=linea).delete()
        return

    if _tx_anulada(referencia, linea):
        return

    _upsert_transaccion_conservando_hora(
        referencia=referencia,
        linea=linea,
        defaults={
            "timestamp": timezone.now(),
            "cliente": (devolucion.cliente or "").upper(),
            "pago": MetodoPago.PESOS,
            "monto": devolucion.penalizacion,
            "categoria_vestido": categoria,
        },
    )


def registrar_transaccion_abono(abono: Abono) -> None:
    renta = abono.renta
    linea = renta.linea_negocio or LineaNegocio.TRAJES
    categoria = renta.categoria_vestido if linea == LineaNegocio.VESTIDOS else None
    referencia = f"A{abono.pk}"
    if abono.monto <= 0:
        if not _tx_anulada(referencia, linea):
            Transaccion.objects.filter(referencia=referencia, linea_negocio=linea).delete()
        return

    if _tx_anulada(referencia, linea):
        return

    pago = abono.metodo_pago or MetodoPago.PESOS
    if pago == MetodoPago.MIXTO:
        pago = MetodoPago.PESOS

    Transaccion.objects.update_or_create(
        referencia=referencia,
        linea_negocio=linea,
        defaults={
            "timestamp": abono.creado_en,
            "cliente": _cliente_renta(renta) or f"RENTA #{renta.pk}",
            "pago": pago,
            "monto": abono.monto,
            "categoria_vestido": categoria,
        },
    )


def registrar_transaccion_danos(devolucion: Devolucion) -> None:
    linea = devolucion.renta.linea_negocio if devolucion.renta_id else LineaNegocio.TRAJES
    categoria = None
    if devolucion.renta_id and linea == LineaNegocio.VESTIDOS:
        categoria = devolucion.renta.categoria_vestido
    referencia = f"D{devolucion.pk}"
    if devolucion.cargo_danos <= 0:
        if not _tx_anulada(referencia, linea):
            Transaccion.objects.filter(referencia=referencia, linea_negocio=linea).delete()
        return

    if _tx_anulada(referencia, linea):
        return

    _upsert_transaccion_conservando_hora(
        referencia=referencia,
        linea=linea,
        defaults={
            "timestamp": timezone.now(),
            "cliente": (devolucion.cliente or "").upper(),
            "pago": MetodoPago.PESOS,
            "monto": devolucion.cargo_danos,
            "categoria_vestido": categoria,
        },
    )


def registrar_transaccion_multa_renta(renta: Renta) -> None:
    linea = renta.linea_negocio or LineaNegocio.TRAJES
    categoria = renta.categoria_vestido if linea == LineaNegocio.VESTIDOS else None
    qs = _qs_multa_renta(renta.pk, linea)

    if renta.cargo_danos <= 0:
        qs.filter(anulada=False).delete()
        return

    activa = qs.filter(anulada=False).order_by("-id").first()
    defaults = {
        "timestamp": timezone.now(),
        "cliente": _cliente_renta(renta) or f"RENTA #{renta.pk}",
        "pago": MetodoPago.PESOS,
        "monto": renta.cargo_danos,
        "categoria_vestido": categoria,
    }
    if activa:
        _aplicar_defaults_sin_mover_hora(activa, defaults)
        return

    Transaccion.objects.create(
        referencia=_siguiente_ref_multa_renta(renta.pk, linea),
        linea_negocio=linea,
        **defaults,
    )


def _anular_transaccion_ref(referencia: str, linea: str) -> None:
    now = timezone.now()
    Transaccion.objects.filter(
        referencia=referencia,
        linea_negocio=linea,
        anulada=False,
    ).update(anulada=True, anulada_en=now)


def anular_transacciones_renta(renta: Renta) -> None:
    """Al eliminar una renta, sus movimientos de corte ya no deben contar en ingresos."""
    linea = renta.linea_negocio or LineaNegocio.TRAJES
    _anular_transaccion_ref(f"R{renta.pk}", linea)
    for abono_id in renta.abonos.values_list("pk", flat=True):
        _anular_transaccion_ref(f"A{abono_id}", linea)
    for ref in _qs_multa_renta(renta.pk, linea).values_list("referencia", flat=True):
        _anular_transaccion_ref(ref, linea)


def _limpiar_transacciones_huerfanas(linea_negocio: str) -> None:
    """Rentas/abonos borrados dejan transacciones R*/A* activas: se anulan."""
    txs = Transaccion.objects.filter(linea_negocio=linea_negocio, anulada=False)
    for tx in txs.iterator():
        ref = tx.referencia or ""
        if len(ref) > 1 and ref[0] == "R" and ref[1:].isdigit():
            if not Renta.objects.filter(pk=int(ref[1:])).exists():
                _anular_transaccion_ref(ref, linea_negocio)
        elif len(ref) > 1 and ref[0] == "A" and ref[1:].isdigit():
            if not Abono.objects.filter(pk=int(ref[1:])).exists():
                _anular_transaccion_ref(ref, linea_negocio)


def sincronizar_transacciones_dia(fecha: date, linea_negocio: str) -> None:
    _limpiar_transacciones_huerfanas(linea_negocio)
    inicio, fin = _inicio_fin_dia(fecha)
    with transaction.atomic():
        for renta in Renta.objects.filter(
            creado_en__range=(inicio, fin),
            linea_negocio=linea_negocio,
        ):
            registrar_transaccion_renta(renta)

        for abono in Abono.objects.filter(
            creado_en__range=(inicio, fin),
            renta__linea_negocio=linea_negocio,
        ).select_related("renta"):
            registrar_transaccion_abono(abono)

        for dev in Devolucion.objects.filter(
            estatus=Devolucion.Estatus.REGRESADO,
            renta__linea_negocio=linea_negocio,
        ):
            registrar_transaccion_multa(dev)
            registrar_transaccion_danos(dev)

        for renta in Renta.objects.filter(
            cargo_danos__gt=0,
            linea_negocio=linea_negocio,
        ):
            registrar_transaccion_multa_renta(renta)


def _corte_turno(fecha: date, linea_negocio: str, turno: str, categoria: str | None = None) -> CorteDia | None:
    return CorteDia.objects.filter(
        fecha=fecha,
        linea_negocio=linea_negocio,
        turno=turno,
        categoria_vestido=categoria,
    ).first()


def _ultimo_corte_cerrado_antes(fecha: date, linea_negocio: str, turno: str, categoria: str | None = None) -> CorteDia | None:
    """Último corte cerrado inmediatamente anterior a fecha/turno."""
    if turno == TurnoCorte.TARDE:
        manana = _corte_turno(fecha, linea_negocio, TurnoCorte.MANANA, categoria)
        if manana and manana.cerrado:
            return manana

    anterior = fecha - timedelta(days=1)
    tarde_ant = _corte_turno(anterior, linea_negocio, TurnoCorte.TARDE, categoria)
    if tarde_ant and tarde_ant.cerrado:
        return tarde_ant
    manana_ant = _corte_turno(anterior, linea_negocio, TurnoCorte.MANANA, categoria)
    if manana_ant and manana_ant.cerrado:
        return manana_ant
    return None


def _fondo_herencia(fecha: date, linea_negocio: str, turno: str, categoria: str | None = None) -> tuple[Decimal, dict] | None:
    corte_ant = _ultimo_corte_cerrado_antes(fecha, linea_negocio, turno, categoria)
    if not corte_ant:
        return None
    fondo = corte_ant.fondo_inicial if corte_ant.fondo_inicial > 0 else obtener_fondo_feria(linea_negocio)
    conteo = normalizar_conteo(corte_ant.conteo_fondo)
    return fondo, conteo


def _conteo_tiene_desglose(conteo: dict | None) -> bool:
    t = totales_conteo(conteo)
    return (
        Decimal(str(t.get("mxnVales", 0))) > 0
        or Decimal(str(t["mxnBilletes"])) > 0
        or Decimal(str(t["mxnMonedas"])) > 0
        or Decimal(str(t["usdTotal"])) > 0
    )


def vales_esperados_fondo(conteo_fondo: dict | None, vales_pendientes_total: Decimal) -> Decimal:
    """Vales que deben contarse en fondo: pendientes en BD o ya registrados en conteo."""
    t = totales_conteo(conteo_fondo)
    mxn_vales_conteo = Decimal(str(t.get("mxnVales", 0)))
    return max(vales_pendientes_total, mxn_vales_conteo)


def _preservar_vales_conteo_fondo(
    nuevo: dict,
    anterior: dict,
    vales_pendientes_total: Decimal,
) -> dict:
    """Evita perder vales al cerrar si el conteo enviado no incluyó la fila de vales."""
    resultado = normalizar_conteo(nuevo)
    if int(resultado.get("valesMxn", 0) or 0) > 0:
        return resultado

    prev = normalizar_conteo(anterior)
    vales_prev = int(prev.get("valesMxn", 0) or 0)
    if vales_prev > 0:
        resultado["valesMxn"] = vales_prev
        return resultado

    if vales_pendientes_total > 0:
        resultado["valesMxn"] = int(vales_pendientes_total.to_integral_value())
    return resultado


def _sincronizar_fondo_feria(corte: CorteDia) -> CorteDia:
    if corte.cerrado:
        return corte
    changed = False
    herencia = _fondo_herencia(corte.fecha, corte.linea_negocio, corte.turno, corte.categoria_vestido)
    if corte.fondo_inicial <= 0:
        corte.fondo_inicial = herencia[0] if herencia else obtener_fondo_feria(corte.linea_negocio)
        changed = True
    if herencia:
        _, conteo_heredado = herencia
        actual = normalizar_conteo(corte.conteo_fondo)
        heredado = normalizar_conteo(conteo_heredado)
        vales_actual = int(actual.get("valesMxn", 0) or 0)
        vales_heredado = int(heredado.get("valesMxn", 0) or 0)
        if not corte.conteo_fondo:
            corte.conteo_fondo = heredado
            changed = True
        elif not _conteo_tiene_desglose(actual) and _conteo_tiene_desglose(heredado):
            corte.conteo_fondo = heredado
            changed = True
        elif vales_heredado > vales_actual:
            actual["valesMxn"] = vales_heredado
            corte.conteo_fondo = actual
            changed = True
    if changed:
        corte.save(update_fields=["fondo_inicial", "conteo_fondo", "actualizado_en"])
    return corte


def resolver_turno(fecha: date, linea_negocio: str, turno: str | None = None, categoria: str | None = None) -> str:
    if turno in (TurnoCorte.MANANA, TurnoCorte.TARDE):
        return turno

    manana = _corte_turno(fecha, linea_negocio, TurnoCorte.MANANA, categoria)
    tarde = _corte_turno(fecha, linea_negocio, TurnoCorte.TARDE, categoria)

    if manana and not manana.cerrado:
        return TurnoCorte.MANANA
    if tarde and not tarde.cerrado:
        return TurnoCorte.TARDE
    if manana and manana.cerrado and (not tarde or not tarde.cerrado):
        return TurnoCorte.TARDE
    return TurnoCorte.MANANA


def obtener_o_crear_corte(
    fecha: date,
    linea_negocio: str,
    turno: str | None = None,
    categoria: str | None = None,
) -> CorteDia:
    turno = resolver_turno(fecha, linea_negocio, turno, categoria)
    herencia = _fondo_herencia(fecha, linea_negocio, turno, categoria)
    defaults: dict = {
        "fondo_inicial": obtener_fondo_feria(linea_negocio),
        "conteo_fondo": {},
    }
    if herencia:
        fondo, conteo = herencia
        defaults = {"fondo_inicial": fondo, "conteo_fondo": conteo}

    corte, created = CorteDia.objects.get_or_create(
        fecha=fecha,
        linea_negocio=linea_negocio,
        turno=turno,
        categoria_vestido=categoria,
        defaults=defaults,
    )
    if not created:
        corte = _sincronizar_fondo_feria(corte)
    return corte


def corte_incluye_manana(corte: CorteDia) -> bool:
    if corte.turno != TurnoCorte.TARDE:
        return False
    manana = _corte_turno(corte.fecha, corte.linea_negocio, TurnoCorte.MANANA, corte.categoria_vestido)
    if not manana:
        return False
    if manana.omitido:
        return True
    return not manana.cerrado


def _rango_transacciones_corte(corte: CorteDia) -> tuple[datetime, datetime]:
    inicio_dia, fin_dia = _inicio_fin_dia(corte.fecha)
    manana = _corte_turno(corte.fecha, corte.linea_negocio, TurnoCorte.MANANA, corte.categoria_vestido)

    if corte.turno == TurnoCorte.MANANA:
        inicio = inicio_dia
        if corte.cerrado and corte.cerrado_en:
            fin = corte.cerrado_en
        else:
            fin = min(timezone.now(), fin_dia)
        return inicio, fin

    if manana and manana.cerrado and manana.cerrado_en and not manana.omitido:
        inicio = manana.cerrado_en
    else:
        inicio = inicio_dia

    if corte.cerrado and corte.cerrado_en:
        fin = corte.cerrado_en
    else:
        fin = min(timezone.now(), fin_dia)
    return inicio, fin


def _filtro_categoria_transaccion(qs, categoria: str | None):
    """Trajes usa categoria NULL; algunas filas viejas tienen cadena vacía."""
    if categoria:
        return qs.filter(categoria_vestido=categoria)
    return qs.filter(Q(categoria_vestido__isnull=True) | Q(categoria_vestido=""))


def transacciones_del_corte(corte: CorteDia):
    inicio, fin = _rango_transacciones_corte(corte)
    qs = Transaccion.objects.filter(
        timestamp__range=(inicio, fin),
        linea_negocio=corte.linea_negocio,
        anulada=False,
    )
    return _filtro_categoria_transaccion(qs, corte.categoria_vestido).order_by("-timestamp")


def transacciones_del_dia(fecha: date, linea_negocio: str):
    inicio, fin = _inicio_fin_dia(fecha)
    return Transaccion.objects.filter(
        timestamp__range=(inicio, fin),
        linea_negocio=linea_negocio,
        anulada=False,
    ).order_by("-timestamp")


def _categorias_corte_coinciden(tx_categoria: str | None, corte_categoria: str | None) -> bool:
    tx_cat = tx_categoria or None
    corte_cat = corte_categoria or None
    if tx_cat is None and corte_cat is None:
        return True
    return tx_cat == corte_cat


def anular_transaccion(corte: CorteDia, tx: Transaccion) -> Transaccion:
    """Saca un movimiento del corte de forma permanente (caso excepcional)."""
    if corte.cerrado:
        raise ValueError("No se pueden anular movimientos en un corte cerrado.")
    if tx.anulada:
        raise ValueError("Este movimiento ya fue anulado.")
    if tx.linea_negocio != corte.linea_negocio:
        raise ValueError("El movimiento no corresponde a esta línea de negocio.")
    if not _categorias_corte_coinciden(tx.categoria_vestido, corte.categoria_vestido):
        raise ValueError("El movimiento no corresponde a esta categoría.")

    inicio, fin = _rango_transacciones_corte(corte)
    if not (inicio <= tx.timestamp <= fin):
        raise ValueError("El movimiento no pertenece a este turno de corte.")

    from api.services.vales import es_gasto_fondo, reponer_vale

    with transaction.atomic():
        if es_gasto_fondo(tx.referencia):
            vale = Vale.objects.filter(transaccion=tx).first()
            if vale and vale.estatus == Vale.Estatus.PENDIENTE:
                reponer_vale(corte, vale, ajustar_fondo=True)

        tx.anulada = True
        tx.anulada_en = timezone.now()
        tx.save(update_fields=["anulada", "anulada_en"])

    return tx


def mover_transaccion_a_turno(corte: CorteDia, tx: Transaccion, turno_destino: str) -> Transaccion:
    """Pasa un movimiento al otro turno del mismo día (ej. multa cobrada en la mañana)."""
    if corte.cerrado:
        raise ValueError("Reabre el corte para mover un movimiento a otro turno.")
    if tx.anulada:
        raise ValueError("No se puede mover un movimiento anulado.")
    if tx.linea_negocio != corte.linea_negocio:
        raise ValueError("El movimiento no corresponde a esta línea de negocio.")
    if not _categorias_corte_coinciden(tx.categoria_vestido, corte.categoria_vestido):
        raise ValueError("El movimiento no corresponde a esta categoría.")
    if turno_destino not in (TurnoCorte.MANANA, TurnoCorte.TARDE):
        raise ValueError("Turno destino inválido.")
    if turno_destino == corte.turno:
        raise ValueError("El movimiento ya está en ese turno.")

    inicio, fin = _rango_transacciones_corte(corte)
    if not (inicio <= tx.timestamp <= fin):
        raise ValueError("El movimiento no pertenece a este turno de corte.")

    inicio_dia, fin_dia = _inicio_fin_dia(corte.fecha)
    manana = _corte_turno(corte.fecha, corte.linea_negocio, TurnoCorte.MANANA, corte.categoria_vestido)

    if turno_destino == TurnoCorte.MANANA:
        if manana and manana.cerrado and manana.cerrado_en and not manana.omitido:
            nuevo = manana.cerrado_en - timedelta(seconds=1)
        else:
            nuevo = inicio_dia + timedelta(hours=10)
    elif manana and manana.cerrado and manana.cerrado_en and not manana.omitido:
        nuevo = manana.cerrado_en + timedelta(seconds=1)
    else:
        nuevo = inicio_dia + timedelta(hours=16)

    if nuevo < inicio_dia:
        nuevo = inicio_dia + timedelta(minutes=1)
    if nuevo > fin_dia:
        nuevo = fin_dia

    tx.timestamp = nuevo
    tx.save(update_fields=["timestamp"])
    return tx


def multas_tardias_activas(linea_negocio: str, categoria: str | None = None):
    qs = Devolucion.objects.filter(
        penalizacion__gt=0,
        estatus=Devolucion.Estatus.RETRASADO,
        renta__linea_negocio=linea_negocio,
    ).select_related("renta")
    if categoria:
        qs = qs.filter(renta__categoria_vestido=categoria)
    return qs


def _fondo_fisico_en_caja(
    fondo_inicial: Decimal,
    conteo_fondo: dict | None,
    linea_negocio: str,
    vales_pendientes_total: Decimal,
) -> Decimal:
    """Efectivo físico del fondo (billetes/monedas), sin vales que ya salieron de la caja."""
    t = totales_conteo(conteo_fondo)
    mxn_vales = Decimal(str(t.get("mxnVales", 0)))
    tiene_desglose = (
        mxn_vales > 0
        or Decimal(str(t["mxnBilletes"])) > 0
        or Decimal(str(t["mxnMonedas"])) > 0
        or Decimal(str(t["usdTotal"])) > 0
    )
    if tiene_desglose:
        tc = obtener_tipo_cambio(linea_negocio)
        return (
            Decimal(str(t["mxnTotal"]))
            - mxn_vales
            + Decimal(str(t["usdTotal"])) * tc
        )
    return max(Decimal("0"), fondo_inicial - vales_pendientes_total)


def calcular_resumen(corte: CorteDia) -> dict:
    from api.services.vales import es_gasto_fondo, vales_pendientes

    txs = list(transacciones_del_corte(corte))
    ingresos = Decimal("0")
    gastos_fondo = Decimal("0")
    caja_dia = Decimal("0")
    digital_pesos = Decimal("0")

    for tx in txs:
        monto = Decimal(tx.monto)
        monto_mxn = _monto_en_pesos(monto, tx.pago, corte.linea_negocio)

        if es_gasto_fondo(tx.referencia):
            gastos_fondo += abs(monto_mxn)
            continue

        if monto > 0:
            ingresos += monto_mxn

        if tx.pago in (MetodoPago.PESOS, MetodoPago.DLLS):
            caja_dia += monto_mxn
        elif es_pago_digital(tx.pago):
            if monto > 0:
                digital_pesos += monto_mxn

    vales = vales_pendientes(corte.linea_negocio, corte.categoria_vestido)
    vales_pendientes_total = sum((Decimal(v.monto_mxn) for v in vales), Decimal("0"))
    vales_esperados = vales_esperados_fondo(corte.conteo_fondo, vales_pendientes_total)
    fondo_fisico = _fondo_fisico_en_caja(
        corte.fondo_inicial,
        corte.conteo_fondo,
        corte.linea_negocio,
        vales_pendientes_total,
    )

    total_en_caja = fondo_fisico + caja_dia
    return {
        "ingresosTotales": float(ingresos),
        "cajaDelDia": float(caja_dia),
        "totalEnCaja": float(total_en_caja),
        "efectivoEnCaja": float(total_en_caja),
        "gastosDelFondo": float(gastos_fondo),
        "gastosDiarios": float(gastos_fondo),
        "valesPendientesTotal": float(vales_pendientes_total),
        "valesEsperadosFondo": float(vales_esperados),
        "ingresosTarjeta": float(max(digital_pesos, Decimal("0"))),
        "fondoInicial": float(corte.fondo_inicial),
        "fondoFisico": float(fondo_fisico),
    }


def _omitir_corte_manana(manana: CorteDia) -> None:
    if manana.cerrado:
        return
    manana.cerrado = True
    manana.omitido = True
    manana.cerrado_en = timezone.now()
    manana.save(update_fields=["cerrado", "omitido", "cerrado_en", "actualizado_en"])


def _propagar_fondo_tras_cierre(corte: CorteDia) -> None:
    fondo = corte.fondo_inicial if corte.fondo_inicial > 0 else obtener_fondo_feria(corte.linea_negocio)
    conteo = normalizar_conteo(corte.conteo_fondo)

    if corte.turno == TurnoCorte.MANANA:
        fecha_sig = corte.fecha
        turno_sig = TurnoCorte.TARDE
    else:
        fecha_sig = corte.fecha + timedelta(days=1)
        turno_sig = TurnoCorte.MANANA

    corte_sig, created = CorteDia.objects.get_or_create(
        fecha=fecha_sig,
        linea_negocio=corte.linea_negocio,
        turno=turno_sig,
        categoria_vestido=corte.categoria_vestido,
        defaults={
            "fondo_inicial": fondo,
            "conteo_fondo": conteo,
        },
    )
    if created or not corte_sig.cerrado:
        corte_sig.fondo_inicial = fondo
        corte_sig.conteo_fondo = conteo
        corte_sig.save(update_fields=["fondo_inicial", "conteo_fondo", "actualizado_en"])


def estado_turnos_dia(fecha: date, linea_negocio: str, categoria: str | None = None) -> list[dict]:
    turnos = []
    for turno in (TurnoCorte.MANANA, TurnoCorte.TARDE):
        corte = _corte_turno(fecha, linea_negocio, turno, categoria)
        turnos.append(
            {
                "turno": turno,
                "label": dict(TurnoCorte.choices)[turno],
                "existe": corte is not None,
                "cerrado": bool(corte and corte.cerrado),
                "omitido": bool(corte and corte.omitido),
                "cerradoEn": corte.cerrado_en.isoformat() if corte and corte.cerrado_en else None,
                "empleadoCorte": corte.empleado_corte if corte and corte.empleado_corte else None,
            }
        )
    return turnos


def _merge_totales_conteo(a: dict, b: dict) -> dict:
    return {
        "mxnBilletes": a["mxnBilletes"] + b["mxnBilletes"],
        "mxnMonedas": a["mxnMonedas"] + b["mxnMonedas"],
        "mxnVales": a.get("mxnVales", 0) + b.get("mxnVales", 0),
        "mxnTotal": a["mxnTotal"] + b["mxnTotal"],
        "usdTotal": a["usdTotal"] + b["usdTotal"],
    }


def cerrar_corte(
    fecha: date,
    linea_negocio: str,
    turno: str | None = None,
    conteo_fisico: dict | None = None,
    conteo_fondo: dict | None = None,
    conteo_caja: dict | None = None,
    empleado: str = "",
    categoria: str | None = None,
) -> CorteDia:
    empleado = str(empleado or "").strip().upper()
    if not empleado:
        raise ValueError("El nombre del empleado es obligatorio.")

    turno = resolver_turno(fecha, linea_negocio, turno, categoria)
    corte = obtener_o_crear_corte(fecha, linea_negocio, turno, categoria)

    if corte.turno == TurnoCorte.TARDE:
        manana = _corte_turno(fecha, linea_negocio, TurnoCorte.MANANA, categoria)
        if manana and not manana.cerrado:
            _omitir_corte_manana(manana)

    corte.cerrado = True
    corte.cerrado_en = timezone.now()
    corte.empleado_corte = empleado

    from api.services.vales import vales_pendientes

    vales_pendientes_total = sum(
        (Decimal(v.monto_mxn) for v in vales_pendientes(linea_negocio)),
        Decimal("0"),
    )

    update_fields = ["cerrado", "cerrado_en", "empleado_corte", "actualizado_en"]
    if conteo_fondo is not None and conteo_caja is not None:
        corte.conteo_fondo = _preservar_vales_conteo_fondo(
            conteo_fondo,
            corte.conteo_fondo,
            vales_pendientes_total,
        )
        corte.conteo_caja = normalizar_conteo(conteo_caja)
        update_fields.extend(["conteo_fondo", "conteo_caja"])
    elif conteo_fisico is not None:
        corte.conteo_fisico = normalizar_conteo(conteo_fisico)
        update_fields.append("conteo_fisico")
    else:
        raise ValueError("Se requiere el conteo de fondo y caja, o un conteo físico total.")

    corte.save(update_fields=update_fields)
    _propagar_fondo_tras_cierre(corte)
    return corte


def reabrir_corte(
    fecha: date,
    linea_negocio: str,
    turno: str | None = None,
    categoria: str | None = None,
) -> CorteDia:
    """Reabre un corte cerrado para corregir el conteo y volver a cerrarlo."""
    turno = resolver_turno(fecha, linea_negocio, turno, categoria)
    corte = obtener_o_crear_corte(fecha, linea_negocio, turno, categoria)
    if not corte.cerrado:
        raise ValueError("Este corte ya está abierto.")

    corte.cerrado = False
    corte.omitido = False
    corte.cerrado_en = None
    corte.save(update_fields=["cerrado", "omitido", "cerrado_en", "actualizado_en"])
    return corte
