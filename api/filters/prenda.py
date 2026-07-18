import django_filters
from django.db.models import Q

from api.models import Prenda


class PrendaFilter(django_filters.FilterSet):
    talla = django_filters.CharFilter(lookup_expr="iexact")
    color = django_filters.CharFilter(lookup_expr="icontains")
    marca = django_filters.CharFilter(lookup_expr="icontains")
    codigo = django_filters.CharFilter(method="filter_codigo")
    estatus = django_filters.ChoiceFilter(choices=Prenda.Estatus.choices)

    class Meta:
        model = Prenda
        fields = ["talla", "color", "marca", "estatus", "ubicacion"]

    def filter_codigo(self, queryset, name, value):
        return queryset.filter(
            Q(codigo_new__icontains=value) | Q(codigo_old__icontains=value)
        )
