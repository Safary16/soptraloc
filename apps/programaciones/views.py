from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly
from django.conf import settings
from django.db import transaction, IntegrityError
from django.utils import timezone
from datetime import timedelta
from dateutil import parser as date_parser
import logging
import uuid

from .filters import ProgramacionFilter
from .models import Programacion
from .serializers import (
    ProgramacionSerializer,
    RutaManualSerializer,
    ProgramacionListSerializer,
    ProgramacionCreateSerializer
)
from apps.core.services.assignment import AssignmentService
from apps.core.utils import normalizar_cliente
from apps.drivers.serializers import DriverDisponibleSerializer


logger = logging.getLogger(__name__)


class ProgramacionViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de programaciones
    """
    queryset = Programacion.objects.select_related('container', 'driver', 'cd').all()
    serializer_class = ProgramacionSerializer
    # N3/N9 (auditoría 2026-09-22): filterset con lookups que el panel de
    # asignación ya enviaba (driver__isnull, fecha_asignacion__gte) y cliente
    # normalizado + iexact. Ver apps/programaciones/filters.py
    filterset_class = ProgramacionFilter
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

    def perform_destroy(self, instance):
        """Elimina una programación evitando IntegrityError por la relación
        OneToOne entre Container y Programacion y por filas hijas que
        referencian al contenedor asociado.

        Comportamiento:
        1. Deslinkea el contenedor (libera container.estado, limpia fechas y
           el OneToOne inverso para evitar UNIQUE collisions si el operador
           re-crea inmediatamente la programacion).
        2. Borra la programacion (cascade a RegistroOperacion, SET_NULL en
           TiempoViaje/TiempoOperacion, CASCADE en Eventos).

        Sin esto, el DELETE del frontend (operaciones.html → eliminarPreAsignacion)
        podia fallar con IntegrityError en escenarios de re-asignacion inmediata.
        """
        with transaction.atomic():
            container = getattr(instance, 'container', None)
            if container is not None:
                # Limpiar estado y timestamps del contenedor para que no quede
                # colgado en 'programado'/'asignado' tras la baja. Usamos
                # cambiar_estado que respeta el FSM; si el estado no permite
                # transicion directa, forzar via atributo y save (caso admin).
                try:
                    estado_actual = getattr(container, 'estado', None)
                    if estado_actual in ('programado', 'asignado', 'secuenciado', 'incidente'):
                        # Cancelado es el destino valido desde varios estados FSM.
                        container.cambiar_estado('cancelado')
                    elif estado_actual in ('en_ccti', 'por_arribar', 'liberado'):
                        # No requiere cambio de estado; solo limpia timestamps stale.
                        pass
                    # Reset timestamps operativos sobre el contenedor.
                    update_fields = []
                    for f in (
                        'fecha_programacion', 'fecha_secuenciado', 'fecha_asignacion',
                        'fecha_incidente', 'fecha_inicio_ruta',
                    ):
                        if getattr(container, f, None) is not None:
                            setattr(container, f, None)
                            update_fields.append(f)
                    if update_fields:
                        container.save(update_fields=update_fields)
                except Exception:
                    logger.exception(
                        'No se pudo limpiar el contenedor asociado a la programacion %s; '
                        'se procede al DELETE igualmente.', instance.pk,
                    )
            instance.delete()

    @action(detail=False, methods=['get'], url_path='por-container/(?P<container_id>[^/.]+)')
    def por_container(self, request, container_id=None):
        from apps.containers.models import Container
        try:
            normalized = Container.normalize_container_id(container_id)
            container = Container.objects.get(container_id=normalized)
            programacion = Programacion.objects.select_related('container', 'driver', 'cd').get(container=container)
        except Container.DoesNotExist:
            return Response({'found': False, 'error': 'Contenedor no encontrado'}, status=status.HTTP_404_NOT_FOUND)
        except Programacion.DoesNotExist:
            return Response({'found': False, 'error': 'Contenedor no tiene programacion'}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(programacion)
        return Response({'found': True, 'programacion': serializer.data})

    @action(detail=False, methods=['get'], url_path='por-dia')
    def por_dia(self, request):
        """
        Programaciones del día (default hoy) con su conductor, CD, cliente y
        estado, listas para la vista operacional. Acepta ?fecha=YYYY-MM-DD.
        """
        from datetime import datetime
        fecha_str = request.query_params.get('fecha')
        if fecha_str:
            try:
                dia = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            except ValueError:
                return Response({'success': False, 'error': 'Formato de fecha inválido, use YYYY-MM-DD'}, status=400)
        else:
            dia = timezone.localdate()

        qs = self.queryset.filter(
            fecha_programada__date=dia
        )
        cliente_filtro = normalizar_cliente(request.query_params.get('cliente'))
        if cliente_filtro:
            qs = qs.filter(cliente__iexact=cliente_filtro)
        qs = qs.order_by('fecha_programada')

        serializer = ProgramacionListSerializer(qs, many=True)
        return Response({
            'success': True,
            'fecha': dia.isoformat(),
            'total': qs.count(),
            'programaciones': serializer.data
        })

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
        
        ACTUALIZADO: Muestra contenedores en todos los estados activos (no solo liberados)
        para dar visibilidad completa del riesgo de demurrage.
        """
        from apps.containers.models import Container
        from apps.containers.serializers import ContainerListSerializer
        
        # Fecha límite: hoy + 2 días
        fecha_limite = timezone.now() + timedelta(days=2)
        
        # Contenedores con fecha_demurrage próxima a vencer
        # Estados activos: liberado, programado, asignado, en_ruta, entregado
        # Excluir soltado/descargado/vacío: el viaje lleno ya terminó.
        containers_riesgo = Container.objects.filter(
            fecha_demurrage__isnull=False,
            fecha_demurrage__lte=fecha_limite,
            estado__in=['liberado', 'programado', 'asignado', 'en_ruta', 'entregado']
        ).select_related('cd_entrega').order_by('fecha_demurrage')
        
        # Calcular días restantes para cada contenedor
        resultados = []
        for container in containers_riesgo:
            dias_restantes = (container.fecha_demurrage - timezone.now()).days
            container_data = ContainerListSerializer(container).data
            container_data['dias_hasta_demurrage'] = dias_restantes
            container_data['vencido'] = dias_restantes < 0
            container_data['estado'] = container.estado
            container_data['tiene_programacion'] = container.tiene_programacion()
            resultados.append(container_data)
        
        return Response({
            'success': True,
            'total': len(resultados),
            'containers_en_riesgo': resultados,
            'mensaje': f'{len(resultados)} contenedores con demurrage próximo a vencer o vencido'
        })
    
    @action(detail=True, methods=['post'], permission_classes=[AllowAny])
    def asignar_conductor(self, request, pk=None):
        """
        Asigna un conductor específico a una programación
        Permite acceso anónimo para operaciones manuales desde el panel.
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
        
        usuario = request.user.username if request.user.is_authenticated else 'operador_manual'
        from django.core.exceptions import ValidationError as DjangoValidationError
        try:
            programacion.asignar_conductor(driver, usuario)
        except DjangoValidationError as exc:
            return Response(
                {'error': '; '.join(exc.messages) if hasattr(exc, 'messages') else str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        serializer = self.get_serializer(programacion)
        return Response({
            'success': True,
            'mensaje': f'Conductor {driver.nombre} asignado',
            'programacion': serializer.data
        })
    
    @action(detail=True, methods=['post'], permission_classes=[AllowAny])
    def desasignar(self, request, pk=None):
        """
        Desasigna el conductor de una programación,
        regresando el contenedor asociado de 'asignado' a 'programado'.
        """
        programacion = self.get_object()
        
        if not programacion.driver:
            return Response(
                {'error': 'Esta programación no tiene conductor asignado.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        container = programacion.container
        if container and container.estado not in ['asignado', 'programado']:
            return Response(
                {'error': f'El contenedor está en estado {container.get_estado_display()}, no se puede desasignar.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Liberar capacidad del conductor ANTES de limpiar la asignación:
        # liberar_conductor() decrementa num_entregas_dia (idempotente vía fecha_liberacion_conductor).
        programacion.liberar_conductor()
        programacion.driver = None
        programacion.fecha_asignacion = None
        programacion.save(update_fields=['driver', 'fecha_asignacion'])

        # Regresar el contenedor a 'programado' vía el FSM atómico. Esto:
        # 1) Bloquea la fila con select_for_update (evita race con asignaciones
        #    concurrentes que podrian re-asignar entre nuestro read y write).
        # 2) Emite Event('cambio_estado') en apps.events, requerido por auditoría.
        # 3) Actualiza fecha_programacion (timestamp del nuevo estado) a now.
        # Adicionalmente limpiamos container.fecha_asignacion explícitamente
        # porque cambiar_estado conserva el timestamp del estado_anterior
        # como referencia histórica; en este caso la asignación ya no existe
        # en la programación, así que el timestamp del contenedor debe ir a None.
        if container:
            try:
                container.cambiar_estado(
                    'programado',
                    request.user.username if request.user.is_authenticated else 'operador_manual',
                )
            except Exception as _fsm_exc:
                # Fallback defensivo: si por algún motivo el FSM rechaza la
                # transición directa (estado no contemplado), replicar el flujo
                # manual antiguo + emitir Event para no perder auditoría.
                logger.warning(
                    'desasignar_fsm_fallback container_id=%s estado=%s detalle=%s',
                    getattr(container, 'container_id', None),
                    getattr(container, 'estado', None),
                    _fsm_exc,
                )
                from apps.events.models import Event as _EventFallback
                container.estado = 'programado'
                container.fecha_asignacion = None
                container.save(update_fields=['estado', 'fecha_asignacion'])
                _EventFallback.objects.create(
                    container=container,
                    event_type='cambio_estado',
                    detalles={'estado_anterior': 'asignado', 'estado_nuevo': 'programado'},
                    usuario=request.user.username if request.user.is_authenticated else 'operador_manual',
                )
            else:
                # FSM aplicado correctamente; igualamos fecha_asignacion a None
                # porque ya no hay conductor asignado en la programación.
                if container.fecha_asignacion is not None:
                    container.fecha_asignacion = None
                    container.save(update_fields=['fecha_asignacion'])
        
        return Response({
            'success': True,
            'mensaje': f'Conductor desasignado exitosamente de la programación #{programacion.id}. Contenedor regresado a estado programado.'
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[AllowAny])
    def crear_preasignacion(self, request, pk=None):
        """
        Crea una pre-asignación: reserva conductor en una programación
        SIN cambiar el estado del contenedor, calculando métricas ML
        de ETA y confianza para decisión del operador.

        Payload: { "driver_id": int, "fecha_salida": "ISO8601" }
        """
        from apps.core.services.learning_engine import OperationalLearningEngine
        from apps.core.services.mapbox import MapboxService
        from apps.programaciones.models import RegistroOperacion
        from dateutil import parser as date_parser
        import uuid, logging
        logger = logging.getLogger(__name__)

        programacion = self.get_object()
        driver_id = request.data.get('driver_id')
        fecha_salida_str = request.data.get('fecha_salida')

        if not driver_id:
            return Response({'error': 'driver_id es requerido'}, status=status.HTTP_400_BAD_REQUEST)
        if not fecha_salida_str:
            return Response({'error': 'fecha_salida es requerida'}, status=status.HTTP_400_BAD_REQUEST)

        from apps.drivers.models import Driver
        try:
            driver = Driver.objects.get(id=driver_id)
        except Driver.DoesNotExist:
            return Response({'error': f'Conductor ID {driver_id} no encontrado'}, status=status.HTTP_404_NOT_FOUND)

        if not driver.esta_disponible:
            return Response(
                {'error': f'Conductor {driver.nombre} no está disponible'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if programacion.driver:
            return Response(
                {'error': f'Ya tiene conductor asignado ({programacion.driver.nombre}). Use desasignar primero.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            fecha_salida = date_parser.parse(fecha_salida_str)
        except Exception:
            return Response({'error': 'fecha_salida con formato inválido. Use ISO 8601.'}, status=status.HTTP_400_BAD_REQUEST)

        container = programacion.container
        cd = programacion.cd

        # -- Origen: posición física del contenedor o fallback a ubicación del driver --
        origen_coords = None
        if container.posicion_fisica:
            try:
                geocode = MapboxService.geocode(container.posicion_fisica)
                if geocode and geocode.get('success'):
                    origen_coords = (geocode['lat'], geocode['lng'])
            except Exception:
                pass

        if not origen_coords:
            if driver.ultima_posicion_lat is not None and driver.ultima_posicion_lng is not None:
                origen_coords = (float(driver.ultima_posicion_lat), float(driver.ultima_posicion_lng))
            else:
                origen_coords = (-33.4489, -70.6693)  # Santiago fallback

        destino_coords = (float(cd.lat), float(cd.lng))

        # -- Ruta base Mapbox --
        mapbox_route = MapboxService.calcular_ruta(
            float(origen_coords[1]), float(origen_coords[0]),
            float(destino_coords[1]), float(destino_coords[0])
        )
        if not mapbox_route.get('duration_minutes'):
            return Response(
                {'error': f'No se pudo calcular ruta desde {origen_coords} hasta {cd.nombre}.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        base_route = {
            'duration_minutes': float(mapbox_route['duration_minutes']),
            'distance_km': float(mapbox_route.get('distance_km', 0)),
            'route_index': 0,
            'route_signature': mapbox_route.get('route_signature', ''),
        }

        # -- Predicción híbrida ML --
        prediccion = OperationalLearningEngine.predict_route(
            origen_coords, destino_coords, fecha_salida,
            base_route, driver=driver
        )

        eta_minutos = prediccion['predicted_minutes']
        confianza = prediccion['confidence']
        fuente = prediccion['source']
        factor_ml = prediccion['learned_factor']
        muestras_ml = prediccion['samples']
        perfil_conductor = prediccion.get('driver_profile')
        mapa_minutos = prediccion['mapbox_minutes']

        # -- Guardar predicción ML en Programacion (auditable) --
        programacion.prediccion_ml = {
            'driver_id': driver.id,
            'driver_nombre': driver.nombre,
            'fecha_salida': fecha_salida.isoformat(),
            'eta_minutos': eta_minutos,
            'confianza': confianza,
            'fuente': fuente,
            'factor_ml': factor_ml,
            'muestras_ml': muestras_ml,
            'mapbox_minutos': mapa_minutos,
            'distancia_km': base_route['distance_km'],
            'perfil_conductor': perfil_conductor,
            'origen_coords': list(origen_coords),
            'destino_coords': list(destino_coords),
            'cd_destino': cd.nombre,
        }
        programacion.save(update_fields=['prediccion_ml', 'updated_at'])

        # -- Bitácora RegistroOperacion --
        service_id = f"preasign-{programacion.id}-{uuid.uuid4().hex[:8]}"
        RegistroOperacion.objects.create(
            programacion=programacion,
            service_id=service_id,
            recurso_asignado=f"{driver.nombre} (pre-asignación ML)",
            score_por_dimension={
                'eta_minutos': eta_minutos,
                'confianza': confianza,
                'factor_ml': factor_ml,
                'muestras_ml': muestras_ml,
            }
        )

        # -- Recomendación horario óptimo --
        recomendacion = OperationalLearningEngine.recommend(
            origen_coords, destino_coords, fecha_salida,
            driver=driver, window_hours=3
        )
        horario_optimo = None
        if recomendacion.get('success') and recomendacion.get('recommended'):
            rec = recomendacion['recommended']
            horario_optimo = {
                'hora_salida': rec.get('departure').isoformat() if rec.get('departure') else None,
                'eta_min': rec.get('predicted_minutes'),
                'confianza': rec.get('confidence'),
            }

        # -- Alerta demurrage --
        riesgo_demurrage = None
        if container.fecha_demurrage:
            horas_vencimiento = (container.fecha_demurrage - fecha_salida).total_seconds() / 3600
            riesgo_demurrage = {
                'horas_hasta_vencimiento': round(horas_vencimiento, 1),
                'alerta': horas_vencimiento < (eta_minutos / 60),
                'mensaje': '⚠️ Demurrage por vencer' if horas_vencimiento < (eta_minutos / 60) else None,
            }

        logger.info(
            f"Pre-asignación ML: prog={programacion.id} driver={driver.nombre} "
            f"ETA={eta_minutos}min confianza={confianza:.0%} muestras={muestras_ml}"
        )

        return Response({
            'success': True,
            'mensaje': f'Pre-asignación creada para {driver.nombre}',
            'programacion_id': programacion.id,
            'driver': {
                'id': driver.id,
                'nombre': driver.nombre,
                'patente': driver.patente,
            },
            'ml': {
                'eta_minutos': eta_minutos,
                'confianza': round(confianza, 3),
                'fuente': fuente,
                'factor_ml': factor_ml,
                'muestras_ml': muestras_ml,
                'mapbox_minutos': mapa_minutos,
                'distancia_km': base_route['distance_km'],
                'perfil_conductor': perfil_conductor,
            },
            'horario_optimo': horario_optimo,
            'riesgo_demurrage': riesgo_demurrage,
            'service_id': service_id,
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], permission_classes=[AllowAny])
    def asignar_automatico(self, request, pk=None):
        """
        Asigna automáticamente el mejor conductor disponible
        Permite acceso anónimo para operaciones automáticas desde el panel.
        """
        programacion = self.get_object()
        usuario = request.user.username if request.user.is_authenticated else 'operador_manual'
        
        resultado = AssignmentService.asignar_mejor_conductor(programacion, usuario)
        
        if resultado['success']:
            # La asignación de conductor, el cambio de estado a 'asignado',
            # el incremento de contador y el evento de auditoría ya los hace
            # Programacion.asignar_conductor() dentro del servicio.
            # No duplicar transición ni evento aquí (auditado 2026-09-17).

            serializer = self.get_serializer(programacion)
            return Response({
                'success': True,
                'mensaje': f'Conductor {resultado["driver"].nombre} asignado automáticamente',
                'score': float(resultado['score']),
                'desglose': {k: float(v) for k, v in resultado['desglose'].items()},
                'clasificacion': resultado.get('classification'),
                'confianza': resultado.get('confidence'),
                'anomalias': resultado.get('anomalies', []),
                'similitud_historica': resultado.get('similar_cases', []),
                'razon': resultado.get('reason'),
                'alternativas': resultado.get('alternatives', []),
                'programacion': serializer.data
            })
        else:
            if resultado.get('requires_operator'):
                return Response({
                    'success': False,
                    'requires_operator': True,
                    'mensaje': 'Se requiere revisión humana antes de despacho',
                    'driver_recomendado': resultado['driver'].nombre if resultado.get('driver') else None,
                    'score': float(resultado['score']) if resultado.get('score') else None,
                    'desglose': {k: float(v) for k, v in (resultado.get('desglose') or {}).items()},
                    'clasificacion': resultado.get('classification'),
                    'confianza': resultado.get('confidence'),
                    'anomalias': resultado.get('anomalies', []),
                    'similitud_historica': resultado.get('similar_cases', []),
                    'razon': resultado.get('reason'),
                    'alternativas': resultado.get('alternatives', []),
                }, status=status.HTTP_409_CONFLICT)
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
            driver_data['clasificacion'] = item.get('classification')
            driver_data['confianza'] = item.get('confidence')
            driver_data['anomalias'] = item.get('anomalies', [])
            driver_data['razon'] = item.get('reason')
            resultados.append(driver_data)
        
        return Response({
            'success': True,
            'total': len(resultados),
            'conductores': resultados
        })
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def asignar_multiples(self, request):
        """
        Asigna conductores automáticamente a múltiples programaciones
        Permite acceso anónimo para operaciones masivas desde el panel.
        """
        programacion_ids = request.data.get('programacion_ids', [])
        
        if not programacion_ids:
            return Response(
                {'error': 'programacion_ids no proporcionado'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        programaciones = self.queryset.filter(id__in=programacion_ids, driver__isnull=True)
        usuario = request.user.username if request.user.is_authenticated else 'operador_manual'
        
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
        
        SOLO muestra programaciones activas (pendientes de completar):
        - Estados válidos: programado, asignado, en_ruta, entregado, descargado
        - Excluye: vacio, vacio_en_ruta, devuelto (ya completados)
        """
        ahora = timezone.now()
        
        # Filtrar solo programaciones con contenedores en estados activos
        # Excluir contenedores que ya están vacíos o devueltos (completados)
        estados_activos = ['programado', 'secuenciado', 'asignado', 'en_ruta', 'entregado', 'soltado', 'descargado']
        programaciones = self.queryset.filter(
            container__estado__in=estados_activos
        ).select_related('container', 'driver', 'cd')
        
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
                'fecha_inicio_ruta': prog.fecha_inicio_ruta,
                'eta_minutos': prog.eta_minutos,
                'eta_recalculado_min': prog.eta_recalculado_min,
                'eta_timestamp': (
                    prog.fecha_inicio_ruta + timedelta(minutes=prog.eta_minutos)
                    if prog.fecha_inicio_ruta and prog.eta_minutos is not None
                    else None
                ),
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
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def crear_ruta_manual(self, request):
        """
        Crea una ruta manual para retiro desde puerto
        Permite acceso anónimo para operaciones manuales desde el panel.
        
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
            cd_destino = CD.objects.filter(tipo='ccti').first()
            if not cd_destino:
                return Response(
                    {'error': 'No se encontró ningún CCTI en el sistema'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:  # retiro_directo
            cd_destino = data['_cd_destino']
        
        # Pre-validación: si el contenedor ya tiene una programación asociada,
        # evitamos el IntegrityError del OneToOne respondiendo 400 (consistente
        # con containers.views.programar). Hace la re-ejecución sobre el mismo
        # contenedor idempotente para el operador en vez de un 500 opaco.
        tiene_prog, existing_prog = Programacion.container_tiene_programacion(container)
        if tiene_prog and existing_prog is not None:
            return Response(
                {
                    'error': f'Este contenedor ya tiene una programación asociada (ID: {existing_prog.id})',
                    'programacion_existente': {
                        'id': existing_prog.id,
                        'fecha_programada': existing_prog.fecha_programada.isoformat(),
                        'cd': existing_prog.cd.nombre if existing_prog.cd else None,
                        'tiene_conductor': existing_prog.driver is not None,
                        'estado_container': container.estado,
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Crear la programación dentro de transacción atómica y capturar
        # IntegrityError por si una carrera concurrente inserta la fila OneToOne
        # entre la validación previa y el create().
        try:
            with transaction.atomic():
                programacion = Programacion.objects.create(
                    container=container,
                    cd=cd_destino,
                    fecha_programada=data['fecha_programacion'],
                    cliente=normalizar_cliente(data.get('cliente', '')),
                    direccion_entrega=cd_destino.direccion,
                    observaciones=data.get('observaciones', f'Retiro manual desde {container.posicion_fisica}')
                )

                usuario = request.user.username if request.user.is_authenticated else None
                container.cambiar_estado('programado', usuario)

                # Crear evento de auditoría
                from apps.events.models import Event
                Event.objects.create(
                    container=container,
                    event_type='import_programacion',
                    usuario=request.user.username if request.user.is_authenticated else None,
                    detalles={
                        'accion': 'ruta_manual_creada',
                        'descripcion': f'Ruta manual creada: {tipo_movimiento}',
                        'tipo_movimiento': tipo_movimiento,
                        'origen': container.posicion_fisica,
                        'destino': cd_destino.nombre,
                        'programacion_id': programacion.id,
                        'fecha_programacion': data['fecha_programacion'].isoformat()
                    }
                )

                # P1-4: registrar TiempoOperacion para carga_ccti o retiro_puerto
                # según tipo_movimiento. started_at = ahora (sin dato histórico real),
                # finished_at = fecha_programacion (estimación del operador).
                try:
                    from apps.core.services.operations import OperationalFlowService
                    tipo_op = 'carga_ccti' if tipo_movimiento == 'retiro_ccti' else 'retiro_puerto'
                    OperationalFlowService.registrar_operacion_tiempo(
                        container=container,
                        tipo_operacion=tipo_op,
                        started_at=timezone.now(),
                        finished_at=data['fecha_programacion'],
                        cd_origen=cd_destino,
                        cd_destino=cd_destino,
                        conductor=None,
                        observaciones=f'Carga/retiro programado (ruta manual {tipo_movimiento})',
                    )
                except Exception as _p1_exc:
                    logger.warning('crear_ruta_manual tiempo_operacion_failed: %s', _p1_exc)
        except IntegrityError:
            logger.warning(
                'crear_ruta_manual_integrity_error',
                extra={'container_id': getattr(container, 'container_id', None)},
            )
            return Response(
                {'error': 'Este contenedor ya tiene una programación asociada. Por favor, recargue la página.'},
                status=status.HTTP_409_CONFLICT,
            )
        
        return Response({
            'success': True,
            'mensaje': 'Ruta manual creada exitosamente',
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
        
        NOTA: Este endpoint permite AllowAny por compatibilidad con sistemas externos.
        """
        if 'file' not in request.FILES:
            return Response(
                {'error': 'No se proporcionó archivo'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        archivo = request.FILES['file']
        
        # Validar extensión de archivo
        if not archivo.name.endswith(('.xlsx', '.xls')):
            return Response(
                {'error': 'Formato de archivo inválido. Solo se permiten archivos .xlsx o .xls'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validar tamaño de archivo (máximo 10MB)
        max_size = 10 * 1024 * 1024  # 10MB en bytes
        if archivo.size > max_size:
            return Response(
                {'error': 'Archivo demasiado grande. Tamaño máximo: 10MB'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
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
                'mensaje': 'Importación de programación completada',
                'programados': resultados['programados'],
                'no_encontrados': resultados['no_encontrados'],
                'cd_no_encontrado': resultados['cd_no_encontrado'],
                'errores': resultados['errores'],
                'alertas_generadas': resultados['alertas_generadas'],
                'detalles': resultados['detalles']
            })
        
        except ValueError as e:
            logger.warning('import_programacion_endpoint_value_error', extra={'usuario': usuario, 'detalle': str(e)})
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.exception('import_programacion_endpoint_failed', extra={'usuario': usuario})
            return Response(
                {
                    'error': 'No fue posible completar la importación de programación',
                    'detalle': str(e)
                },
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
        
        # Perfil ML del conductor para la advertencia (histórico real)
        perfil_ml = None
        try:
            from apps.core.services.learning_engine import OperationalLearningEngine
            perfil_ml = OperationalLearningEngine.driver_profile(driver)
        except Exception as exc:
            # Antes: 'except Exception: pass' silenciaba el fallo del ML.
            # Si el ML rompe por un bug, el operador ve advertencias incompletas
            # sin pista de por qué. Logueamos para diagnosticar y devolvemos
            # sin el bloque ML (la validacion sigue funcionando).
            logger.warning(
                'No se pudo cargar el perfil ML para conductor %s: %s',
                getattr(driver, 'id', None), exc,
            )
        
        return Response({
            'success': True,
            'disponible': resultado['disponible'],
            'conflictos': resultado['conflictos'],
            'retraso_maximo_min': resultado.get('retraso_maximo_min'),
            'tiempo_requerido': resultado['tiempo_requerido'],
            'ventana_ocupada': resultado['ventana_ocupada'],
            'nueva_ventana': resultado.get('nueva_ventana'),
            'conductor': {
                'id': driver.id,
                'nombre': driver.nombre,
                'patente': driver.patente,
            },
            'perfil_ml': perfil_ml,
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
        programacion.posicion_actual_lat = lat
        programacion.posicion_actual_lng = lng
        programacion.ultima_actualizacion_tracking = timezone.now()
        
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
        
        # Calcular y guardar ETA híbrido (Mapbox + aprendizaje histórico).
        from apps.core.services.learning_engine import OperationalLearningEngine
        from apps.core.services.ml_predictor import MLTimePredictor
        eta_ok = False
        try:
            recomendacion = OperationalLearningEngine.recommend(
                (float(lat), float(lng)),
                (float(programacion.cd.lat), float(programacion.cd.lng)),
                programacion.fecha_inicio_ruta,
                driver=programacion.driver,
                window_hours=0,
            )
            if recomendacion.get('success'):
                prediccion = recomendacion['recommended']
                programacion.eta_minutos = prediccion['predicted_minutes']
                programacion.distancia_km = prediccion['distance_km']
                programacion.ruta_geojson = prediccion.get('geometry')
                programacion.ruta_firma = prediccion.get('route_signature')
                programacion.prediccion_ml = {
                    'source': prediccion['source'],
                    'mapbox_minutes': prediccion['mapbox_minutes'],
                    'predicted_minutes': prediccion['predicted_minutes'],
                    'learned_factor': prediccion['learned_factor'],
                    'samples': prediccion['samples'],
                    'confidence': prediccion['confidence'],
                    'driver_profile': prediccion.get('driver_profile'),
                    'explanation': recomendacion['explanation'],
                }
                eta_ok = True
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Error calculando ETA (recommend) para programación: {str(e)}")
        
        # Fallback: si Mapbox/ML recomendación falla, usar el predictor con fallback
        # (siempre debe quedar una ETA operable para advertir choques y mostrar llegada).
        if not eta_ok:
            try:
                pred_fb = MLTimePredictor.predecir_tiempo_viaje(
                    (float(lat), float(lng)),
                    (float(programacion.cd.lat), float(programacion.cd.lng)),
                    programacion.fecha_inicio_ruta,
                    conductor=programacion.driver,
                )
                programacion.eta_minutos = int(pred_fb['tiempo_estimado_min'])
                programacion.distancia_km = pred_fb.get('distancia_km') or 0
                programacion.prediccion_ml = {
                    'source': pred_fb.get('fuente', 'fallback'),
                    'mapbox_minutes': pred_fb.get('tiempo_mapbox_min', 0),
                    'predicted_minutes': programacion.eta_minutos,
                    'learned_factor': None,
                    'samples': 0,
                    'confidence': None,
                    'driver_profile': None,
                    'explanation': 'ETA de respaldo (fuente: %s).' % pred_fb.get('fuente', 'fallback'),
                }
                eta_ok = True
            except Exception as e2:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Error calculando ETA (fallback) para programación: {str(e2)}")
        
        if eta_ok:
            programacion.save(update_fields=[
                'eta_minutos', 'distancia_km', 'ruta_geojson', 'ruta_firma',
                'prediccion_ml', 'updated_at'
            ])
        
        # Crear notificación con ETA (pasar la ETA ya calculada de la programación
        # para no recalcular con Mapbox y quedar sin ella si Mapbox falla).
        try:
            notificacion = NotificationService.crear_notificacion_inicio_ruta(
                programacion, programacion.driver,
                eta_minutos=programacion.eta_minutos,
                distancia_km=programacion.distancia_km,
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
    
    def _update_registro_operacion_on_completion(self, programacion: Programacion, estado_final: str):
        from apps.programaciones.models import RegistroOperacion, TiempoViaje
        import logging

        logger = logging.getLogger(__name__)

        try:
            registro = RegistroOperacion.objects.filter(programacion=programacion).order_by('-created_at').first()
            if not registro:
                logger.warning(f"No se encontró RegistroOperacion para Programacion ID {programacion.id}. No se actualizará al finalizar.")
                return
            
            # Calcular ETA real
            eta_real_min = None
            if programacion.fecha_inicio_ruta and programacion.container.fecha_entrega:
                duration = programacion.container.fecha_entrega - programacion.fecha_inicio_ruta
                eta_real_min = int(duration.total_seconds() / 60)

            registro.eta_real_min = eta_real_min
            registro.estado_final = estado_final
            registro.incidentes_ejecucion = programacion.incidentes_registrados # Copiar incidentes al log final
            registro.save(update_fields=['eta_real_min', 'estado_final', 'incidentes_ejecucion'])

            # Alimentar la estimación adaptativa con un viaje real completo.
            if (
                programacion.fecha_inicio_ruta
                and programacion.container.fecha_entrega
                and programacion.gps_inicio_lat is not None
                and programacion.gps_inicio_lng is not None
                and programacion.cd
                and programacion.eta_minutos
                and not TiempoViaje.objects.filter(programacion=programacion).exists()
            ):
                real_min = max(1, int((programacion.container.fecha_entrega - programacion.fecha_inicio_ruta).total_seconds() / 60))
                estimado = max(1, int(programacion.eta_minutos))
                TiempoViaje.objects.create(
                    conductor=programacion.driver,
                    programacion=programacion,
                    origen_lat=programacion.gps_inicio_lat,
                    origen_lon=programacion.gps_inicio_lng,
                    destino_lat=programacion.cd.lat,
                    destino_lon=programacion.cd.lng,
                    origen_nombre='Inicio de ruta',
                    destino_nombre=programacion.cd.nombre,
                    tiempo_mapbox_min=estimado,
                    tiempo_real_min=real_min,
                    hora_salida=programacion.fecha_inicio_ruta,
                    hora_llegada=programacion.container.fecha_entrega,
                    hora_del_dia=programacion.fecha_inicio_ruta.hour,
                    dia_semana=programacion.fecha_inicio_ruta.weekday(),
                    distancia_km=programacion.distancia_km or 0,
                    ruta_firma=programacion.ruta_firma,
                    anomalia=real_min >= estimado * 3,
                )
            logger.info(f"RegistroOperacion {registro.id} actualizado al finalizar Programacion {programacion.id} con estado {estado_final}.")
        except Exception as e:
            logger.error(f"Error actualizando RegistroOperacion para Programacion {programacion.id}: {str(e)}", exc_info=True)

    def _registrar_arribo(self, programacion, lat, lng, origen, usuario=None):
        """Registra una sola vez el arribo, sea manual o disparado por geocerca.

        Delega en el servicio operacional central (OperationalFlowService): una única
        fuente de verdad compartida con el flujo de containers (fix duplicación de caminos).
        """
        from apps.core.services.operations import OperationalFlowService

        locked, created = OperationalFlowService.registrar_arribo(
            programacion, lat, lng, origen, usuario
        )
        if created:
            self._update_registro_operacion_on_completion(locked, 'ENTREGADO')
        return locked, created

    @staticmethod
    def _usuario_puede_operar_viaje(request, programacion):
        """Un conductor solo puede operar su propio viaje; staff conserva acceso."""
        if not request.user.is_authenticated:
            return False
        if request.user.is_staff:
            return True
        return programacion.driver_id and programacion.driver.user_id == request.user.id


    @action(detail=True, methods=['post'])
    def notificar_arribo(self, request, pk=None):
        """
        Notifica que el conductor ha arribado al CD (llegó al destino)
        Cambia el estado del contenedor a 'entregado'
        
        Payload requerido:
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
        if not self._usuario_puede_operar_viaje(request, programacion):
            return Response(
                {'error': 'No puede registrar el arribo de otro conductor.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        
        lat = request.data.get('lat')
        lng = request.data.get('lng')
        if lat is None or lng is None:
            return Response(
                {'error': 'Se requiere GPS para registrar el arribo manual.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        usuario = request.user.username if request.user.is_authenticated else None
        try:
            programacion, created = self._registrar_arribo(
                programacion, lat, lng, 'manual', usuario
            )
        except ValueError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = self.get_serializer(programacion)
        return Response({
            'success': True,
            'mensaje': f'Arribo registrado en {programacion.cd.nombre}',
            'programacion': serializer.data,
            'nuevo_estado': 'entregado',
            'fecha_arribo_cd': programacion.fecha_arribo_cd,
            'gps_registrado': {'lat': str(programacion.gps_arribo_lat), 'lng': str(programacion.gps_arribo_lng)},
            'origen_arribo': programacion.origen_arribo,
            'ya_registrado': not created,
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
        if not self._usuario_puede_operar_viaje(request, programacion):
            return Response({'error': 'No puede operar un viaje ajeno.'}, status=status.HTTP_403_FORBIDDEN)
        
        # El conductor confirma la descarga solo cuando esperó con el equipo.
        # Tras un drop & hook, la confirmación corresponde al operador del CD.
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
        
        usuario = request.user.username if request.user.is_authenticated else None
        from apps.core.services.operations import OperationalFlowService
        try:
            programacion, timing = OperationalFlowService.mark_empty(
                programacion, usuario, source='portal_conductor'
            )
        except ValueError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        # 🆕 Actualizar RegistroOperacion con estado final
        # La entrega del contenedor LLENO se completó: la devolución del vacío es
        # un servicio posterior que se registra aparte (semántica de negocio).
        self._update_registro_operacion_on_completion(programacion, 'ENTREGADO')
        
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
            'mensaje': 'Contenedor marcado como vacío. Listo para retiro.',
            'programacion': serializer.data,
            'nuevo_estado': 'vacio',
            'tiempo_descarga_min': timing.tiempo_real_min if timing else None,
        })
    
    @action(detail=True, methods=['post'])
    def soltar_contenedor(self, request, pk=None):
        """
        Permite al conductor soltar el contenedor y quedar libre inmediatamente (Drop & Hook)
        Solo disponible si el CD permite soltar contenedor
        
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
        if not self._usuario_puede_operar_viaje(request, programacion):
            return Response({'error': 'No puede operar un viaje ajeno.'}, status=status.HTTP_403_FORBIDDEN)
        
        # Verificar que el CD permita soltar contenedor
        if not programacion.cd.permite_soltar_contenedor:
            return Response(
                {'error': f'El CD {programacion.cd.nombre} no permite Drop & Hook. El conductor debe esperar la descarga.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Permitir reintento idempotente desde conexiones móviles inestables.
        if programacion.container.estado not in {'entregado', 'soltado'}:
            return Response(
                {'error': f'Solo se puede soltar el contenedor después de haberlo entregado. Estado actual: {programacion.container.get_estado_display()}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Actualizar posición del conductor si se proporciona
        lat = request.data.get('lat')
        lng = request.data.get('lng')
        if lat and lng:
            programacion.driver.actualizar_posicion(lat, lng)
        
        usuario = request.user.username if request.user.is_authenticated else None
        from apps.core.services.operations import OperationalFlowService
        try:
            programacion, created = OperationalFlowService.drop_container(programacion, usuario)
        except ValueError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        
        # El viaje lleno terminó: la entrega se completó; la descarga pendiente
        # del CD se registra con su propio timing (coherencia de estado_final).
        self._update_registro_operacion_on_completion(programacion, 'ENTREGADO')
        
        # Crear evento de contenedor soltado
        from apps.events.models import Event
        if created:
            Event.objects.create(
                container=programacion.container,
                event_type='contenedor_soltado',
                detalles={
                    'conductor': programacion.driver.nombre,
                    'cd': programacion.cd.nombre,
                    'tipo': 'drop_and_hook',
                    'gps_lat': str(lat) if lat else None,
                    'gps_lng': str(lng) if lng else None,
                    'timestamp': timezone.now().isoformat()
                },
                usuario=usuario
            )
        
        serializer = self.get_serializer(programacion)
        return Response({
            'success': True,
            'mensaje': f'Contenedor soltado en {programacion.cd.nombre}. Conductor libre para nueva asignación.',
            'programacion': serializer.data,
            'nuevo_estado': 'soltado',
            'conductor_liberado': True,
            'ya_registrado': not created,
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
        if not self._usuario_puede_operar_viaje(request, programacion):
            return Response(
                {'error': 'No puede actualizar el viaje de otro conductor.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        
        lat = request.data.get('lat')
        lng = request.data.get('lng')
        
        if lat is None or lng is None:
            return Response(
                {'error': 'lat y lng requeridos'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Arribo automático: permanece dormido hasta que el CD tenga un radio.
        # Se comprueba antes del tracking ordinario para registrar una sola muestra GPS.
        if (
            programacion.container.estado == 'en_ruta'
            and programacion.cd.contiene_en_geocerca(lat, lng)
        ):
            programacion, created = self._registrar_arribo(
                programacion, lat, lng, 'geocerca', 'system_geocerca'
            )
            return Response({
                'success': True,
                'mensaje': 'Arribo registrado automáticamente por geocerca',
                'arribo_automatico': True,
                'arribo_creado': created,
                'fecha_arribo_cd': programacion.fecha_arribo_cd,
                'nuevo_estado': 'entregado',
            })

        # Fuera de geocerca, guardar tracking y recalcular ETA normalmente.
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

        programacion.eta_recalculado_min = resultado['eta_minutos']
        configured_delay_threshold = int(getattr(settings, 'ETA_DELAY_ALERT_MIN', 15))
        request_override_threshold = request.query_params.get('eta_delay_alert_min')
        eta_delay_threshold = int(request_override_threshold) if request_override_threshold else configured_delay_threshold
        if programacion.eta_minutos and (resultado['eta_minutos'] - programacion.eta_minutos) > eta_delay_threshold:
            desvio = {
                'tipo': 'ETA_DELAY',
                'mensaje': 'ETA recalculado supera lo prometido',
                'valor_min': int(resultado['eta_minutos'] - programacion.eta_minutos),
                'timestamp': timezone.now().isoformat(),
            }
            programacion.desviaciones_detectadas = (programacion.desviaciones_detectadas or []) + [desvio]
        programacion.save(update_fields=[
            'posicion_actual_lat', 'posicion_actual_lng', 'ultima_actualizacion_tracking',
            'eta_recalculado_min', 'desviaciones_detectadas'
        ])
        
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
    def recomendacion_ml(self, request, pk=None):
        """Compara horarios, rutas y conductor usando historial real + Mapbox."""
        from apps.core.services.learning_engine import OperationalLearningEngine

        programacion = self.get_object()
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')
        if lat is None or lng is None:
            if programacion.driver and programacion.driver.ultima_posicion_lat is not None:
                lat = programacion.driver.ultima_posicion_lat
                lng = programacion.driver.ultima_posicion_lng
            elif programacion.gps_inicio_lat is not None:
                lat, lng = programacion.gps_inicio_lat, programacion.gps_inicio_lng
            else:
                return Response(
                    {'error': 'Se necesita una ubicación de origen (lat/lng).'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        try:
            window_hours = min(8, max(0, int(request.query_params.get('ventana_horas', 3))))
        except ValueError:
            return Response({'error': 'ventana_horas debe ser entero'}, status=status.HTTP_400_BAD_REQUEST)
        salida = programacion.fecha_inicio_ruta or timezone.now()
        recommendation = OperationalLearningEngine.recommend(
            (float(lat), float(lng)),
            (float(programacion.cd.lat), float(programacion.cd.lng)),
            salida,
            driver=programacion.driver,
            window_hours=window_hours,
        )
        if not recommendation.get('success'):
            return Response(recommendation, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response(recommendation)

    @action(detail=True, methods=['post'])
    def confirmar_recomendacion(self, request, pk=None):
        """Confirma la recomendación y CONCRETA la asignación del conductor recomendado.

        Cierra el ciclo preasignación → confirmar: si la predicción ML dejó un
        driver recomendado y aún no hay asignación, se asigna (validando disponibilidad).
        """
        from django.core.exceptions import ValidationError as DjangoValidationError
        programacion = self.get_object()
        programacion.decision_operador = 'CONFIRMAR'
        programacion.motivo_override = ''
        programacion.save(update_fields=['decision_operador', 'motivo_override'])

        if not programacion.driver:
            driver_id = (programacion.prediccion_ml or {}).get('driver_id')
            if driver_id:
                try:
                    from apps.drivers.models import Driver
                    driver = Driver.objects.get(pk=driver_id)
                    programacion.asignar_conductor(
                        driver, request.user.username if request.user.is_authenticated else 'operador_manual'
                    )
                    # Trazabilidad: la confirmación del operador queda en la
                    # bitácora (la preasignación creó el registro inicial;
                    # aquí se cierra el ciclo con su decisión).
                    from apps.programaciones.models import RegistroOperacion
                    RegistroOperacion.objects.create(
                        programacion=programacion,
                        service_id=f"confirm-{programacion.id}-{uuid.uuid4().hex[:8]}",
                        recurso_asignado=driver.nombre,
                        clasificacion_sistema='REVISION_OPERADOR',
                        decision_operador='CONFIRMAR',
                        motivo_override='',
                        timestamp_despacho=timezone.now(),
                    )
                except Driver.DoesNotExist:
                    programacion.refresh_from_db()
                    return Response(
                        {'success': False, 'error': 'El conductor recomendado ya no existe. Re-evaluar.'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                except DjangoValidationError as exc:
                    programacion.refresh_from_db()
                    return Response(
                        {'success': False, 'error': '; '.join(exc.messages) if hasattr(exc, 'messages') else str(exc)},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

        serializer = self.get_serializer(programacion)
        return Response({
            'success': True,
            'mensaje': 'Recomendación confirmada por operador.'
                       + (' Conductor asignado.' if programacion.driver else ''),
            'conductor_asignado': programacion.driver.nombre if programacion.driver else None,
            'programacion': serializer.data,
        })

    @action(detail=True, methods=['post'])
    def rechazar_recomendacion(self, request, pk=None):
        """Rechaza recomendación con motivo obligatorio."""
        programacion = self.get_object()
        motivo = (request.data.get('motivo') or '').strip()
        if not motivo:
            return Response({'error': 'motivo es obligatorio para rechazar'}, status=status.HTTP_400_BAD_REQUEST)
        programacion.decision_operador = 'RECHAZAR'
        programacion.motivo_override = motivo
        programacion.save(update_fields=['decision_operador', 'motivo_override'])
        return Response({'success': True, 'mensaje': 'Recomendación rechazada y registrada.'})

    @action(detail=True, methods=['post'])
    def escalar_supervisor(self, request, pk=None):
        """Escala la operación a supervisor."""
        programacion = self.get_object()
        motivo = (request.data.get('motivo') or 'Escalado manual por operador').strip()
        programacion.decision_operador = 'ESCALAR'
        programacion.motivo_override = motivo
        programacion.save(update_fields=['decision_operador', 'motivo_override'])
        return Response({'success': True, 'mensaje': 'Caso escalado a supervisor.'})

    @action(detail=True, methods=['post'])
    def reevaluar(self, request, pk=None):
        """Permite modificar parámetros operativos y recalcular recomendación."""
        programacion = self.get_object()
        urgencia = request.data.get('urgencia_servicio')
        seguimiento = request.data.get('requiere_seguimiento_especial')
        if urgencia in ['NORMAL', 'URGENTE', 'CRITICO']:
            programacion.urgencia_servicio = urgencia
        if isinstance(seguimiento, bool):
            programacion.requiere_seguimiento_especial = seguimiento
        if request.data.get('ventana_horaria_inicio'):
            try:
                programacion.ventana_horaria_inicio = date_parser.parse(request.data.get('ventana_horaria_inicio'))
            except Exception:
                return Response({'error': 'ventana_horaria_inicio inválida (usar ISO 8601)'}, status=status.HTTP_400_BAD_REQUEST)
        if request.data.get('ventana_horaria_fin'):
            try:
                programacion.ventana_horaria_fin = date_parser.parse(request.data.get('ventana_horaria_fin'))
            except Exception:
                return Response({'error': 'ventana_horaria_fin inválida (usar ISO 8601)'}, status=status.HTTP_400_BAD_REQUEST)
        programacion.decision_operador = 'MODIFICAR'
        programacion.save()

        usuario = request.user.username if request.user.is_authenticated else 'operador_manual'
        resultado = AssignmentService.asignar_mejor_conductor(programacion, usuario)
        # success real refleja si la asignación concretó o requiere operador (auditado 2026-09-17)
        return Response({'success': resultado.get('success', False), 'resultado': resultado})
    
    @action(detail=True, methods=['post'], permission_classes=[AllowAny])
    def reportar_incidente(self, request, pk=None):
        """
        Permite al conductor o a un operador registrar un incidente durante un viaje.
        Este incidente se añade al campo `incidentes_registrados` de la programación.

        Payload:
        {
            "tipo_incidente": "ACCIDENTE" | "AVERIA" | "DEMORA_TRAFICO" | "OTRO",
            "descripcion": "Descripción detallada del incidente",
            "gravedad": "LEVE" | "MODERADA" | "ALTA" | "CRITICA",
            "lat": -33.4372,      // Ubicación GPS actual (opcional)
            "lng": -70.6506       // Ubicación GPS actual (opcional)
        }
        """
        programacion = self.get_object()
        
        tipo_incidente = request.data.get('tipo_incidente')
        descripcion = request.data.get('descripcion', '').strip()
        gravedad = request.data.get('gravedad', 'MODERADA')
        lat = request.data.get('lat')
        lng = request.data.get('lng')

        if not tipo_incidente or not descripcion:
            return Response(
                {'error': 'tipo_incidente y descripcion son campos obligatorios.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validar tipo de incidente y gravedad (opcional, pero buena práctica)
        tipos_validos = ["ACCIDENTE", "AVERIA", "DEMORA_TRAFICO", "OTRO"]
        gravedades_validas = ["LEVE", "MODERADA", "ALTA", "CRITICA"]

        # P2-3: nota de deprecación. Los 4 tipos arriba cambian container.estado a
        # 'incidente' (FSM). Problemas operativos que NO escalan el estado (guía
        # faltante, dirección incorrecta, cliente cerrado, problema administrativo)
        # deben reportarse vía reportar_problema con tipos FALTA_GUIA/DIRECCION_*
        # /CLIENTE_CERRADO/PROBLEMA_ADMINISTRATIVO/OTRO.
        # Mantener ambos caminos para no romper integraciones existentes; este
        # docstring queda como contrato para el frontend y operadores.

        if tipo_incidente not in tipos_validos:
            return Response(
                {'error': f'Tipo de incidente inválido. Tipos permitidos: {", ".join(tipos_validos)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if gravedad not in gravedades_validas:
            return Response(
                {'error': f'Gravedad inválida. Gravedades permitidas: {", ".join(gravedades_validas)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        incidente_data = {
            'tipo': tipo_incidente,
            'descripcion': descripcion,
            'gravedad': gravedad,
            'timestamp': timezone.now().isoformat(),
            'reportado_por': request.user.username if request.user.is_authenticated else 'anonimo',
        }
        if lat and lng:
            incidente_data['gps_lat'] = str(lat)
            incidente_data['gps_lng'] = str(lng)

        # Append atómico sobre `incidentes_registrados` (JSONField): bloqueamos la
        # fila con select_for_update, re-leemos la lista vigente bajo el lock y
        # hacemos append + save dentro de transaction.atomic. Sin el lock, dos
        # incidentes concurrentes pueden leer la misma lista base y pisarse mutuamente
        # perdiendo uno. JSONField no soporta F() nativo de forma segura para append.
        from apps.events.models import Event
        try:
            with transaction.atomic():
                locked = Programacion.objects.select_for_update().get(pk=programacion.pk)
                lista_actual = locked.incidentes_registrados or []
                lista_actual.append(incidente_data)
                locked.incidentes_registrados = lista_actual
                locked.save(update_fields=['incidentes_registrados'])

                # Propagar la lista actualizada al objeto que devolvemos al caller
                # para que el serializer refleje el incidente recién agregado.
                programacion.incidentes_registrados = lista_actual

                # Crear evento de auditoría dentro del mismo lock para que la
                # trazabilidad sea consistente con el append.
                Event.objects.create(
                    container=locked.container,
                    event_type='incidente_reportado',
                    detalles=incidente_data,
                    usuario=request.user.username if request.user.is_authenticated else 'anonimo'
                )
        except Exception as _lock_exc:
            logger.error(
                'reportar_incidente_lock_failure programacion_id=%s detalle=%s',
                getattr(programacion, 'pk', None),
                _lock_exc,
                exc_info=True,
            )
            return Response(
                {'error': 'No se pudo registrar el incidente de forma atómica. Reintente.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        # Notificar a operadores vía OpenClaw si es de alta gravedad. Se hace
        # FUERA del atomic para no mantener el row lock durante la llamada de red;
        # un fallo de notificación no debe revertir el incidente ya persistido.
        # Se sigue el patrón del fix e9e88b46 (asignar_automatico).
        if gravedad in ['ALTA', 'CRITICA']:
            try:
                from apps.core.services.openclaw import OpenClawService
                OpenClawService.notify_anomaly(
                    programacion,
                    [
                        {
                            'code': f"INCIDENTE_{gravedad}",
                            'severity': 'P0' if gravedad == 'CRITICA' else 'P1',
                            'message': f"Incidente reportado: {tipo_incidente} - {descripcion}",
                            'recommended_action': "Revisar de inmediato y coordinar asistencia."
                        }
                    ]
                )
            except Exception as _openclaw_exc:
                # Notificación fallida no rompe el flujo; el incidente ya está guardado.
                logger.warning(
                    'reportar_incidente_openclaw_notify_failed programacion_id=%s gravedad=%s detalle=%s',
                    getattr(programacion, 'pk', None),
                    gravedad,
                    _openclaw_exc,
                )

        serializer = self.get_serializer(programacion)
        return Response({
            'success': True,
            'mensaje': 'Incidente registrado exitosamente.',
            'incidente': incidente_data,
            'programacion': serializer.data
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def notificar_inicio_descarga(self, request, pk=None):
        """P1-1: marca el clic "Iniciar Descarga" del conductor en CD.

        Diferencia clave con notificar_arribo: este endpoint solo guarda
        Programacion.fecha_inicio_descarga para medir la duración real de la
        descarga cuando llegue notificar_fin_descarga. NO cambia
        container.estado (sigue en 'entregado' o 'soltado').

        Payload opcional:
        {
            "lat": -33.4372,
            "lng": -70.6506
        }
        """
        programacion = self.get_object()
        if not programacion.driver:
            return Response(
                {'error': 'Programación no tiene conductor asignado.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not self._usuario_puede_operar_viaje(request, programacion):
            return Response(
                {'error': 'No puede operar un viaje ajeno.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        if programacion.container.estado not in ('entregado', 'soltado'):
            return Response(
                {'error': f'Contenedor debe estar entregado o soltado. Estado: {programacion.container.get_estado_display()}.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if programacion.fecha_inicio_descarga:
            return Response(
                {'error': 'La descarga ya fue marcada como iniciada.', 'fecha_inicio_descarga': programacion.fecha_inicio_descarga.isoformat()},
                status=status.HTTP_409_CONFLICT,
            )

        now = timezone.now()
        lat = request.data.get('lat')
        lng = request.data.get('lng')
        with transaction.atomic():
            locked = Programacion.objects.select_for_update().get(pk=programacion.pk)
            locked.fecha_inicio_descarga = now
            update_fields = ['fecha_inicio_descarga', 'updated_at']
            if lat and lng:
                locked.posicion_actual_lat = lat
                locked.posicion_actual_lng = lng
                locked.ultima_actualizacion_tracking = now
                update_fields += ['posicion_actual_lat', 'posicion_actual_lng', 'ultima_actualizacion_tracking']
            locked.save(update_fields=update_fields)

        from apps.events.models import Event
        Event.objects.create(
            container=programacion.container,
            event_type='inicio_descarga',
            detalles={
                'cd': programacion.cd.nombre,
                'conductor': programacion.driver.nombre,
                'lat': str(lat) if lat else None,
                'lng': str(lng) if lng else None,
                'timestamp': now.isoformat(),
            },
            usuario=request.user.username if request.user.is_authenticated else 'conductor',
        )

        return Response({
            'success': True,
            'mensaje': 'Inicio de descarga registrado.',
            'fecha_inicio_descarga': now.isoformat(),
            'programacion_id': programacion.pk,
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def notificar_fin_descarga(self, request, pk=None):
        """P1-1: cierra la descarga del contenedor.

        Usa Programacion.fecha_inicio_descarga como hora_inicio del
        TiempoOperacion (descarga_cd). Si no existe (clic del conductor
        faltante), cae al histórico (fecha_soltado/fecha_entrega) en el
        servicio central.

        Cambia container.estado a 'descargado' vía complete_discharge.
        """
        programacion = self.get_object()
        if not programacion.driver:
            return Response(
                {'error': 'Programación no tiene conductor asignado.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not self._usuario_puede_operar_viaje(request, programacion):
            return Response(
                {'error': 'No puede operar un viaje ajeno.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        if programacion.container.estado not in ('entregado', 'soltado'):
            return Response(
                {'error': f'Contenedor debe estar entregado o soltado. Estado: {programacion.container.get_estado_display()}.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        usuario = request.user.username if request.user.is_authenticated else 'conductor'
        from apps.core.services.operations import OperationalFlowService
        try:
            locked, timing, created = OperationalFlowService.complete_discharge(
                programacion, usuario=usuario, source='portal_conductor',
            )
        except ValueError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        # Si la programación ya estaba cerrada, retornar 409 con el timing previo
        if not created:
            return Response(
                {'error': 'La descarga ya fue cerrada.', 'nuevo_estado': locked.container.estado},
                status=status.HTTP_409_CONFLICT,
            )

        serializer = self.get_serializer(locked)
        return Response({
            'success': True,
            'mensaje': 'Descarga cerrada.',
            'programacion': serializer.data,
            'nuevo_estado': 'descargado',
            'tiempo_descarga_min': timing.tiempo_real_min if timing else None,
            'anomalia': bool(timing.anomalia) if timing else False,
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def asignar_conductor_retiro_vacio(self, request):
        """P1-2: asigna un conductor a un retiro de vacío.

        Crea Programacion de retiro si no existe, usa destino del retorno
        (Container.retorno_destino_cd o Container.cd_entrega) y notifica al
        conductor.

        Payload:
        {
            "container_id": int,   // contenedor en estado 'vacio' o 'en_ccti'
            "driver_id": int        // conductor disponible
        }
        """
        container_id = request.data.get('container_id')
        driver_id = request.data.get('driver_id')
        if not container_id or not driver_id:
            return Response(
                {'error': 'container_id y driver_id son obligatorios.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        from apps.containers.models import Container as ContainerModel
        from apps.drivers.models import Driver as DriverModel
        try:
            container = ContainerModel.objects.get(pk=container_id)
            driver = DriverModel.objects.get(pk=driver_id)
        except (ContainerModel.DoesNotExist, DriverModel.DoesNotExist):
            return Response(
                {'error': 'container_id o driver_id no existen.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        if container.estado not in ('vacio', 'en_ccti', 'vacio_en_ruta'):
            return Response(
                {'error': f'Contenedor en estado {container.estado}; solo se asigna retiro si está vacío o en CCTI.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not driver.esta_disponible:
            return Response(
                {'error': f'Conductor {driver.nombre} no está disponible.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        cd_destino = container.retorno_destino_cd or container.cd_entrega
        if not cd_destino:
            return Response(
                {'error': 'Contenedor no tiene CD de retorno configurado.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # Reusar programación existente si la hay; si no, crear nueva.
        programacion = getattr(container, 'programacion', None)
        if programacion is None:
            programacion = Programacion.objects.create(
                container=container,
                cd=cd_destino,
                cliente=container.cliente or 'RETIRO VACIO',
                fecha_programada=timezone.now() + timedelta(minutes=15),
                direccion_entrega=cd_destino.direccion,
                urgencia_servicio='NORMAL',
                observaciones='Retiro de vacío asignado por operador.',
            )
        try:
            programacion.asignar_conductor(
                driver,
                usuario=request.user.username if request.user.is_authenticated else 'operador',
            )
        except Exception as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(programacion)
        return Response({
            'success': True,
            'mensaje': f'Conductor {driver.nombre} asignado al retiro.',
            'programacion': serializer.data,
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'], url_path='eta-stream/')
    def eta_stream(self, request, pk=None):
        """P2-1: SSE liviano para propagar eta_recalculado_min en tiempo (casi) real.

        StreamingHttpResponse con content_type='text/event-stream'. No usa
        Channels/ASGI ni WebSocket: solo polling liviano a la BD (1 Hz) que
        emite un evento SSE cuando cambia el eta_recalculado_min o el estado
        del contenedor. Timeout 30s para no bloquear workers; el cliente
        debe reconectar (EventSource lo hace automáticamente).

        Riesgo evaluado:
        - NO requiere cambiar el server (render.yaml sigue siendo WSGI).
        - NO requiere Channels/Redis.
        - Cierra el ciclo de E3 sin polling agresivo del frontend.

        Si en el futuro se quiere tiempo real estricto (<1s), migrar a
        Channels/ASGI; ese cambio queda fuera de este pase por costo de
        infraestructura (ver P2-1 nota en plan).
        """
        import time
        from django.http import StreamingHttpResponse
        programacion = self.get_object()
        programacion_id = programacion.pk

        def _stream():
            last_eta = None
            last_estado = None
            start = time.time()
            max_duration = 30  # segundos por conexión
            poll_interval = 1.0
            try:
                while time.time() - start < max_duration:
                    try:
                        prog = Programacion.objects.only(
                            'eta_recalculado_min', 'estado',
                        ).select_related('container').get(pk=programacion_id)
                        estado_actual = prog.container.estado if prog.container else 'sin_contenedor'
                        eta_actual = prog.eta_recalculado_min
                        if eta_actual != last_eta or estado_actual != last_estado:
                            import json
                            payload = json.dumps({
                                'eta_recalculado_min': eta_actual,
                                'estado': estado_actual,
                                'timestamp': timezone.now().isoformat(),
                            })
                            yield f'data: {payload}\n\n'
                            last_eta = eta_actual
                            last_estado = estado_actual
                    except Programacion.DoesNotExist:
                        yield 'event: close\ndata: {"reason":"programacion_deleted"}\n\n'
                        break
                    # Comentario SSE para mantener conexión viva
                    yield ': keepalive\n\n'
                    time.sleep(poll_interval)
                # Cierre ordenado del stream
                yield 'event: close\ndata: {"reason":"timeout"}\n\n'
            except GeneratorExit:
                # Cliente cerró la conexión; salida silenciosa.
                return

        response = StreamingHttpResponse(_stream(), content_type='text/event-stream')
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'  # desactivar buffering en nginx
        return response

    @action(detail=True, methods=['post'])
    def aceptar_asignacion(self, request, pk=None):
        """
        Permite al conductor confirmar que acepta la asignación de un servicio.

        Diferencia clave con reportar_incidente: este endpoint NO cambia
        container.estado. Solo registra la decisión del conductor para
        trazabilidad y dispara una notificación/evento para auditoría.

        Payload: {} (no requiere body; se valida request.user.driver)
        """
        programacion = self.get_object()

        if not programacion.driver_id:
            return Response(
                {'error': 'La programación no tiene conductor asignado.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if container_estado := programacion.container.estado:
            if container_estado not in ('asignado', 'programado'):
                return Response(
                    {'error': f'Contenedor en estado {container_estado}; solo se acepta en estado asignado/programado.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Validación: solo el conductor asignado puede aceptar (o staff).
        if request.user.is_authenticated and not request.user.is_staff:
            try:
                from apps.drivers.models import Driver
                driver_user = Driver.objects.filter(user=request.user).first()
            except Exception:
                driver_user = None
            if not driver_user or driver_user.id != programacion.driver_id:
                return Response(
                    {'error': 'Solo el conductor asignado puede aceptar la asignación.'},
                    status=status.HTTP_403_FORBIDDEN,
                )

        from apps.events.models import Event
        with transaction.atomic():
            locked = Programacion.objects.select_for_update().get(pk=programacion.pk)
            locked.decision_operador = 'CONFIRMAR'
            locked.save(update_fields=['decision_operador', 'updated_at'])
            Event.objects.create(
                container=locked.container,
                event_type='asignacion_conductor',
                detalles={
                    'driver_id': locked.driver_id,
                    'aceptada': True,
                    'decision_operador': 'CONFIRMAR',
                    'reportado_por': request.user.username if request.user.is_authenticated else 'anonimo',
                },
                usuario=request.user.username if request.user.is_authenticated else 'anonimo',
            )

        # Propagar al objeto externo
        programacion.decision_operador = 'CONFIRMAR'

        serializer = self.get_serializer(programacion)
        return Response({
            'success': True,
            'mensaje': 'Asignación aceptada por el conductor.',
            'programacion': serializer.data,
            'decision_operador': 'CONFIRMAR',
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def reportar_problema(self, request, pk=None):
        """
        Reporte operativo que NO cambia container.estado (a diferencia de
        reportar_incidente que escala a estado 'incidente').

        Casos de uso: guía faltante al arribo, dirección incorrecta,
        cliente cerrado, problema administrativo u otro que requiere
        acción del operador pero NO bloquea el flujo del contenedor.

        Payload:
        {
            "tipo": "FALTA_GUIA" | "DIRECCION_INCORRECTA" | "CLIENTE_CERRADO"
                    | "PROBLEMA_ADMINISTRATIVO" | "OTRO",
            "descripcion": "Detalle del problema (obligatorio)",
            "lat": -33.43,  // opcional
            "lng": -70.65   // opcional
        }
        """
        programacion = self.get_object()

        tipos_validos = [
            'FALTA_GUIA', 'DIRECCION_INCORRECTA', 'CLIENTE_CERRADO',
            'PROBLEMA_ADMINISTRATIVO', 'OTRO',
        ]
        tipo = request.data.get('tipo')
        descripcion = (request.data.get('descripcion') or '').strip()

        if not tipo or tipo not in tipos_validos:
            return Response(
                {'error': f'tipo inválido. Permitidos: {", ".join(tipos_validos)}'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not descripcion:
            return Response(
                {'error': 'descripcion es obligatoria.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not self._usuario_puede_operar_viaje(request, programacion):
            return Response(
                {'error': 'No puede reportar problemas sobre un viaje ajeno.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        problema_data = {
            'tipo': tipo,
            'descripcion': descripcion,
            'timestamp': timezone.now().isoformat(),
            'reportado_por': request.user.username if request.user.is_authenticated else 'anonimo',
        }
        lat = request.data.get('lat')
        lng = request.data.get('lng')
        if lat and lng:
            problema_data['gps_lat'] = str(lat)
            problema_data['gps_lng'] = str(lng)

        usuario = request.user.username if request.user.is_authenticated else 'anonimo'
        # Append atómico sobre JSONField bajo lock (paridad con reportar_incidente)
        from apps.events.models import Event
        with transaction.atomic():
            locked = Programacion.objects.select_for_update().get(pk=programacion.pk)
            lista_actual = locked.incidentes_registrados or []
            # Marca diferencia: tipo_problema distinto de tipo_incidente
            problema_data['es_problema'] = True
            lista_actual.append(problema_data)
            locked.incidentes_registrados = lista_actual
            locked.save(update_fields=['incidentes_registrados'])
            programacion.incidentes_registrados = lista_actual

            Event.objects.create(
                container=locked.container,
                event_type='reporte_problema',
                detalles=problema_data,
                usuario=usuario,
            )

            # Notificación alta para el operador (no cambia estado del contenedor)
            from apps.notifications.models import Notification
            Notification.objects.create(
                container=locked.container,
                programacion=locked,
                tipo='problema_reportado',
                prioridad='alta',
                titulo=f'Problema reportado - {locked.container.container_id}',
                mensaje=(
                    f'{tipo}: {descripcion}'
                    + (f' · CD {locked.cd.nombre}' if locked.cd else '')
                ),
                detalles={
                    'tipo_problema': tipo,
                    'descripcion': descripcion,
                    'cd': locked.cd.nombre if locked.cd else None,
                    'cliente': locked.cliente,
                    'conductor': locked.driver.nombre if locked.driver else None,
                    'es_problema': True,
                },
            )

        serializer = self.get_serializer(programacion)
        return Response({
            'success': True,
            'mensaje': 'Problema reportado. Operador notificado.',
            'problema': problema_data,
            'programacion': serializer.data,
        }, status=status.HTTP_201_CREATED)

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
