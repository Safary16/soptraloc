from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta

from .models import Programacion
from .serializers import (
    ProgramacionSerializer,
    RutaManualSerializer,
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
    permission_classes = [IsAuthenticatedOrReadOnly]
    
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
    
    @action(detail=False, methods=['get'])
    def alertas_demurrage(self, request):
        """
        Lista contenedores con fecha_demurrage crítica (< 2 días para vencer)
        
        Lógica: Demurrage vence el día indicado, día siguiente ya se paga.
        Alertamos si quedan menos de 2 días para el vencimiento.
        """
        from apps.containers.models import Container
        from apps.containers.serializers import ContainerListSerializer
        
        # Fecha límite: hoy + 2 días
        fecha_limite = timezone.now() + timedelta(days=2)
        
        # Contenedores con fecha_demurrage próxima a vencer
        # Estados relevantes: liberado, programado, asignado (no entregados ni descargados)
        containers_riesgo = Container.objects.filter(
            fecha_demurrage__isnull=False,
            fecha_demurrage__lte=fecha_limite,
            estado__in=['liberado', 'programado', 'asignado']
        ).select_related('cd_entrega').order_by('fecha_demurrage')
        
        # Calcular días restantes para cada contenedor
        resultados = []
        for container in containers_riesgo:
            dias_restantes = (container.fecha_demurrage - timezone.now()).days
            container_data = ContainerListSerializer(container).data
            container_data['dias_hasta_demurrage'] = dias_restantes
            container_data['vencido'] = dias_restantes < 0
            resultados.append(container_data)
        
        return Response({
            'success': True,
            'total': len(resultados),
            'containers_en_riesgo': resultados,
            'mensaje': f'{len(resultados)} contenedores con demurrage próximo a vencer o vencido'
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
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """
        Dashboard con priorización inteligente
        Score = 50% días_hasta_programacion + 50% días_hasta_demurrage
        Ordena por urgencia (score más bajo = más urgente)
        """
        ahora = timezone.now()
        programaciones = self.queryset.select_related('container', 'driver', 'cd')
        
        resultados = []
        for prog in programaciones:
            # Calcular días hasta programación
            dias_hasta_prog = (prog.fecha_programada - ahora).total_seconds() / 86400
            
            # Calcular días hasta demurrage (si existe)
            dias_hasta_demurrage = None
            if prog.container.fecha_demurrage:
                dias_hasta_demurrage = (prog.container.fecha_demurrage - ahora).total_seconds() / 86400
            
            # Score de prioridad (más bajo = más urgente)
            if dias_hasta_demurrage is not None:
                score_prioridad = (dias_hasta_prog * 0.5) + (dias_hasta_demurrage * 0.5)
            else:
                score_prioridad = dias_hasta_prog  # Solo considerar programación si no hay demurrage
            
            # Determinar nivel de urgencia
            if score_prioridad < 1:
                urgencia = 'CRÍTICA'
            elif score_prioridad < 2:
                urgencia = 'ALTA'
            elif score_prioridad < 3:
                urgencia = 'MEDIA'
            else:
                urgencia = 'BAJA'
            
            resultados.append({
                'id': prog.id,
                'container_id': prog.container.container_id,
                'fecha_programada': prog.fecha_programada,
                'fecha_demurrage': prog.container.fecha_demurrage,
                'conductor': prog.driver.nombre if prog.driver else None,
                'cd': prog.cd.nombre,
                'dias_hasta_programacion': round(dias_hasta_prog, 1),
                'dias_hasta_demurrage': round(dias_hasta_demurrage, 1) if dias_hasta_demurrage else None,
                'score_prioridad': round(score_prioridad, 2),
                'urgencia': urgencia,
                'estado_container': prog.container.estado
            })
        
        # Ordenar por score (más urgente primero)
        resultados.sort(key=lambda x: x['score_prioridad'])
        
        return Response({
            'success': True,
            'total': len(resultados),
            'programaciones': resultados,
            'leyenda': {
                'CRÍTICA': 'Menos de 1 día',
                'ALTA': '1-2 días',
                'MEDIA': '2-3 días',
                'BAJA': 'Más de 3 días'
            }
        })
    
    @action(detail=False, methods=['post'])
    def crear_ruta_manual(self, request):
        """
        Crea una ruta manual para retiro desde puerto
        
        Casos de uso:
        1. retiro_ccti: CCTI va a buscar contenedor al puerto y lo lleva a CCTI
        2. retiro_directo: CCTI va a buscar al puerto y entrega directo a cliente
        
        Payload:
        {
            "container_id": "ABCD1234567",
            "tipo_movimiento": "retiro_ccti" | "retiro_directo",
            "cd_destino_id": 1,  // Solo para retiro_directo
            "fecha_programacion": "2025-10-15T10:00:00",
            "cliente": "Cliente XYZ",
            "observaciones": "..."
        }
        """
        serializer = RutaManualSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {'error': 'Datos inválidos', 'detalles': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        data = serializer.validated_data
        container = data['_container']
        tipo_movimiento = data['tipo_movimiento']
        
        # Actualizar tipo de movimiento en el contenedor
        container.tipo_movimiento = tipo_movimiento
        container.save(update_fields=['tipo_movimiento'])
        
        # Determinar CD destino
        if tipo_movimiento == 'retiro_ccti':
            # Buscar el primer CCTI
            from apps.cds.models import CD
            cd_destino = CD.objects.filter(tipo='CCTI').first()
            if not cd_destino:
                return Response(
                    {'error': 'No se encontró ningún CCTI en el sistema'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:  # retiro_directo
            cd_destino = data['_cd_destino']
        
        # Crear la programación
        programacion = Programacion.objects.create(
            container=container,
            cd=cd_destino,
            fecha_programada=data['fecha_programacion'],
            cliente=data.get('cliente', ''),
            direccion_entrega=cd_destino.direccion,
            observaciones=data.get('observaciones', f'Retiro manual desde {container.posicion_fisica}')
        )
        
        # Cambiar estado del contenedor a programado
        container.estado = 'programado'
        container.save(update_fields=['estado'])
        
        # Crear evento de auditoría
        from apps.events.models import Event
        Event.objects.create(
            container=container,
            tipo_evento='ruta_manual_creada',
            descripcion=f'Ruta manual creada: {tipo_movimiento}',
            usuario=request.user.username if request.user.is_authenticated else None,
            detalles={
                'tipo_movimiento': tipo_movimiento,
                'origen': container.posicion_fisica,
                'destino': cd_destino.nombre,
                'programacion_id': programacion.id,
                'fecha_programacion': data['fecha_programacion'].isoformat()
            }
        )
        
        return Response({
            'success': True,
            'mensaje': f'Ruta manual creada exitosamente',
            'programacion': ProgramacionSerializer(programacion).data,
            'tipo_movimiento': tipo_movimiento,
            'origen': container.posicion_fisica,
            'destino': cd_destino.nombre
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser, FormParser], url_path='import-excel', permission_classes=[AllowAny])
    def import_excel(self, request):
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
        
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
            for chunk in archivo.chunks():
                tmp.write(chunk)
            tmp_path = tmp.name
        
        try:
            from apps.containers.importers.programacion import ProgramacionImporter
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
                {'error': f'Error al importar: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    @action(detail=True, methods=['post'])
    def validar_asignacion(self, request, pk=None):
        """
        Valida si un conductor puede ser asignado considerando ventanas de tiempo
        
        Payload:
        {
            "driver_id": 1
        }
        """
        from apps.core.services.validation import PreAssignmentValidationService
        from apps.drivers.models import Driver
        
        programacion = self.get_object()
        driver_id = request.data.get('driver_id')
        
        if not driver_id:
            return Response(
                {'error': 'driver_id no proporcionado'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            driver = Driver.objects.get(id=driver_id)
        except Driver.DoesNotExist:
            return Response(
                {'error': f'Conductor con ID {driver_id} no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Validar disponibilidad temporal
        resultado = PreAssignmentValidationService.validar_disponibilidad_temporal(
            driver, programacion
        )
        
        return Response({
            'success': True,
            'disponible': resultado['disponible'],
            'conflictos': resultado['conflictos'],
            'tiempo_requerido': resultado['tiempo_requerido'],
            'ventana_ocupada': resultado['ventana_ocupada'],
            'nueva_ventana': resultado.get('nueva_ventana'),
            'conductor': driver.nombre
        })
    
    @action(detail=True, methods=['post'])
    def iniciar_ruta(self, request, pk=None):
        """
        Inicia la ruta de una programación y crea notificación con ETA
        
        Payload opcional:
        {
            "lat": -33.4372,
            "lng": -70.6506
        }
        """
        from apps.notifications.services import NotificationService
        
        programacion = self.get_object()
        
        if not programacion.driver:
            return Response(
                {'error': 'Programación no tiene conductor asignado'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Actualizar posición del conductor si se proporciona
        lat = request.data.get('lat')
        lng = request.data.get('lng')
        if lat and lng:
            programacion.driver.actualizar_posicion(lat, lng)
        
        # Cambiar estado del contenedor a 'en_ruta'
        programacion.container.cambiar_estado('en_ruta', request.user.username if request.user.is_authenticated else None)
        
        # Crear notificación con ETA
        notificacion = NotificationService.crear_notificacion_inicio_ruta(
            programacion, programacion.driver
        )
        
        serializer = self.get_serializer(programacion)
        return Response({
            'success': True,
            'mensaje': f'Ruta iniciada por conductor {programacion.driver.nombre}',
            'programacion': serializer.data,
            'notificacion': {
                'id': notificacion.id,
                'titulo': notificacion.titulo,
                'mensaje': notificacion.mensaje,
                'eta_minutos': notificacion.eta_minutos,
                'eta_timestamp': notificacion.eta_timestamp,
                'distancia_km': str(notificacion.distancia_km) if notificacion.distancia_km else None
            }
        })
    
    @action(detail=True, methods=['post'])
    def actualizar_posicion(self, request, pk=None):
        """
        Actualiza la posición del conductor y recalcula ETA
        
        Payload:
        {
            "lat": -33.4372,
            "lng": -70.6506
        }
        """
        from apps.notifications.services import NotificationService
        
        programacion = self.get_object()
        
        if not programacion.driver:
            return Response(
                {'error': 'Programación no tiene conductor asignado'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        lat = request.data.get('lat')
        lng = request.data.get('lng')
        
        if not lat or not lng:
            return Response(
                {'error': 'lat y lng requeridos'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Actualizar posición del conductor
        programacion.driver.actualizar_posicion(lat, lng)
        
        # Actualizar ETA y crear notificación si cambió significativamente
        resultado = NotificationService.actualizar_eta(
            programacion, programacion.driver, lat, lng
        )
        
        if not resultado:
            return Response(
                {'error': 'No se pudo calcular ETA actualizado'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Verificar si debe crear alerta de arribo próximo
        if resultado['eta_minutos'] <= 15:
            NotificationService.crear_alerta_arribo_proximo(programacion)
        
        response_data = {
            'success': True,
            'mensaje': 'Posición actualizada y ETA recalculado',
            'eta_minutos': resultado['eta_minutos'],
            'distancia_km': str(resultado['distancia_km']),
            'eta_timestamp': resultado['eta_timestamp']
        }
        
        if resultado['notificacion']:
            response_data['notificacion'] = {
                'id': resultado['notificacion'].id,
                'titulo': resultado['notificacion'].titulo,
                'mensaje': resultado['notificacion'].mensaje
            }
        
        return Response(response_data)
    
    @action(detail=True, methods=['get'])
    def eta(self, request, pk=None):
        """
        Calcula el ETA actual para una programación
        """
        from apps.core.services.mapbox import MapboxService
        
        programacion = self.get_object()
        
        if not programacion.driver:
            return Response(
                {'error': 'Programación no tiene conductor asignado'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        driver = programacion.driver
        cd = programacion.cd
        
        if not driver.ultima_posicion_lat or not driver.ultima_posicion_lng:
            return Response(
                {'error': 'Conductor no tiene posición GPS conocida'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Calcular ETA con Mapbox
        resultado = MapboxService.calcular_ruta(
            float(driver.ultima_posicion_lng),
            float(driver.ultima_posicion_lat),
            float(cd.lng),
            float(cd.lat)
        )
        
        if not resultado.get('success'):
            return Response(
                {'error': f'Error calculando ETA: {resultado.get("error")}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        eta_timestamp = timezone.now() + timedelta(minutes=resultado['duration_minutes'])
        
        return Response({
            'success': True,
            'eta_minutos': resultado['duration_minutes'],
            'distancia_km': resultado['distance_km'],
            'eta_timestamp': eta_timestamp,
            'conductor': driver.nombre,
            'destino': cd.nombre,
            'posicion_actual': {
                'lat': str(driver.ultima_posicion_lat),
                'lng': str(driver.ultima_posicion_lng)
            }
        })
