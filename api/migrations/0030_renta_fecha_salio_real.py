from datetime import timedelta

from django.db import migrations, models


def _estatus_desde_celda(celda):
    if isinstance(celda, dict):
        return str(celda.get("estatus") or "normal")
    return "normal"


def _renta_esta_salio(renta) -> bool:
    if renta.estatus_fila == "salio":
        return True
    for field in ("saco", "chaleco", "pantalon", "color", "accesorio"):
        if _estatus_desde_celda(getattr(renta, field, None)) == "salio":
            return True
    return False


def _parse_fecha_mx(fecha: str):
    if not fecha:
        return None
    try:
        dia, mes, anio = fecha.strip().split("/")
        from datetime import date

        return date(int(anio), int(mes), int(dia))
    except (ValueError, AttributeError):
        return None


def migrar_devoluciones_salio(apps, schema_editor):
    Renta = apps.get_model("api", "Renta")
    Devolucion = apps.get_model("api", "Devolucion")
    DIAS_RENTA = 3

    for renta in Renta.objects.all():
        if not _renta_esta_salio(renta):
            continue
        if renta.fecha_salio_real:
            continue
        fallback = _parse_fecha_mx(renta.fecha_salida)
        renta.fecha_salio_real = fallback
        renta.save(update_fields=["fecha_salio_real"])

    for dev in Devolucion.objects.exclude(estatus="regresado"):
        renta = dev.renta
        if not renta:
            continue
        if not _renta_esta_salio(renta):
            if dev.estatus in ("afuera", "retrasado"):
                dev.estatus = "revisar_salida"
                dev.penalizacion = 0
                dev.save(update_fields=["estatus", "penalizacion"])
            continue

        fecha_salio = renta.fecha_salio_real or _parse_fecha_mx(renta.fecha_salida)
        if not fecha_salio:
            continue
        fecha_limite = fecha_salio + timedelta(days=DIAS_RENTA)
        dev.fecha_limite = fecha_limite
        from django.utils import timezone

        hoy = timezone.localdate()
        if fecha_limite < hoy:
            dev.estatus = "retrasado"
        elif dev.estatus == "revisar_salida":
            dev.estatus = "afuera"
        dev.save(update_fields=["fecha_limite", "estatus"])


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0029_devolucion_multa_danos"),
    ]

    operations = [
        migrations.AddField(
            model_name="renta",
            name="fecha_salio_real",
            field=models.DateField(
                blank=True,
                help_text="Fecha en que el cliente recogió el traje (al marcar salió en rentas).",
                null=True,
            ),
        ),
        migrations.RunPython(migrar_devoluciones_salio, migrations.RunPython.noop),
    ]
