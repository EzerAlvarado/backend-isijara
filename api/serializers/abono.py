from rest_framework import serializers

from api.models import Abono, MetodoPago


class AbonoSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source="pk", read_only=True)
    metodoPago = serializers.CharField(source="metodo_pago")
    pagoEfectivoMxn = serializers.DecimalField(
        source="pago_efectivo_mxn",
        max_digits=10,
        decimal_places=2,
        read_only=True,
    )
    pagoEfectivoUsd = serializers.DecimalField(
        source="pago_efectivo_usd",
        max_digits=10,
        decimal_places=2,
        read_only=True,
    )
    montoMxn = serializers.DecimalField(source="monto_mxn", max_digits=10, decimal_places=2, read_only=True)
    creadoEn = serializers.DateTimeField(source="creado_en", read_only=True)

    class Meta:
        model = Abono
        fields = [
            "id",
            "monto",
            "metodoPago",
            "pagoEfectivoMxn",
            "pagoEfectivoUsd",
            "montoMxn",
            "creadoEn",
        ]


class AbonoCreateSerializer(serializers.Serializer):
    monto = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, min_value=0)
    metodoPago = serializers.ChoiceField(choices=MetodoPago.choices, required=False, default=MetodoPago.PESOS)
    pagoPesos = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, min_value=0, default=0)
    pagoDlls = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, min_value=0, default=0)

    def validate(self, attrs):
        metodo = attrs.get("metodoPago", MetodoPago.PESOS)
        monto = attrs.get("monto")
        pago_pesos = attrs.get("pagoPesos") or 0
        pago_dlls = attrs.get("pagoDlls") or 0

        if metodo in (MetodoPago.PESOS, MetodoPago.DLLS, MetodoPago.MIXTO):
            if pago_pesos <= 0 and pago_dlls <= 0 and (monto is None or monto <= 0):
                raise serializers.ValidationError(
                    {"monto": "Indica el monto del abono o el efectivo recibido."}
                )
        elif monto is None or monto <= 0:
            raise serializers.ValidationError({"monto": "El monto debe ser mayor a cero."})

        return attrs
