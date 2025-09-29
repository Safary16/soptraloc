from django.urls import path
from . import views


urlpatterns = [
    path('schedules/unassigned/', views.UnassignedSchedulesView.as_view(), name='unassigned-schedules'),
    path('schedules/<uuid:schedule_id>/assign/', views.AssignScheduleView.as_view(), name='assign-schedule'),
]
