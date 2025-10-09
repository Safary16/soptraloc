from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Company, Vehicle, MovementCode
from .serializers import CompanySerializer, VehicleSerializer, MovementCodeSerializer


class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.filter(is_active=True)
    serializer_class = CompanySerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['code', 'is_active']
    search_fields = ['name', 'code', 'rut', 'email']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)


class VehicleViewSet(viewsets.ModelViewSet):
    queryset = Vehicle.objects.filter(is_active=True)
    serializer_class = VehicleSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['vehicle_type', 'status', 'brand', 'is_active']
    search_fields = ['plate', 'brand', 'model']
    ordering_fields = ['plate', 'created_at']
    ordering = ['plate']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    @action(detail=False, methods=['get'])
    def available(self, request):
        """Obtiene solo los vehículos disponibles."""
        available_vehicles = self.queryset.filter(status='available')
        serializer = self.get_serializer(available_vehicles, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['patch'])
    def change_status(self, request, pk=None):
        """Cambia el estado de un vehículo."""
        vehicle = self.get_object()
        new_status = request.data.get('status')
        
        if new_status not in dict(Vehicle.VEHICLE_STATUS):
            return Response(
                {'error': 'Estado no válido'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        vehicle.status = new_status
        vehicle.updated_by = request.user
        vehicle.save()
        
        serializer = self.get_serializer(vehicle)
        return Response(serializer.data)


class MovementCodeViewSet(viewsets.ModelViewSet):
    queryset = MovementCode.objects.all()
    serializer_class = MovementCodeSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['movement_type', 'is_active']
    search_fields = ['code', 'movement_type']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    @action(detail=False, methods=['post'])
    def generate(self, request):
        """Genera un nuevo código de movimiento."""
        movement_type = request.data.get('movement_type')
        
        if movement_type not in ['load', 'unload', 'transfer']:
            return Response(
                {'error': 'Tipo de movimiento no válido. Use: load, unload, transfer'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        movement_code = MovementCode.generate_code(movement_type)
        movement_code.created_by = request.user
        movement_code.save()
        
        serializer = self.get_serializer(movement_code)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['patch'])
    def use_code(self, request, pk=None):
        """Marca un código como usado."""
        movement_code = self.get_object()
        
        if movement_code.used_at:
            return Response(
                {'error': 'Este código ya ha sido usado'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        movement_code.use_code()
        movement_code.updated_by = request.user
        movement_code.save()
        
        serializer = self.get_serializer(movement_code)
        return Response(serializer.data)