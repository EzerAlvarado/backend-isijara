from rest_framework import serializers

from api.models import Devolucion, Prenda, Renta


class DevolucionSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source="pk", read_only=True)
    rentaId = serializers.PrimaryKeyRelatedField(
        source="renta",
        queryset=Renta.objects.all(),
    )
    prendaId = serializers.PrimaryKeyRelatedField(
        source="prenda",
        queryset=Prenda.objects.all(),
        allow_null=True,
        required=False,
    )
    prendaNombre = serializers.CharField(source="prenda_nombre")
    fechaLimite = serializers.DateField(source="fecha_limite", format="%Y-%m-%d")
    multaPerdonada = serializers.BooleanField(source="multa_perdonada", required=False)
    cargoDanos = serializers.DecimalField(
        source="cargo_danos",
        max_digits=10,
        decimal_places=2,
        required=False,
    )
    notaDanos = serializers.CharField(source="nota_danos", required=False, allow_blank=True)
    confirmarSalio = serializers.BooleanField(
        source="confirmar_salio",
        required=False,
        default=False,
        write_only=True,
    )
    fechaSalioReal = serializers.DateField(
        source="renta.fecha_salio_real",
        format="%Y-%m-%d",
        read_only=True,
        allow_null=True,
    )
    fechaEntrega = serializers.SerializerMethodField()

    class Meta:
        model = Devolucion
        fields = [
            "id",
            "rentaId",
            "cliente",
            "prendaId",
            "prendaNombre",
            "cantidad",
            "estatus",
            "fechaLimite",
            "penalizacion",
            "multaPerdonada",
            "cargoDanos",
            "notaDanos",
            "confirmarSalio",
            "fechaSalioReal",
            "fechaEntrega",
        ]

    def get_fechaEntrega(self, obj: Devolucion) -> str:
        """Misma fecha que el formulario / columna Entrega de rentas (fecha_salida)."""
        renta = getattr(obj, "renta", None)
        if renta is None:
            return ""
        salida = str(getattr(renta, "fecha_salida", "") or "").strip()
        if salida:
            return salida
        cita = getattr(renta, "fecha_cita", None)
        if isinstance(cita, dict):
            return str(cita.get("valor") or "").strip()
        return ""
