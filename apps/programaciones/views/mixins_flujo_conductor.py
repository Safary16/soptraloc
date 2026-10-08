"""mixins_flujo_conductor — iteración 10 (partir views.py por dominios).
Flujo del conductor en viaje: ruta, avances, arribos, incidents, drop, tracking y descarga.
Extraído de apps/programaciones/views.py (ProgramacionViewSet) sin cambios de comportamiento.
"""
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db import transaction
from django.utils import timezone
import logging

from ..models import Programacion


logger = logging.getLogger(__name__)



class FlujoConductorMixin:
    """Flujo del conductor en viaje: ruta, avances, arribos, incidents, drop, tracking y descarga."""

    @action(detail=True, methods=['post'], permission_classes=[AllowAny])
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
        programacion = self.get_object()

        from apps.core.services.operations import OperationalFlowService
        resultado = OperationalFlowService.iniciar_ruta_con_eta(
            programacion,
            patente=request.data.get('patente') or '',
            lat=request.data.get('lat'),
            lng=request.data.get('lng'),
            usuario=request.user.username if request.user.is_authenticated else None,
        )
        if not resultado['ok']:
            payload = {'error': resultado['error']}
            for k in ('patente_esperada', 'patente_ingresada', 'success'):
                if k in resultado:
                    payload[k] = resultado[k]
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)

        if resultado.get('idempotente'):
            serializer = self.get_serializer(resultado['programacion'])
            return Response({
                'success': True,
                'mensaje': 'La ruta ya fue iniciada previamente (respuesta idempotente).',
                'idempotente': True,
                'programacion': serializer.data,
            })

        serializer = self.get_serializer(resultado['programacion'])
        response_data = {
            'success': True,
            'mensaje': f'Ruta iniciada por conductor {resultado["programacion"].driver.nombre} con patente {resultado["patente_confirmada"]}',
            'programacion': serializer.data,
            'patente_confirmada': resultado['patente_confirmada'],
            'gps_registrado': resultado['gps'],
        }

        if resultado['notificacion_data']:
            response_data['notificacion'] = resultado['notificacion_data']

        return Response(response_data)


    @action(detail=True, methods=['post'], permission_classes=[AllowAny])
    def reportar_avance(self, request, pk=None):
        """
        SIMULADOR GPS REAL (Seba 04-oct-2026): persiste la ruta real (OSRM) y el
        ETA recalculado de una programación en ruta, para que el operador y los
        subagentes tomen decisiones con datos vivos (si hay atraso: pivotar a otro
        conductor o solicitar holgura al cliente).

        Payload (parcial opcional):
        {
          "ruta_geojson": {"type":"LineString","coordinates":[[lng,lat],...]} o Feature,
          "eta_recalculado_min": 42.5,
          "posicion_actual_lat": -33.4569,
          "posicion_actual_lng": -70.6483,
          "distancia_km": 12.3
        }
        """
        programacion = self.get_object()
        with transaction.atomic():
            locked = Programacion.objects.select_for_update().get(pk=programacion.pk)
            geo = request.data.get('ruta_geojson')
            if geo is not None:
                # Acepta Feature con geometry LineString, o LineString directo.
                # OJO (bug 04-oct): un Feature NO tiene 'coordinates' a nivel raíz,
                # vive en geo['geometry']['coordinates']; el check anterior lo
                # descartaba silenciosamente pese a responder success:true.
                if isinstance(geo, dict) and geo.get('type') == 'Feature' \
                        and isinstance(geo.get('geometry'), dict) \
                        and geo['geometry'].get('type') == 'LineString' \
                        and geo['geometry'].get('coordinates'):
                    locked.ruta_geojson = geo
                elif isinstance(geo, dict) and geo.get('type') == 'LineString' and geo.get('coordinates'):
                    locked.ruta_geojson = {
                        'type': 'Feature',
                        'properties': {'source': 'osrm', 'simulador': True},
                        'geometry': geo,
                    }
            eta = request.data.get('eta_recalculado_min')
            if eta is not None:
                locked.eta_recalculado_min = float(eta)
                locked.eta_minutos = int(float(eta))
            plat = request.data.get('posicion_actual_lat')
            plng = request.data.get('posicion_actual_lng')
            updated = ['updated_at']
            if plat is not None and plng is not None:
                locked.posicion_actual_lat = plat
                locked.posicion_actual_lng = plng
                locked.ultima_actualizacion_tracking = timezone.now()
                updated += ['posicion_actual_lat', 'posicion_actual_lng', 'ultima_actualizacion_tracking']
            dkm = request.data.get('distancia_km')
            if dkm is not None:
                locked.distancia_km = float(dkm)
                updated.append('distancia_km')
            if (request.data.get('ruta_geojson') is not None) or (eta is not None) or (plat is not None):
                updated.append('ruta_geojson' if request.data.get('ruta_geojson') is not None else 'eta_recalculado_min')
                locked.save(update_fields=list(set(updated)))
        return Response({
            'success': True,
            'mensaje': 'Avance registrado',
            'eta_recalculado_min': locked.eta_recalculado_min,
            'tiene_ruta': bool(locked.ruta_geojson),
        })


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

        from apps.core.services.operations import OperationalFlowService
        resultado = OperationalFlowService.soltar_contenedor_drop(
            programacion,
            lat=request.data.get('lat'),
            lng=request.data.get('lng'),
            usuario=request.user.username if request.user.is_authenticated else None,
        )

        if not resultado['ok']:
            return Response(
                {'error': resultado['error']},
                status=status.HTTP_400_BAD_REQUEST
            )

        prog = resultado['programacion']
        created = resultado['created']
        retorno = resultado['retorno_programacion']

        self._update_registro_operacion_on_completion(prog, 'ENTREGADO')

        serializer = self.get_serializer(prog)
        return Response({
            'success': True,
            'mensaje': f'Contenedor soltado en {prog.cd.nombre}. Conductor libre para nueva asignación.',
            'programacion': serializer.data,
            'nuevo_estado': 'soltado',
            'conductor_liberado': True,
            'ya_registrado': not created,
            'retorno_automatico': retorno.id if retorno is not None else None,
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
        
        from apps.core.services.operations import OperationalFlowService
        resultado = OperationalFlowService.actualizar_posicion_gps(
            programacion,
            lat=request.data.get('lat'),
            lng=request.data.get('lng'),
            usuario=request.user.username if request.user.is_authenticated else None,
            eta_delay_threshold=int(request.query_params.get('eta_delay_alert_min')) if request.query_params.get('eta_delay_alert_min') else None,
        )

        if not resultado['ok']:
            return Response(
                {'error': resultado['error']},
                status=resultado.get('status_code', status.HTTP_400_BAD_REQUEST)
            )

        if resultado.get('arribo_automatico'):
            return Response({
                'success': True,
                'mensaje': 'Arribo registrado automáticamente por geocerca',
                'arribo_automatico': True,
                'arribo_creado': resultado['arribo_creado'],
                'fecha_arribo_cd': resultado['fecha_arribo_cd'],
                'nuevo_estado': 'entregado',
            })

        res = resultado['resultado']
        response_data = {
            'success': True,
            'mensaje': 'Posición actualizada y ETA recalculado',
            'eta_minutos': res['eta_minutos'],
            'distancia_km': str(res['distancia_km']),
            'eta_timestamp': res['eta_timestamp']
        }

        if res['notificacion']:
            response_data['notificacion'] = {
                'id': res['notificacion'].id,
                'titulo': res['notificacion'].titulo,
                'mensaje': res['notificacion'].mensaje
            }

        return Response(response_data)


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

        from apps.core.services.operations import OperationalFlowService
        resultado = OperationalFlowService.registrar_incidente_viaje(
            programacion,
            tipo_incidente=request.data.get('tipo_incidente'),
            descripcion=(request.data.get('descripcion') or '').strip(),
            gravedad=request.data.get('gravedad', 'MODERADA'),
            lat=request.data.get('lat'),
            lng=request.data.get('lng'),
            usuario=request.user.username if request.user.is_authenticated else None,
        )
        if not resultado['ok']:
            status_code = (status.HTTP_503_SERVICE_UNAVAILABLE
                           if resultado.get('lock_failure')
                           else status.HTTP_400_BAD_REQUEST)
            return Response({'error': resultado['error']}, status=status_code)

        serializer = self.get_serializer(programacion)
        return Response({
            'success': True,
            'mensaje': 'Incidente registrado exitosamente.',
            'incidente': resultado['incidente'],
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

        HAL-9 (decisión creativa): aceptar también el estado 'descargado' como
        no-op idempotente para evitar rechazos por timing cuando el clic del
        conductor llega después de la transición automática del CD. Esto NO rompe
        el FSM: si fecha_inicio_descarga ya está seteada, devolvemos 409 (el
        click original sí se respetó). Pero si el container ya pasó a 'descargado'
        Y fecha_inicio_descarga sigue vacía, lo aceptamos como una corrección
        operativa (caso: el operador del CD cerró la descarga mientras el
        conductor entraba al camión) y devolvemos 200 con un flag
        'fuera_de_secuencia' para que el panel de auditoría lo registre.
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
        # HAL-9: aceptamos 'descargado' cuando el clic llega fuera de secuencia
        # (caso de timing con el cierre del CD). El resto del FSM no se ve
        # afectado: este endpoint sigue SIN transicionar container.estado.
        if programacion.container.estado not in ('entregado', 'soltado', 'descargado'):
            return Response(
                {'error': f'Contenedor debe estar entregado, soltado o descargado. Estado: {programacion.container.get_estado_display()}.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        fuera_de_secuencia = programacion.container.estado == 'descargado'
        if programacion.fecha_inicio_descarga:
            return Response(
                {'error': 'La descarga ya fue marcada como iniciada.', 'fecha_inicio_descarga': programacion.fecha_inicio_descarga.isoformat()},
                status=status.HTTP_409_CONFLICT,
            )

        from apps.core.services.operations import OperationalFlowService
        ahora = OperationalFlowService.registrar_inicio_descarga(
            programacion,
            lat=request.data.get('lat'),
            lng=request.data.get('lng'),
            usuario=request.user.username if request.user.is_authenticated else 'conductor',
            fuera_de_secuencia=fuera_de_secuencia,
        )

        return Response({
            'success': True,
            'mensaje': 'Inicio de descarga registrado.',
            'fecha_inicio_descarga': ahora['fecha_inicio_descarga'].isoformat(),
            'programacion_id': programacion.pk,
            # HAL-9: flag para que la UI/auditoría distinga el flujo normal del
            # caso de timing con el CD.
            'fuera_de_secuencia': ahora['fuera_de_secuencia'],
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

        usuario = request.user.username if request.user.is_authenticated else 'anonimo'
        from apps.core.services.operations import OperationalFlowService
        resultado = OperationalFlowService.reportar_problema_operador(
            programacion,
            tipo=tipo,
            descripcion=descripcion,
            lat=request.data.get('lat'),
            lng=request.data.get('lng'),
            usuario=usuario,
        )

        serializer = self.get_serializer(programacion)
        return Response({
            'success': True,
            'mensaje': 'Problema reportado. Operador notificado.',
            'problema': resultado['problema'],
            'programacion': serializer.data,
        }, status=status.HTTP_201_CREATED)


    @action(detail=True, methods=['post'])
    def escalar_supervisor(self, request, pk=None):
        """Escala la operación a supervisor."""
        programacion = self.get_object()
        motivo = (request.data.get('motivo') or 'Escalado manual por operador').strip()
        programacion.decision_operador = 'ESCALAR'
        programacion.motivo_override = motivo
        programacion.save(update_fields=['decision_operador', 'motivo_override'])
        return Response({'success': True, 'mensaje': 'Caso escalado a supervisor.'})


