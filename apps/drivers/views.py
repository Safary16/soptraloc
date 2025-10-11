from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import models

from .models import Driver
from .serializers import DriverSerializer, DriverListSerializer


class DriverViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de conductores
    """
    queryset = Driver.objects.all()
    serializer_class = DriverSerializer
    filterset_fields = ['presente', 'activo']
    search_fields = ['nombre', 'rut', 'telefono']
    ordering_fields = ['nombre', 'cumplimiento_porcentaje', 'num_entregas_dia']
    ordering = ['nombre']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return DriverListSerializer
        return DriverSerializer
    
    @action(detail=False, methods=['get'])
    def disponibles(self, request):
        """
        Lista solo conductores disponibles para asignación
        """
        drivers = self.queryset.filter(
            activo=True,
            presente=True
        ).exclude(
            num_entregas_dia__gte=models.F('max_entregas_dia')
        )
        
        serializer = DriverListSerializer(drivers, many=True)
        return Response({
            'success': True,
            'total': drivers.count(),
            'conductores': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def actualizar_posicion(self, request, pk=None):
        """
        Actualiza la última posición conocida del conductor
        """
        driver = self.get_object()
        lat = request.data.get('lat')
        lng = request.data.get('lng')
        
        if not lat or not lng:
            return Response(
                {'error': 'lat y lng son requeridos'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            driver.actualizar_posicion(float(lat), float(lng))
            serializer = self.get_serializer(driver)
            return Response({
                'success': True,
                'mensaje': 'Posición actualizada',
                'driver': serializer.data
            })
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def registrar_entrega(self, request, pk=None):
        """
        Registra una entrega completada
        """
        driver = self.get_object()
        a_tiempo = request.data.get('a_tiempo', True)
        
        driver.registrar_entrega(a_tiempo=a_tiempo)
        
        serializer = self.get_serializer(driver)
        return Response({
            'success': True,
            'mensaje': 'Entrega registrada',
            'driver': serializer.data
        })
    
    @action(detail=False, methods=['post'])
    def resetear_entregas_dia(self, request):
        """
        Resetea el contador de entregas del día para todos los conductores
        Útil para ejecutar diariamente
        """
        count = 0
        for driver in self.queryset.all():
            driver.resetear_entregas_dia()
            count += 1
        
        return Response({
            'success': True,
            'mensaje': f'Entregas reseteadas para {count} conductores'
        })
    
    @action(detail=True, methods=['post'])
    def marcar_presente(self, request, pk=None):
        """
        Marca un conductor como presente
        """
        driver = self.get_object()
        driver.presente = True
        driver.save(update_fields=['presente'])
        
        serializer = self.get_serializer(driver)
        return Response({
            'success': True,
            'mensaje': f'{driver.nombre} marcado como presente',
            'driver': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def marcar_ausente(self, request, pk=None):
        """
        Marca un conductor como ausente
        """
        driver = self.get_object()
        driver.presente = False
        driver.save(update_fields=['presente'])
        
        serializer = self.get_serializer(driver)
        return Response({
            'success': True,
            'mensaje': f'{driver.nombre} marcado como ausente',
            'driver': serializer.data
        })
