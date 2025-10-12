from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from .models import CD
from .serializers import CDSerializer, CDListSerializer


class CDViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de Centros de Distribución
    """
    queryset = CD.objects.all()
    serializer_class = CDSerializer
    filterset_fields = ['tipo', 'activo', 'comuna']
    search_fields = ['nombre', 'codigo', 'direccion', 'comuna']
    ordering_fields = ['nombre', 'tipo']
    ordering = ['nombre']
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return CDListSerializer
        return CDSerializer
    
    @action(detail=False, methods=['get'])
    def cctis(self, request):
        """
        Lista solo los CCTIs activos
        """
        cctis = self.queryset.filter(tipo='ccti', activo=True)
        serializer = self.get_serializer(cctis, many=True)
        return Response({
            'success': True,
            'total': cctis.count(),
            'cctis': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def clientes(self, request):
        """
        Lista solo los clientes activos
        """
        clientes = self.queryset.filter(tipo='cliente', activo=True)
        serializer = self.get_serializer(clientes, many=True)
        return Response({
            'success': True,
            'total': clientes.count(),
            'clientes': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def recibir_vacio(self, request, pk=None):
        """
        Registra la recepción de un contenedor vacío en CCTI
        """
        cd = self.get_object()
        
        if cd.tipo != 'ccti':
            return Response(
                {'error': 'Solo los CCTIs pueden recibir vacíos'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if cd.recibir_vacio():
            serializer = self.get_serializer(cd)
            return Response({
                'success': True,
                'mensaje': f'Vacío recibido en {cd.nombre}',
                'cd': serializer.data
            })
        else:
            return Response(
                {'error': 'CCTI sin capacidad disponible'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def retirar_vacio(self, request, pk=None):
        """
        Registra el retiro de un contenedor vacío de CCTI
        """
        cd = self.get_object()
        
        if cd.tipo != 'ccti':
            return Response(
                {'error': 'Solo los CCTIs gestionan vacíos'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if cd.retirar_vacio():
            serializer = self.get_serializer(cd)
            return Response({
                'success': True,
                'mensaje': f'Vacío retirado de {cd.nombre}',
                'cd': serializer.data
            })
        else:
            return Response(
                {'error': 'No hay vacíos disponibles'},
                status=status.HTTP_400_BAD_REQUEST
            )
