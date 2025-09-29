from django.urls import path
from . import views

app_name = 'drivers'

urlpatterns = [
    path('', views.drivers_view, name='drivers'),
    path('attendance/', views.attendance_view, name='attendance'),
    path('mark-present/', views.mark_present, name='mark_present'),
    path('mass-entry/', views.mass_entry, name='mass_entry'),
    path('auto-assign/', views.auto_assign_drivers, name='auto_assign'),
    path('auto-assign-single/', views.auto_assign_single, name='auto_assign_single'),
    path('update-location/<int:driver_id>/', views.update_driver_location, name='update_location'),
    path('assign/', views.assign_container, name='assign_container'),
    path('unassign/', views.unassign_driver, name='unassign_driver'),
    path('available/', views.get_available_drivers, name='available_drivers'),
    path('check-availability/', views.check_driver_availability, name='check_availability'),
    path('alerts/', views.alerts_view, name='alerts'),
    path('alerts/resolve/', views.resolve_alert, name='resolve_alert'),
]