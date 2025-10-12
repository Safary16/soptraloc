"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.containers.views import ContainerViewSet
from apps.drivers.views import DriverViewSet
from apps.programaciones.views import ProgramacionViewSet
from apps.cds.views import CDViewSet
from apps.notifications.views import NotificationViewSet, NotificationPreferenceViewSet

# Router para la API REST
router = DefaultRouter()
router.register(r'containers', ContainerViewSet, basename='container')
router.register(r'drivers', DriverViewSet, basename='driver')
router.register(r'programaciones', ProgramacionViewSet, basename='programacion')
router.register(r'cds', CDViewSet, basename='cd')
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'notification-preferences', NotificationPreferenceViewSet, basename='notification-preference')

from apps.core.views import (
    home, asignacion, importar, estados, container_detail, 
    containers_list, drivers_list, operaciones, driver_dashboard,
    executive_dashboard
)
from apps.core.api_views import (
    dashboard_stats, dashboard_alertas, analytics_conductores,
    analytics_eficiencia, analytics_tendencias
)

urlpatterns = [
    # Frontend pages
    path("", home, name="home"),
    path("asignacion/", asignacion, name="asignacion"),
    path("operaciones/", operaciones, name="operaciones"),
    path("importar/", importar, name="importar"),
    path("estados/", estados, name="estados"),
    path("containers/", containers_list, name="containers_list"),
    path("container/<str:container_id>/", container_detail, name="container_detail"),
    path("drivers/", drivers_list, name="drivers_list"),
    path("driver/dashboard/", driver_dashboard, name="driver_dashboard"),
    path("executive/", executive_dashboard, name="executive_dashboard"),
    
    # Admin and API
    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),
    
    # Dashboard & Analytics API
    path("api/dashboard/stats/", dashboard_stats, name="dashboard_stats"),
    path("api/dashboard/alertas/", dashboard_alertas, name="dashboard_alertas"),
    path("api/analytics/conductores/", analytics_conductores, name="analytics_conductores"),
    path("api/analytics/eficiencia/", analytics_eficiencia, name="analytics_eficiencia"),
    path("api/analytics/tendencias/", analytics_tendencias, name="analytics_tendencias"),
]
