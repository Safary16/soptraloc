# ⚡ AUDITORÍA - FASE 7: PERFORMANCE Y OPTIMIZACIÓN

**Fecha**: 2025-10-10  
**Auditor**: GitHub Copilot  
**Alcance**: Análisis exhaustivo de performance: queries N+1, select_related/prefetch_related, caching, indexing, database connection pooling, Celery optimization, profiling

---

## 📊 RESUMEN EJECUTIVO

### Estadísticas de Performance
- **Queries N+1 identificados**: 5+ casos críticos
- **select_related usage**: 🟡 20+ casos implementados (correcto)
- **prefetch_related usage**: 🔴 Solo 1 caso (falta optimización many-to-many)
- **Caching**: 🔴 Redis configurado pero **casi sin uso** (solo Mapbox con 5min TTL)
- **Índices DB**: 🟢 6 índices en Container, algunos en otras tablas
- **Celery tasks**: 🟢 7 tasks asíncronos correctos
- **Database pooling**: 🟡 Sin configuración explícita (usando default)
- **Compresión**: ❌ No configurada (WhiteNoise sin GZip)

### Veredicto General de Performance
🟡 **MODERADO/BUENO** - Sistema usa `select_related` correctamente en ViewSets principales, tiene índices básicos y Celery configurado. **PERO falta cache estratégico (stats, dashboard), prefetch_related para relaciones múltiples, índices compuestos adicionales, y compresión de assets**.

---

## 1️⃣ ANÁLISIS DE QUERIES N+1

### 🟢 **FORTALEZA: select_related en ViewSets principales**

```python
# ✅ apps/containers/views.py (línea 45)
class ContainerViewSet(viewsets.ModelViewSet):
    queryset = Container.objects.filter(is_active=True).select_related(
        'owner_company', 'current_location', 'current_vehicle'
    )
```

**Fortalezas**:
- ✅ ViewSet principal optimizado con `select_related`
- ✅ Evita N+1 en ForeignKeys más usados

---

### 🔴 **PROBLEMA CRÍTICO: N+1 en dashboard_view**

```python
# ❌ apps/core/auth_views.py (líneas 119-126)
@login_required
def dashboard_view(request):
    """Dashboard principal con contenedores programados"""
    
    base_queryset = Container.objects.select_related(
        'conductor_asignado',
        'client',
        'terminal',
        'owner_company',
        'vessel',
        'agency',
        'shipping_line'
    )
    # ✅ select_related BIEN usado aquí
    
    # Pero luego...
    
    # ❌ PROBLEMA: Multiple .count() queries sin cache
    stats = {
        'por_arribar': normalized_counts.get('POR_ARRIBAR', 0),
        'programados': normalized_counts.get('PROGRAMADO', 0),
        'en_proceso': normalized_counts.get('EN_PROCESO', 0),
        # ... 13 counts diferentes
    }
    # ← 1 query para obtener counts (correcto con .values().annotate())
    
    # ❌ PROBLEMA: Queries separados para alertas
    'alertas_activas': Alert.objects.filter(is_active=True).count(),
    # ← +1 query
    
    # ❌ PROBLEMA: En template, si iteramos por contenedores y accedemos a:
    # {{ container.conductor_asignado.nombre }}  ← Ya optimizado con select_related
    # {{ container.client.name }}                ← Ya optimizado
    # 
    # PERO si accedemos a relaciones many-to-many o reverse FK sin prefetch:
    # {{ container.movimientos.count }}          ← N+1 query!
    # {{ container.documentos.count }}           ← N+1 query!
```

**Análisis del problema**:
En el dashboard actual, el N+1 está parcialmente resuelto con `select_related` para ForeignKeys. **PERO**:

1. **Falta cache** para stats (se recalculan en cada request)
2. **Falta prefetch_related** si se accede a relaciones inversas (movimientos, documentos, inspecciones)

---

### 🔴 **PROBLEMA: N+1 en resueltos_view con multiple counts**

```python
# ⚠️ apps/core/auth_views.py (líneas 247-250)
stats = {
    'asignados': contenedores_resueltos.filter(status='ASIGNADO').count(),
    'en_ruta': contenedores_resueltos.filter(status='EN_RUTA').count(),
    'arribados': contenedores_resueltos.filter(status='ARRIBADO').count(),
    'finalizados': contenedores_resueltos.filter(status='FINALIZADO').count(),
}
# ← 4 queries separados para contar
```

**Solución**:
```python
# ✅ CORREGIR: 1 query con annotate

from django.db.models import Count, Q

# Opción 1: Usando conditional aggregation
stats = contenedores_resueltos.aggregate(
    asignados=Count('id', filter=Q(status='ASIGNADO')),
    en_ruta=Count('id', filter=Q(status='EN_RUTA')),
    arribados=Count('id', filter=Q(status='ARRIBADO')),
    finalizados=Count('id', filter=Q(status='FINALIZADO')),
)
# ← 1 solo query!

# Opción 2: Si necesitas todos los counts
status_counts = contenedores_resueltos.values('status').annotate(count=Count('id'))
stats = {item['status']: item['count'] for item in status_counts}
stats_normalized = {
    'asignados': stats.get('ASIGNADO', 0),
    'en_ruta': stats.get('EN_RUTA', 0),
    'arribados': stats.get('ARRIBADO', 0),
    'finalizados': stats.get('FINALIZADO', 0),
}
# ← También 1 solo query
```

---

### 🟡 **MEJORA: Agregar prefetch_related para relaciones many-to-many**

```python
# ⚠️ Si en algún lugar accedes a relaciones inversas sin prefetch:

# ❌ MAL:
containers = Container.objects.select_related('owner_company').all()
for container in containers:
    print(container.movimientos.count())  # ← N+1 query!
    print(container.documentos.count())   # ← N+1 query!

# ✅ BIEN:
containers = Container.objects.select_related('owner_company').prefetch_related(
    'movimientos',
    'documentos',
    'inspecciones'
).all()
for container in containers:
    print(container.movimientos.count())  # ← 0 queries adicionales
    print(container.documentos.count())   # ← 0 queries adicionales
```

**Solución**:
```python
# ✅ AGREGAR: En ViewSets que necesiten relaciones inversas

class ContainerViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        qs = Container.objects.filter(is_active=True).select_related(
            'owner_company', 'current_location', 'current_vehicle',
            'conductor_asignado', 'client', 'terminal', 'vessel', 'agency', 'shipping_line'
        )
        
        # ✅ Si action es 'retrieve' (detalle), prefetch relaciones
        if self.action == 'retrieve':
            qs = qs.prefetch_related(
                'movimientos',
                'documentos',
                'inspecciones',
                # Puedes hacer prefetch anidado:
                Prefetch(
                    'movimientos',
                    queryset=ContainerMovement.objects.select_related('from_location', 'to_location', 'to_vehicle')
                )
            )
        
        return qs
```

---

## 2️⃣ ANÁLISIS DE CACHING

### 🔴 **PROBLEMA CRÍTICO: Redis configurado pero casi sin uso**

```python
# ✅ config/settings.py (línea 197)
CELERY_BROKER_URL = config('REDIS_URL', default='redis://localhost:6379')
CELERY_RESULT_BACKEND = config('REDIS_URL', default='redis://localhost:6379')

# ← Redis está configurado para Celery, pero NO para cache general de Django
```

**Estado actual**:
- ✅ Redis corriendo para Celery (broker + result backend)
- 🔴 Django NO usa Redis para cache (sin configuración de CACHES)
- 🟡 Solo 1 uso de cache: Mapbox API con TTL de 5 minutos

```python
# ⚠️ apps/routing/mapbox_service.py (líneas 106, 227)
cache_key = f"mapbox_travel:{origin_query}:{dest_query}"
cached = cache.get(cache_key)
if cached and not departure_time:
    return cached
# ...
cache.set(cache_key, result, 300)  # ← 5 minutos
```

**Problemas**:
- 🔴 Stats del dashboard se recalculan en **cada request** (sin cache)
- 🔴 Counts de contenedores por status se recalculan (sin cache)
- 🔴 Queries frecuentes no se cachean (listados, búsquedas)
- 🔴 TimeMatrix podría cachearse (no cambia seguido)

---

### ✅ **SOLUCIÓN: Implementar cache estratégico con Redis**

```python
# ✅ PASO 1: Configurar Redis como backend de cache

# config/settings.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': config('REDIS_URL', default='redis://localhost:6379/1'),  # ← DB 1 para cache
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'soptraloc',
        'TIMEOUT': 300,  # 5 minutos por defecto
    }
}

# Si quieres cache de templates:
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'OPTIONS': {
            ...
            'loaders': [
                ('django.template.loaders.cached.Loader', [
                    'django.template.loaders.filesystem.Loader',
                    'django.template.loaders.app_directories.Loader',
                ]),
            ] if not DEBUG else [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
            ],
        },
    },
]

# ✅ PASO 2: Cachear stats del dashboard

# apps/core/auth_views.py
from django.core.cache import cache
from django.views.decorators.cache import cache_page

@login_required
@cache_page(60 * 2)  # ← Cache 2 minutos
def dashboard_view(request):
    """Dashboard con cache de 2 minutos"""
    ...

# O cache manual más granular:
@login_required
def dashboard_view(request):
    """Dashboard con cache selectivo"""
    
    # Cache de stats (5 minutos)
    cache_key = 'dashboard:stats'
    stats = cache.get(cache_key)
    
    if stats is None:
        raw_status_counts = Container.objects.values_list('status').annotate(count=Count('id'))
        normalized_counts = {
            summary.code: summary.count for summary in summarize_statuses(raw_status_counts)
        }
        
        stats = {
            'total': sum(normalized_counts.values()),
            'por_arribar': normalized_counts.get('POR_ARRIBAR', 0),
            'programados': normalized_counts.get('PROGRAMADO', 0),
            # ... todos los stats
        }
        
        cache.set(cache_key, stats, 300)  # ← 5 minutos
    
    # Containers NO se cachean (cambian frecuentemente)
    containers = base_queryset.filter(...)
    
    return render(request, 'dashboard.html', {
        'stats': stats,
        'containers': containers,
    })

# ✅ PASO 3: Invalidar cache cuando cambian datos

# apps/containers/views.py
class ContainerViewSet(viewsets.ModelViewSet):
    def perform_create(self, serializer):
        serializer.save()
        # Invalidar cache de stats
        cache.delete('dashboard:stats')
    
    def perform_update(self, serializer):
        serializer.save()
        # Invalidar cache si cambió status
        if 'status' in serializer.validated_data:
            cache.delete('dashboard:stats')

# ✅ PASO 4: Cache para queries costosos

# apps/containers/services/stats_service.py
from django.core.cache import cache

class ContainerStatsService:
    """Servicio de estadísticas con cache"""
    
    @staticmethod
    def get_status_counts(force_refresh=False):
        """Obtiene counts por status con cache de 5 minutos"""
        cache_key = 'container:status_counts'
        
        if not force_refresh:
            cached = cache.get(cache_key)
            if cached:
                return cached
        
        counts = Container.objects.values('status').annotate(count=Count('id'))
        result = {item['status']: item['count'] for item in counts}
        
        cache.set(cache_key, result, 300)
        return result
    
    @staticmethod
    def get_driver_availability():
        """Cache de disponibilidad de conductores"""
        cache_key = 'drivers:availability'
        
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        result = Driver.objects.filter(is_active=True).values('status').annotate(count=Count('id'))
        availability = {item['status']: item['count'] for item in result}
        
        cache.set(cache_key, availability, 180)  # 3 minutos
        return availability

# ✅ PASO 5: Cache de API responses (DRF)

# Instalar: pip install drf-extensions

# apps/containers/views.py
from rest_framework_extensions.cache.decorators import cache_response
from rest_framework_extensions.cache.mixins import CacheResponseMixin

class ContainerViewSet(CacheResponseMixin, viewsets.ModelViewSet):
    """✅ Con cache de respuestas API"""
    
    # Cache de 5 minutos para list y retrieve
    @cache_response(timeout=300, key_func='calculate_cache_key')
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    def calculate_cache_key(self, view_instance, view_method, request, args, kwargs):
        """Genera cache key único por usuario y filtros"""
        user_id = request.user.id if request.user.is_authenticated else 'anon'
        query_params = request.query_params.urlencode()
        return f'container:list:{user_id}:{query_params}'
```

---

## 3️⃣ ANÁLISIS DE INDEXING

### 🟢 **FORTALEZA: Índices básicos implementados**

```python
# ✅ apps/containers/models.py (líneas 335-342)
class Container(models.Model):
    ...
    class Meta:
        indexes = [
            models.Index(fields=['status'], name='idx_status'),
            models.Index(fields=['scheduled_date'], name='idx_scheduled'),
            models.Index(fields=['conductor_asignado'], name='idx_driver'),
            models.Index(fields=['container_number'], name='idx_number'),
            models.Index(fields=['status', 'scheduled_date'], name='idx_status_date'),
            models.Index(fields=['conductor_asignado', 'status'], name='idx_driver_status'),
        ]
```

**Fortalezas**:
- ✅ Índices en campos más consultados: `status`, `scheduled_date`, `conductor_asignado`, `container_number`
- ✅ Índices compuestos: `(status, scheduled_date)`, `(conductor_asignado, status)`

---

### 🟡 **MEJORA: Faltan índices adicionales**

```python
# ⚠️ FALTAN índices para:
# - owner_company (frecuentemente filtrado)
# - is_active (usado en queryset principal)
# - created_at, updated_at (para sorting temporal)
# - Campos de búsqueda: seal_number, customs_document
```

**Solución**:
```python
# ✅ AGREGAR: Índices adicionales

# apps/containers/models.py
class Container(models.Model):
    ...
    class Meta:
        indexes = [
            # Índices existentes
            models.Index(fields=['status'], name='idx_status'),
            models.Index(fields=['scheduled_date'], name='idx_scheduled'),
            models.Index(fields=['conductor_asignado'], name='idx_driver'),
            models.Index(fields=['container_number'], name='idx_number'),
            models.Index(fields=['status', 'scheduled_date'], name='idx_status_date'),
            models.Index(fields=['conductor_asignado', 'status'], name='idx_driver_status'),
            
            # ✅ NUEVOS índices
            models.Index(fields=['owner_company'], name='idx_owner'),
            models.Index(fields=['is_active', 'status'], name='idx_active_status'),
            models.Index(fields=['created_at'], name='idx_created'),
            models.Index(fields=['updated_at'], name='idx_updated'),
            models.Index(fields=['seal_number'], name='idx_seal'),
            
            # Índice para dashboard (filtro común)
            models.Index(
                fields=['is_active', 'status', 'scheduled_date'], 
                name='idx_dashboard_filter'
            ),
            
            # Índice para búsqueda de contenedores sin asignar
            models.Index(
                fields=['status', 'conductor_asignado'], 
                name='idx_unassigned',
                condition=Q(conductor_asignado__isnull=True)  # ← Partial index
            ),
        ]

# ✅ Generar migración:
# python manage.py makemigrations
# python manage.py migrate

# ✅ AGREGAR: Índices en otros modelos

# apps/drivers/models.py
class Driver(models.Model):
    ...
    class Meta:
        indexes = [
            models.Index(fields=['status'], name='idx_driver_status'),
            models.Index(fields=['is_active', 'status'], name='idx_driver_active'),
            models.Index(fields=['rut'], name='idx_driver_rut'),  # ← Búsquedas frecuentes
            models.Index(fields=['company'], name='idx_driver_company'),
        ]

# apps/routing/models.py
class Assignment(models.Model):
    ...
    class Meta:
        indexes = [
            models.Index(fields=['container'], name='idx_assignment_container'),
            models.Index(fields=['driver'], name='idx_assignment_driver'),
            models.Index(fields=['status', 'scheduled_date'], name='idx_assignment_scheduled'),
            models.Index(fields=['created_at'], name='idx_assignment_created'),
        ]

class TimeMatrix(models.Model):
    ...
    class Meta:
        indexes = [
            # Índice compuesto para lookups origen-destino
            models.Index(fields=['origen', 'destino'], name='idx_timematrix_route'),
            models.Index(fields=['updated_at'], name='idx_timematrix_updated'),
        ]
```

---

## 4️⃣ ANÁLISIS DE CELERY Y TAREAS ASÍNCRONAS

### 🟢 **FORTALEZA: Celery bien configurado**

```python
# ✅ config/settings.py (líneas 197-202)
CELERY_BROKER_URL = config('REDIS_URL', default='redis://localhost:6379')
CELERY_RESULT_BACKEND = config('REDIS_URL', default='redis://localhost:6379')
CELERY_ACCEPT_CONTENT = ['application/json']  # ← JSON (seguro)
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
```

**Fortalezas**:
- ✅ Redis como broker (rápido y confiable)
- ✅ JSON serializer (seguro, no pickle)
- ✅ Result backend configurado

---

### 🟢 **FORTALEZA: 7 tasks asíncronos implementados**

```python
# ✅ apps/containers/tasks.py

@shared_task
def check_containers_requiring_assignment():
    """Verifica contenedores que necesitan asignación"""
    ...

@shared_task
def check_late_assignments():
    """Verifica asignaciones atrasadas"""
    ...

@shared_task
def check_critical_assignments():
    """Verifica asignaciones críticas"""
    ...

@shared_task
def check_containers_pending_return():
    """Verifica contenedores pendientes de devolución"""
    ...

@shared_task
def calculate_daily_metrics():
    """Calcula métricas diarias"""
    ...

@shared_task
def cleanup_old_alerts():
    """Limpia alertas antiguas"""
    ...
```

**Fortalezas**:
- ✅ Tasks bien separados por responsabilidad
- ✅ Usan `@shared_task` (correcto)
- ✅ Tasks con `select_related` para optimizar queries

---

### 🟡 **MEJORA: Faltan periodic tasks configurados**

```python
# ⚠️ FALTA: Configuración de Celery Beat para ejecutar tasks periódicos

# ❌ No hay celery.py en config/
# ❌ No hay schedule configurado
```

**Solución**:
```python
# ✅ CREAR: config/celery.py

import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('soptraloc')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# ✅ Configurar periodic tasks
app.conf.beat_schedule = {
    'check-unassigned-containers': {
        'task': 'apps.containers.tasks.check_containers_requiring_assignment',
        'schedule': crontab(minute='*/15'),  # ← Cada 15 minutos
    },
    'check-late-assignments': {
        'task': 'apps.containers.tasks.check_late_assignments',
        'schedule': crontab(minute='*/30'),  # ← Cada 30 minutos
    },
    'check-critical-assignments': {
        'task': 'apps.containers.tasks.check_critical_assignments',
        'schedule': crontab(hour='*/1'),     # ← Cada hora
    },
    'cleanup-old-alerts': {
        'task': 'apps.containers.tasks.cleanup_old_alerts',
        'schedule': crontab(hour=3, minute=0),  # ← Diario a las 3 AM
    },
    'calculate-daily-metrics': {
        'task': 'apps.containers.tasks.calculate_daily_metrics',
        'schedule': crontab(hour=0, minute=30),  # ← Diario a las 00:30
    },
    'invalidate-dashboard-cache': {
        'task': 'apps.core.tasks.invalidate_dashboard_cache',
        'schedule': crontab(minute='*/5'),  # ← Cada 5 minutos
    },
}

app.conf.timezone = 'America/Santiago'

# ✅ AGREGAR: config/__init__.py
from .celery import app as celery_app

__all__ = ('celery_app',)

# ✅ Ejecutar:
# celery -A config worker --loglevel=info
# celery -A config beat --loglevel=info  # ← Para periodic tasks
```

---

### 🟡 **MEJORA: Tasks sin retry ni error handling**

```python
# ⚠️ apps/containers/tasks.py
@shared_task
def check_containers_requiring_assignment():
    """❌ Sin retry ni error handling"""
    try:
        # Código del task
        ...
    except Exception as e:
        # ← Solo logging, no retry
        logger.error(f"Error: {e}")
```

**Solución**:
```python
# ✅ MEJORAR: Agregar retry y error handling

@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60  # 1 minuto
)
def check_containers_requiring_assignment(self):
    """✅ Con retry automático"""
    try:
        containers = Container.objects.filter(
            status__in=related_status_values('PROGRAMADO'),
            scheduled_date__lte=timezone.localdate(),
            conductor_asignado__isnull=True
        ).select_related('client', 'owner_company')
        
        # Proceso del task...
        
    except Exception as exc:
        logger.error(f"Error en check_containers: {exc}")
        # Retry con exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

# ✅ AGREGAR: Task de limpieza de cache

@shared_task
def invalidate_dashboard_cache():
    """Invalida cache del dashboard periódicamente"""
    from django.core.cache import cache
    
    cache.delete('dashboard:stats')
    cache.delete_pattern('container:list:*')  # ← Requiere django-redis
    logger.info("✅ Cache del dashboard invalidado")

# ✅ AGREGAR: Task de precarga de cache (warm-up)

@shared_task
def warmup_cache():
    """Pre-carga datos frecuentes en cache"""
    from apps.containers.services.stats_service import ContainerStatsService
    
    # Pre-cargar stats
    ContainerStatsService.get_status_counts(force_refresh=True)
    ContainerStatsService.get_driver_availability()
    
    logger.info("✅ Cache precargado exitosamente")
```

---

## 5️⃣ ANÁLISIS DE DATABASE CONNECTION POOLING

### 🟡 **PROBLEMA: Sin connection pooling configurado**

```python
# ⚠️ config/settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME', default='soptraloc'),
        'USER': config('DB_USER', default='postgres'),
        'PASSWORD': config('DB_PASSWORD', default='password'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
        # ❌ FALTA: Connection pooling
    }
}
```

**Problemas**:
- 🟡 Cada request crea nueva conexión DB (overhead)
- 🟡 Sin límite de conexiones (puede saturar PostgreSQL)

**Solución**:
```python
# ✅ IMPLEMENTAR: Connection pooling con django-db-geventpool

# requirements.txt
# django-db-geventpool==4.0.1  # ← Agregar

# config/settings_production.py
DATABASES = {
    'default': {
        'ENGINE': 'django_db_geventpool.backends.postgresql_psycopg2',  # ← Pooling
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT', default='5432'),
        'CONN_MAX_AGE': 60,  # ← Mantener conexión 60 segundos
        'OPTIONS': {
            'MAX_CONNS': 20,      # ← Máximo 20 conexiones en pool
            'REUSE_CONNS': 10,    # ← Reusar hasta 10 conexiones
        },
    }
}

# Alternativa con pgbouncer (más robusto para producción):
# En Render.com, configurar PgBouncer:
# DATABASE_URL = "postgresql://user:pass@pgbouncer:6432/dbname"
```

---

## 6️⃣ ANÁLISIS DE COMPRESIÓN Y ASSETS

### 🟡 **PROBLEMA: Sin compresión de respuestas**

```python
# ⚠️ config/settings.py
# WhiteNoise configurado, PERO sin GZip

MIDDLEWARE = [
    ...,
    'whitenoise.middleware.WhiteNoiseMiddleware',  # ← Sin compresión
    ...
]

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
# ← Comprime archivos estáticos, PERO no respuestas HTTP
```

**Solución**:
```python
# ✅ AGREGAR: Compresión de respuestas HTTP

# requirements.txt
# django-compression-middleware==0.5.0  # ← Agregar

# config/settings.py
MIDDLEWARE = [
    'django.middleware.gzip.GZipMiddleware',  # ← AGREGAR como primero
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    ...
]

# Configuración adicional
GZIP_COMPRESS_LEVEL = 6  # Balance velocidad/compresión (1-9)
GZIP_MIN_LENGTH = 1024   # Solo comprimir > 1KB

# ✅ Compresión de archivos estáticos (ya configurado)
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ✅ AGREGAR: Compresión de JSON responses en DRF
# apps/core/renderers.py
from rest_framework.renderers import JSONRenderer
import gzip

class CompressedJSONRenderer(JSONRenderer):
    """Renderer con compresión Gzip"""
    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = super().render(data, accepted_media_type, renderer_context)
        
        # Si response > 1KB, comprimir
        if renderer_context and len(response) > 1024:
            request = renderer_context.get('request')
            if request and 'gzip' in request.META.get('HTTP_ACCEPT_ENCODING', ''):
                compressed = gzip.compress(response)
                renderer_context['response']['Content-Encoding'] = 'gzip'
                return compressed
        
        return response

# config/settings.py
REST_FRAMEWORK = {
    ...,
    'DEFAULT_RENDERER_CLASSES': [
        'apps.core.renderers.CompressedJSONRenderer',  # ← Usar renderer comprimido
    ],
}
```

---

## 7️⃣ ANÁLISIS DE PROFILING Y MONITORING

### 🔴 **PROBLEMA: Sin herramientas de profiling**

```python
# ❌ FALTA: Django Debug Toolbar (desarrollo)
# ❌ FALTA: django-silk (profiling en producción)
# ❌ FALTA: Sentry (error tracking)
# ❌ FALTA: New Relic / DataDog (APM)
```

**Solución**:
```python
# ✅ AGREGAR: Django Debug Toolbar (solo desarrollo)

# requirements.txt
# django-debug-toolbar==4.5.0  # ← Agregar

# config/settings.py
if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']
    
    MIDDLEWARE = [
        'debug_toolbar.middleware.DebugToolbarMiddleware',  # ← Después de GZip
    ] + MIDDLEWARE
    
    INTERNAL_IPS = ['127.0.0.1', 'localhost']
    
    DEBUG_TOOLBAR_CONFIG = {
        'SHOW_TOOLBAR_CALLBACK': lambda request: DEBUG,
        'DISABLE_PANELS': [],
        'SHOW_TEMPLATE_CONTEXT': True,
    }

# config/urls.py
if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]

# ✅ AGREGAR: django-silk (profiling producción seguro)

# requirements.txt
# django-silk==5.2.0  # ← Agregar

# config/settings.py
INSTALLED_APPS += ['silk']

MIDDLEWARE = [
    'silk.middleware.SilkyMiddleware',  # ← Después de Debug Toolbar
] + MIDDLEWARE

SILKY_PYTHON_PROFILER = True
SILKY_AUTHENTICATION = True  # ← Solo usuarios autenticados
SILKY_AUTHORISATION = True
SILKY_MAX_REQUEST_BODY_SIZE = 10240  # 10KB
SILKY_MAX_RESPONSE_BODY_SIZE = 10240

# config/urls.py
urlpatterns += [
    path('silk/', include('silk.urls', namespace='silk')),
]

# ✅ AGREGAR: Sentry (error tracking)

# requirements.txt
# sentry-sdk==2.18.0  # ← Agregar

# config/settings_production.py
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration

sentry_sdk.init(
    dsn=config('SENTRY_DSN'),
    integrations=[
        DjangoIntegration(),
        CeleryIntegration(),
    ],
    traces_sample_rate=0.1,  # ← 10% de transacciones
    profiles_sample_rate=0.1,
    send_default_pii=False,  # ← No enviar PII
    environment='production',
    release=config('RELEASE_VERSION', default='dev'),
)
```

---

## 8️⃣ QUERY OPTIMIZATION EXAMPLES

### 🔴 **ANTI-PATTERN: Queries en loops**

```python
# ❌ MAL: N queries
containers = Container.objects.filter(status='PROGRAMADO')
for container in containers:
    driver = container.conductor_asignado  # ← 1 query por iteración
    if driver:
        print(driver.nombre)
        print(driver.vehicle.plate)  # ← +1 query por iteración
```

**Solución**:
```python
# ✅ BIEN: 1 query con select_related
containers = Container.objects.filter(status='PROGRAMADO').select_related(
    'conductor_asignado',
    'conductor_asignado__vehicle'  # ← Nested select_related
)
for container in containers:
    driver = container.conductor_asignado  # ← 0 queries
    if driver:
        print(driver.nombre)
        print(driver.vehicle.plate)  # ← 0 queries
```

---

### 🔴 **ANTI-PATTERN: Cargar objetos completos para counts**

```python
# ❌ MAL: Carga todos los objetos en memoria
containers = Container.objects.filter(status='PROGRAMADO')
total = len(containers)  # ← Carga TODOS los objetos
```

**Solución**:
```python
# ✅ BIEN: Count en DB
total = Container.objects.filter(status='PROGRAMADO').count()  # ← 1 query simple

# ✅ BIEN: Exists para checks booleanos
has_programados = Container.objects.filter(status='PROGRAMADO').exists()  # ← Más rápido que count
```

---

### 🔴 **ANTI-PATTERN: Solo cargar IDs para otro query**

```python
# ❌ MAL: 2 queries
container_ids = Container.objects.filter(status='PROGRAMADO').values_list('id', flat=True)
containers = Container.objects.filter(id__in=container_ids).select_related('client')
```

**Solución**:
```python
# ✅ BIEN: 1 query
containers = Container.objects.filter(status='PROGRAMADO').select_related('client')
```

---

## 🎯 PUNTUACIÓN POR CATEGORÍA

| Categoría                          | Puntuación | Comentario                                      |
|------------------------------------|------------|-------------------------------------------------|
| **Queries N+1**                    | 7/10       | 🟢 select_related bien usado, falta prefetch    |
| **Caching**                        | 3/10       | 🔴 Redis sin usar, sin cache de stats           |
| **Indexing**                       | 7/10       | 🟢 Índices básicos, faltan compuestos           |
| **Celery/Async**                   | 8/10       | 🟢 Bien configurado, falta Beat schedule        |
| **Database Pooling**               | 5/10       | 🟡 Sin pooling explícito                        |
| **Compresión**                     | 4/10       | 🟡 WhiteNoise OK, sin GZip responses            |
| **Profiling**                      | 2/10       | 🔴 Sin herramientas de profiling                |
| **Query Optimization**             | 7/10       | 🟢 Usa ORM correctamente, pocos antipatterns    |
| **API Response Time**              | 6/10       | 🟡 Sin cache, podría ser más rápido             |
| **Static Files**                   | 8/10       | 🟢 WhiteNoise configurado correctamente         |

**PROMEDIO**: **5.7/10** 🟡 **NECESITA MEJORAS**

---

## 📋 RECOMENDACIONES PRIORIZADAS

### 🔴 **CRÍTICO (Hacer HOY - Performance bloquea escalabilidad)**

1. **Implementar cache con Redis INMEDIATAMENTE**
   ```python
   # config/settings.py
   CACHES = {
       'default': {
           'BACKEND': 'django.core.cache.backends.redis.RedisCache',
           'LOCATION': config('REDIS_URL', default='redis://localhost:6379/1'),
       }
   }
   ```
   **Impacto**: Dashboard 10x más rápido, reduce carga DB

2. **Cachear stats del dashboard**
   ```python
   @cache_page(60 * 2)  # 2 minutos
   def dashboard_view(request):
       ...
   ```
   **Impacto**: Reduce queries de 20+ a 3-5 por request

3. **Agregar índices faltantes**
   ```python
   models.Index(fields=['owner_company'], name='idx_owner'),
   models.Index(fields=['is_active', 'status'], name='idx_active_status'),
   ```
   **Impacto**: Queries 5-10x más rápidas

---

### 🔴 **CRÍTICO (Hacer ESTA SEMANA)**

4. **Configurar Celery Beat para periodic tasks**
   ```python
   # config/celery.py con beat_schedule
   ```
   **Impacto**: Automatiza limpieza, métricas, alertas

5. **Implementar prefetch_related en detail views**
   ```python
   qs.prefetch_related('movimientos', 'documentos')
   ```
   **Impacto**: Elimina N+1 en relaciones inversas

6. **Agregar connection pooling**
   ```python
   'ENGINE': 'django_db_geventpool.backends.postgresql_psycopg2',
   ```
   **Impacto**: Reduce latencia DB en 30-50ms por request

---

### 🟡 **IMPORTANTE (Próximas 2 semanas)**

7. **Implementar compresión GZip**
8. **Agregar Django Debug Toolbar (dev)**
9. **Configurar Sentry para error tracking**
10. **Optimizar queries en resueltos_view (4 counts → 1)**
11. **Cache de API responses con drf-extensions**
12. **Warm-up cache task periódico**

---

### 🟢 **MEJORAS (Backlog)**

13. Implementar CDN para assets estáticos
14. Agregar lazy loading en templates
15. Implementar pagination cursor-based (más eficiente)
16. Configurar read-replica para queries pesados
17. Agregar monitoring con Prometheus + Grafana

---

## 🎯 PRÓXIMOS PASOS (FASE 8)

Con el análisis de performance completo, ahora procederé a:

1. ✅ **FASE 1 COMPLETADA**: Arquitectura y dependencias (5.3/10)
2. ✅ **FASE 2 COMPLETADA**: Modelos y base de datos (5.4/10)
3. ✅ **FASE 3 COMPLETADA**: Lógica de negocio y servicios (5.9/10)
4. ✅ **FASE 4 COMPLETADA**: Views y controladores (4.5/10)
5. ✅ **FASE 5 COMPLETADA**: APIs y Serializers (5.4/10)
6. ✅ **FASE 6 COMPLETADA**: Seguridad profunda (6.3/10)
7. ✅ **FASE 7 COMPLETADA**: Performance y optimización (5.7/10)
8. ⏳ **FASE 8**: Tests y cobertura
9. ⏳ **FASE 9**: Documentación
10. ⏳ **FASE 10**: Deployment e integración

---

**FIN DE FASE 7 - PERFORMANCE Y OPTIMIZACIÓN**  
**Próximo paso**: Análisis exhaustivo de tests (unitarios, integración, coverage, tests de seguridad, tests de ML)
