from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from api.permissions import TienePerfilNegocio, linea_negocio_usuario
from api.serializers.finanzas import ConfiguracionFinanzasSerializer
from api.services.finanzas import obtener_configuracion
from api.services.ingresos import ingresos_mensuales
from api.services.ocupacion import alertas_reuso_vestido, conteo_piezas_anio


@api_view(["GET", "PATCH"])
@permission_classes([TienePerfilNegocio])
def configuracion_finanzas(request):
    linea = linea_negocio_usuario(request.user)
    config = obtener_configuracion(linea)

    if request.method == "PATCH":
        serializer = ConfiguracionFinanzasSerializer(config, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        config.refresh_from_db()

    return Response(ConfiguracionFinanzasSerializer(config).data)


@api_view(["GET"])
@permission_classes([TienePerfilNegocio])
def ingresos_mes(request):
    ahora = timezone.now()
    try:
        anio = int(request.query_params.get("anio") or ahora.year)
        mes = int(request.query_params.get("mes") or ahora.month)
    except (TypeError, ValueError):
        return Response({"detail": "Año o mes inválido."}, status=400)
    if anio < 2000 or anio > 2100 or mes < 1 or mes > 12:
        return Response({"detail": "Año o mes fuera de rango."}, status=400)
    return Response(ingresos_mensuales(anio, mes))


@api_view(["GET"])
@permission_classes([TienePerfilNegocio])
def ocupacion_anio(request):
    ahora = timezone.now()
    try:
        anio = int(request.query_params.get("anio") or ahora.year)
    except (TypeError, ValueError):
        return Response({"detail": "Año inválido."}, status=400)
    if anio < 2000 or anio > 2100:
        return Response({"detail": "Año fuera de rango."}, status=400)
    return Response(conteo_piezas_anio(anio))


@api_view(["GET"])
@permission_classes([TienePerfilNegocio])
def alertas_reuso(request):
    try:
        dias = int(request.query_params.get("dias") or 10)
    except (TypeError, ValueError):
        return Response({"detail": "Días inválidos."}, status=400)
    if dias < 1 or dias > 60:
        return Response({"detail": "Días fuera de rango."}, status=400)
    categoria = (request.query_params.get("categoria") or "quince").strip().lower()
    return Response(alertas_reuso_vestido(dias_alerta=dias, categoria=categoria))
