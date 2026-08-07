from rest_framework import serializers

from api.models import Pedido


class PedidoSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    tipoPedido = serializers.ChoiceField(
        source="tipo_pedido",
        choices=Pedido.TipoPedido.choices,
    )
    estiloPiezas = serializers.CharField(
        source="estilo_piezas",
        allow_blank=True,
        required=False,
        default="",
    )
    fechaEntrega = serializers.CharField(
        source="fecha_entrega",
        allow_blank=True,
        required=False,
        default="",
    )
    mesEtiqueta = serializers.CharField(
        source="mes_etiqueta",
        allow_blank=True,
        required=False,
        default="",
    )
    creadoEn = serializers.DateTimeField(source="creado_en", read_only=True)
    actualizadoEn = serializers.DateTimeField(source="actualizado_en", read_only=True)

    class Meta:
        model = Pedido
        fields = [
            "id",
            "cliente",
            "tipoPedido",
            "estatus",
            "estiloPiezas",
            "servicio",
            "fechaEntrega",
            "comentarios",
            "mesEtiqueta",
            "orden",
            "creadoEn",
            "actualizadoEn",
        ]

    def validate_cliente(self, value: str) -> str:
        valor = (value or "").strip()
        if not valor:
            raise serializers.ValidationError("El cliente es obligatorio.")
        return valor.upper()

    def validate_estiloPiezas(self, value: str) -> str:
        return (value or "").strip().upper()

    def validate_fechaEntrega(self, value: str) -> str:
        return (value or "").strip().upper()

    def validate_comentarios(self, value: str) -> str:
        return (value or "").strip()

    def validate_mesEtiqueta(self, value: str) -> str:
        return (value or "").strip().upper()
