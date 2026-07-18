from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from api.permissions import TienePerfilNegocio, linea_negocio_usuario
from api.serializers.finanzas import ConfiguracionFinanzasSerializer
from api.services.finanzas import obtener_configuracion


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
