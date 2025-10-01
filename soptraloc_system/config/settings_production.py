"""
Django settings optimizadas para PRODUCCIÓN en Render.com
Sistema SoptraLoc TMS con ML - v2.0
"""

import os
import dj_database_url
from pathlib import Path
from decouple import config

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY - Producción estricta
SECRET_KEY = config(
    'SECRET_KEY',
    default='django-insecure-CHANGE-ME-IN-RENDER-ASAP-' + os.urandom(32).hex()
)
# TEMPORAL: DEBUG=True para diagnosticar error 500
# ⚠️ CAMBIAR A FALSE DESPUÉS DE VER EL ERROR
DEBUG = True

# Render.com specific configuration
RENDER_EXTERNAL_HOSTNAME = config('RENDER_EXTERNAL_HOSTNAME', default='soptraloc.onrender.com')

# Allowed hosts - TEMPORAL: Permitir todos para diagnóstico
# ⚠️ RESTRINGIR DESPUÉS DE VER EL ERROR
ALLOWED_HOSTS = [
    '*',  # Temporal: permitir todos
    RENDER_EXTERNAL_HOSTNAME,
    '.onrender.com',
    'soptraloc.onrender.com',
]

# CSRF Configuration - Solo HTTPS en producción
CSRF_TRUSTED_ORIGINS = [
    f'https://{RENDER_EXTERNAL_HOSTNAME}',
    'https://*.onrender.com',
    'https://soptraloc.onrender.com',
]

# Security settings - TEMPORALMENTE DESACTIVADO PARA DIAGNÓSTICO
# ⚠️ REACTIVAR DESPUÉS DE VER EL ERROR
SECURE_SSL_REDIRECT = False  # Temporal: era True
SESSION_COOKIE_SECURE = False  # Temporal: era True
CSRF_COOKIE_SECURE = False  # Temporal: era True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 0  # Temporal: era 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = False  # Temporal: era True
SECURE_HSTS_PRELOAD = False  # Temporal: era True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Application definition
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_filters',
    'drf_yasg',
    'django_extensions',
]

LOCAL_APPS = [
    'apps.core',         # Modelos base y autenticación ✅
    'apps.containers',   # Gestión de contenedores ✅
    'apps.routing',      # Sistema de tiempos y ML ✅
    'apps.drivers',      # Conductores, asignaciones y alertas ✅
    'apps.warehouses',   # Ubicaciones y almacenes ✅
    # Apps vacías eliminadas: scheduling, alerts, optimization
    # Las alertas están en apps.drivers.models.Alert
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database - PostgreSQL en Render (SIEMPRE)
DATABASE_URL = config(
    'DATABASE_URL',
    default='postgresql://user:pass@localhost:5432/defaultdb'
)

DATABASES = {
    'default': dj_database_url.config(
        default=DATABASE_URL,
        conn_max_age=600,
        conn_health_checks=True,
        ssl_require=True,
    )
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'es-es'
TIME_ZONE = 'America/Santiago'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]
STATIC_ROOT = BASE_DIR / 'staticfiles'

# WhiteNoise static file serving
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Autenticación
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'

# Django REST Framework - Producción
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
}

# Simple JWT Configuration
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=2),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}

# CORS - Solo dominios autorizados
CORS_ALLOWED_ORIGINS = [
    f'https://{RENDER_EXTERNAL_HOSTNAME}',
    'https://soptraloc.onrender.com',
]
CORS_ALLOW_CREDENTIALS = True

# Cache - Local memory (futuro: Redis)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'soptraloc-cache',
    }
}

# Email - Console backend (futuro: SMTP)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Logging optimizado para Render
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Print configuración al cargar
print("=" * 60)
print("✅ CONFIGURACIÓN DE PRODUCCIÓN CARGADA - RENDER.COM")
print("=" * 60)
print(f"DEBUG: {DEBUG}")
print(f"ALLOWED_HOSTS: {ALLOWED_HOSTS}")
print(f"DATABASE: PostgreSQL (Render)")
print(f"STATIC_ROOT: {STATIC_ROOT}")
print(f"SECURE_SSL_REDIRECT: {SECURE_SSL_REDIRECT}")
print(f"APPS INSTALADAS: {len(INSTALLED_APPS)}")
for app in LOCAL_APPS:
    print(f"  - {app}")
print("=" * 60)
