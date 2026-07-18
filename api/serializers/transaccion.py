from rest_framework import serializers

from api.models import Transaccion
from api.services.transacciones import concepto_transaccion


class TransaccionSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source="pk", read_only=True)
    concepto = serializers.SerializerMethodField()

    class Meta:
        model = Transaccion
        fields = ["id", "timestamp", "referencia", "concepto", "cliente", "pago", "monto"]

    def get_concepto(self, obj: Transaccion) -> str:
        return concepto_transaccion(obj)
