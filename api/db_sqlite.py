"""Ajustes de SQLite para desarrollo local (concurrencia lectura/escritura)."""

from django.db.backends.signals import connection_created


def _activar_wal_y_timeout(sender, connection, **kwargs):
    if connection.vendor != "sqlite":
        return
    with connection.cursor() as cursor:
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA busy_timeout=30000;")


def configurar_sqlite():
    connection_created.connect(_activar_wal_y_timeout)
