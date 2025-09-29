from django.db.models import Count, Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib import messages

from apps.core.models import MovementCode
from .models import Container, ContainerDocument, ContainerInspection, ContainerMovement
from .serializers import (
    ContainerCreateUpdateSerializer,
    ContainerDocumentCreateSerializer,
    ContainerDocumentSerializer,
    ContainerInspectionCreateSerializer,
    ContainerInspectionSerializer,
    ContainerMovementCreateSerializer,
    ContainerMovementSerializer,
    ContainerSerializer,
    ContainerSummarySerializer,
)
from apps.drivers.models import Driver, Assignment
import json


class ContainerViewSet(viewsets.ModelViewSet):
    queryset = Container.objects.filter(is_active=True).select_related(
        'owner_company', 'current_location', 'current_vehicle'
    )
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = [
        'container_type', 'status', 'position_status', 'owner_company', 
        'current_location', 'is_active'
    ]
    search_fields = ['container_number', 'seal_number', 'customs_document']
    ordering_fields = ['container_number', 'created_at', 'updated_at']
    ordering = ['container_number']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ContainerCreateUpdateSerializer
        elif self.action == 'list':
            return ContainerSummarySerializer
        return ContainerSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Resumen estadístico de contenedores."""
        total = self.queryset.count()
        by_status = self.queryset.values('status').annotate(count=Count('id'))
        by_position = self.queryset.values('position_status').annotate(count=Count('id'))
        by_type = self.queryset.values('container_type').annotate(count=Count('id'))
        
        return Response({
            'total': total,
            'by_status': list(by_status),
            'by_position': list(by_position),
            'by_type': list(by_type)
        })

    @action(detail=False, methods=['get'])
    def available(self, request):
        """Obtiene contenedores disponibles."""
        available_containers = self.queryset.filter(status='available')
        serializer = self.get_serializer(available_containers, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def on_chassis(self, request):
        """Obtiene contenedores en chasis."""
        on_chassis = self.queryset.filter(position_status='chassis')
        serializer = self.get_serializer(on_chassis, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def on_floor(self, request):
        """Obtiene contenedores en piso."""
        on_floor = self.queryset.filter(position_status='floor')
        serializer = self.get_serializer(on_floor, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def movements(self, request, pk=None):
        """Obtiene el historial de movimientos de un contenedor."""
        container = self.get_object()
        movements = container.movements.all()
        serializer = ContainerMovementSerializer(movements, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def documents(self, request, pk=None):
        """Obtiene los documentos de un contenedor."""
        container = self.get_object()
        documents = container.documents.all()
        serializer = ContainerDocumentSerializer(documents, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def inspections(self, request, pk=None):
        """Obtiene las inspecciones de un contenedor."""
        container = self.get_object()
        inspections = container.inspections.all()
        serializer = ContainerInspectionSerializer(inspections, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['patch'])
    def change_status(self, request, pk=None):
        """Cambia el estado de un contenedor."""
        container = self.get_object()
        new_status = request.data.get('status')
        
        if new_status not in dict(Container.CONTAINER_STATUS):
            return Response(
                {'error': 'Estado no válido'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        container.status = new_status
        container.updated_by = request.user
        container.save()
        
        serializer = self.get_serializer(container)
        return Response(serializer.data)


class ContainerMovementViewSet(viewsets.ModelViewSet):
    queryset = ContainerMovement.objects.all().select_related(
        'container', 'movement_code', 'from_location', 'to_location',
        'from_vehicle', 'to_vehicle'
    )
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = [
        'container', 'movement_type', 'from_location', 'to_location',
        'from_vehicle', 'to_vehicle', 'movement_date'
    ]
    search_fields = ['container__container_number', 'movement_code__code', 'notes']
    ordering_fields = ['movement_date', 'created_at']
    ordering = ['-movement_date']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ContainerMovementCreateSerializer
        return ContainerMovementSerializer

    def perform_create(self, serializer):
        # Generar código de movimiento si no se proporciona
        if not serializer.validated_data.get('movement_code'):
            movement_type = serializer.validated_data['movement_type']
            code_type = {
                'load_chassis': 'load',
                'unload_chassis': 'unload',
            }.get(movement_type, 'transfer')
            
            movement_code = MovementCode.generate_code(code_type)
            movement_code.created_by = self.request.user
            movement_code.save()
            serializer.validated_data['movement_code'] = movement_code
        
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Obtiene los movimientos más recientes."""
        recent_movements = self.queryset[:20]
        serializer = self.get_serializer(recent_movements, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_container(self, request):
        """Obtiene movimientos filtrados por contenedor."""
        container_number = request.query_params.get('container_number')
        if not container_number:
            return Response(
                {'error': 'Se requiere el parámetro container_number'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        movements = self.queryset.filter(
            container__container_number__icontains=container_number
        )
        serializer = self.get_serializer(movements, many=True)
        return Response(serializer.data)


class ContainerDocumentViewSet(viewsets.ModelViewSet):
    queryset = ContainerDocument.objects.all().select_related('container')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['container', 'document_type', 'document_date']
    search_fields = ['container__container_number', 'document_number', 'description']
    ordering_fields = ['document_date', 'created_at']
    ordering = ['-document_date']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ContainerDocumentCreateSerializer
        return ContainerDocumentSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)


class ContainerInspectionViewSet(viewsets.ModelViewSet):
    queryset = ContainerInspection.objects.all().select_related('container')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = [
        'container', 'inspection_type', 'overall_condition', 
        'repair_required', 'inspection_date'
    ]
    search_fields = ['container__container_number', 'inspector_name', 'observations']
    ordering_fields = ['inspection_date', 'created_at']
    ordering = ['-inspection_date']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ContainerInspectionCreateSerializer
        return ContainerInspectionSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    @action(detail=False, methods=['get'])
    def requiring_repair(self, request):
        """Obtiene inspecciones que requieren reparación."""
        requiring_repair = self.queryset.filter(repair_required=True)
        serializer = self.get_serializer(requiring_repair, many=True)
        return Response(serializer.data)


# Vistas adicionales para gestión de contenedores
@login_required
def container_detail(request, container_id):
    """Vista de detalle del contenedor"""
    container = get_object_or_404(Container, id=container_id)
    
    context = {
        'container': container,
        'today': timezone.now().date(),
        'tomorrow': timezone.now().date() + timezone.timedelta(days=1),
    }
    
    return render(request, 'containers/container_detail.html', context)


@login_required
def update_position(request):
    """Actualizar la posición de un contenedor"""
    if request.method == 'POST':
        try:
            container_id = request.POST.get('container_id')
            new_position = request.POST.get('position')
            
            container = get_object_or_404(Container, id=container_id)
            
            # Actualizar posición
            container.current_position = new_position
            container.position_updated_at = timezone.now()
            container.position_updated_by = request.user
            
            # Si se mueve a CD, actualizar también el estado
            if new_position.startswith('CD_'):
                container.status = 'EN_TRANSITO'
                if not container.cd_arrival_date:
                    container.cd_arrival_date = timezone.now().date()
                    container.cd_arrival_time = timezone.now().time()
            elif new_position == 'DEPOSITO_DEVOLUCION':
                container.status = 'COMPLETADO'
                if not container.return_date:
                    container.return_date = timezone.now().date()
            elif new_position == 'EN_RUTA':
                container.status = 'EN_TRANSITO'
            
            container.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Posición actualizada a {new_position}',
                'new_position': container.get_current_position_display() if hasattr(container, 'get_current_position_display') else new_position
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al actualizar posición: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'})


@login_required
def update_status(request):
    """Actualizar el estado del contenedor (inicio de ruta, arribo, etc.)"""
    if request.method == 'POST':
        try:
            container_id = request.POST.get('container_id')
            action = request.POST.get('action')
            
            container = get_object_or_404(Container, id=container_id)
            
            if action == 'start_route':
                # Iniciar ruta
                if container.status == 'ASIGNADO' and container.conductor_asignado:
                    container.status = 'EN_RUTA'
                    container.position_updated_at = timezone.now()
                    container.position_updated_by = request.user
                    
                    # Actualizar asignación
                    assignment = Assignment.objects.filter(
                        container=container,
                        driver=container.conductor_asignado,
                        estado='PENDIENTE'
                    ).first()
                    
                    if assignment:
                        assignment.estado = 'EN_CURSO'
                        assignment.fecha_inicio = timezone.now()
                        assignment.save()
                    
                    container.save()
                    
                    return JsonResponse({
                        'success': True,
                        'message': f'Ruta iniciada para contenedor {container.container_number}'
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'message': 'El contenedor debe estar asignado a un conductor'
                    })
                    
            elif action == 'mark_arrived':
                # Marcar arribado
                arrival_location = request.POST.get('arrival_location')
                
                if container.status == 'EN_RUTA':
                    container.status = 'ARRIBADO'
                    container.current_position = arrival_location
                    container.position_updated_at = timezone.now()
                    container.position_updated_by = request.user
                    
                    # Registrar arribo en CD si aplica
                    if arrival_location.startswith('CD_'):
                        container.cd_arrival_date = timezone.now().date()
                        container.cd_arrival_time = timezone.now().time()
                        
                        # Determinar CD location basado en la selección
                        cd_mapping = {
                            'CD_QUILICURA': 'CD Quilicura',
                            'CD_PENON': 'CD El Peñón', 
                            'CD_MADERO': 'CD Puerto Madero',
                            'CD_CAMPOS': 'CD Campos'
                        }
                        container.cd_location = cd_mapping.get(arrival_location, container.cd_location)
                    
                    # Actualizar asignación
                    assignment = Assignment.objects.filter(
                        container=container,
                        driver=container.conductor_asignado,
                        estado='EN_CURSO'
                    ).first()
                    
                    if assignment:
                        assignment.estado = 'COMPLETADA'
                        assignment.fecha_completada = timezone.now()
                        assignment.save()
                    
                    container.save()
                    
                    return JsonResponse({
                        'success': True,
                        'message': f'Arribo registrado en {arrival_location.replace("_", " ")}'
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'message': 'El contenedor debe estar en ruta'
                    })
            
            return JsonResponse({
                'success': False,
                'message': 'Acción no válida'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al actualizar estado: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'})


@login_required
def assign_driver_quick(request):
    """Asignación rápida de conductor desde alertas o dashboard"""
    if request.method == 'POST':
        try:
            container_id = request.POST.get('container_id')
            driver_id = request.POST.get('driver_id')
            
            container = get_object_or_404(Container, id=container_id)
            driver = get_object_or_404(Driver, id=driver_id)
            
            # Verificar disponibilidad del conductor
            if container.scheduled_date and container.scheduled_time:
                scheduled_datetime = timezone.datetime.combine(
                    container.scheduled_date, 
                    container.scheduled_time
                ).replace(tzinfo=timezone.get_current_timezone())
                
                # Verificar conflictos de horario
                existing_assignments = Assignment.objects.filter(
                    driver=driver,
                    fecha_programada__date=scheduled_datetime.date(),
                    estado__in=['PENDIENTE', 'EN_CURSO']
                )
                
                if existing_assignments.exists():
                    return JsonResponse({
                        'success': False,
                        'message': f'El conductor {driver.nombre} ya tiene asignaciones en esa fecha/hora'
                    })
            else:
                scheduled_datetime = timezone.now()
            
            # Crear asignación
            assignment = Assignment.objects.create(
                container=container,
                driver=driver,
                fecha_programada=scheduled_datetime,
                origen_legacy=container.terminal.name if container.terminal else 'Terminal',
                destino_legacy=container.cd_location or 'CD',
                created_by=request.user
            )
            
            # Calcular tiempo estimado
            assignment.calculate_estimated_time()
            assignment.save()
            
            # Actualizar estado del contenedor con tiempo de asignación
            container.status = 'ASIGNADO'  # Cambiar a ASIGNADO en lugar de EN_PROCESO
            container.conductor_asignado = driver
            container.tiempo_asignacion = timezone.now()  # Registrar tiempo de asignación
            container.save()
            
            # Actualizar conductor
            driver.contenedor_asignado = container
            driver.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Conductor {driver.nombre} asignado exitosamente'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al asignar conductor: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'})


@login_required
def update_container_status_view(request, container_id):
    """Vista para actualizar el estado de un contenedor"""
    if request.method == 'POST':
        try:
            container = get_object_or_404(Container, id=container_id)
            data = json.loads(request.body)
            new_status = data.get('status')
            
            if not new_status:
                return JsonResponse({'success': False, 'message': 'Estado requerido'})
            
            # Validar estados permitidos
            valid_statuses = [choice[0] for choice in Container.CONTAINER_STATUS]
            if new_status not in valid_statuses:
                return JsonResponse({'success': False, 'message': 'Estado no válido'})
            
            # Actualizar estado con tiempos
            old_status = container.status
            container.status = new_status
            now = timezone.now()
            
            # Registrar tiempo según el nuevo estado
            if new_status == 'ASIGNADO' and not container.tiempo_asignacion:
                container.tiempo_asignacion = now
            elif new_status == 'EN_RUTA':
                if not container.tiempo_inicio_ruta:
                    container.tiempo_inicio_ruta = now
                    # Calcular duración desde asignación
                    if container.tiempo_asignacion:
                        delta = now - container.tiempo_asignacion
                        container.duracion_ruta = int(delta.total_seconds() / 60)
            elif new_status == 'ARRIBADO':
                if not container.tiempo_llegada:
                    container.tiempo_llegada = now
                    # Calcular duración de ruta
                    if container.tiempo_inicio_ruta:
                        delta = now - container.tiempo_inicio_ruta
                        container.duracion_ruta = int(delta.total_seconds() / 60)
            elif new_status == 'FINALIZADO':
                if not container.tiempo_finalizacion:
                    container.tiempo_finalizacion = now
                    # Calcular duración de descarga
                    if container.tiempo_llegada:
                        delta = now - container.tiempo_llegada
                        container.duracion_descarga = int(delta.total_seconds() / 60)
                    # Calcular duración total
                    if container.tiempo_asignacion:
                        delta_total = now - container.tiempo_asignacion
                        container.duracion_total = int(delta_total.total_seconds() / 60)
            
            container.save()
            
            # Registrar el movimiento
            ContainerMovement.objects.create(
                container=container,
                movement_type='status_change',
                origin_location=container.current_location,
                destination_location=container.current_location,
                movement_date=timezone.now(),
                notes=f'Estado cambiado de {old_status} a {new_status}',
                created_by=request.user
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Estado actualizado a {container.get_status_display()}'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al actualizar estado: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'})


@login_required
def update_container_position_view(request, container_id):
    """Vista para actualizar la posición de un contenedor"""
    if request.method == 'POST':
        try:
            container = get_object_or_404(Container, id=container_id)
            data = json.loads(request.body)
            new_position = data.get('position')
            
            if not new_position:
                return JsonResponse({'success': False, 'message': 'Posición requerida'})
            
            # Validar posiciones permitidas
            valid_positions = [choice[0] for choice in Container.POSITION_STATUS] + [
                'CCTI', 'ZEAL', 'CLEP', 'CD_QUILICURA', 'CD_CAMPOS', 
                'CD_MADERO', 'CD_PENON', 'EN_RUTA', 'DEPOSITO_DEVOLUCION'
            ]
            
            if new_position not in valid_positions:
                return JsonResponse({'success': False, 'message': 'Posición no válida'})
            
            # Actualizar posición
            old_position = container.current_position
            container.current_position = new_position
            container.position_updated_at = timezone.now()
            container.position_updated_by = request.user
            container.save()
            
            # Registrar el movimiento
            ContainerMovement.objects.create(
                container=container,
                movement_type='position_update',
                origin_location=container.current_location,
                movement_date=timezone.now(),
                notes=f'Posición actualizada de {old_position or "No definida"} a {new_position}',
                created_by=request.user
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Posición actualizada exitosamente'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al actualizar posición: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'})


@login_required
def container_detail_uuid(request, container_id):
    """Vista de detalles del contenedor usando UUID"""
    container = get_object_or_404(Container, id=container_id)
    
    if request.headers.get('Accept') == 'application/json':
        # Respuesta JSON para AJAX
        data = {
            'id': str(container.id),
            'container_number': container.container_number,
            'container_type': container.container_type,
            'container_type_display': container.get_container_type_display() if container.container_type else None,
            'status': container.status,
            'status_display': container.get_status_display(),
            'seal_number': container.seal_number,
            'client': {
                'id': container.client.id if container.client else None,
                'name': container.client.name if container.client else None,
            } if container.client else None,
            'conductor_asignado': {
                'id': container.conductor_asignado.id if container.conductor_asignado else None,
                'nombre': container.conductor_asignado.nombre if container.conductor_asignado else None,
                'ppu': container.conductor_asignado.ppu if container.conductor_asignado else None,
            } if container.conductor_asignado else None,
            
            # Fechas
            'scheduled_date': container.scheduled_date.isoformat() if container.scheduled_date else None,
            'scheduled_time': container.scheduled_time.isoformat() if container.scheduled_time else None,
            'eta': container.eta.isoformat() if container.eta else None,
            'release_date': container.release_date.isoformat() if container.release_date else None,
            'release_time': container.release_time.isoformat() if container.release_time else None,
            'cd_arrival_date': container.cd_arrival_date.isoformat() if container.cd_arrival_date else None,
            'cd_arrival_time': container.cd_arrival_time.isoformat() if container.cd_arrival_time else None,
            
            # Pesos
            'weight_empty': float(container.weight_empty) if container.weight_empty else None,
            'cargo_weight': float(container.cargo_weight) if container.cargo_weight else None,
            'total_weight': float(container.total_weight) if container.total_weight else None,
            'max_weight': float(container.max_weight) if container.max_weight else None,
            
            # Información marítima
            'vessel': {
                'name': container.vessel.name if container.vessel else None,
            } if container.vessel else None,
            'shipping_line': {
                'name': container.shipping_line.name if container.shipping_line else None,
            } if container.shipping_line else None,
            'agency': {
                'name': container.agency.name if container.agency else None,
            } if container.agency else None,
            'terminal': {
                'name': container.terminal.name if container.terminal else None,
            } if container.terminal else None,
            
            # Ubicación
            'current_position': container.current_position,
            'cd_location': container.cd_location,
            
            # Descripción y observaciones
            'cargo_description': container.cargo_description,
            'observation_1': container.observation_1,
            'observation_2': container.observation_2,
            
            # Tiempos operativos
            'tiempo_asignacion': container.tiempo_asignacion.strftime('%d/%m/%Y %H:%M') if container.tiempo_asignacion else None,
            'tiempo_inicio_ruta': container.tiempo_inicio_ruta.strftime('%d/%m/%Y %H:%M') if container.tiempo_inicio_ruta else None,
            'tiempo_llegada': container.tiempo_llegada.strftime('%d/%m/%Y %H:%M') if container.tiempo_llegada else None,
            'tiempo_descarga': container.tiempo_descarga.strftime('%d/%m/%Y %H:%M') if container.tiempo_descarga else None,
            'tiempo_finalizacion': container.tiempo_finalizacion.strftime('%d/%m/%Y %H:%M') if container.tiempo_finalizacion else None,
            
            # Duraciones
            'duracion_total': container.duracion_total,
            'duracion_ruta': container.duracion_ruta,
            'duracion_descarga': container.duracion_descarga,
        }
        return JsonResponse(data)
    
    # Si no es JSON, redirigir a la vista de resueltos
    from django.shortcuts import redirect
    return redirect('resueltos')