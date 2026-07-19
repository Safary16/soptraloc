"""
URL Configuration for SoptraLoc TMS
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from rest_framework.routers import DefaultRouter
import os

# Import viewsets
from apps.drivers.views import DriverViewSet, driver_login, driver_logout, driver_dashboard, monitoring
from apps.containers.views import ContainerViewSet
from apps.programaciones.views import ProgramacionViewSet
from apps.cds.views import CDViewSet
from apps.clientes.views import (
    cliente_login, cliente_logout, cliente_dashboard, solicitudes_operaciones,
    api_stock, api_centros, api_recomendaciones, api_solicitudes, api_situaciones,
    api_solicitudes_operaciones, api_revisar_solicitud,
    api_situaciones_operaciones, api_revisar_situacion,
)
from apps.core.access_views import role_landing, staff_login, staff_logout, control_hub

# Import frontend views
from apps.core.views import (
    home, asignacion, estados, importar, 
    containers_list, container_detail,
    operaciones, drivers_list, cds_list, executive_dashboard,
    operaciones_diarias as operaciones_diarias_view
)

# Import API views
from apps.core.api_views import (
    dashboard_stats, dashboard_alertas, analytics_conductores,
    analytics_eficiencia, analytics_tendencias, ml_learning_stats,
    operaciones_diarias
)

# Setup API router
router = DefaultRouter()
router.register(r'drivers', DriverViewSet, basename='driver')
router.register(r'containers', ContainerViewSet, basename='container')
router.register(r'programaciones', ProgramacionViewSet, basename='programacion')
router.register(r'cds', CDViewSet, basename='cd')

urlpatterns = [
    # Frontend pages
    path('', role_landing, name='role_landing'),
    path('operaciones/dashboard/', home, name='operations_dashboard'),
    path('cuenta/login/', staff_login, name='staff_login'),
    path('cuenta/logout/', staff_logout, name='staff_logout'),
    path('control/', control_hub, name='control_hub'),
    path('asignacion/', asignacion, name='asignacion'),
    path('estados/', estados, name='estados'),
    path('importar/', importar, name='importar'),
    path('containers/', containers_list, name='containers_list'),
    path('container/<str:container_id>/', container_detail, name='container_detail'),
    path('operaciones/', operaciones, name='operaciones'),
    path('drivers/', drivers_list, name='drivers_list'),
    path('cds/', cds_list, name='cds_list'),
    path('executive/', executive_dashboard, name='executive_dashboard'),
    path('operaciones-diarias/', operaciones_diarias_view, name='operaciones_diarias_view'),
    
    # Admin
    path('admin/', admin.site.urls),
    
    # Client portal
    path('cliente/login/', cliente_login, name='cliente_login'),
    path('cliente/logout/', cliente_logout, name='cliente_logout'),
    path('cliente/', cliente_dashboard, name='cliente_dashboard'),
    path('operaciones/solicitudes-clientes/', solicitudes_operaciones, name='solicitudes_operaciones'),
    path('api/cliente/stock/', api_stock, name='cliente_stock'),
    path('api/cliente/centros/', api_centros, name='cliente_centros'),
    path('api/cliente/recomendaciones/', api_recomendaciones, name='cliente_recomendaciones'),
    path('api/cliente/solicitudes/', api_solicitudes, name='cliente_solicitudes'),
    path('api/cliente/situaciones/', api_situaciones, name='cliente_situaciones'),
    path('api/operaciones/solicitudes-clientes/', api_solicitudes_operaciones, name='operaciones_solicitudes_clientes'),
    path('api/operaciones/solicitudes-clientes/<int:pk>/revisar/', api_revisar_solicitud, name='revisar_solicitud_cliente'),
    path('api/operaciones/situaciones-clientes/', api_situaciones_operaciones, name='operaciones_situaciones_clientes'),
    path('api/operaciones/situaciones-clientes/<int:pk>/revisar/', api_revisar_situacion, name='revisar_situacion_cliente'),

    # Driver authentication
    path('driver/login/', driver_login, name='driver_login'),
    path('driver/logout/', driver_logout, name='driver_logout'),
    path('driver/dashboard/', driver_dashboard, name='driver_dashboard'),
    
    # Monitoring
    path('monitoring/', monitoring, name='monitoring'),
    
    # API
    path('api/', include(router.urls)),
    
    # API Analytics and Stats
    path('api/dashboard/stats/', dashboard_stats, name='dashboard_stats'),
    path('api/dashboard/alertas/', dashboard_alertas, name='dashboard_alertas'),
    path('api/analytics/conductores/', analytics_conductores, name='analytics_conductores'),
    path('api/analytics/eficiencia/', analytics_eficiencia, name='analytics_eficiencia'),
    path('api/analytics/tendencias/', analytics_tendencias, name='analytics_tendencias'),
    path('api/ml/learning-stats/', ml_learning_stats, name='ml_learning_stats'),
    path('api/operaciones/diarias/', operaciones_diarias, name='operaciones_diarias'),
    
    # API Authentication
    path('api-auth/', include('rest_framework.urls')),
    
    # Digital Asset Links for Android TWA
    re_path(r'^\.well-known/(?P<path>.*)$', serve, {
        'document_root': os.path.join(settings.BASE_DIR, 'static', '.well-known'),
    }),
]

# Static and media files
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    if hasattr(settings, 'MEDIA_URL'):
        urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
