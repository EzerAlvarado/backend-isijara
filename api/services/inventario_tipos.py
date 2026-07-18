from api.models.linea_negocio import LineaNegocio
from api.models.pieza import Pieza

TIPOS_POR_LINEA = {
    LineaNegocio.TRAJES: {
        Pieza.Tipo.SACO,
        Pieza.Tipo.CHALECO,
        Pieza.Tipo.PANTALON,
    },
    LineaNegocio.VESTIDOS: {
        Pieza.Tipo.QUINCE,
        Pieza.Tipo.BODA,
        Pieza.Tipo.NOCHE,
    },
}


def tipos_permitidos(linea_negocio: str) -> set[str]:
    return TIPOS_POR_LINEA.get(linea_negocio, set())


def tipo_permitido(linea_negocio: str, tipo: str) -> bool:
    return tipo in tipos_permitidos(linea_negocio)
