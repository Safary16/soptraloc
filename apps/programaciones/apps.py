from django.apps import AppConfig


class ProgramacionesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.programaciones"

    def ready(self):
        import importlib
        importlib.import_module('apps.programaciones.signals')  # registra receivers al importar
