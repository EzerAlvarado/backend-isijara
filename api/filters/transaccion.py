import django_filters

from api.models import MetodoPago, Transaccion


class TransaccionFilter(django_filters.FilterSet):
    cliente = django_filters.CharFilter(lookup_expr="icontains")
    referencia = django_filters.CharFilter(lookup_expr="icontains")
    pago = django_filters.ChoiceFilter(choices=MetodoPago.choices)
    timestamp = django_filters.DateTimeFilter(field_name="timestamp")
    timestamp_desde = django_filters.DateTimeFilter(field_name="timestamp", lookup_expr="gte")
    timestamp_hasta = django_filters.DateTimeFilter(field_name="timestamp", lookup_expr="lte")

    class Meta:
        model = Transaccion
        fields = ["cliente", "referencia", "pago", "timestamp"]
