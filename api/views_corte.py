from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from api.models import LineaNegocio, MetodoPago, Transaccion, Vale
from api.permissions import TienePerfilNegocio, categoria_vestido_usuario, linea_negocio_usuario
from api.serializers.corte import CorteDiaSerializer, parse_fecha_query, parse_turno_query
from api.serializers.transaccion import TransaccionSerializer
from api.services.corte import (
    calcular_resumen,
    cerrar_corte,
    corte_incluye_manana,
    estado_turnos_dia,
    multas_tardias_activas,
    obtener_o_crear_corte,
    resolver_turno,
    sincronizar_transacciones_dia,
    transacciones_del_corte,
)
from api.serializers.vale import ValeSerializer
from api.services.conteo_caja import normalizar_conteo, totales_conteo
from api.services.corte import _merge_totales_conteo
from api.services.finanzas import obtener_fondo_feria, obtener_tipo_cambio
from api.services.vales import registrar_gasto_fondo, reponer_vale, vales_pendientes


def _parse_categoria_query(categoria_param: str | None, linea: str, user) -> str | None:
    """Resuelve la categoría de vestido: desde query param o perfil de usuario."""
    if linea != LineaNegocio.VESTIDOS:
        return None
    if categoria_param:
        return categoria_param
    return categoria_vestido_usuario(user)


def _payload_corte(fecha, linea_negocio, turno=None, categoria=None):
    sincronizar_transacciones_dia(fecha, linea_negocio)
    turno = resolver_turno(fecha, linea_negocio, turno, categoria)
    corte = obtener_o_crear_corte(fecha, linea_negocio, turno, categoria)
    txs = transacciones_del_corte(corte)
    multas = [
        {
            "cliente": d.cliente,
            "rentaId": str(d.renta_id),
            "monto": float(d.penalizacion),
        }
        for d in multas_tardias_activas(linea_negocio, categoria)
    ]
    resumen = calcular_resumen(corte)
    conteo_cierre = normalizar_conteo(corte.conteo_fisico)
    conteo_fondo = normalizar_conteo(corte.conteo_fondo)
    conteo_caja = normalizar_conteo(corte.conteo_caja)
    totales_cierre = totales_conteo(conteo_cierre)
    totales_fondo = totales_conteo(conteo_fondo)
    totales_caja = totales_conteo(conteo_caja)
    tc = float(obtener_tipo_cambio(linea_negocio))

    usa_conteo_separado = bool(corte.conteo_caja)
    if usa_conteo_separado:
        totales_resumen = _merge_totales_conteo(totales_fondo, totales_caja)
        contado_mxn = (
            totales_fondo["mxnTotal"]
            + totales_fondo["usdTotal"] * tc
            + totales_caja["mxnTotal"]
            + totales_caja["usdTotal"] * tc
        )
    else:
        totales_resumen = totales_cierre
        contado_mxn = totales_cierre["mxnTotal"] + totales_cierre["usdTotal"] * tc

    vales_esperados_fondo = resumen.get(
        "valesEsperadosFondo",
        max(resumen["valesPendientesTotal"], totales_fondo.get("mxnVales", 0)),
    )
    esperado_total = (
        resumen["fondoFisico"]
        + resumen["cajaDelDia"]
        + vales_esperados_fondo
    )
    vales = list(vales_pendientes(linea_negocio, categoria))
    return {
        "fecha": fecha.isoformat(),
        "turno": corte.turno,
        "turnoLabel": corte.get_turno_display(),
        "incluyeManana": corte_incluye_manana(corte),
        "turnosDia": estado_turnos_dia(fecha, linea_negocio, categoria),
        "categoriaVestido": corte.categoria_vestido,
        "fondoInicial": float(corte.fondo_inicial),
        "fondoFeriaConfig": float(obtener_fondo_feria(linea_negocio)),
        "cerrado": corte.cerrado,
        "omitido": corte.omitido,
        "empleadoCorte": corte.empleado_corte or None,
        "cerradoEn": corte.cerrado_en.isoformat() if corte.cerrado_en else None,
        "conteoFondo": conteo_fondo,
        "conteoCaja": conteo_caja,
        "conteoFisico": conteo_cierre,
        "totalesFondo": {
            **totales_fondo,
            "equivalenteMxn": totales_fondo["mxnTotal"] + totales_fondo["usdTotal"] * tc,
        },
        "totalesCaja": {
            **totales_caja,
            "equivalenteMxn": totales_caja["mxnTotal"] + totales_caja["usdTotal"] * tc,
        },
        "totalesConteo": {
            **totales_resumen,
            "equivalenteMxn": contado_mxn,
            "tipoCambioUsd": tc,
            "diferenciaMxn": (contado_mxn - esperado_total) if corte.cerrado else None,
        },
        "resumen": resumen,
        "transacciones": TransaccionSerializer(txs, many=True).data,
        "valesPendientes": ValeSerializer(vales, many=True).data,
        "multasTardias": multas,
    }


@api_view(["GET", "PATCH"])
@permission_classes([TienePerfilNegocio])
def corte_dia(request):
    linea = linea_negocio_usuario(request.user)
    categoria = _parse_categoria_query(
        request.query_params.get("categoria"),
        linea,
        request.user,
    )
    try:
        fecha = parse_fecha_query(request.query_params.get("fecha"))
        turno = parse_turno_query(request.query_params.get("turno"))
    except Exception as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    corte = obtener_o_crear_corte(fecha, linea, turno, categoria)

    if request.method == "PATCH":
        if corte.cerrado:
            return Response(
                {"detail": "El corte de este turno ya está cerrado."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = CorteDiaSerializer(corte, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

    return Response(_payload_corte(fecha, linea, corte.turno, categoria))


@api_view(["POST"])
@permission_classes([TienePerfilNegocio])
def corte_cierre(request):
    linea = linea_negocio_usuario(request.user)
    categoria = _parse_categoria_query(
        request.data.get("categoria") or request.query_params.get("categoria"),
        linea,
        request.user,
    )
    try:
        fecha = parse_fecha_query(request.data.get("fecha") or request.query_params.get("fecha"))
        turno = parse_turno_query(request.data.get("turno") or request.query_params.get("turno"))
    except Exception as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    corte = obtener_o_crear_corte(fecha, linea, turno, categoria)
    if corte.cerrado:
        return Response(
            {"detail": "Este corte ya fue cerrado."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    conteo_fondo_raw = request.data.get("conteoFondo")
    conteo_caja_raw = request.data.get("conteoCaja")
    conteo_fisico_raw = request.data.get("conteoFisico")
    conteo_fondo = normalizar_conteo(conteo_fondo_raw) if conteo_fondo_raw is not None else None
    conteo_caja = normalizar_conteo(conteo_caja_raw) if conteo_caja_raw is not None else None
    conteo_fisico = normalizar_conteo(conteo_fisico_raw) if conteo_fisico_raw is not None else None
    empleado = str(request.data.get("empleado") or "").strip()
    if not empleado:
        return Response(
            {"detail": "El nombre del empleado es obligatorio."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        turno_cierre = turno or corte.turno
        if conteo_fondo is not None and conteo_caja is not None:
            cerrar_corte(
                fecha,
                linea,
                turno=turno_cierre,
                conteo_fondo=conteo_fondo,
                conteo_caja=conteo_caja,
                empleado=empleado,
                categoria=categoria,
            )
        elif conteo_fisico is not None:
            cerrar_corte(
                fecha,
                linea,
                turno=turno_cierre,
                conteo_fisico=conteo_fisico,
                empleado=empleado,
                categoria=categoria,
            )
        else:
            return Response(
                {"detail": "Se requiere conteoFondo y conteoCaja, o conteoFisico."},
                status=status.HTTP_400_BAD_REQUEST,
            )
    except ValueError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    return Response(_payload_corte(fecha, linea, corte.turno, categoria))


@api_view(["POST"])
@permission_classes([TienePerfilNegocio])
def corte_gasto(request):
    linea = linea_negocio_usuario(request.user)
    categoria = _parse_categoria_query(
        request.data.get("categoria"),
        linea,
        request.user,
    )
    try:
        fecha = parse_fecha_query(request.data.get("fecha"))
        turno = parse_turno_query(request.data.get("turno"))
    except Exception as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    corte = obtener_o_crear_corte(fecha, linea, turno, categoria)
    if corte.cerrado:
        return Response(
            {"detail": "No se pueden agregar movimientos a un corte cerrado."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    cliente = str(request.data.get("cliente", "Gasto operativo")).upper()
    monto = abs(float(request.data.get("monto", 0)))
    pago = request.data.get("pago", MetodoPago.PESOS)
    if pago not in (MetodoPago.PESOS, MetodoPago.DLLS):
        pago = MetodoPago.PESOS

    if monto <= 0:
        return Response({"detail": "El monto debe ser mayor a cero."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        tx, vale = registrar_gasto_fondo(corte, cliente, monto, pago)
    except ValueError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    return Response(
        {
            "transaccion": TransaccionSerializer(tx).data,
            "vale": ValeSerializer(vale).data,
            **_payload_corte(fecha, linea, corte.turno, categoria),
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["POST"])
@permission_classes([TienePerfilNegocio])
def corte_reponer_vale(request, vale_id):
    linea = linea_negocio_usuario(request.user)
    categoria = _parse_categoria_query(
        request.data.get("categoria"),
        linea,
        request.user,
    )
    try:
        fecha = parse_fecha_query(request.data.get("fecha"))
        turno = parse_turno_query(request.data.get("turno"))
    except Exception as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    corte = obtener_o_crear_corte(fecha, linea, turno, categoria)
    try:
        vale = Vale.objects.get(pk=vale_id, linea_negocio=linea, categoria_vestido=categoria)
    except Vale.DoesNotExist:
        return Response({"detail": "Vale no encontrado."}, status=status.HTTP_404_NOT_FOUND)

    try:
        vale = reponer_vale(
            corte,
            vale,
            ajustar_fondo=not bool(request.data.get("desdeConteo")),
        )
    except ValueError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    return Response(
        {
            "vale": ValeSerializer(vale).data,
            **_payload_corte(fecha, linea, corte.turno, categoria),
        },
    )
