import django_filters

from django.db.models import Q

from api.models import Pieza


class PiezaFilter(django_filters.FilterSet):
    tipo = django_filters.ChoiceFilter(choices=Pieza.Tipo.choices)
    color = django_filters.CharFilter(lookup_expr="icontains")
    marca = django_filters.CharFilter(lookup_expr="icontains")
    estatus = django_filters.ChoiceFilter(choices=Pieza.Estatus.choices)
    ubicacion = django_filters.CharFilter(lookup_expr="icontains")
    codigo = django_filters.CharFilter(method="filter_codigo")
    talla = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = Pieza
        fields = ["tipo", "color", "marca", "estatus", "ubicacion", "talla"]

    def filter_codigo(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            Q(codigo_new__icontains=value) | Q(codigo_old__icontains=value)
        )
