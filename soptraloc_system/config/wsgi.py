"""
WSGI config for soptraloc_system project - PRODUCCIÓN
"""

import os

from django.core.wsgi import get_wsgi_application

# CRÍTICO: Usar settings_production en producción
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_production')

application = get_wsgi_application()