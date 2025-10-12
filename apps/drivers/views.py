from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
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
    
    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def import_conductores(self, request):
        """
        Importa conductores desde archivo Excel
        
        El archivo debe tener:
        - Header en fila 1
        - Columnas: N°, Conductor, PPU, RUT, Teléfono, ASISTENCIA, etc.
        
        Upload: multipart/form-data con campo 'file'
        """
        if 'file' not in request.FILES:
            return Response(
                {'error': 'No se proporcionó archivo. Use campo "file" en form-data'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        archivo = request.FILES['file']
        usuario = request.user.username if request.user.is_authenticated else None
        
        # Guardar temporalmente
        import tempfile
        import os
        
        try:
            # Crear archivo temporal
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
                for chunk in archivo.chunks():
                    tmp.write(chunk)
                temp_path = tmp.name
            
            # Importar
            from apps.drivers.importers import ConductorImporter
            importer = ConductorImporter(temp_path, usuario)
            resultados = importer.procesar()
            
            # Limpiar archivo temporal
            os.unlink(temp_path)
            
            return Response({
                'success': True,
                'mensaje': f'Importación completada',
                'creados': resultados['creados'],
                'actualizados': resultados['actualizados'],
                'errores': resultados['errores'],
                'detalles': resultados['detalles']
            })
        
        except Exception as e:
            # Limpiar archivo temporal si existe
            if 'temp_path' in locals():
                try:
                    os.unlink(temp_path)
                except:
                    pass
            
            return Response(
                {'error': f'Error al importar: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser, FormParser], url_path='import-excel')
    def import_excel(self, request):
        """
        Alias for import_conductores to match the frontend URL pattern
        """
        return self.import_conductores(request)
