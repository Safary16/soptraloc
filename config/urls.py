"""
URL Configuration for SoptraLoc TMS
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter

# Import viewsets
from apps.drivers.views import DriverViewSet, driver_login, driver_logout, driver_dashboard, monitoring
from apps.containers.views import ContainerViewSet
from apps.programaciones.views import ProgramacionViewSet

# Setup API router
router = DefaultRouter()
router.register(r'drivers', DriverViewSet, basename='driver')
router.register(r'containers', ContainerViewSet, basename='container')
router.register(r'programaciones', ProgramacionViewSet, basename='programacion')

urlpatterns = [
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
]

# Static and media files
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    if hasattr(settings, 'MEDIA_URL'):
        urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
