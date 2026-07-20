from rest_framework.permissions import BasePermission

from api.models.linea_negocio import LineaNegocio


def linea_negocio_usuario(user) -> str | None:
    if not user or not user.is_authenticated:
        return None
    perfil = getattr(user, "perfil", None)
    if perfil is None:
        return None
    return perfil.linea_negocio


def categoria_vestido_usuario(user) -> str | None:
    """Retorna la categoría de vestido asignada al usuario, si aplica."""
    if not user or not user.is_authenticated:
        return None
    perfil = getattr(user, "perfil", None)
    if perfil is None:
        return None
    return perfil.perfil_vestido


class TienePerfilNegocio(BasePermission):
    message = "Tu usuario no tiene una línea de negocio asignada."

    def has_permission(self, request, view):
        return linea_negocio_usuario(request.user) in LineaNegocio.values
