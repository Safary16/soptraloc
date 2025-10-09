"""
Inicialización de la aplicación Django.
Carga automática de Celery cuando Django arranca (si está instalado).
"""
# Importación condicional de Celery - solo si está instalado
try:
    from .celery import app as celery_app
    __all__ = ('celery_app',)
except ImportError:
    # Celery no está instalado, continuar sin él
    # Para instalar: pip install celery redis
    __all__ = ()
    celery_app = None
