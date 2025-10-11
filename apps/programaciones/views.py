from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta

from .models import Programacion
from .serializers import (
    ProgramacionSerializer,
    ProgramacionListSerializer,
    ProgramacionCreateSerializer
)
from apps.core.services.assignment import AssignmentService
from apps.drivers.serializers import DriverDisponibleSerializer


class ProgramacionViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de programaciones
    """
    queryset = Programacion.objects.select_related('container', 'driver', 'cd').all()
    serializer_class = ProgramacionSerializer
    filterset_fields = ['fecha_programada', 'requiere_alerta', 'driver', 'cd']
    search_fields = ['container__container_id', 'cliente']
    ordering_fields = ['fecha_programada', 'created_at']
    ordering = ['fecha_programada']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ProgramacionListSerializer
        elif self.action == 'create':
            return ProgramacionCreateSerializer
        return ProgramacionSerializer
    
    @action(detail=False, methods=['get'])
    def alertas(self, request):
        """
        Lista programaciones que requieren alerta (< 48h sin conductor)
        """
        alertas = self.queryset.filter(
            requiere_alerta=True,
            driver__isnull=True
        )
        
        serializer = ProgramacionListSerializer(alertas, many=True)
        return Response({
            'success': True,
            'total': alertas.count(),
            'alertas': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def asignar_conductor(self, request, pk=None):
        """
        Asigna un conductor específico a una programación
        """
        programacion = self.get_object()
        driver_id = request.data.get('driver_id')
        
        if not driver_id:
            return Response(
                {'error': 'driver_id no proporcionado'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from apps.drivers.models import Driver
        try:
            driver = Driver.objects.get(id=driver_id)
        except Driver.DoesNotExist:
            return Response(
                {'error': f'Conductor con ID {driver_id} no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if not driver.esta_disponible:
            return Response(
                {'error': f'Conductor {driver.nombre} no está disponible'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        usuario = request.user.username if request.user.is_authenticated else None
        programacion.asignar_conductor(driver, usuario)
        
        serializer = self.get_serializer(programacion)
        return Response({
            'success': True,
            'mensaje': f'Conductor {driver.nombre} asignado',
            'programacion': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def asignar_automatico(self, request, pk=None):
        """
        Asigna automáticamente el mejor conductor disponible
        """
        programacion = self.get_object()
        usuario = request.user.username if request.user.is_authenticated else None
        
        resultado = AssignmentService.asignar_mejor_conductor(programacion, usuario)
        
        if resultado['success']:
            serializer = self.get_serializer(programacion)
            return Response({
                'success': True,
                'mensaje': f'Conductor {resultado["driver"].nombre} asignado automáticamente',
                'score': float(resultado['score']),
                'desglose': {k: float(v) for k, v in resultado['desglose'].items()},
                'programacion': serializer.data
            })
        else:
            return Response(
                {'error': resultado['error']},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'])
    def conductores_disponibles(self, request, pk=None):
        """
        Lista conductores disponibles con su score de asignación
        """
        programacion = self.get_object()
        
        conductores = AssignmentService.obtener_conductores_disponibles_con_score(programacion)
        
        # Serializar con scores
        resultados = []
        for item in conductores:
            driver_data = DriverDisponibleSerializer(item['driver']).data
            driver_data['score'] = float(item['score'])
            driver_data['desglose'] = {k: float(v) for k, v in item['desglose'].items()}
            resultados.append(driver_data)
        
        return Response({
            'success': True,
            'total': len(resultados),
            'conductores': resultados
        })
    
    @action(detail=False, methods=['post'])
    def asignar_multiples(self, request):
        """
        Asigna conductores automáticamente a múltiples programaciones
        """
        programacion_ids = request.data.get('programacion_ids', [])
        
        if not programacion_ids:
            return Response(
                {'error': 'programacion_ids no proporcionado'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        programaciones = self.queryset.filter(id__in=programacion_ids, driver__isnull=True)
        usuario = request.user.username if request.user.is_authenticated else None
        
        resultados = AssignmentService.asignar_multiples(programaciones, usuario)
        
        return Response({
            'success': True,
            'asignadas': resultados['asignadas'],
            'fallidas': resultados['fallidas'],
            'detalles': resultados['detalles']
        })
