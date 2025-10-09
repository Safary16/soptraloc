"""
Configuración de Celery para Soptraloc TMS.
"""
import os
from celery import Celery
from celery.schedules import crontab

# Establecer el módulo de configuración de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('soptraloc')

# Usar una cadena aquí significa que el worker no tiene que serializar
# la configuración cuando se pasan las tareas entre workers
app.config_from_object('django.conf:settings', namespace='CELERY')

# Cargar módulos de tareas desde todas las apps registradas
app.autodiscover_tasks()

# Configuración de tareas periódicas (Celery Beat)
app.conf.beat_schedule = {
    # Generar alertas de demurrage cada hora
    'generate-demurrage-alerts-hourly': {
        'task': 'apps.containers.tasks.generate_demurrage_alerts',
        'schedule': crontab(minute=0),  # Cada hora en punto
    },
    # Verificar entregas retrasadas cada 30 minutos
    'check-delayed-deliveries': {
        'task': 'apps.containers.tasks.check_delayed_deliveries',
        'schedule': crontab(minute='*/30'),  # Cada 30 minutos
    },
    # Actualizar matriz de tiempos desde tráfico en tiempo real (cada 15 minutos)
    'update-traffic-times': {
        'task': 'apps.drivers.tasks.update_traffic_based_times',
        'schedule': crontab(minute='*/15'),  # Cada 15 minutos
    },
}

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Tarea de debug para verificar que Celery funciona."""
    print(f'Request: {self.request!r}')
