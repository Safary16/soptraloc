"""
Django settings for SoptraLoc TMS
"""
import os
from pathlib import Path
from decouple import config
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# Security
SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-in-production')
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='*', cast=lambda v: [s.strip() for s in v.split(',')])

# Guardas de producción (hardening 2026-09-17): si DEBUG=False deben existir secret y hosts concretos
if not DEBUG:
    if SECRET_KEY == 'django-insecure-change-in-production' or not SECRET_KEY.strip():
        from django.core.exceptions import ImproperlyConfigured
        raise ImproperlyConfigured('SECRET_KEY debe definirse en producción (env).')
    if '*' in ALLOWED_HOSTS:
        from django.core.exceptions import ImproperlyConfigured
        raise ImproperlyConfigured('ALLOWED_HOSTS no puede ser "*" en producción.')

CSRF_TRUSTED_ORIGINS = [
    "https://*.github.dev",
    "https://localhost:8000",
    "https://soptraloc.onrender.com",
    "https://soptraloc-qiss.onrender.com",
    "https://soptraloc.up.railway.app",
]

# Render.com automatic hostname
RENDER_EXTERNAL_HOSTNAME = config('RENDER_EXTERNAL_HOSTNAME', default=None)
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# Security settings for production
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000  # 1 año
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True

# Apps
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party
    'rest_framework',
    'rest_framework_simplejwt',
    'django_filters',
    'corsheaders',
    'drf_yasg',
    
    # Local apps
    'apps.core',
    'apps.containers',
    'apps.drivers',
    'apps.programaciones',
    'apps.events',
    'apps.cds',
    'apps.notifications',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
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

# Database
DELETED_RENDER_DB_HOST = 'dpg-d9e1pj3rjlhs73bii2c0-a'  # Postgres free de Render eliminado (~30 días)
IS_RENDER = (
    os.environ.get('RENDER', '').strip().lower() == 'true'
    or bool(os.environ.get('RENDER_EXTERNAL_HOSTNAME'))
)
database_url = config('DATABASE_URL', default='').strip()
db_url_valid = bool(database_url) and DELETED_RENDER_DB_HOST not in database_url

if db_url_valid:
    DATABASES = {
        'default': dj_database_url.config(
            default=database_url,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
elif IS_RENDER:
    # NUNCA arrancar sobre SQLite efímero en Render: el filesystem es efímero y
    # toda la data se pierde en cada deploy/reinicio (verificado 2026-09-15).
    from django.core.exceptions import ImproperlyConfigured
    raise ImproperlyConfigured(
        'DATABASE_URL inválida o ausente en Render (host eliminado: '
        f'{DELETED_RENDER_DB_HOST}). Render NO provisionó la base de datos.\n'
        'SOLUCIÓN: crea el servicio con el Blueprint (render.yaml) para que Render '
        'provisione el Postgres "soptraloc-db" e inyecte DATABASE_URL, o crea una '
        'PostgreSQL en el dashboard y pega su connectionString en la env var '
        'DATABASE_URL (Environment tab). Luego Manual Deploy → Clear build cache & deploy.'
    )
else:
    # Desarrollo local sin Postgres → SQLite (aceptable solo fuera de Render)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'es-es'
TIME_ZONE = 'America/Santiago'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        # BasicAuthentication deshabilitada: disparaba el popup HTTP Basic del
        # navegador ('requiere usuario y contraseña') antes de llegar a Django.
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
}

# CORS
CORS_ALLOW_ALL_ORIGINS = DEBUG
CORS_ALLOW_CREDENTIALS = True

# Mapbox
MAPBOX_API_KEY = config('MAPBOX_API_KEY', default=None)

# Alertas
ALERTA_PROGRAMACION_DIAS = config('ALERTA_PROGRAMACION_DIAS', default=2, cast=int)
ALERTA_DEMURRAGE_DIAS = config('ALERTA_DEMURRAGE_DIAS', default=2, cast=int)

# Asignación automática
PESO_DISPONIBILIDAD = config('PESO_DISPONIBILIDAD', default=0.30, cast=float)
PESO_OCUPACION = config('PESO_OCUPACION', default=0.25, cast=float)
PESO_CUMPLIMIENTO = config('PESO_CUMPLIMIENTO', default=0.30, cast=float)
PESO_PROXIMIDAD = config('PESO_PROXIMIDAD', default=0.15, cast=float)

# Login URLs
LOGIN_URL = '/driver/login/'
LOGIN_REDIRECT_URL = '/driver/dashboard/'
LOGOUT_REDIRECT_URL = '/driver/login/'

SITE_URL = config('SITE_URL', default='http://localhost:8000')

# Logging para capturar cualquier error 500 en producción (Render)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
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
            'propagate': True,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}

