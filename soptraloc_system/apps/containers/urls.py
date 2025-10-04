from django.urls import path

from . import views
from . import views_return

app_name = 'containers'

urlpatterns = [
    path('<uuid:container_id>/', views.container_detail_uuid, name='container_detail_uuid'),
    path('<int:container_id>/', views.container_detail, name='container_detail'),
    path('update-position/', views.update_position, name='update_position'),
    path('update-status/', views.update_status, name='update_status'),
    path('assign-driver-quick/', views.assign_driver_quick, name='assign_driver_quick'),
    path('<uuid:container_id>/update-status/', views.update_container_status_view, name='update_container_status'),
    path('<uuid:container_id>/update-position/', views.update_container_position_view, name='update_container_position'),
    path('urgent/', views.urgent_containers_api, name='urgent_containers_api'),
    
    # Rutas para flujo de devolución
    path('mark-ready-for-return/', views_return.mark_ready_for_return, name='mark_ready_for_return'),
    path('assign-return-driver/', views_return.assign_return_driver, name='assign_return_driver'),
    path('start-return-route/', views_return.start_return_route, name='start_return_route'),
    path('finalize-container/', views_return.finalize_container, name='finalize_container'),
]