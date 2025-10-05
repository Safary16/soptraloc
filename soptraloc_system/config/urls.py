"""
URL configuration for soptraloc_system project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from apps.core.home_views import HomeView, health_check, api_info
from apps.core.health_views import health_check_detailed, health_check_simple
from apps.core.auth_views import get_token, auth_info, home_view, dashboard_view, resueltos_view
from apps.containers.views_import import setup_initial_view, check_system_status

# Personalización del sitio admin
admin.site.site_header = "SoptraLoc - Administración"
admin.site.site_title = "SoptraLoc Admin"
admin.site.index_title = "Panel de Administración del Sistema"

schema_view = get_schema_view(
    openapi.Info(
        title="SOPTRALOC API",
        default_version='v1',
        description="Sistema de optimización para transporte de contenedores",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@soptraloc.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Setup inicial (sin autenticación)
    path('setup/', setup_initial_view, name='setup-initial'),
    path('setup/initial/', setup_initial_view, name='setup-initial-alt'),
    path('api/system-status/', check_system_status, name='system-status'),
    
    # Health checks (para Render y monitoring)
    path('health/', health_check_simple, name='health-check-simple'),
    path('api/health/', health_check_detailed, name='health-check-detailed'),
    path('api/info/', api_info, name='api-info'),
    
    # Página principal y dashboard
    path('', home_view, name='home'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('resueltos/', resueltos_view, name='resueltos'),
    path('drivers/', include('apps.drivers.urls')),
    path('containers/', include('apps.containers.urls')),
    
    # Autenticación
    path('accounts/', include('django.contrib.auth.urls')),
    
    # Admin
    path('admin/', admin.site.urls),
    
    # Auth endpoints
    path('api/v1/auth/token/', get_token, name='get-token'),
    path('api/v1/auth/info/', auth_info, name='auth-info'),
    
    # APIs
    path('api/v1/core/', include('apps.core.urls')),
    path('api/v1/containers/', include('apps.containers.api_urls')),
    path('api/v1/warehouses/', include('apps.warehouses.urls')),
    path('api/v1/routing/', include('apps.routing.urls')),  # Tiempos y ML
    # Apps scheduling, alerts, optimization eliminadas - funcionalidad en apps.drivers
    
    # API Documentation
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)