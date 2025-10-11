from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.utils import timezone
from django.db.models import Q
import tempfile
import os

from .models import Container
from .serializers import (
    ContainerSerializer, 
    ContainerListSerializer,
    ContainerStockExportSerializer
)
from .importers.embarque import EmbarqueImporter
from .importers.liberacion import LiberacionImporter
from .importers.programacion import ProgramacionImporter


class ContainerViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de contenedores
    """
    queryset = Container.objects.all()
    serializer_class = ContainerSerializer
    filterset_fields = ['estado', 'tipo', 'secuenciado', 'puerto', 'posicion_fisica']
    search_fields = ['container_id', 'nave', 'vendor', 'comuna']
    ordering_fields = ['created_at', 'fecha_programacion', 'fecha_liberacion']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ContainerListSerializer
        return ContainerSerializer
    
    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def import_embarque(self, request):
        """
        Importa contenedores desde Excel de embarque
        Crea contenedores con estado 'por_arribar'
        """
        if 'file' not in request.FILES:
            return Response(
                {'error': 'No se proporcionó archivo'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        archivo = request.FILES['file']
        usuario = request.user.username if request.user.is_authenticated else None
        
        # Guardar temporalmente
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
            for chunk in archivo.chunks():
                tmp.write(chunk)
            tmp_path = tmp.name
        
        try:
            # Procesar con el importador
            importer = EmbarqueImporter(tmp_path, usuario)
            resultados = importer.procesar()
            
            return Response({
                'success': True,
                'mensaje': f'Importación completada',
                'creados': resultados['creados'],
                'actualizados': resultados['actualizados'],
                'errores': resultados['errores'],
                'detalles': resultados['detalles']
            })
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        finally:
            # Limpiar archivo temporal
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def import_liberacion(self, request):
        """
        Importa liberaciones desde Excel
        Actualiza contenedores a estado 'liberado' y asigna posición física
        """
        if 'file' not in request.FILES:
            return Response(
                {'error': 'No se proporcionó archivo'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        archivo = request.FILES['file']
        usuario = request.user.username if request.user.is_authenticated else None
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
            for chunk in archivo.chunks():
                tmp.write(chunk)
            tmp_path = tmp.name
        
        try:
            importer = LiberacionImporter(tmp_path, usuario)
            resultados = importer.procesar()
            
            return Response({
                'success': True,
                'mensaje': f'Importación de liberación completada',
                'liberados': resultados['liberados'],
                'no_encontrados': resultados['no_encontrados'],
                'errores': resultados['errores'],
                'detalles': resultados['detalles']
            })
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def import_programacion(self, request):
        """
        Importa programaciones desde Excel
        Crea programaciones y actualiza contenedores a 'programado'
        """
        if 'file' not in request.FILES:
            return Response(
                {'error': 'No se proporcionó archivo'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        archivo = request.FILES['file']
        usuario = request.user.username if request.user.is_authenticated else None
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
            for chunk in archivo.chunks():
                tmp.write(chunk)
            tmp_path = tmp.name
        
        try:
            importer = ProgramacionImporter(tmp_path, usuario)
            resultados = importer.procesar()
            
            return Response({
                'success': True,
                'mensaje': f'Importación de programación completada',
                'programados': resultados['programados'],
                'no_encontrados': resultados['no_encontrados'],
                'cd_no_encontrado': resultados['cd_no_encontrado'],
                'errores': resultados['errores'],
                'alertas_generadas': resultados['alertas_generadas'],
                'detalles': resultados['detalles']
            })
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    @action(detail=False, methods=['get'])
    def export_stock(self, request):
        """
        Exporta stock de contenedores liberados y por arribar
        Incluye flag de 'secuenciado' para próximas liberaciones
        """
        # Filtrar solo liberados y por_arribar
        containers = Container.objects.filter(
            Q(estado='liberado') | Q(estado='por_arribar')
        ).order_by('secuenciado', '-fecha_liberacion')
        
        serializer = ContainerStockExportSerializer(containers, many=True)
        
        return Response({
            'success': True,
            'total': containers.count(),
            'containers': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def cambiar_estado(self, request, pk=None):
        """
        Cambia manualmente el estado de un contenedor
        """
        container = self.get_object()
        nuevo_estado = request.data.get('estado')
        
        if not nuevo_estado:
            return Response(
                {'error': 'Estado no proporcionado'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if nuevo_estado not in dict(Container.ESTADOS):
            return Response(
                {'error': f'Estado inválido: {nuevo_estado}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        usuario = request.user.username if request.user.is_authenticated else None
        container.cambiar_estado(nuevo_estado, usuario)
        
        serializer = self.get_serializer(container)
        return Response({
            'success': True,
            'mensaje': f'Estado cambiado a {container.get_estado_display()}',
            'container': serializer.data
        })
