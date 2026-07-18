from decimal import Decimal

from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from api.filters import (
    DevolucionFilter,
    PiezaFilter,
    PrendaFilter,
    RentaFilter,
    TransaccionFilter,
)
from api.mixins import FiltrarDevolucionPorLineaMixin, FiltrarPorLineaMixin
from api.models import Devolucion, Pieza, Prenda, Renta, Transaccion
from api.permissions import TienePerfilNegocio
from api.serializers import (
    DevolucionSerializer,
    PiezaSerializer,
    PrendaSerializer,
    RentaSerializer,
    TransaccionSerializer,
)
from api.serializers.abono import AbonoCreateSerializer, AbonoSerializer
from api.services.abonos import crear_abono
from api.services.corte import (
    registrar_transaccion_danos,
    registrar_transaccion_multa,
    registrar_transaccion_renta,
)
from api.services.devoluciones import calcular_penalizacion, sincronizar_estado_devoluciones
from api.services.inventario_renta import (
    cancelar_renta,
    liberar_pieza,
    marcar_renta_salio,
    procesar_devolucion,
    sincronizar_devolucion,
    sincronizar_renta_inventario,
)


@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    return Response(
        {
            "status": "ok",
            "service": "isijara-api",
            "time": timezone.now().isoformat(),
        }
    )


class PiezaViewSet(FiltrarPorLineaMixin, viewsets.ModelViewSet):
    queryset = Pieza.objects.all()
    serializer_class = PiezaSerializer
    permission_classes = [TienePerfilNegocio]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = PiezaFilter
    search_fields = ["color", "marca", "talla", "codigo_new", "codigo_old", "detalles"]
    ordering_fields = ["tipo", "color", "talla", "marca", "estatus", "precio_renta"]
    ordering = ["tipo", "color", "talla"]

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["linea_negocio"] = self.get_linea_negocio()
        return ctx

    def perform_create(self, serializer):
        serializer.save(linea_negocio=self.get_linea_negocio())


class PrendaViewSet(FiltrarPorLineaMixin, viewsets.ModelViewSet):
    queryset = Prenda.objects.all()
    serializer_class = PrendaSerializer
    permission_classes = [TienePerfilNegocio]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = PrendaFilter
    search_fields = ["color", "marca", "codigo_new", "codigo_old", "detalles"]
    ordering_fields = ["codigo_new", "talla", "color", "estatus"]
    ordering = ["codigo_new", "talla"]


class RentaViewSet(FiltrarPorLineaMixin, viewsets.ModelViewSet):
    queryset = Renta.objects.select_related(
        "pieza_saco", "pieza_chaleco", "pieza_pantalon"
    ).prefetch_related("abonos")
    serializer_class = RentaSerializer
    permission_classes = [TienePerfilNegocio]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = RentaFilter
    ordering_fields = ["semana_inicio", "fondo", "multa", "id"]
    ordering = ["-semana_inicio", "-id"]

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["linea_negocio"] = self.get_linea_negocio()
        return ctx

    def perform_create(self, serializer):
        renta = serializer.save(linea_negocio=self.get_linea_negocio())
        sincronizar_renta_inventario(renta)
        registrar_transaccion_renta(renta)

    def perform_update(self, serializer):
        anterior = self.get_object()
        if anterior.cancelada:
            from rest_framework.exceptions import ValidationError

            raise ValidationError({"detail": "Esta renta está cancelada y no se puede modificar."})
        renta = serializer.save()
        sincronizar_renta_inventario(renta, anterior)
        registrar_transaccion_renta(renta)

    @action(detail=True, methods=["post"])
    def cancelar(self, request, pk=None):
        renta = self.get_object()
        if renta.cancelada:
            return Response(
                {"detail": "Esta renta ya está cancelada."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        cancelar_renta(renta)
        renta.refresh_from_db()
        serializer = self.get_serializer(renta)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="abono")
    def abono(self, request, pk=None):
        renta = self.get_object()
        ser = AbonoCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
        try:
            abono = crear_abono(
                renta,
                monto=data.get("monto"),
                metodo_pago=data.get("metodoPago", "pesos"),
                pago_pesos=data.get("pagoPesos") or Decimal("0"),
                pago_dlls=data.get("pagoDlls") or Decimal("0"),
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        renta.refresh_from_db()
        return Response(
            {
                "abono": AbonoSerializer(abono).data,
                "renta": self.get_serializer(renta).data,
            },
            status=status.HTTP_201_CREATED,
        )

    def perform_destroy(self, instance):
        ids = [
            i
            for i in (
                instance.pieza_saco_id,
                instance.pieza_chaleco_id,
                instance.pieza_pantalon_id,
            )
            if i
        ]
        instance.delete()
        for pieza_id in ids:
            liberar_pieza(pieza_id)


class DevolucionViewSet(FiltrarDevolucionPorLineaMixin, viewsets.ModelViewSet):
    queryset = Devolucion.objects.select_related("renta", "prenda")
    serializer_class = DevolucionSerializer
    permission_classes = [TienePerfilNegocio]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = DevolucionFilter
    search_fields = ["cliente", "prenda_nombre"]
    ordering_fields = ["fecha_limite", "penalizacion", "id"]
    ordering = ["fecha_limite", "-id"]

    def list(self, request, *args, **kwargs):
        sincronizar_estado_devoluciones(self.get_linea_negocio())
        return super().list(request, *args, **kwargs)

    def perform_update(self, serializer):
        instance = serializer.instance
        nuevo_estatus = serializer.validated_data.get("estatus", instance.estatus)
        multa_perdonada = serializer.validated_data.get(
            "multa_perdonada",
            instance.multa_perdonada,
        )
        confirmar_salio = bool(serializer.validated_data.pop("confirmar_salio", False))

        pendientes = (
            Devolucion.Estatus.AFUERA,
            Devolucion.Estatus.RETRASADO,
            Devolucion.Estatus.REVISAR_SALIDA,
        )

        if (
            nuevo_estatus == Devolucion.Estatus.REGRESADO
            and instance.estatus in pendientes
        ):
            if instance.estatus == Devolucion.Estatus.REVISAR_SALIDA:
                if not confirmar_salio:
                    from rest_framework.exceptions import ValidationError

                    raise ValidationError(
                        {
                            "confirmarSalio": (
                                "Confirma que el cliente ya recogió el traje antes de registrar la devolución."
                            )
                        }
                    )
                renta = instance.renta
                if renta:
                    marcar_renta_salio(renta)
                    sincronizar_devolucion(renta)
                    instance.refresh_from_db()

            linea = instance.renta.linea_negocio if instance.renta_id else self.get_linea_negocio()
            penalizacion = calcular_penalizacion(instance.fecha_limite, linea)
            if multa_perdonada:
                penalizacion = Decimal("0")
                serializer.validated_data["multa_perdonada"] = True
            serializer.validated_data["penalizacion"] = penalizacion

        devolucion = serializer.save()
        if devolucion.estatus == Devolucion.Estatus.REGRESADO:
            procesar_devolucion(devolucion)
            registrar_transaccion_multa(devolucion)
            registrar_transaccion_danos(devolucion)


class TransaccionViewSet(FiltrarPorLineaMixin, viewsets.ModelViewSet):
    queryset = Transaccion.objects.all()
    serializer_class = TransaccionSerializer
    permission_classes = [TienePerfilNegocio]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = TransaccionFilter
    search_fields = ["cliente", "referencia"]
    ordering_fields = ["timestamp", "monto"]
    ordering = ["-timestamp"]
