from rest_framework import serializers

from api.models import Prenda

_CAMPOS_MAYUS = (
    "talla",
    "color",
    "detalles",
    "marca",
    "saco",
    "chaleco",
    "pantalon",
    "codigo_old",
    "codigo_new",
    "ubicacion",
)


class PrendaSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source="pk", read_only=True)
    codigoOld = serializers.CharField(source="codigo_old", allow_blank=True, required=False)
    codigoNew = serializers.CharField(source="codigo_new", allow_blank=True, required=False)

    class Meta:
        model = Prenda
        fields = [
            "id",
            "talla",
            "color",
            "detalles",
            "marca",
            "saco",
            "chaleco",
            "pantalon",
            "codigoOld",
            "codigoNew",
            "estatus",
            "ubicacion",
        ]

    def validate(self, attrs):
        for field in _CAMPOS_MAYUS:
            if field in attrs and attrs[field] is not None:
                attrs[field] = str(attrs[field]).upper()
        return attrs
