from rest_framework import serializers

from api.models import Vale


class ValeSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source="pk", read_only=True)
    referencia = serializers.SerializerMethodField()
    repuestoEn = serializers.DateTimeField(source="repuesto_en", read_only=True)

    class Meta:
        model = Vale
        fields = [
            "id",
            "fecha",
            "concepto",
            "monto",
            "pago",
            "montoMxn",
            "estatus",
            "referencia",
            "repuestoEn",
        ]

    montoMxn = serializers.DecimalField(source="monto_mxn", max_digits=10, decimal_places=2, read_only=True)

    def get_referencia(self, obj: Vale) -> str | None:
        if obj.transaccion_id:
            return obj.transaccion.referencia
        return None
