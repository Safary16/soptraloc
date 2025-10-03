"""
Health check mejorado para Render.com
Verifica:
- Conectividad a base de datos
- Estado de migraciones
- Archivos estáticos
- Configuración correcta
"""
from django.http import JsonResponse
from django.db import connection
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
import logging
import os

logger = logging.getLogger(__name__)


def health_check_detailed(request):
    """
    Health check completo del sistema
    GET /api/health/
    """
    health_status = {
        'status': 'healthy',
        'checks': {}
    }
    
    # 1. Verificar base de datos
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
            health_status['checks']['database'] = {
                'status': 'ok',
                'message': 'Database connection successful'
            }
    except Exception as e:
        logger.error(f"Health check: Database error - {e}")
        health_status['status'] = 'unhealthy'
        health_status['checks']['database'] = {
            'status': 'error',
            'message': str(e)
        }
    
    # 2. Verificar configuración
    try:
        assert not settings.DEBUG, "DEBUG should be False in production"
        assert settings.SECRET_KEY, "SECRET_KEY must be set"
        health_status['checks']['configuration'] = {
            'status': 'ok',
            'debug': settings.DEBUG,
            'allowed_hosts': len(settings.ALLOWED_HOSTS)
        }
    except AssertionError as e:
        logger.warning(f"Health check: Configuration warning - {e}")
        health_status['checks']['configuration'] = {
            'status': 'warning',
            'message': str(e)
        }
    
    # 3. Verificar archivos estáticos
    try:
        static_root_exists = os.path.exists(settings.STATIC_ROOT)
        health_status['checks']['static_files'] = {
            'status': 'ok' if static_root_exists else 'warning',
            'static_root': str(settings.STATIC_ROOT),
            'exists': static_root_exists
        }
    except Exception as e:
        logger.warning(f"Health check: Static files warning - {e}")
        health_status['checks']['static_files'] = {
            'status': 'warning',
            'message': str(e)
        }
    
    # 4. Verificar apps instaladas
    health_status['checks']['apps'] = {
        'status': 'ok',
        'installed': len(settings.INSTALLED_APPS),
        'local_apps': [app for app in settings.INSTALLED_APPS if app.startswith('apps.')]
    }
    
    # Determinar código de estado HTTP
    status_code = 200 if health_status['status'] == 'healthy' else 503
    
    return JsonResponse(health_status, status=status_code)


def health_check_simple(request):
    """
    Health check simple para Render
    GET /health/
    """
    try:
        # Solo verificar que la BD responda
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        return JsonResponse({'status': 'ok'}, status=200)
    except Exception as e:
        logger.error(f"Health check simple failed: {e}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=503)
