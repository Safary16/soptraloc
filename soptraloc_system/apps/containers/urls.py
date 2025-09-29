from django.urls import path

from . import views

app_name = 'containers'

urlpatterns = [
    path('<uuid:container_id>/', views.container_detail_uuid, name='container_detail_uuid'),
    path('<int:container_id>/', views.container_detail, name='container_detail'),
    path('update-position/', views.update_position, name='update_position'),
    path('update-status/', views.update_status, name='update_status'),
    path('assign-driver-quick/', views.assign_driver_quick, name='assign_driver_quick'),
    path('<uuid:container_id>/update-status/', views.update_container_status_view, name='update_container_status'),
    path('<uuid:container_id>/update-position/', views.update_container_position_view, name='update_container_position'),
]