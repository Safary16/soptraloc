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
    
    def get_queryset(self):
        """
        Override to support driver__isnull filter for programaciones sin asignar
        """
        queryset = super().get_queryset()
        
        # Filtro especial para driver__isnull
        driver_isnull = self.request.query_params.get('driver__isnull', None)
        if driver_isnull is not None:
            if driver_isnull.lower() == 'true':
                queryset = queryset.filter(driver__isnull=True)
            elif driver_isnull.lower() == 'false':
                queryset = queryset.filter(driver__isnull=False)
        
        return queryset
    
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
        
        Requiere confirmación de patente del conductor para verificar que está usando el vehículo correcto.
        
        Payload requerido:
        {
            "patente": "ABC123",  // Patente del vehículo que está usando
            "lat": -33.4372,      // Ubicación GPS actual (opcional)
            "lng": -70.6506       // Ubicación GPS actual (opcional)
        }
        """
        from apps.notifications.services import NotificationService
        
        programacion = self.get_object()
        
        if not programacion.driver:
            return Response(
                {'error': 'Programación no tiene conductor asignado'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validar que se proporcione la patente
        patente_ingresada = request.data.get('patente', '').strip().upper()
        if not patente_ingresada:
            return Response(
                {'error': 'Debe ingresar la patente del vehículo para confirmar'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Si el conductor tiene una patente asignada, validar que coincida
        if programacion.driver.patente and programacion.driver.patente.strip():
            patente_asignada = programacion.driver.patente.strip().upper()
            if patente_ingresada != patente_asignada:
                return Response({
                    'error': f'La patente ingresada ({patente_ingresada}) no coincide con la asignada ({patente_asignada})',
                    'patente_esperada': patente_asignada,
                    'patente_ingresada': patente_ingresada,
                    'success': False
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            # Si no hay patente asignada, aceptar cualquiera pero registrarla
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f'Conductor {programacion.driver.nombre} no tiene patente asignada. Usando: {patente_ingresada}')
        
        # Obtener coordenadas GPS (requeridas para registrar posición de inicio)
        lat = request.data.get('lat')
        lng = request.data.get('lng')
        
        if not lat or not lng:
            return Response(
                {'error': 'Se requieren coordenadas GPS (lat, lng) para iniciar la ruta'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Actualizar posición del conductor
        programacion.driver.actualizar_posicion(lat, lng)
        
        # Guardar datos de inicio de ruta en la programación
        programacion.patente_confirmada = patente_ingresada
        programacion.fecha_inicio_ruta = timezone.now()
        programacion.gps_inicio_lat = lat
        programacion.gps_inicio_lng = lng
        programacion.save()
        
        # Cambiar estado del contenedor a 'en_ruta'
        usuario = request.user.username if request.user.is_authenticated else None
        programacion.container.cambiar_estado('en_ruta', usuario)
        
        # Crear evento de inicio de ruta con datos GPS
        from apps.events.models import Event
        Event.objects.create(
            container=programacion.container,
            event_type='inicio_ruta',
            detalles={
                'conductor': programacion.driver.nombre,
                'patente': patente_ingresada,
                'gps_lat': str(lat),
                'gps_lng': str(lng),
                'timestamp': timezone.now().isoformat()
            },
            usuario=usuario
        )
        
        # Crear notificación con ETA
        try:
            notificacion = NotificationService.crear_notificacion_inicio_ruta(
                programacion, programacion.driver
            )
            notificacion_data = {
                'id': notificacion.id,
                'titulo': notificacion.titulo,
                'mensaje': notificacion.mensaje,
                'eta_minutos': notificacion.eta_minutos,
                'eta_timestamp': notificacion.eta_timestamp,
                'distancia_km': str(notificacion.distancia_km) if notificacion.distancia_km else None
            }
        except Exception as e:
            # Si falla la notificación, continuar pero registrar el error
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Error creando notificación de inicio de ruta: {str(e)}")
            notificacion_data = None
        
        serializer = self.get_serializer(programacion)
        response_data = {
            'success': True,
            'mensaje': f'Ruta iniciada por conductor {programacion.driver.nombre} con patente {patente_ingresada}',
            'programacion': serializer.data,
            'patente_confirmada': patente_ingresada,
            'gps_registrado': {'lat': str(lat), 'lng': str(lng)}
        }
        
        if notificacion_data:
            response_data['notificacion'] = notificacion_data
        
        return Response(response_data)
    
    @action(detail=True, methods=['post'])
    def notificar_arribo(self, request, pk=None):
        """
        Notifica que el conductor ha arribado al CD (llegó al destino)
        Cambia el estado del contenedor a 'entregado'
        
        Payload opcional:
        {
            "lat": -33.4372,
            "lng": -70.6506
        }
        """
        programacion = self.get_object()
        
        if not programacion.driver:
            return Response(
                {'error': 'Programación no tiene conductor asignado'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if programacion.container.estado != 'en_ruta':
            return Response(
                {'error': f'Contenedor debe estar en ruta. Estado actual: {programacion.container.get_estado_display()}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Actualizar posición del conductor si se proporciona
        lat = request.data.get('lat')
        lng = request.data.get('lng')
        if lat and lng:
            programacion.driver.actualizar_posicion(lat, lng)
        
        # Cambiar estado del contenedor a 'entregado'
        usuario = request.user.username if request.user.is_authenticated else None
        programacion.container.cambiar_estado('entregado', usuario)
        
        # Registrar tiempo de viaje real para ML (si hay datos de inicio)
        if programacion.fecha_inicio_ruta and programacion.gps_inicio_lat and programacion.gps_inicio_lng:
            try:
                from apps.programaciones.models import TiempoViaje
                from apps.core.services.mapbox import MapboxService
                
                # Calcular tiempo real del viaje
                tiempo_real_min = int((timezone.now() - programacion.fecha_inicio_ruta).total_seconds() / 60)
                
                # Obtener tiempo que Mapbox estimó originalmente
                tiempo_mapbox_result = MapboxService.calcular_ruta(
                    float(programacion.gps_inicio_lng), float(programacion.gps_inicio_lat),
                    float(programacion.cd.lng), float(programacion.cd.lat)
                )
                tiempo_mapbox = tiempo_mapbox_result.get('duration_minutes', 60) if tiempo_mapbox_result else 60
                distancia_km = tiempo_mapbox_result.get('distance_km', 0) if tiempo_mapbox_result else 0
                
                # Detectar anomalías (tiempo real > 3x estimado = probable pausa/desvío)
                anomalia = tiempo_real_min > (tiempo_mapbox * 3)
                
                # Crear registro de TiempoViaje para ML
                TiempoViaje.objects.create(
                    conductor=programacion.driver,
                    programacion=programacion,
                    origen_lat=programacion.gps_inicio_lat,
                    origen_lon=programacion.gps_inicio_lng,
                    destino_lat=programacion.cd.lat,
                    destino_lon=programacion.cd.lng,
                    origen_nombre=programacion.container.posicion_fisica or 'Puerto',
                    destino_nombre=programacion.cd.nombre,
                    tiempo_mapbox_min=tiempo_mapbox,
                    tiempo_real_min=tiempo_real_min,
                    hora_salida=programacion.fecha_inicio_ruta,
                    hora_llegada=timezone.now(),
                    hora_del_dia=programacion.fecha_inicio_ruta.hour,
                    dia_semana=programacion.fecha_inicio_ruta.weekday(),
                    distancia_km=distancia_km,
                    anomalia=anomalia,
                    observaciones='Registrado automáticamente al marcar entregado'
                )
                
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f'ML: TiempoViaje registrado - Real: {tiempo_real_min}min, Mapbox: {tiempo_mapbox}min, Anomalía: {anomalia}')
            
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f'Error registrando TiempoViaje para ML: {str(e)}')
        
        # Crear evento de arribo
        from apps.events.models import Event
        Event.objects.create(
            container=programacion.container,
            event_type='arribo_cd',
            detalles={
                'conductor': programacion.driver.nombre,
                'cd': programacion.cd.nombre,
                'gps_lat': str(lat) if lat else None,
                'gps_lng': str(lng) if lng else None,
                'timestamp': timezone.now().isoformat()
            },
            usuario=usuario
        )
        
        serializer = self.get_serializer(programacion)
        return Response({
            'success': True,
            'mensaje': f'Arribo registrado en {programacion.cd.nombre}',
            'programacion': serializer.data,
            'nuevo_estado': 'entregado'
        })
    
    @action(detail=True, methods=['post'])
    def notificar_vacio(self, request, pk=None):
        """
        Notifica que el contenedor está vacío (descargado y listo para retiro)
        Cambia el estado del contenedor a 'vacio'
        
        Payload opcional:
        {
            "lat": -33.4372,
            "lng": -70.6506
        }
        """
        programacion = self.get_object()
        
        if not programacion.driver:
            return Response(
                {'error': 'Programación no tiene conductor asignado'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Permitir notificar vacío desde 'entregado' o 'descargado'
        if programacion.container.estado not in ['entregado', 'descargado']:
            return Response(
                {'error': f'Contenedor debe estar entregado o descargado. Estado actual: {programacion.container.get_estado_display()}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Actualizar posición del conductor si se proporciona
        lat = request.data.get('lat')
        lng = request.data.get('lng')
        if lat and lng:
            programacion.driver.actualizar_posicion(lat, lng)
        
        # Si está entregado, pasar primero por descargado y registrar tiempo de operación para ML
        if programacion.container.estado == 'entregado':
            usuario = request.user.username if request.user.is_authenticated else None
            programacion.container.cambiar_estado('descargado', usuario)
            
            # Registrar tiempo de operación real para ML
            if programacion.container.fecha_entrega:
                try:
                    from apps.programaciones.models import TiempoOperacion
                    
                    # Calcular tiempo real de descarga
                    tiempo_real_min = int((timezone.now() - programacion.container.fecha_entrega).total_seconds() / 60)
                    
                    # Tiempo estimado inicial (del CD o default)
                    tiempo_estimado = programacion.cd.tiempo_promedio_descarga_min or 60
                    
                    # Detectar anomalías (> 3x estimado)
                    anomalia = tiempo_real_min > (tiempo_estimado * 3)
                    
                    # Crear registro de TiempoOperacion para ML
                    TiempoOperacion.objects.create(
                        cd=programacion.cd,
                        conductor=programacion.driver,
                        container=programacion.container,
                        tipo_operacion='descarga_cd',
                        tiempo_estimado_min=tiempo_estimado,
                        tiempo_real_min=tiempo_real_min,
                        hora_inicio=programacion.container.fecha_entrega,
                        hora_fin=timezone.now(),
                        anomalia=anomalia,
                        observaciones='Registrado automáticamente al marcar vacío'
                    )
                    
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.info(f'ML: TiempoOperacion registrado - CD: {programacion.cd.nombre}, Real: {tiempo_real_min}min, Estimado: {tiempo_estimado}min, Anomalía: {anomalia}')
                
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f'Error registrando TiempoOperacion para ML: {str(e)}')
        
        # Cambiar estado del contenedor a 'vacio'
        usuario = request.user.username if request.user.is_authenticated else None
        programacion.container.cambiar_estado('vacio', usuario)
        
        # Crear evento de vacío
        from apps.events.models import Event
        Event.objects.create(
            container=programacion.container,
            event_type='contenedor_vacio',
            detalles={
                'conductor': programacion.driver.nombre,
                'cd': programacion.cd.nombre,
                'gps_lat': str(lat) if lat else None,
                'gps_lng': str(lng) if lng else None,
                'timestamp': timezone.now().isoformat()
            },
            usuario=usuario
        )
        
        serializer = self.get_serializer(programacion)
        return Response({
            'success': True,
            'mensaje': f'Contenedor marcado como vacío. Listo para retiro.',
            'programacion': serializer.data,
            'nuevo_estado': 'vacio'
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
    
    @action(detail=False, methods=['get'])
    def ml_stats(self, request):
        """
        Estadísticas de Machine Learning
        Muestra datos de aprendizaje del sistema
        """
        from apps.programaciones.models import TiempoOperacion, TiempoViaje
        from django.db.models import Avg, Count
        
        # Estadísticas de TiempoViaje
        viajes_stats = TiempoViaje.objects.filter(anomalia=False).aggregate(
            total_viajes=Count('id'),
            tiempo_mapbox_promedio=Avg('tiempo_mapbox_min'),
            tiempo_real_promedio=Avg('tiempo_real_min')
        )
        
        # Factor de corrección promedio
        if viajes_stats['tiempo_mapbox_promedio'] and viajes_stats['tiempo_real_promedio']:
            factor_correccion = viajes_stats['tiempo_real_promedio'] / viajes_stats['tiempo_mapbox_promedio']
        else:
            factor_correccion = 1.0
        
        # Estadísticas de TiempoOperacion
        operaciones_stats = TiempoOperacion.objects.filter(anomalia=False).aggregate(
            total_operaciones=Count('id'),
            tiempo_estimado_promedio=Avg('tiempo_estimado_min'),
            tiempo_real_promedio=Avg('tiempo_real_min')
        )
        
        # Precisión del sistema (% de no anomalías)
        total_viajes = TiempoViaje.objects.count()
        viajes_normales = TiempoViaje.objects.filter(anomalia=False).count()
        precision_viajes = (viajes_normales / total_viajes * 100) if total_viajes > 0 else 0
        
        total_operaciones = TiempoOperacion.objects.count()
        operaciones_normales = TiempoOperacion.objects.filter(anomalia=False).count()
        precision_operaciones = (operaciones_normales / total_operaciones * 100) if total_operaciones > 0 else 0
        
        return Response({
            'success': True,
            'ml_activo': True,
            'viajes': {
                'total_registros': viajes_stats['total_viajes'] or 0,
                'tiempo_mapbox_promedio': round(viajes_stats['tiempo_mapbox_promedio'] or 0, 1),
                'tiempo_real_promedio': round(viajes_stats['tiempo_real_promedio'] or 0, 1),
                'factor_correccion': round(factor_correccion, 2),
                'precision': round(precision_viajes, 1)
            },
            'operaciones': {
                'total_registros': operaciones_stats['total_operaciones'] or 0,
                'tiempo_estimado_promedio': round(operaciones_stats['tiempo_estimado_promedio'] or 0, 1),
                'tiempo_real_promedio': round(operaciones_stats['tiempo_real_promedio'] or 0, 1),
                'precision': round(precision_operaciones, 1)
            },
            'mensaje': f'Sistema ML con {viajes_stats["total_viajes"] or 0} viajes y {operaciones_stats["total_operaciones"] or 0} operaciones registradas'
        })
