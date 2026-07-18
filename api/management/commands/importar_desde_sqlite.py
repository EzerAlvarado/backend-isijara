"""
Copia datos de db.sqlite3 a PostgreSQL.

Uso (con Postgres corriendo y DB_ENGINE=postgresql en .env):
    python manage.py importar_desde_sqlite
"""

import tempfile
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import connections


class Command(BaseCommand):
    help = "Importa datos de db.sqlite3 al PostgreSQL configurado como default."

    def handle(self, *args, **options):
        if "sqlite_legacy" not in settings.DATABASES:
            raise CommandError(
                "No se encontró db.sqlite3. Coloca el archivo en backend/db.sqlite3 "
                "o usa DB_ENGINE=sqlite si aún no migras."
            )

        default_engine = settings.DATABASES["default"]["ENGINE"]
        if default_engine.endswith("sqlite3"):
            raise CommandError(
                "DB_ENGINE debe ser postgresql en .env para importar. "
                "Actual: sqlite."
            )

        self.stdout.write("Creando esquema en PostgreSQL…")
        call_command("migrate", interactive=False, verbosity=0)

        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".json",
            delete=False,
            encoding="utf-8",
        ) as tmp:
            tmp_path = tmp.name

        self.stdout.write("Exportando datos desde SQLite…")
        try:
            with open(tmp_path, "w", encoding="utf-8") as out:
                call_command(
                    "dumpdata",
                    database="sqlite_legacy",
                    exclude=["contenttypes", "auth.permission"],
                    indent=2,
                    stdout=out,
                )
        except Exception as exc:
            Path(tmp_path).unlink(missing_ok=True)
            raise CommandError(f"Error al exportar SQLite: {exc}") from exc

        if Path(tmp_path).stat().st_size <= 4:
            Path(tmp_path).unlink(missing_ok=True)
            self.stdout.write(self.style.WARNING("SQLite vacío; no hay datos que importar."))
            return

        self.stdout.write("Importando datos a PostgreSQL…")
        try:
            call_command("loaddata", tmp_path, verbosity=1)
        finally:
            Path(tmp_path).unlink(missing_ok=True)

        self._ajustar_secuencias()
        self.stdout.write(self.style.SUCCESS("Importación completada."))

    def _ajustar_secuencias(self):
        """Sincroniza serial IDs de PostgreSQL tras loaddata."""
        conn = connections["default"]
        if conn.vendor != "postgresql":
            return
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT c.relname
                FROM pg_class c
                JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE c.relkind = 'S'
                  AND n.nspname = 'public'
                  AND c.relname LIKE '%_id_seq'
                """
            )
            for (seq_name,) in cursor.fetchall():
                table = seq_name.removesuffix("_id_seq")
                cursor.execute(
                    f"""
                    SELECT setval(
                        %s,
                        COALESCE((SELECT MAX(id) FROM "{table}"), 1),
                        (SELECT MAX(id) FROM "{table}") IS NOT NULL
                    )
                    """,
                    [seq_name],
                )
