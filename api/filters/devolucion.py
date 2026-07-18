import django_filters

from api.models import Devolucion, Renta


class DevolucionFilter(django_filters.FilterSet):
    renta = django_filters.NumberFilter(field_name="renta_id")
    categoria_vestido = django_filters.ChoiceFilter(
        field_name="renta__categoria_vestido",
        choices=Renta.CategoriaVestido.choices,
    )
    cliente = django_filters.CharFilter(lookup_expr="icontains")
    prenda_nombre = django_filters.CharFilter(lookup_expr="icontains")
    estatus = django_filters.ChoiceFilter(choices=Devolucion.Estatus.choices)
    fecha_limite = django_filters.DateFilter(field_name="fecha_limite")
    fecha_limite_desde = django_filters.DateFilter(
        field_name="fecha_limite",
        lookup_expr="gte",
    )
    fecha_limite_hasta = django_filters.DateFilter(
        field_name="fecha_limite",
        lookup_expr="lte",
    )

    class Meta:
        model = Devolucion
        fields = ["renta", "cliente", "prenda_nombre", "estatus", "fecha_limite"]
