from django.apps import AppConfig


class ContainersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.containers"
    
    def ready(self):
        """Importar signals cuando la app esté lista"""
        import apps.containers.signals
