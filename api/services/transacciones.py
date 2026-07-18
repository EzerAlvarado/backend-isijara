from api.models import Abono, Renta, Transaccion
from api.services.pagos_renta import etiqueta_operacion


def _renta_desde_referencia(referencia: str) -> Renta | None:
    ref = (referencia or "").upper()
    if ref.startswith("R"):
        pk = ref[1:]
        if pk.isdigit():
            return Renta.objects.filter(pk=int(pk)).first()
    if ref.startswith("A"):
        pk = ref[1:]
        if pk.isdigit():
            abono = Abono.objects.select_related("renta").filter(pk=int(pk)).first()
            return abono.renta if abono else None
    return None


def concepto_transaccion(tx: Transaccion) -> str:
    ref = (tx.referencia or "").upper()
    if ref.startswith("G"):
        return "Vale"
    if ref.startswith("M"):
        return "Multa"
    if ref.startswith("D"):
        return "Daños"
    if ref.startswith("R"):
        renta = _renta_desde_referencia(ref)
        if renta:
            return etiqueta_operacion(renta.tipo_operacion)
        return "Renta"
    if ref.startswith("A"):
        renta = _renta_desde_referencia(ref)
        if renta:
            return f"Abono ({etiqueta_operacion(renta.tipo_operacion)})"
        return "Abono"
    return "Otro"
