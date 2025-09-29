from django.urls import path
from . import views


urlpatterns = [
    path('optimize/', views.OptimizeRouteView.as_view(), name='optimize-route'),
    path('history/', views.OptimizationHistoryView.as_view(), name='optimization-history'),
]
