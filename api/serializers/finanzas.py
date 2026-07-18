from decimal import Decimal

from rest_framework import serializers

from api.models.configuracion import ConfiguracionSistema


class PrecioReferenciaSerializer(serializers.Serializer):
    id = serializers.CharField(max_length=64)
    nombre = serializers.CharField(max_length=200)
    precioMxn = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0"),
    )


class ConfiguracionFinanzasSerializer(serializers.ModelSerializer):
    tipoCambioUsd = serializers.DecimalField(
        source="tipo_cambio_usd",
        max_digits=8,
        decimal_places=2,
        min_value=Decimal("0.01"),
    )
    multaPorDia = serializers.DecimalField(
        source="multa_por_dia",
        max_digits=8,
        decimal_places=2,
        min_value=Decimal("0"),
    )
    fondoFeria = serializers.DecimalField(
        source="fondo_feria",
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0"),
    )
    preciosReferencia = PrecioReferenciaSerializer(
        source="precios_referencia",
        many=True,
    )
    usarCodigosNuevosPantalon = serializers.BooleanField(
        source="usar_codigos_nuevos_pantalon",
        required=False,
    )

    class Meta:
        model = ConfiguracionSistema
        fields = [
            "tipoCambioUsd",
            "multaPorDia",
            "fondoFeria",
            "preciosReferencia",
            "usarCodigosNuevosPantalon",
            "actualizadoEn",
        ]
        read_only_fields = ["actualizadoEn"]

    actualizadoEn = serializers.DateTimeField(source="actualizado_en", read_only=True)

    def validate_preciosReferencia(self, value):
        if not value:
            raise serializers.ValidationError("Debe haber al menos un precio de referencia.")
        ids = [item["id"] for item in value]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError("Los identificadores de precio deben ser únicos.")
        return [
            {
                "id": item["id"],
                "nombre": item["nombre"],
                "precioMxn": float(item["precioMxn"]),
            }
            for item in value
        ]
