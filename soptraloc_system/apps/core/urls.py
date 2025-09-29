from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'companies', views.CompanyViewSet)
router.register(r'drivers', views.DriverViewSet)
router.register(r'vehicles', views.VehicleViewSet)
router.register(r'locations', views.LocationViewSet)
router.register(r'movement-codes', views.MovementCodeViewSet)

urlpatterns = [
    path('', include(router.urls)),
]