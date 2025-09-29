from rest_framework.response import Response
from rest_framework.views import APIView


class WarehouseStatsView(APIView):
    """Vista para estadísticas de almacenes."""
    def get(self, request):
        return Response({
            'message': 'Warehouse statistics endpoint - to be implemented',
            'status': 'placeholder'
        })


class WarehouseInventoryView(APIView):
    """Vista para inventario de almacén."""
    def get(self, request, warehouse_id):
        return Response({
            'message': f'Inventory for warehouse {warehouse_id} endpoint - to be implemented',
            'status': 'placeholder'
        })
