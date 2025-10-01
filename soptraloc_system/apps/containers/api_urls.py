from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r'', views.ContainerViewSet, basename='container')
router.register(r'movements', views.ContainerMovementViewSet, basename='container-movement')
router.register(r'documents', views.ContainerDocumentViewSet, basename='container-document')
router.register(r'inspections', views.ContainerInspectionViewSet, basename='container-inspection')

urlpatterns = [
    path('', include(router.urls)),
    path('urgent/', views.urgent_containers_api, name='urgent-containers-api'),
]
