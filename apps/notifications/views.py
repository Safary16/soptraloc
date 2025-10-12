from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django.utils import timezone

from apps.notifications.models import Notification, NotificationPreference
from apps.notifications.serializers import (
    NotificationSerializer,
    NotificationListSerializer,
    NotificationPreferenceSerializer
)
from apps.notifications.services import NotificationService


class NotificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de notificaciones
    """
    queryset = Notification.objects.select_related('container', 'driver', 'programacion').all()
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filterset_fields = ['tipo', 'prioridad', 'estado', 'container', 'driver']
    search_fields = ['titulo', 'mensaje', 'container__container_id']
    ordering_fields = ['created_at', 'prioridad', 'eta_timestamp']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return NotificationListSerializer
        return NotificationSerializer
    
    @action(detail=False, methods=['get'])
    def activas(self, request):
        """
        Lista notificaciones activas (pendientes y enviadas)
        """
        notificaciones = NotificationService.obtener_notificaciones_activas(
            limit=int(request.query_params.get('limit', 20))
        )
        
        serializer = NotificationListSerializer(notificaciones, many=True)
        return Response({
            'success': True,
            'total': notificaciones.count(),
            'notificaciones': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def recientes(self, request):
        """
        Lista notificaciones recientes (últimos 30 minutos)
        """
        limite_tiempo = timezone.now() - timezone.timedelta(minutes=30)
        notificaciones = self.queryset.filter(
            created_at__gte=limite_tiempo,
            estado__in=['pendiente', 'enviada']
        ).order_by('-created_at')
        
        serializer = NotificationListSerializer(notificaciones, many=True)
        return Response({
            'success': True,
            'total': notificaciones.count(),
            'notificaciones': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def por_prioridad(self, request):
        """
        Agrupa notificaciones activas por prioridad
        """
        notificaciones_activas = self.queryset.filter(
            estado__in=['pendiente', 'enviada']
        )
        
        resultado = {
            'critica': [],
            'alta': [],
            'media': [],
            'baja': []
        }
        
        for notif in notificaciones_activas:
            serializer = NotificationListSerializer(notif)
            resultado[notif.prioridad].append(serializer.data)
        
        return Response({
            'success': True,
            'total': notificaciones_activas.count(),
            'por_prioridad': resultado,
            'resumen': {
                'critica': len(resultado['critica']),
                'alta': len(resultado['alta']),
                'media': len(resultado['media']),
                'baja': len(resultado['baja'])
            }
        })
    
    @action(detail=True, methods=['post'])
    def marcar_leida(self, request, pk=None):
        """
        Marca una notificación como leída
        """
        notificacion = self.get_object()
        notificacion.marcar_leida()
        
        serializer = self.get_serializer(notificacion)
        return Response({
            'success': True,
            'mensaje': 'Notificación marcada como leída',
            'notificacion': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def archivar(self, request, pk=None):
        """
        Archiva una notificación
        """
        notificacion = self.get_object()
        notificacion.archivar()
        
        serializer = self.get_serializer(notificacion)
        return Response({
            'success': True,
            'mensaje': 'Notificación archivada',
            'notificacion': serializer.data
        })
    
    @action(detail=False, methods=['post'])
    def marcar_todas_leidas(self, request):
        """
        Marca todas las notificaciones activas como leídas
        """
        actualizadas = self.queryset.filter(
            estado__in=['pendiente', 'enviada']
        ).update(
            estado='leida',
            leida_at=timezone.now()
        )
        
        return Response({
            'success': True,
            'mensaje': f'{actualizadas} notificaciones marcadas como leídas',
            'total': actualizadas
        })
    
    @action(detail=False, methods=['post'])
    def limpiar_antiguas(self, request):
        """
        Archiva notificaciones antiguas
        """
        dias = int(request.data.get('dias', 7))
        actualizadas = NotificationService.limpiar_notificaciones_antiguas(dias)
        
        return Response({
            'success': True,
            'mensaje': f'{actualizadas} notificaciones antiguas archivadas',
            'total': actualizadas
        })


class NotificationPreferenceViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de preferencias de notificación
    """
    queryset = NotificationPreference.objects.all()
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filterset_fields = ['usuario', 'canal', 'activo']
    ordering = ['usuario', 'canal']
    
    @action(detail=False, methods=['get'])
    def por_usuario(self, request):
        """
        Obtiene preferencias de un usuario específico
        """
        usuario = request.query_params.get('usuario')
        if not usuario:
            return Response(
                {'error': 'Parámetro usuario requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        preferencias = self.queryset.filter(usuario=usuario)
        serializer = self.get_serializer(preferencias, many=True)
        
        return Response({
            'success': True,
            'usuario': usuario,
            'preferencias': serializer.data
        })
