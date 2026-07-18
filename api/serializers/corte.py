from datetime import datetime

from rest_framework import serializers

from api.models import CorteDia, Transaccion


class TransaccionSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source="pk", read_only=True)

    class Meta:
        model = Transaccion
        fields = ["id", "timestamp", "referencia", "cliente", "pago", "monto"]

    def validate_referencia(self, value):
        return str(value).upper()

    def validate_cliente(self, value):
        return str(value).upper()


class CorteDiaSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source="pk", read_only=True)
    fondoInicial = serializers.DecimalField(
        source="fondo_inicial",
        max_digits=10,
        decimal_places=2,
        required=False,
    )
    conteoFondo = serializers.JSONField(source="conteo_fondo", required=False)
    cerradoEn = serializers.DateTimeField(source="cerrado_en", read_only=True)

    class Meta:
        model = CorteDia
        fields = ["id", "fecha", "fondoInicial", "conteoFondo", "cerrado", "cerradoEn"]

    def validate_conteoFondo(self, value):
        from api.services.conteo_caja import normalizar_conteo

        return normalizar_conteo(value)


def parse_fecha_query(valor: str | None):
    if not valor:
        from django.utils import timezone

        return timezone.localdate()
    try:
        return datetime.strptime(valor, "%Y-%m-%d").date()
    except ValueError as exc:
        raise serializers.ValidationError({"fecha": "Formato inválido. Use YYYY-MM-DD."}) from exc


def parse_turno_query(valor: str | None) -> str | None:
    if not valor:
        return None
    from api.models import TurnoCorte

    turno = str(valor).lower().strip()
    if turno not in (TurnoCorte.MANANA, TurnoCorte.TARDE):
        raise serializers.ValidationError({"turno": "Turno inválido. Use manana o tarde."})
    return turno
