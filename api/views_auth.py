from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from api.permissions import TienePerfilNegocio, linea_negocio_usuario

PERFIL_VESTIDO_A_SLUG = {
    "noche": "noche",
    "quince": "xv",
    "boda": "novia",
}


def _usuario_payload(user):
    perfil = user.perfil
    payload = {
        "username": user.username,
        "lineaNegocio": perfil.linea_negocio,
        "lineaLabel": perfil.get_linea_negocio_display(),
    }
    if perfil.perfil_vestido:
        slug = PERFIL_VESTIDO_A_SLUG.get(perfil.perfil_vestido)
        if slug:
            payload["perfilVestido"] = slug
    return payload


@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
    username = str(request.data.get("username", "")).strip().lower()
    password = request.data.get("password", "")

    if not username or not password:
        return Response(
            {"detail": "Usuario y contraseña son obligatorios."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = authenticate(request, username=username, password=password)
    if user is None:
        return Response(
            {"detail": "Usuario o contraseña incorrectos."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    if not hasattr(user, "perfil"):
        return Response(
            {"detail": "Este usuario no tiene perfil de negocio asignado."},
            status=status.HTTP_403_FORBIDDEN,
        )

    token, _ = Token.objects.get_or_create(user=user)
    return Response({"token": token.key, "usuario": _usuario_payload(user)})


@api_view(["POST"])
@permission_classes([IsAuthenticated, TienePerfilNegocio])
def logout(request):
    Token.objects.filter(user=request.user).delete()
    return Response({"detail": "Sesión cerrada."})


@api_view(["GET"])
@permission_classes([IsAuthenticated, TienePerfilNegocio])
def me(request):
    return Response(
        {
            "usuario": _usuario_payload(request.user),
            "lineaNegocio": linea_negocio_usuario(request.user),
        }
    )
