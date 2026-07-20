from rest_framework import serializers

from api.models import Pieza, Renta
from api.models.linea_negocio import LineaNegocio
from api.serializers.abono import AbonoSerializer
from api.services.inventario_tipos import tipos_permitidos
from api.services.inventario_renta import semana_key_desde_fecha_salida, validar_disponibilidad_renta
from api.services.pagos_renta import (
    restante_mxn,
    total_abonado_mxn,
    total_cobrar_mxn,
    total_pagado_mxn,
    esta_pagada,
)

_CELDA_FIELDS = (
    "color",
    "saco",
    "chaleco",
    "pantalon",
    "camisa",
    "corbata_mono",
    "cinto",
    "accesorio",
    "empleado",
    "cliente",
    "fecha_cita",
    "horario",
    "detalles",
)
_TEXT_FIELDS = (
    "telefono",
    "direccion",
    "ajustes",
    "marca",
    "color_chaleco",
    "color_pantalon",
    "marca_chaleco",
    "marca_pantalon",
)


def _upper_celda(data):
    if isinstance(data, dict) and "valor" in data:
        valor = data.get("valor", "")
        if valor is not None:
            data = {**data, "valor": str(valor).upper()}
    return data


class RentaSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source="pk", read_only=True)
    corbataMono = serializers.JSONField(source="corbata_mono")
    tipoEntrega = serializers.CharField(source="tipo_entrega")
    fechaCita = serializers.JSONField(source="fecha_cita")
    estatusFila = serializers.CharField(source="estatus_fila", allow_blank=True, required=False)
    semanaInicio = serializers.DateField(source="semana_inicio", format="%Y-%m-%d")
    fechaSalida = serializers.CharField(source="fecha_salida")
    fechaRegreso = serializers.CharField(source="fecha_regreso")
    fechaSalioReal = serializers.DateField(
        source="fecha_salio_real",
        format="%Y-%m-%d",
        allow_null=True,
        required=False,
    )
    colorChaleco = serializers.CharField(source="color_chaleco", allow_blank=True, required=False)
    colorPantalon = serializers.CharField(source="color_pantalon", allow_blank=True, required=False)
    marcaChaleco = serializers.CharField(source="marca_chaleco", allow_blank=True, required=False)
    marcaPantalon = serializers.CharField(source="marca_pantalon", allow_blank=True, required=False)
    piezaSacoId = serializers.PrimaryKeyRelatedField(
        source="pieza_saco",
        queryset=Pieza.objects.all(),
        allow_null=True,
        required=False,
    )
    piezaChalecoId = serializers.PrimaryKeyRelatedField(
        source="pieza_chaleco",
        queryset=Pieza.objects.all(),
        allow_null=True,
        required=False,
    )
    piezaPantalonId = serializers.PrimaryKeyRelatedField(
        source="pieza_pantalon",
        queryset=Pieza.objects.all(),
        allow_null=True,
        required=False,
    )
    metodoPago = serializers.CharField(source="metodo_pago", required=False)
    pagoEfectivoMxn = serializers.DecimalField(
        source="pago_efectivo_mxn",
        max_digits=10,
        decimal_places=2,
        required=False,
    )
    pagoEfectivoUsd = serializers.DecimalField(
        source="pago_efectivo_usd",
        max_digits=10,
        decimal_places=2,
        required=False,
    )
    feriaMxn = serializers.DecimalField(
        source="feria_mxn",
        max_digits=10,
        decimal_places=2,
        required=False,
    )
    categoriaVestido = serializers.ChoiceField(
        source="categoria_vestido",
        choices=Renta.CategoriaVestido.choices,
        allow_blank=True,
        required=False,
    )
    cancelada = serializers.BooleanField(read_only=True)
    tipoOperacion = serializers.ChoiceField(
        source="tipo_operacion",
        choices=Renta.TipoOperacion.choices,
        required=False,
    )
    depositoReembolsable = serializers.CharField(
        source="deposito_reembolsable",
        allow_blank=True,
        required=False,
    )
    totalCobrar = serializers.SerializerMethodField()
    totalPagado = serializers.SerializerMethodField()
    totalAbonado = serializers.SerializerMethodField()
    restante = serializers.SerializerMethodField()
    pagado = serializers.SerializerMethodField()
    abonos = AbonoSerializer(many=True, read_only=True)

    class Meta:
        model = Renta
        fields = [
            "id",
            "color",
            "saco",
            "chaleco",
            "pantalon",
            "camisa",
            "corbataMono",
            "cinto",
            "accesorio",
            "tipoEntrega",
            "empleado",
            "cliente",
            "telefono",
            "direccion",
            "fechaCita",
            "horario",
            "detalles",
            "ajustes",
            "marca",
            "colorChaleco",
            "colorPantalon",
            "marcaChaleco",
            "marcaPantalon",
            "estatusFila",
            "semanaInicio",
            "fechaSalida",
            "fechaRegreso",
            "fechaSalioReal",
            "piezaSacoId",
            "piezaChalecoId",
            "piezaPantalonId",
            "fondo",
            "anticipo",
            "multa",
            "metodoPago",
            "pagoEfectivoMxn",
            "pagoEfectivoUsd",
            "feriaMxn",
            "categoriaVestido",
            "cancelada",
            "tipoOperacion",
            "depositoReembolsable",
            "totalCobrar",
            "totalPagado",
            "totalAbonado",
            "restante",
            "pagado",
            "abonos",
        ]

    def get_totalCobrar(self, obj: Renta) -> float:
        return float(total_cobrar_mxn(obj))

    def get_totalPagado(self, obj: Renta) -> float:
        return float(total_pagado_mxn(obj))

    def get_totalAbonado(self, obj: Renta) -> float:
        return float(total_abonado_mxn(obj))

    def get_restante(self, obj: Renta) -> float:
        return float(restante_mxn(obj))

    def get_pagado(self, obj: Renta) -> bool:
        return esta_pagada(obj)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        linea = self.context.get("linea_negocio")
        if not linea:
            return
        base = Pieza.objects.filter(linea_negocio=linea)
        if linea == LineaNegocio.VESTIDOS:
            tipos = list(tipos_permitidos(linea))
            self.fields["piezaSacoId"].queryset = base.filter(tipo__in=tipos)
            self.fields["piezaChalecoId"].queryset = Pieza.objects.none()
            self.fields["piezaPantalonId"].queryset = Pieza.objects.none()
        else:
            self.fields["piezaSacoId"].queryset = base.filter(tipo=Pieza.Tipo.SACO)
            self.fields["piezaChalecoId"].queryset = base.filter(tipo=Pieza.Tipo.CHALECO)
            self.fields["piezaPantalonId"].queryset = base.filter(tipo=Pieza.Tipo.PANTALON)

    def validate(self, attrs):
        if self.instance and self.instance.cancelada:
            raise serializers.ValidationError(
                {"detail": "Esta renta está cancelada y no se puede modificar."}
            )

        linea = self.context.get("linea_negocio")
        categoria = attrs.get(
            "categoria_vestido",
            getattr(self.instance, "categoria_vestido", "") if self.instance else "",
        )

        if linea == LineaNegocio.VESTIDOS:
            if not categoria:
                raise serializers.ValidationError(
                    {"categoriaVestido": "La categoría (noche, quince o novia) es obligatoria."}
                )
        elif linea == LineaNegocio.TRAJES:
            attrs["categoria_vestido"] = ""

        tipo_op = attrs.get(
            "tipo_operacion",
            getattr(self.instance, "tipo_operacion", Renta.TipoOperacion.RENTA)
            if self.instance
            else Renta.TipoOperacion.RENTA,
        )
        if tipo_op == Renta.TipoOperacion.PATROCINIO:
            attrs["fondo"] = 0
            attrs["anticipo"] = 0
            attrs["pago_efectivo_mxn"] = 0
            attrs["pago_efectivo_usd"] = 0
            attrs["feria_mxn"] = 0

        for field in _CELDA_FIELDS:
            if field in attrs:
                attrs[field] = _upper_celda(attrs[field])
        for field in _TEXT_FIELDS:
            if field in attrs and attrs[field] is not None:
                attrs[field] = str(attrs[field]).upper()

        if linea:
            instancia = self.instance
            fecha_salida = attrs.get(
                "fecha_salida",
                getattr(instancia, "fecha_salida", "") if instancia else "",
            )
            pieza_saco = attrs.get("pieza_saco", getattr(instancia, "pieza_saco", None) if instancia else None)
            pieza_chaleco = attrs.get(
                "pieza_chaleco",
                getattr(instancia, "pieza_chaleco", None) if instancia else None,
            )
            pieza_pantalon = attrs.get(
                "pieza_pantalon",
                getattr(instancia, "pieza_pantalon", None) if instancia else None,
            )
            if fecha_salida and any((pieza_saco, pieza_chaleco, pieza_pantalon)):
                probe = Renta(
                    linea_negocio=linea,
                    fecha_salida=fecha_salida,
                    pieza_saco=pieza_saco,
                    pieza_chaleco=pieza_chaleco,
                    pieza_pantalon=pieza_pantalon,
                    semana_inicio=attrs.get(
                        "semana_inicio",
                        getattr(instancia, "semana_inicio", None) if instancia else None,
                    )
                    or semana_key_desde_fecha_salida(fecha_salida),
                )
                msg = validar_disponibilidad_renta(
                    probe,
                    excluir_renta_id=instancia.pk if instancia else None,
                )
                if msg:
                    raise serializers.ValidationError({"piezaSacoId": msg})

        return attrs
