"""mixins_rutas_ml — iteración 10 (partir views.py por dominios).
Rutas manuales y recomendaciones ML.
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



class RutasMlMixin:
    """Rutas manuales y recomendaciones ML."""

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def crear_ruta_manual(self, request):
        """
        Crea una ruta manual para retiro desde puerto
        Permite acceso anónimo para operaciones manuales desde el panel.
        
        Casos de uso:
        1. retiro_patio: Patio va a buscar contenedor al puerto y lo lleva a Patio
        2. retiro_directo: Patio va a buscar al puerto y entrega directo a cliente
        
        Payload:
        {
            "container_id": "ABCD1234567",
            "tipo_movimiento": "retiro_patio" | "retiro_directo",
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

        from apps.core.services.operations import OperationalFlowService
        resultado = OperationalFlowService.crear_ruta_manual(
            container,
            tipo_movimiento=tipo_movimiento,
            cd_destino=data.get('_cd_destino'),
            fecha_programacion=data['fecha_programacion'],
            cliente=data.get('cliente', ''),
            observaciones=data.get('observaciones'),
            usuario=request.user.username if request.user.is_authenticated else None,
        )
        if not resultado['ok']:
            payload = {'error': resultado['error']}
            if resultado.get('programacion_existente'):
                payload['programacion_existente'] = resultado['programacion_existente']
            return Response(payload, status=resultado.get('status_code', status.HTTP_400_BAD_REQUEST))

        programacion = resultado['programacion']
        return Response({
            'success': True,
            'mensaje': 'Ruta manual creada exitosamente',
            'programacion': ProgramacionSerializer(programacion).data,
            'tipo_movimiento': tipo_movimiento,
            'origen': container.posicion_fisica,
            'destino': resultado['cd_destino'].nombre
        }, status=status.HTTP_201_CREATED)


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


