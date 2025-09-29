from rest_framework.response import Response
from rest_framework.views import APIView


class UnassignedSchedulesView(APIView):
    """Vista para programaciones no asignadas."""
    def get(self, request):
        return Response({
            'message': 'Unassigned schedules endpoint - to be implemented',
            'status': 'placeholder'
        })


class AssignScheduleView(APIView):
    """Vista para asignar programaciones."""
    def post(self, request, schedule_id):
        return Response({
            'message': f'Assign schedule {schedule_id} endpoint - to be implemented',
            'status': 'placeholder'
        })