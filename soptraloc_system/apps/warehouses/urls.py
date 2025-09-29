from django.urls import path
from . import views


urlpatterns = [
    path('stats/', views.WarehouseStatsView.as_view(), name='warehouse-stats'),
    path('<uuid:warehouse_id>/inventory/', views.WarehouseInventoryView.as_view(), name='warehouse-inventory'),
]
