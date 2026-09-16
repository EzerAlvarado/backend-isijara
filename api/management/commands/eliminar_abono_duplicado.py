from decimal import Decimal

from django.core.management.base import BaseCommand

from api.models import Abono, LineaNegocio, MetodoPago, Renta
from api.services.abonos import eliminar_abono


class Command(BaseCommand):
    help = (
        "Elimina un abono Zelle duplicado de BEATRIZ CAMPUS (XV). "
        "Por defecto quita el segundo abono idéntico (mismo monto USD)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--cliente",
            default="BEATRIZ CAMPUS",
            help="Texto a buscar en cliente.valor",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Solo muestra qué borraría, sin eliminar.",
        )
        parser.add_argument(
            "--abono-id",
            type=int,
            default=None,
            help="Si se indica, elimina ese abono concreto (debe ser de la renta encontrada).",
        )

    def handle(self, *args, **options):
        cliente_q = str(options["cliente"]).strip().upper()
        dry = bool(options["dry_run"])
        abono_id = options["abono_id"]

        rentas = Renta.objects.filter(
            linea_negocio=LineaNegocio.VESTIDOS,
            categoria_vestido="quince",
        ).prefetch_related("abonos")

        encontradas = []
        for renta in rentas:
            cliente = ""
            if isinstance(renta.cliente, dict):
                cliente = str(renta.cliente.get("valor") or "")
            else:
                cliente = str(renta.cliente or "")
            if cliente_q in cliente.upper():
                encontradas.append(renta)

        if not encontradas:
            self.stderr.write(self.style.ERROR(f"No se encontró renta XV para «{cliente_q}»."))
            return

        if len(encontradas) > 1:
            self.stdout.write(
                self.style.WARNING(
                    f"Hay {len(encontradas)} rentas; se usa la de fondo más alto / más reciente."
                )
            )
            encontradas.sort(key=lambda r: (r.fondo, r.pk), reverse=True)

        renta = encontradas[0]
        abonos = list(renta.abonos.order_by("creado_en", "id"))
        self.stdout.write(
            f"Renta #{renta.pk} — {cliente_q} — fondo ${renta.fondo} — {len(abonos)} abonos"
        )
        for a in abonos:
            self.stdout.write(
                f"  Abono #{a.pk} {a.creado_en} {a.metodo_pago} "
                f"monto={a.monto} mxn={a.monto_mxn} usd={a.pago_efectivo_usd}"
            )

        target: Abono | None = None
        if abono_id:
            target = next((a for a in abonos if a.pk == abono_id), None)
            if not target:
                self.stderr.write(self.style.ERROR(f"Abono #{abono_id} no pertenece a esta renta."))
                return
        else:
            zelles = [
                a
                for a in abonos
                if a.metodo_pago == MetodoPago.ZELLE
                and (
                    a.monto == Decimal("153.95")
                    or a.pago_efectivo_usd == Decimal("153.95")
                    or a.monto_mxn == Decimal("2524.78")
                )
            ]
            if len(zelles) < 2:
                # Fallback: cualquier par Zelle idéntico
                by_key: dict[tuple, list[Abono]] = {}
                for a in abonos:
                    if a.metodo_pago != MetodoPago.ZELLE:
                        continue
                    key = (a.monto, a.monto_mxn, a.pago_efectivo_usd)
                    by_key.setdefault(key, []).append(a)
                dupes = [v for v in by_key.values() if len(v) >= 2]
                if not dupes:
                    self.stderr.write(
                        self.style.ERROR(
                            "No hay abonos Zelle duplicados (153.95 / 2524.78) en esta renta."
                        )
                    )
                    return
                zelles = sorted(dupes[0], key=lambda a: (a.creado_en, a.pk))
            else:
                zelles = sorted(zelles, key=lambda a: (a.creado_en, a.pk))
            # Conserva el primero; elimina el segundo (07:24 en el recibo)
            target = zelles[1]

        self.stdout.write(
            self.style.WARNING(
                f"{'DRY-RUN → ' if dry else ''}Eliminar abono #{target.pk} "
                f"({target.metodo_pago} {target.monto} / ${target.monto_mxn} MXN)"
            )
        )
        if dry:
            return

        eliminar_abono(target)
        self.stdout.write(self.style.SUCCESS(f"Abono #{target.pk} eliminado y anulado en corte."))
