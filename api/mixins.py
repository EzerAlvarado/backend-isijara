from api.permissions import linea_negocio_usuario


class FiltrarPorLineaMixin:
    """Filtra y asigna la línea de negocio del usuario autenticado."""

    campo_linea = "linea_negocio"

    def get_linea_negocio(self) -> str:
        return linea_negocio_usuario(self.request.user)

    def get_queryset(self):
        qs = super().get_queryset()
        linea = self.get_linea_negocio()
        if linea:
            return qs.filter(**{self.campo_linea: linea})
        return qs.none()

    def perform_create(self, serializer):
        serializer.save(**{self.campo_linea: self.get_linea_negocio()})


class FiltrarDevolucionPorLineaMixin:
    def get_linea_negocio(self) -> str:
        return linea_negocio_usuario(self.request.user)

    def get_queryset(self):
        qs = super().get_queryset()
        linea = self.get_linea_negocio()
        if linea:
            return qs.filter(renta__linea_negocio=linea)
        return qs.none()
