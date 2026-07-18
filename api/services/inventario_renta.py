from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Q
from django.utils import timezone

from api.models import Devolucion, Pieza, Renta
from api.models.linea_negocio import LineaNegocio
from api.services.devoluciones import calcular_penalizacion

DIAS_RENTA_DEFAULT = 3


def parse_fecha_mx(fecha: str) -> date | None:
    if not fecha:
        return None
    try:
        dia, mes, anio = fecha.strip().split("/")
        return date(int(anio), int(mes), int(dia))
    except (ValueError, AttributeError):
        return None


def _valor_celda(celda) -> str:
    if isinstance(celda, dict):
        return str(celda.get("valor", "")).strip().upper()
    return ""


def _pieza_valida(valor: str) -> bool:
    return bool(valor) and valor not in ("X", "—", "-", "NO", "N/A")


def _color_coincide(qs, color: str):
    if not color:
        return qs
    return qs.filter(Q(color__iexact=color) | Q(color__icontains=color))


def semana_key_desde_fecha_salida(fecha: str) -> date | None:
    d = parse_fecha_mx(fecha)
    if not d:
        return None
    lunes = d - timedelta(days=d.weekday())  # weekday: Mon=0, Sun=6
    return lunes


def _semana_desplazada(semana: date, semanas: int) -> date:
    from datetime import timedelta

    return semana + timedelta(days=7 * semanas)


def _ids_piezas_renta_obj(renta: Renta) -> list[int]:
    return [i for i in (renta.pieza_saco_id, renta.pieza_chaleco_id, renta.pieza_pantalon_id) if i]


def conflicto_pieza_en_rentas(
    pieza_id: int,
    fecha_salida: str,
    linea_negocio: str,
    excluir_renta_id: int | None = None,
) -> dict | None:
    semana_ref = semana_key_desde_fecha_salida(fecha_salida)
    if not semana_ref or not pieza_id:
        return None

    semana_sig = _semana_desplazada(semana_ref, 1)
    aviso_siguiente = None

    qs = Renta.objects.filter(linea_negocio=linea_negocio, cancelada=False).filter(
        Q(pieza_saco_id=pieza_id) | Q(pieza_chaleco_id=pieza_id) | Q(pieza_pantalon_id=pieza_id),
    )
    if excluir_renta_id:
        qs = qs.exclude(pk=excluir_renta_id)

    for renta in qs:
        if pieza_id not in _ids_piezas_renta_obj(renta):
            continue

        sem_r = semana_key_desde_fecha_salida(renta.fecha_salida) or renta.semana_inicio
        if sem_r == semana_ref:
            return {
                "estado": "ocupada_misma_semana",
                "renta_id": renta.pk,
                "fecha_salida": renta.fecha_salida,
            }
        if sem_r == semana_sig and aviso_siguiente is None:
            aviso_siguiente = {
                "estado": "reservada_semana_siguiente",
                "renta_id": renta.pk,
                "fecha_salida": renta.fecha_salida,
            }

    return aviso_siguiente


def validar_disponibilidad_renta(renta: Renta, excluir_renta_id: int | None = None) -> str | None:
    fecha = renta.fecha_salida
    linea = renta.linea_negocio
    for pieza, etiqueta in (
        (renta.pieza_saco, "Saco"),
        (renta.pieza_chaleco, "Chaleco"),
        (renta.pieza_pantalon, "Pantalón"),
    ):
        if not pieza:
            continue
        conflicto = conflicto_pieza_en_rentas(pieza.pk, fecha, linea, excluir_renta_id)
        if conflicto and conflicto.get("estado") == "ocupada_misma_semana":
            return (
                f"{etiqueta}: la pieza ya está rentada la semana del {fecha}. "
                f"Sale el {conflicto['fecha_salida']}."
            )
    return None


def marcar_pieza_rentada(pieza_id: int | None) -> None:
    if not pieza_id:
        return
    Pieza.objects.filter(pk=pieza_id).update(estatus=Pieza.Estatus.RENTADO)


def liberar_pieza(pieza_id: int | None, estatus_devolucion: str | None = None) -> None:
    if not pieza_id:
        return
    Pieza.objects.filter(pk=pieza_id).update(estatus=Pieza.Estatus.DISPONIBLE)


def resolver_pieza(
    tipo: str,
    color: str,
    talla: str,
    marca: str = "",
) -> Pieza | None:
    if not _pieza_valida(talla) or not color:
        return None

    qs = Pieza.objects.filter(estatus=Pieza.Estatus.DISPONIBLE, tipo=tipo)
    qs = _color_coincide(qs, color)

    if marca:
        exacta_marca = qs.filter(talla__iexact=talla, marca__iexact=marca).first()
        if exacta_marca:
            return exacta_marca

    exacta = qs.filter(talla__iexact=talla).first()
    if exacta:
        return exacta

    talla_u = talla.upper()
    for pieza in qs.order_by("talla"):
        tv = (pieza.talla or "").upper()
        if tv and (tv.startswith(talla_u) or talla_u in tv):
            return pieza
    return None


def resolver_piezas_desde_renta(renta: Renta) -> dict[str, Pieza | None]:
    color_saco = _valor_celda(renta.color)
    return {
        "saco": resolver_pieza(Pieza.Tipo.SACO, color_saco, _valor_celda(renta.saco), renta.marca),
        "chaleco": resolver_pieza(
            Pieza.Tipo.CHALECO,
            (renta.color_chaleco or color_saco).upper(),
            _valor_celda(renta.chaleco),
            renta.marca_chaleco,
        ),
        "pantalon": resolver_pieza(
            Pieza.Tipo.PANTALON,
            (renta.color_pantalon or color_saco).upper(),
            _valor_celda(renta.pantalon),
            renta.marca_pantalon,
        ),
    }


def _ids_piezas_renta(renta: Renta) -> list[int]:
    return [i for i in (renta.pieza_saco_id, renta.pieza_chaleco_id, renta.pieza_pantalon_id) if i]


def _ids_piezas_anteriores(anterior: Renta | None) -> list[int]:
    if not anterior:
        return []
    return [
        i
        for i in (
            anterior.pieza_saco_id,
            anterior.pieza_chaleco_id,
            anterior.pieza_pantalon_id,
        )
        if i
    ]


def nombre_conjunto_renta(renta: Renta) -> str:
    if renta.linea_negocio == LineaNegocio.VESTIDOS:
        partes = []
        if renta.marca:
            partes.append(renta.marca)
        color = _valor_celda(renta.color)
        if color:
            partes.append(color)
        codigo = _valor_celda(renta.saco)
        if codigo:
            partes.append(f"Cód. {codigo}")
        talla = _valor_celda(renta.pantalon)
        if talla:
            partes.append(f"Talla {talla}")
        color_vestido = _valor_celda(renta.chaleco)
        if color_vestido:
            partes.append(color_vestido)
        return " · ".join(partes) or "Renta de vestido"

    partes = []
    color_saco = _valor_celda(renta.color)
    if color_saco and _pieza_valida(_valor_celda(renta.saco)):
        partes.append(f"Saco {color_saco} {_valor_celda(renta.saco)}")
    cc = (renta.color_chaleco or color_saco).upper()
    if _pieza_valida(_valor_celda(renta.chaleco)):
        partes.append(f"Chaleco {cc} {_valor_celda(renta.chaleco)}")
    cp = (renta.color_pantalon or color_saco).upper()
    if _pieza_valida(_valor_celda(renta.pantalon)):
        partes.append(f"Pantalón {cp} {_valor_celda(renta.pantalon)}")
    return " · ".join(partes) or "Renta de traje"


def _calcular_fecha_limite_desde_salio(fecha_salio: date) -> date:
    return fecha_salio + timedelta(days=DIAS_RENTA_DEFAULT)


def _celdas_prenda_salio(renta: Renta) -> tuple:
    if renta.linea_negocio == LineaNegocio.VESTIDOS:
        return (renta.color, renta.chaleco, renta.saco, renta.pantalon, renta.accesorio)
    return (renta.saco, renta.chaleco, renta.pantalon, renta.color)


def renta_esta_salio(renta: Renta) -> bool:
    if renta.estatus_fila == Renta.EstatusCelda.SALIO:
        return True
    for celda in _celdas_prenda_salio(renta):
        if _estatus_desde_celda(celda) == Renta.EstatusCelda.SALIO:
            return True
    return False


def actualizar_fecha_salio_renta(renta: Renta) -> bool:
    """Sincroniza fecha_salio_real con el estatus salió pintado en la renta."""
    salio = renta_esta_salio(renta)
    cambio = False

    if salio and not renta.fecha_salio_real:
        renta.fecha_salio_real = timezone.localdate()
        cambio = True
    elif not salio and renta.fecha_salio_real:
        renta.fecha_salio_real = None
        cambio = True

    if cambio:
        renta.save(update_fields=["fecha_salio_real", "actualizado_en"])
    return cambio


def marcar_renta_salio(renta: Renta, fecha: date | None = None) -> Renta:
    """Marca la renta como salió (p. ej. al confirmar devolución sin haber pintado antes)."""
    fecha_efectiva = fecha or timezone.localdate()
    update_fields = ["actualizado_en"]

    if not renta.fecha_salio_real:
        renta.fecha_salio_real = fecha_efectiva
        update_fields.append("fecha_salio_real")

    if not renta_esta_salio(renta):
        renta.estatus_fila = Renta.EstatusCelda.SALIO
        update_fields.append("estatus_fila")

    renta.save(update_fields=update_fields)
    sincronizar_estatus_piezas_desde_renta(renta)
    return renta


def _estatus_devolucion_desde_renta(renta: Renta, fecha_limite: date) -> str:
    if not renta_esta_salio(renta):
        return Devolucion.Estatus.REVISAR_SALIDA
    hoy = timezone.localdate()
    if fecha_limite < hoy:
        return Devolucion.Estatus.RETRASADO
    return Devolucion.Estatus.AFUERA


def sincronizar_devolucion(renta: Renta) -> None:
    ids = _ids_piezas_renta(renta)
    if not ids:
        Devolucion.objects.filter(renta=renta).delete()
        return

    cliente = ""
    if isinstance(renta.cliente, dict):
        cliente = str(renta.cliente.get("valor", "")).upper()

    nombre = nombre_conjunto_renta(renta)
    prenda_ref = None

    salio = renta_esta_salio(renta)
    if salio:
        fecha_salio = renta.fecha_salio_real or timezone.localdate()
        if not renta.fecha_salio_real:
            renta.fecha_salio_real = fecha_salio
            renta.save(update_fields=["fecha_salio_real", "actualizado_en"])
        fecha_limite = _calcular_fecha_limite_desde_salio(fecha_salio)
        estatus = _estatus_devolucion_desde_renta(renta, fecha_limite)
        penalizacion = (
            calcular_penalizacion(fecha_limite, renta.linea_negocio)
            if estatus == Devolucion.Estatus.RETRASADO
            else Decimal("0")
        )
    else:
        fecha_limite = parse_fecha_mx(renta.fecha_regreso) or timezone.localdate()
        estatus = Devolucion.Estatus.REVISAR_SALIDA
        penalizacion = Decimal("0")

    devolucion, creada = Devolucion.objects.get_or_create(
        renta=renta,
        defaults={
            "cliente": cliente,
            "prenda_id": prenda_ref,
            "prenda_nombre": nombre,
            "fecha_limite": fecha_limite,
            "estatus": estatus,
            "penalizacion": penalizacion,
        },
    )
    if not creada:
        if devolucion.estatus == Devolucion.Estatus.REGRESADO:
            return
        devolucion.cliente = cliente
        devolucion.prenda_id = prenda_ref
        devolucion.prenda_nombre = nombre
        devolucion.fecha_limite = fecha_limite
        devolucion.estatus = estatus
        devolucion.penalizacion = penalizacion
        devolucion.save(
            update_fields=[
                "cliente",
                "prenda_id",
                "prenda_nombre",
                "fecha_limite",
                "estatus",
                "penalizacion",
            ]
        )

    if salio and penalizacion > 0 and renta.multa != penalizacion:
        Renta.objects.filter(pk=renta.pk).update(multa=penalizacion)
    elif not salio and renta.multa > 0:
        Renta.objects.filter(pk=renta.pk).update(multa=Decimal("0"))


def sincronizar_renta_inventario(renta: Renta, renta_anterior: Renta | None = None) -> None:
    if renta.cancelada:
        return

    ids_nuevos = set(_ids_piezas_renta(renta))
    ids_viejos = set(_ids_piezas_anteriores(renta_anterior))

    for pieza_id in ids_viejos - ids_nuevos:
        liberar_pieza(pieza_id)

    if renta.linea_negocio != LineaNegocio.VESTIDOS:
        resueltas = resolver_piezas_desde_renta(renta)
        cambios = False
        if not renta.pieza_saco_id and resueltas["saco"]:
            renta.pieza_saco = resueltas["saco"]
            cambios = True
        if not renta.pieza_chaleco_id and resueltas["chaleco"]:
            renta.pieza_chaleco = resueltas["chaleco"]
            cambios = True
        if not renta.pieza_pantalon_id and resueltas["pantalon"]:
            renta.pieza_pantalon = resueltas["pantalon"]
            cambios = True
        if cambios:
            renta.save(update_fields=["pieza_saco_id", "pieza_chaleco_id", "pieza_pantalon_id"])
            renta.refresh_from_db()

    for pieza_id in _ids_piezas_renta(renta):
        marcar_pieza_rentada(pieza_id)

    actualizar_fecha_salio_renta(renta)

    if _ids_piezas_renta(renta):
        sincronizar_devolucion(renta)
    else:
        Devolucion.objects.filter(renta=renta).delete()

    sincronizar_estatus_piezas_desde_renta(renta)


_CAMPOS_PRENDA_TRAJES = (
    "color",
    "saco",
    "chaleco",
    "pantalon",
    "camisa",
    "corbata_mono",
    "cinto",
    "accesorio",
)
_CAMPOS_PRENDA_VESTIDOS = ("color", "chaleco", "saco", "pantalon", "accesorio")
_CAMPOS_INFO_VESTIDOS = ("empleado", "cliente", "fecha_cita", "horario", "detalles")


def _celda_tiene_valor(celda) -> bool:
    if not isinstance(celda, dict):
        return False
    valor = str(celda.get("valor", "")).strip()
    return bool(valor) and valor != "—"


def _campos_prenda_renta(renta: Renta) -> tuple[str, ...]:
    if renta.linea_negocio == LineaNegocio.VESTIDOS:
        return _CAMPOS_PRENDA_VESTIDOS
    return _CAMPOS_PRENDA_TRAJES


def _marcar_celda_con_estatus(renta: Renta, field: str, estatus: str) -> bool:
    celda = getattr(renta, field)
    if not _celda_tiene_valor(celda):
        return False
    nueva = dict(celda)
    nueva["estatus"] = estatus
    nueva.pop("nota", None)
    setattr(renta, field, nueva)
    return True


def marcar_prendas_arrugado_renta(renta: Renta) -> bool:
    """Marca estatus post-devolución sin daños: vestidos → entregado; trajes → arrugado en prendas."""
    if renta.linea_negocio == LineaNegocio.VESTIDOS:
        estatus = Renta.EstatusCelda.ENTREGADO
        campos = _CAMPOS_PRENDA_VESTIDOS + _CAMPOS_INFO_VESTIDOS
        renta.estatus_fila = estatus
    else:
        estatus = Renta.EstatusCelda.ARRUGADO
        campos = _campos_prenda_renta(renta)
        renta.estatus_fila = ""

    update_fields: list[str] = ["estatus_fila"]
    for field in campos:
        if _marcar_celda_con_estatus(renta, field, estatus):
            update_fields.append(field)

    if len(update_fields) == 1 and not renta.estatus_fila:
        return False

    renta.save(update_fields=update_fields + ["actualizado_en"])
    return True


def procesar_devolucion(devolucion: Devolucion) -> None:
    renta = devolucion.renta
    if not renta:
        return

    hay_danos = devolucion.cargo_danos > 0 or bool((devolucion.nota_danos or "").strip())

    for pieza_id in _ids_piezas_renta(renta):
        if hay_danos:
            _marcar_pieza_mantenimiento(pieza_id, devolucion.nota_danos)
        else:
            liberar_pieza(pieza_id, devolucion.estatus)

    if not hay_danos:
        marcar_prendas_arrugado_renta(renta)


def _marcar_pieza_mantenimiento(pieza_id: int | None, nota: str) -> None:
    if not pieza_id:
        return
    pieza = Pieza.objects.filter(pk=pieza_id).first()
    if not pieza:
        return

    nota_limpia = (nota or "").strip()
    if nota_limpia:
        prefijo = f"Mantenimiento (devolución): {nota_limpia}"
        detalles = prefijo if not pieza.detalles else f"{pieza.detalles} | {prefijo}"
    else:
        detalles = pieza.detalles or "Mantenimiento (devolución)"

    Pieza.objects.filter(pk=pieza_id).update(
        estatus=Pieza.Estatus.MANTENIMIENTO,
        detalles=detalles[:255],
    )


_ESTATUS_CELDA_PIEZA = {
    "salio": Pieza.Estatus.SALIO,
    "sucio": Pieza.Estatus.SUCIO,
    "mojado": Pieza.Estatus.MOJADO,
    "en_ajustes": Pieza.Estatus.EN_AJUSTES,
    "listo_para_entregar": Pieza.Estatus.LISTO,
    "listo_empacar": Pieza.Estatus.LISTO,
    "arrugado": Pieza.Estatus.SUCIO,
    "otra_situacion": Pieza.Estatus.MANTENIMIENTO,
}


def _estatus_desde_celda(celda) -> str:
    if isinstance(celda, dict):
        return str(celda.get("estatus") or "normal")
    return "normal"


def _estatus_pieza_desde_celda(estatus_celda: str) -> str:
    if not estatus_celda or estatus_celda == "normal":
        return Pieza.Estatus.RENTADO
    return _ESTATUS_CELDA_PIEZA.get(estatus_celda, Pieza.Estatus.RENTADO)


def _resolver_estatus_pieza(*estatus_candidatos: str, fallback_fila: str = "") -> str:
    for estatus in estatus_candidatos:
        if estatus and estatus != "normal":
            return _estatus_pieza_desde_celda(estatus)
    if fallback_fila and fallback_fila != "normal":
        return _estatus_pieza_desde_celda(fallback_fila)
    return Pieza.Estatus.RENTADO


def sincronizar_estatus_piezas_desde_renta(renta: Renta) -> None:
    """Refleja en inventario los colores/estatus pintados en la renta."""
    fila = renta.estatus_fila or ""

    if renta.linea_negocio == LineaNegocio.VESTIDOS:
        if not renta.pieza_saco_id:
            return
        estatus_celda = "normal"
        for celda in (renta.color, renta.chaleco, renta.saco, renta.pantalon, renta.accesorio):
            e = _estatus_desde_celda(celda)
            if e != "normal":
                estatus_celda = e
                break
        if estatus_celda == "normal" and fila:
            estatus_celda = fila
        Pieza.objects.filter(pk=renta.pieza_saco_id).update(
            estatus=_estatus_pieza_desde_celda(estatus_celda),
        )
        return

    if renta.pieza_saco_id:
        est = _resolver_estatus_pieza(
            _estatus_desde_celda(renta.saco),
            _estatus_desde_celda(renta.color),
            fallback_fila=fila,
        )
        Pieza.objects.filter(pk=renta.pieza_saco_id).update(estatus=est)

    if renta.pieza_chaleco_id:
        est = _resolver_estatus_pieza(
            _estatus_desde_celda(renta.chaleco),
            fallback_fila=fila,
        )
        Pieza.objects.filter(pk=renta.pieza_chaleco_id).update(estatus=est)

    if renta.pieza_pantalon_id:
        est = _resolver_estatus_pieza(
            _estatus_desde_celda(renta.pantalon),
            fallback_fila=fila,
        )
        Pieza.objects.filter(pk=renta.pieza_pantalon_id).update(estatus=est)


def cancelar_renta(renta: Renta) -> Renta:
    """Marca la renta como cancelada y libera las piezas al inventario."""
    if renta.cancelada:
        return renta

    ids = _ids_piezas_renta(renta)
    renta.cancelada = True
    renta.save(update_fields=["cancelada", "actualizado_en"])

    for pieza_id in ids:
        liberar_pieza(pieza_id)

    Devolucion.objects.filter(renta=renta).delete()
    return renta
