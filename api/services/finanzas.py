from decimal import Decimal

from api.models.configuracion import ConfiguracionSistema, precios_default_por_linea
from api.models.linea_negocio import LineaNegocio


def obtener_configuracion(linea_negocio: str = LineaNegocio.TRAJES) -> ConfiguracionSistema:
    config, created = ConfiguracionSistema.objects.get_or_create(
        linea_negocio=linea_negocio,
        defaults={"precios_referencia": precios_default_por_linea(linea_negocio)},
    )
    if created or not config.precios_referencia:
        config.precios_referencia = precios_default_por_linea(linea_negocio)
        config.save(update_fields=["precios_referencia"])
    return config


def obtener_tipo_cambio(linea_negocio: str = LineaNegocio.TRAJES) -> Decimal:
    return Decimal(str(obtener_configuracion(linea_negocio).tipo_cambio_usd))


def obtener_multa_por_dia(linea_negocio: str = LineaNegocio.TRAJES) -> Decimal:
    return Decimal(str(obtener_configuracion(linea_negocio).multa_por_dia))


def obtener_fondo_feria(linea_negocio: str = LineaNegocio.TRAJES) -> Decimal:
    return Decimal(str(obtener_configuracion(linea_negocio).fondo_feria))
