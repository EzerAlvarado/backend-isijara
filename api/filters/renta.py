import django_filters

from api.models import Renta


class RentaFilter(django_filters.FilterSet):
    semana_inicio = django_filters.DateFilter(field_name="semana_inicio")
    semana_inicio_desde = django_filters.DateFilter(
        field_name="semana_inicio",
        lookup_expr="gte",
    )
    semana_inicio_hasta = django_filters.DateFilter(
        field_name="semana_inicio",
        lookup_expr="lte",
    )
    tipo_entrega = django_filters.ChoiceFilter(choices=Renta.TipoEntrega.choices)
    estatus_fila = django_filters.ChoiceFilter(choices=Renta.EstatusCelda.choices)
    categoria_vestido = django_filters.ChoiceFilter(choices=Renta.CategoriaVestido.choices)

    class Meta:
        model = Renta
        fields = ["semana_inicio", "tipo_entrega", "estatus_fila", "categoria_vestido"]
