from rest_framework import serializers
from .models import Container, ContainerMovement, ContainerDocument, ContainerInspection
from apps.core.serializers import CompanySerializer, VehicleSerializer, MovementCodeSerializer
from apps.drivers.serializers import LocationSerializer


class ContainerSerializer(serializers.ModelSerializer):
    owner_company = CompanySerializer(read_only=True)
    current_location = LocationSerializer(read_only=True)
    current_vehicle = VehicleSerializer(read_only=True)
    container_type_display = serializers.CharField(source='get_container_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    position_status_display = serializers.CharField(source='get_position_status_display', read_only=True)
    current_position = serializers.CharField(source='get_current_position', read_only=True)

    class Meta:
        model = Container
        # FASE 5: Campos explícitos (antes: fields='__all__' - VULNERABILIDAD DE SEGURIDAD)
        fields = [
            'id', 'container_number', 'container_type', 'container_type_display',
            'status', 'status_display', 'position_status', 'position_status_display',
            'current_position', 'current_position_code',
            'owner_company', 'client_company', 'vendor_company',
            'current_location', 'current_vehicle',
            'vessel', 'agency', 'shipping_line',
            'booking_number', 'bl_number', 'manifest_number',
            'liberation_date', 'programmed_date', 'scheduled_date', 'scheduled_hour',
            'service_type', 'movement_type',
            'origin_port', 'destination_port',
            'seal_number', 'tare_weight', 'cargo_weight', 'total_weight',
            'commodity_description',
            'created_at', 'updated_at', 'created_by', 'updated_by'
        ]
        read_only_fields = ('id', 'created_at', 'updated_at', 'created_by', 'updated_by')


class ContainerCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para crear y actualizar contenedores sin datos anidados."""
    
    class Meta:
        model = Container
        fields = [
            'additional_service',
            'agency',
            'calculated_days',
            'cargo_description',
            'cargo_weight',
            'cd_arrival_date',
            'cd_arrival_time',
            'cd_location',
            'chassis_status',
            'client',
            'conductor_asignado',
            'container_number',
            'container_type',
            'created_at',
            'created_by',
            'current_location',
            'current_position',
            'current_vehicle',
            'customs_document',
            'demurrage_date',
            'deposit_return',
            'direct_service',
            'discharge_date',
            'discharge_time',
            'duracion_descarga',
            'duracion_devolucion',
            'duracion_ruta',
            'duracion_total',
            'eta',
            'extra_storage_days',
            'free_days',
            'has_eir',
            'id',
            'is_active',
            'last_update_date',
            'last_update_time',
            'max_weight',
            'observation_1',
            'observation_2',
            'overtime_2h',
            'overtime_4h',
            'owner_company',
            'port',
            'position_status',
            'position_updated_at',
            'position_updated_by',
            'release_date',
            'release_time',
            'return_date',
            'scheduled_date',
            'scheduled_time',
            'seal_number',
            'sequence_id',
            'service_type',
            'shipping_line',
            'special_requirements',
            'status',
            'storage_location',
            'terminal',
            'tiempo_arribo_devolucion',
            'tiempo_asignacion',
            'tiempo_descarga',
            'tiempo_finalizacion',
            'tiempo_inicio_devolucion',
            'tiempo_inicio_ruta',
            'tiempo_llegada',
            'total_weight',
            'updated_at',
            'updated_by',
            'vessel',
            'weight_empty',
            'weight_loaded'
        ]
        read_only_fields = ('id', 'created_at', 'updated_at', 'created_by', 'updated_by')


class ContainerMovementSerializer(serializers.ModelSerializer):
    container = ContainerSerializer(read_only=True)
    movement_code = MovementCodeSerializer(read_only=True)
    from_location = LocationSerializer(read_only=True)
    to_location = LocationSerializer(read_only=True)
    from_vehicle = VehicleSerializer(read_only=True)
    to_vehicle = VehicleSerializer(read_only=True)
    movement_type_display = serializers.CharField(source='get_movement_type_display', read_only=True)

    class Meta:
        model = ContainerMovement
        fields = [
            'actual_datetime',
            'container',
            'created_at',
            'created_by',
            'from_location',
            'from_vehicle',
            'id',
            'is_active',
            'is_completed',
            'movement_code',
            'movement_date',
            'movement_type',
            'notes',
            'scheduled_datetime',
            'to_location',
            'to_vehicle',
            'updated_at',
            'updated_by',
            'weight_at_movement'
        ]
        read_only_fields = ('id', 'created_at', 'updated_at', 'created_by', 'updated_by')


class ContainerMovementCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear movimientos sin datos anidados."""
    
    class Meta:
        model = ContainerMovement
        fields = [
            'actual_datetime',
            'container',
            'created_at',
            'created_by',
            'from_location',
            'from_vehicle',
            'id',
            'is_active',
            'is_completed',
            'movement_code',
            'movement_date',
            'movement_type',
            'notes',
            'scheduled_datetime',
            'to_location',
            'to_vehicle',
            'updated_at',
            'updated_by',
            'weight_at_movement'
        ]
        read_only_fields = ('id', 'created_at', 'updated_at', 'created_by', 'updated_by')
    
    def validate(self, data):
        """Validaciones personalizadas para movimientos."""
        movement_type = data.get('movement_type')
        
        # Validar que los campos requeridos estén presentes según el tipo de movimiento
        if movement_type == 'load_chassis' and not data.get('to_vehicle'):
            raise serializers.ValidationError("Para cargar en chasis se requiere especificar el vehículo destino")
        
        if movement_type == 'unload_chassis' and not data.get('to_location'):
            raise serializers.ValidationError("Para descargar de chasis se requiere especificar la ubicación destino")
        
        if movement_type in ['transfer_warehouse', 'transfer_location'] and not data.get('to_location'):
            raise serializers.ValidationError("Para transferencias se requiere especificar la ubicación destino")
        
        return data


class ContainerDocumentSerializer(serializers.ModelSerializer):
    container = ContainerSerializer(read_only=True)
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)

    class Meta:
        model = ContainerDocument
        fields = [
            'container',
            'created_at',
            'created_by',
            'description',
            'document_date',
            'document_number',
            'document_type',
            'file',
            'id',
            'is_active',
            'updated_at',
            'updated_by'
        ]
        read_only_fields = ('id', 'created_at', 'updated_at', 'created_by', 'updated_by')


class ContainerDocumentCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear documentos sin datos anidados."""
    
    class Meta:
        model = ContainerDocument
        fields = [
            'container',
            'created_at',
            'created_by',
            'description',
            'document_date',
            'document_number',
            'document_type',
            'file',
            'id',
            'is_active',
            'updated_at',
            'updated_by'
        ]
        read_only_fields = ('id', 'created_at', 'updated_at', 'created_by', 'updated_by')


class ContainerInspectionSerializer(serializers.ModelSerializer):
    container = ContainerSerializer(read_only=True)
    inspection_type_display = serializers.CharField(source='get_inspection_type_display', read_only=True)
    overall_condition_display = serializers.CharField(source='get_overall_condition_display', read_only=True)

    class Meta:
        model = ContainerInspection
        fields = [
            'container',
            'created_at',
            'created_by',
            'damage_description',
            'exterior_condition',
            'id',
            'inspection_date',
            'inspection_type',
            'inspector_name',
            'interior_condition',
            'is_active',
            'observations',
            'overall_condition',
            'photos',
            'repair_notes',
            'repair_required',
            'updated_at',
            'updated_by'
        ]
        read_only_fields = ('id', 'created_at', 'updated_at', 'created_by', 'updated_by')


class ContainerInspectionCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear inspecciones sin datos anidados."""
    
    class Meta:
        model = ContainerInspection
        fields = [
            'container',
            'created_at',
            'created_by',
            'damage_description',
            'exterior_condition',
            'id',
            'inspection_date',
            'inspection_type',
            'inspector_name',
            'interior_condition',
            'is_active',
            'observations',
            'overall_condition',
            'photos',
            'repair_notes',
            'repair_required',
            'updated_at',
            'updated_by'
        ]
        read_only_fields = ('id', 'created_at', 'updated_at', 'created_by', 'updated_by')


class ContainerSummarySerializer(serializers.ModelSerializer):
    """Serializer resumido para listados."""
    owner_company_name = serializers.CharField(source='owner_company.name', read_only=True)
    current_position = serializers.CharField(source='get_current_position', read_only=True)
    container_type_display = serializers.CharField(source='get_container_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Container
        fields = [
            'id', 'container_number', 'container_type', 'container_type_display',
            'status', 'status_display', 'position_status', 'owner_company_name',
            'current_position', 'created_at', 'updated_at'
        ]