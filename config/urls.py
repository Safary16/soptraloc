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

# Import frontend views
from apps.core.views import (
    home, asignacion, estados, importar, 
    containers_list, container_detail,
    operaciones, drivers_list, executive_dashboard
)

# Setup API router
router = DefaultRouter()
router.register(r'drivers', DriverViewSet, basename='driver')
router.register(r'containers', ContainerViewSet, basename='container')
router.register(r'programaciones', ProgramacionViewSet, basename='programacion')
router.register(r'cds', CDViewSet, basename='cd')

urlpatterns = [
    # Frontend pages
    path('', home, name='home'),
    path('asignacion/', asignacion, name='asignacion'),
    path('estados/', estados, name='estados'),
    path('importar/', importar, name='importar'),
    path('containers/', containers_list, name='containers_list'),
    path('container/<str:container_id>/', container_detail, name='container_detail'),
    path('operaciones/', operaciones, name='operaciones'),
    path('drivers/', drivers_list, name='drivers_list'),
    path('executive/', executive_dashboard, name='executive_dashboard'),
    
    # Admin
    path('admin/', admin.site.urls),
    
    # Driver authentication
    path('driver/login/', driver_login, name='driver_login'),
    path('driver/logout/', driver_logout, name='driver_logout'),
    path('driver/dashboard/', driver_dashboard, name='driver_dashboard'),
    
    # Monitoring
    path('monitoring/', monitoring, name='monitoring'),
    
    # API
    path('api/', include(router.urls)),
    
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
