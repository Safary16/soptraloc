from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .api_views import RouteTrackingViewSet

router = DefaultRouter()
router.register(r'time-prediction', views.TimePredictionViewSet, basename='time-prediction')
router.register(r'routes', views.RouteViewSet, basename='route')
router.register(r'route-stops', views.RouteStopViewSet, basename='route-stop')
router.register(r'route-tracking', RouteTrackingViewSet, basename='route-tracking')

app_name = 'routing'

urlpatterns = [
    path('', include(router.urls)),
]
