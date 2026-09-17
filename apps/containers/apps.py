from django.apps import AppConfig


class ContainersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.containers"
    
    def ready(self):
        """Importar signals cuando la app esté lista (efecto secundario: registra receivers)"""
        import importlib
        importlib.import_module('apps.containers.signals')  # registra receivers al importar
