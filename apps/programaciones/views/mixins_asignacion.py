"""mixins_asignacion — iteración 10 (partir views.py por dominios).
Asignación de conductores: manual, automática, múltiples, ML y retiro vacío.
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



class AsignacionMixin:
    """Asignación de conductores: manual, automática, múltiples, ML y retiro vacío."""

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
        
        # Auditoría Flaco 2026-10-02 (revisión safary16): el FSM va PRIMERO.
        # Antes se liberaba al conductor y recién después se intentaba
        # cambiar_estado; si el FSM fallaba (race: el contenedor cambió de
        # estado entre el guard temprano y el lock, o estado corrupto), el 409
        # retornaba con la programación YA sin conductor y el contenedor aún
        # 'asignado' → inconsistencia. Orden correcto: primero el FSM
        # (autoritativo, con select_for_update), y solo si succeede se muta la
        # programación. Así el 409 no necesita revertir nada: nada se tocó.
        # Nota: 'asignado'→'programado' está en TRANSICIONES_VALIDAS y
        # 'programado'→'programado' es no-op, por lo que el 409 solo es
        # alcanzable por race o estado corrupto.
        if container:
            try:
                container.cambiar_estado(
                    'programado',
                    request.user.username if request.user.is_authenticated else 'operador_manual',
                )
            except Exception as _fsm_exc:
                logger.error(
                    'desasignar_fsm_rechazado container_id=%s estado=%s detalle=%s',
                    getattr(container, 'container_id', None),
                    getattr(container, 'estado', None),
                    _fsm_exc,
                )
                return Response(
                    {'error': (
                        'El FSM rechazó la transición del contenedor a programado '
                        f'({getattr(_fsm_exc, "messages", None) or str(_fsm_exc)}). '
                        'La desasignación NO se realizó: el conductor sigue asignado '
                        'y el contenedor conserva su estado. Corrija el estado del '
                        'contenedor por la vía administrativa e intente nuevamente.'
                    )},
                    status=status.HTTP_409_CONFLICT
                )
            else:
                # FSM aplicado correctamente; igualamos fecha_asignacion a None
                # porque ya no hay conductor asignado en la programación.
                # cambiar_estado conserva el timestamp del estado_anterior como
                # referencia histórica; aquí la asignación ya no existe.
                if container.fecha_asignacion is not None:
                    container.fecha_asignacion = None
                    container.save(update_fields=['fecha_asignacion'])

        # FSM OK: recién ahora liberar capacidad del conductor y limpiar la
        # asignación. liberar_conductor() decrementa num_entregas_dia
        # (idempotente vía fecha_liberacion_conductor), así que un reintento
        # tras un fallo parcial aquí es seguro.
        programacion.liberar_conductor()
        programacion.driver = None
        programacion.fecha_asignacion = None
        programacion.save(update_fields=['driver', 'fecha_asignacion'])
        
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
        from apps.core.services.operations import OperationalFlowService

        programacion = self.get_object()
        resultado = OperationalFlowService.calcular_preasignacion_ml(
            programacion,
            driver_id=request.data.get('driver_id'),
            fecha_salida_str=request.data.get('fecha_salida'),
        )
        if not resultado['ok']:
            return Response(
                {'error': resultado['error']},
                status=resultado.get('status_code', status.HTTP_400_BAD_REQUEST),
            )
        return Response(resultado['payload'], status=status.HTTP_201_CREATED)


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
        # Revisión senior (Safari): helper canónico _usuario_puede_operar_viaje
        # para que un request ANÓNIMO sea rechazado (403) — el guard anterior
        # (is_authenticated and not is_staff) dejaba pasar a usuarios no autenticados.
        if not self._usuario_puede_operar_viaje(request, programacion):
            return Response(
                {'error': 'Solo el conductor asignado puede aceptar la asignación.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        from apps.core.services.operations import OperationalFlowService
        resultado = OperationalFlowService.aceptar_asignacion_conductor(
            programacion,
            usuario=request.user.username if request.user.is_authenticated else None,
        )
        if not resultado['ok']:
            return Response(
                {'error': resultado['error']},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(programacion)
        return Response({
            'success': True,
            'mensaje': 'Asignación aceptada por el conductor.',
            'programacion': serializer.data,
            'decision_operador': 'CONFIRMAR',
        }, status=status.HTTP_200_OK)


    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def asignar_conductor_retiro_vacio(self, request):
        """P1-2: asigna un conductor a un retiro de vacío.

        Crea Programacion de retiro si no existe, usa destino del retorno
        (Container.retorno_destino_cd o Container.cd_entrega) y notifica al
        conductor.

        Payload:
        {
            "container_id": int,   // contenedor en estado 'vacio' o 'en_patio'
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
        if container.estado not in ('vacio', 'en_patio', 'vacio_en_ruta'):
            return Response(
                {'error': f'Contenedor en estado {container.estado}; solo se asigna retiro si está vacío o en Patio.'},
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
        elif programacion.driver_id and programacion.fecha_liberacion_conductor:
            # HAL-24: reuso de programación histórica del viaje lleno — el FK
            # driver queda seteado tras el drop (liberar_conductor no limpia el
            # FK, solo fecha_liberacion_conductor y el contador). Chequear
            # idempotencia ANTES de resetear: si la liberación ya ocurrió,
            # el conductor fue descontado y es seguro liberar el FK para
            # reasignar; si NO ocurrió, es un servicio activo → 400 real.
            programacion.driver = None
            programacion.save(update_fields=['driver', 'updated_at'])
        elif programacion.driver_id:
            return Response(
                {'error': 'La programación ya tiene conductor asignado (servicio activo).'},
                status=status.HTTP_400_BAD_REQUEST,
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


