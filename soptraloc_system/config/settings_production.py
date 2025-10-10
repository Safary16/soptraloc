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
DEBUG = False

# Render.com specific configuration
RENDER_EXTERNAL_HOSTNAME = config('RENDER_EXTERNAL_HOSTNAME', default='soptraloc.onrender.com')

# Allowed hosts - Solo dominios autorizados
ALLOWED_HOSTS = [
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

# Security settings - Producción con ajustes para Render
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# CSRF Settings - Configuración específica para Render
CSRF_COOKIE_HTTPONLY = False  # Permitir JavaScript acceso si es necesario
CSRF_COOKIE_SAMESITE = 'Lax'  # Más permisivo que 'Strict' pero seguro
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_USE_SESSIONS = False  # Usar cookies en lugar de sesiones para CSRF

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
    'django_celery_beat',  # Celery Beat scheduler
    'axes',  # Rate limiting and brute force protection
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
    'axes.middleware.AxesMiddleware',  # Must be last
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
        # SSL configurado para Render - no requerir certificado
        ssl_require=False,  # Render maneja SSL en el proxy
    )
}

# Configuración adicional de SSL para PostgreSQL en Render
# Render usa SSL pero no requiere verificación de certificado
if 'DATABASE_URL' in os.environ:
    # Si estamos en Render (tiene DATABASE_URL), configurar SSL sin verificación
    DATABASES['default']['OPTIONS'] = {
        'sslmode': 'require',  # Usar SSL pero sin verificar certificado
        'connect_timeout': 10,  # Timeout de conexión 10 segundos
        'options': '-c statement_timeout=30000'  # Timeout de queries 30 segundos
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
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',  # Anonymous users
        'user': '1000/hour',  # Authenticated users
    },
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

# Cache - Redis in production
REDIS_URL = config('REDIS_URL', default='redis://localhost:6379/1')
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
            'RETRY_ON_TIMEOUT': True,
            'MAX_CONNECTIONS': 50,
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            }
        },
        'KEY_PREFIX': 'soptraloc',
        'TIMEOUT': 300,  # 5 minutes default
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

# Logging de configuración al cargar (usando logger)
import logging
logger = logging.getLogger(__name__)
# Django Axes - Brute force protection
AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesStandaloneBackend',  # AxesBackend should be first
    'django.contrib.auth.backends.ModelBackend',
]

AXES_FAILURE_LIMIT = 5  # Lock after 5 failed attempts
AXES_COOLOFF_TIME = 1  # Lock for 1 hour
AXES_LOCK_OUT_BY_COMBINATION_USER_AND_IP = True
AXES_RESET_ON_SUCCESS = True
AXES_LOCKOUT_TEMPLATE = None  # Return 403
AXES_LOCKOUT_PARAMETERS = ['username', 'ip_address']
AXES_ONLY_ADMIN_SITE = False  # Protect all login forms
AXES_ENABLE_ACCESS_FAILURE_LOG = True
AXES_VERBOSE = True

# Sentry Error Tracking
SENTRY_DSN = config('SENTRY_DSN', default=None)
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.celery import CeleryIntegration
    from sentry_sdk.integrations.redis import RedisIntegration
    
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(),
            CeleryIntegration(),
            RedisIntegration(),
        ],
        traces_sample_rate=0.5,
        send_default_pii=False,
        environment='production',
        release=config('RENDER_GIT_COMMIT', default='unknown'),
        before_send=lambda event, hint: event if not DEBUG else None,
    )
    logger.info("✅ Sentry initialized for error tracking")

# Mapbox API Key validation
MAPBOX_API_KEY = config('MAPBOX_API_KEY', default=None)
if not MAPBOX_API_KEY:
    logger.warning("⚠️  MAPBOX_API_KEY not configured - routing features will be limited")

# AWS S3 Storage for Media Files
USE_S3 = config('USE_S3', default=False, cast=bool)
if USE_S3:
    AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = config('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_REGION_NAME = config('AWS_S3_REGION_NAME', default='us-east-1')
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
    AWS_DEFAULT_ACL = 'public-read'
    AWS_S3_OBJECT_PARAMETERS = {
        'CacheControl': 'max-age=86400',
    }
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'
    logger.info("✅ AWS S3 configured for media storage")
else:
    MEDIA_ROOT = BASE_DIR / 'media'
    MEDIA_URL = '/media/'

logger.info("=" * 60)
logger.info("✅ CONFIGURACIÓN DE PRODUCCIÓN CARGADA - RENDER.COM")
logger.info("=" * 60)
logger.info(f"DEBUG: {DEBUG}")
logger.info(f"ALLOWED_HOSTS: {ALLOWED_HOSTS}")
logger.info(f"DATABASE: PostgreSQL (Render)")
logger.info(f"CACHE: Redis ({REDIS_URL.split('@')[1] if '@' in REDIS_URL else 'localhost'})")
logger.info(f"STATIC_ROOT: {STATIC_ROOT}")
logger.info(f"SECURE_SSL_REDIRECT: {SECURE_SSL_REDIRECT}")
logger.info(f"RATE LIMITING: Enabled (Axes + DRF Throttling)")
logger.info(f"SENTRY: {'Enabled' if SENTRY_DSN else 'Disabled'}")
logger.info(f"S3 STORAGE: {'Enabled' if USE_S3 else 'Local media'}")
logger.info(f"APPS INSTALADAS: {len(INSTALLED_APPS)}")
for app in LOCAL_APPS:
    logger.info(f"  - {app}")
logger.info("=" * 60)
