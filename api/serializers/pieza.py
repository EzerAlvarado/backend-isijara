from rest_framework import serializers

from api.models import Pieza
from api.services.inventario_tipos import tipo_permitido

_CAMPOS_MAYUS = (
    "color",
    "color_vestido",
    "talla",
    "marca",
    "detalles",
    "codigo_old",
    "codigo_new",
    "conjunto",
    "ubicacion",
)


class PiezaSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source="pk", read_only=True)
    codigoOld = serializers.CharField(source="codigo_old", allow_blank=True, required=False)
    codigoNew = serializers.CharField(source="codigo_new", allow_blank=True, required=False)
    colorVestido = serializers.CharField(
        source="color_vestido",
        allow_blank=True,
        required=False,
    )
    precioRenta = serializers.DecimalField(
        source="precio_renta",
        max_digits=10,
        decimal_places=2,
        required=False,
        default=0,
    )
    precioVenta = serializers.DecimalField(
        source="precio_venta",
        max_digits=10,
        decimal_places=2,
        required=False,
        default=0,
    )
    precioPremier = serializers.DecimalField(
        source="precio_premier",
        max_digits=10,
        decimal_places=2,
        required=False,
        default=0,
    )

    class Meta:
        model = Pieza
        fields = [
            "id",
            "tipo",
            "color",
            "colorVestido",
            "talla",
            "marca",
            "detalles",
            "codigoOld",
            "codigoNew",
            "conjunto",
            "estatus",
            "precioRenta",
            "precioVenta",
            "precioPremier",
            "ubicacion",
        ]

    def validate(self, attrs):
        for field in _CAMPOS_MAYUS:
            if field in attrs and attrs[field] is not None:
                attrs[field] = str(attrs[field]).upper()

        linea = self.context.get("linea_negocio")
        tipo = attrs.get("tipo")
        if tipo is None and self.instance:
            tipo = self.instance.tipo
        if linea and tipo and not tipo_permitido(linea, tipo):
            raise serializers.ValidationError(
                {"tipo": f"El tipo '{tipo}' no corresponde a la línea de negocio '{linea}'."}
            )
        return attrs
