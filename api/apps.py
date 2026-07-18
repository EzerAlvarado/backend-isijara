from django.apps import AppConfig


class ApiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "api"

    def ready(self):
        from django.conf import settings

        if settings.DATABASES["default"]["ENGINE"].endswith("sqlite3"):
            from api.db_sqlite import configurar_sqlite

            configurar_sqlite()
