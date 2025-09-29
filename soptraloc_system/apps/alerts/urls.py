from django.urls import path
from . import views


urlpatterns = [
    path('active/', views.ActiveAlertsView.as_view(), name='active-alerts'),
    path('history/', views.AlertHistoryView.as_view(), name='alert-history'),
]
