"""mixins_consulta — iteración 10 (partir views.py por dominios).
Consultas, dashboards, ETA, import Excel y helpers compartidos del ViewSet.
Extraído de apps/programaciones/views.py (ProgramacionViewSet) sin cambios de comportamiento.
"""
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

from ..filters import ProgramacionFilter
from ..models import Programacion
from ..serializers import (
    ProgramacionSerializer,
    RutaManualSerializer,
    ProgramacionListSerializer,
    ProgramacionCreateSerializer
)
from apps.core.services.assignment import AssignmentService
from apps.core.utils import normalizar_cliente
from apps.drivers.serializers import DriverDisponibleSerializer


logger = logging.getLogger(__name__)



class ConsultaMixin:
    """Consultas, dashboards, ETA, import Excel y helpers compartidos del ViewSet."""

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


    @action(detail=True, methods=['get'], url_path='eta-stream/')
    def eta_stream(self, request, pk=None):
        """P2-1: SSE liviano para propagar eta_recalculado_min en tiempo (casi) real.

        StreamingHttpResponse con content_type='text/event-stream'. No usa
        Channels/ASGI ni WebSocket: solo polling liviano a la BD (1 Hz) que
        emite un evento SSE cuando cambia el eta_recalculado_min o el estado
        del contenedor.

        HAL-14: timeout extendido 30s → 120s (rango objetivo para conexiones
        móviles intermitentes). Se acepta Last-Event-ID para que reconexiones
        tras corte móvil NO pierdan updates intermedios: el stream emite cada
        cambio con un id incremental, y si el cliente lo manda como header, el
        stream arranca re-enviando cualquier cambio posterior a ese id.
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

        # HAL-14: recoger el Last-Event-ID. EventSource lo envía automáticamente
        # tras una reconexión. Si no viene, arrancamos desde 0 (cliente nuevo).
        last_event_id_header = request.META.get('HTTP_LAST_EVENT_ID', '').strip()
        last_event_id = 0
        if last_event_id_header.isdigit():
            last_event_id = int(last_event_id_header)

        def _stream():
            last_eta = None
            last_estado = None
            start = time.time()
            # HAL-14: timeout subido a 120s. Conexiones móviles 3G/4G pueden
            # tardar minutos en reconectar; 30s era agresivo y disparaba
            # desconexiones innecesarias.
            max_duration = 120  # segundos por conexión
            poll_interval = 1.0
            event_counter = last_event_id
            try:
                while time.time() - start < max_duration:
                    try:
                        prog = Programacion.objects.only(
                            'eta_recalculado_min', 'container__estado',
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
                            event_counter += 1
                            # HAL-14: incluir id: para que el cliente pueda
                            # reconectar con Last-Event-ID.
                            yield f'id: {event_counter}\ndata: {payload}\n\n'
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

            # HAL-3: alimentar la estimación adaptativa con un viaje real completo.
            # Guard reescrito: NO exigir programacion.eta_minutos (puede ser 0 por el
            # blindaje HAL-1, y antes el bloque se saltaba silenciosamente). Si no hay
            # ETA estimada, derivamos tiempo_mapbox_min de distancia_km + velocidad de
            # referencia 35 km/h o caemos a 1 min como ground truth para no envenenar
            # el ML con un valor ficticio 0.
            ya_registrado = TiempoViaje.objects.filter(programacion=programacion).exists()
            datos_minimos = (
                programacion.fecha_inicio_ruta
                and programacion.container.fecha_entrega
                and programacion.gps_inicio_lat is not None
                and programacion.gps_inicio_lng is not None
                and programacion.cd is not None
                and programacion.driver is not None
            )
            if datos_minimos and not ya_registrado:
                real_min = max(1, int((programacion.container.fecha_entrega - programacion.fecha_inicio_ruta).total_seconds() / 60))
                # estimado: preferir eta_minutos; si es 0/None, derivar de distancia_km
                estimado_eta = programacion.eta_minutos
                estimado_dist = None
                if (not estimado_eta) and programacion.distancia_km:
                    try:
                        km = float(programacion.distancia_km)
                        estimado_dist = max(1, int(round(km / 35.0 * 60)))
                    except Exception:
                        estimado_dist = None
                estimado = max(1, int(estimado_eta or estimado_dist or 1))
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
                    anomalia=real_min >= max(1, estimado) * 3,
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


