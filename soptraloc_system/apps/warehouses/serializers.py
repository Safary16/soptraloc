from rest_framework import serializers
from .models import Warehouse, WarehouseZone, WarehouseStock, WarehouseOperation, WarehouseReservation
from apps.core.serializers import CompanySerializer
from apps.drivers.serializers import LocationSerializer
from apps.containers.serializers import ContainerSerializer


class WarehouseSerializer(serializers.ModelSerializer):
    location = LocationSerializer(read_only=True)
    manager_company = CompanySerializer(read_only=True)
    warehouse_type_display = serializers.CharField(source='get_warehouse_type_display', read_only=True)
    available_capacity = serializers.ReadOnlyField()
    occupancy_percentage = serializers.ReadOnlyField()

    class Meta:
        model = Warehouse
        fields = [
            'area_m2',
            'code',
            'contact_email',
            'contact_phone',
            'created_at',
            'created_by',
            'current_occupancy',
            'has_crane',
            'has_power',
            'has_security',
            'id',
            'is_active',
            'location',
            'manager_company',
            'max_height_m',
            'name',
            'operates_weekends',
            'operating_hours_end',
            'operating_hours_start',
            'total_capacity',
            'updated_at',
            'updated_by',
            'warehouse_type'
        ]
        read_only_fields = ('id', 'created_at', 'updated_at', 'created_by', 'updated_by', 'current_occupancy')


class WarehouseCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para crear y actualizar almacenes."""
    
    class Meta:
        model = Warehouse
        fields = [
            'area_m2',
            'code',
            'contact_email',
            'contact_phone',
            'created_at',
            'created_by',
            'current_occupancy',
            'has_crane',
            'has_power',
            'has_security',
            'id',
            'is_active',
            'location',
            'manager_company',
            'max_height_m',
            'name',
            'operates_weekends',
            'operating_hours_end',
            'operating_hours_start',
            'total_capacity',
            'updated_at',
            'updated_by',
            'warehouse_type'
        ]
        read_only_fields = ('id', 'created_at', 'updated_at', 'created_by', 'updated_by', 'current_occupancy')


class WarehouseZoneSerializer(serializers.ModelSerializer):
    warehouse = WarehouseSerializer(read_only=True)
    available_capacity = serializers.ReadOnlyField()

    class Meta:
        model = WarehouseZone
        fields = [
            'capacity',
            'created_at',
            'created_by',
            'current_occupancy',
            'id',
            'is_active',
            'is_covered',
            'is_hazardous_allowed',
            'is_refrigerated',
            'updated_at',
            'updated_by',
            'warehouse',
            'zone_code',
            'zone_name',
            'zone_type'
        ]
        read_only_fields = ('id', 'created_at', 'updated_at', 'created_by', 'updated_by', 'current_occupancy')


class WarehouseZoneCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para crear y actualizar zonas de almacén."""
    
    class Meta:
        model = WarehouseZone
        fields = [
            'capacity',
            'created_at',
            'created_by',
            'current_occupancy',
            'id',
            'is_active',
            'is_covered',
            'is_hazardous_allowed',
            'is_refrigerated',
            'updated_at',
            'updated_by',
            'warehouse',
            'zone_code',
            'zone_name',
            'zone_type'
        ]
        read_only_fields = ('id', 'created_at', 'updated_at', 'created_by', 'updated_by', 'current_occupancy')


class WarehouseStockSerializer(serializers.ModelSerializer):
    warehouse = WarehouseSerializer(read_only=True)
    zone = WarehouseZoneSerializer(read_only=True)
    container = ContainerSerializer(read_only=True)

    class Meta:
        model = WarehouseStock
        fields = [
            'actual_exit_date',
            'blocked_reason',
            'column',
            'container',
            'created_at',
            'created_by',
            'entry_date',
            'expected_exit_date',
            'id',
            'is_active',
            'is_blocked',
            'notes',
            'row',
            'special_handling',
            'stack_position',
            'updated_at',
            'updated_by',
            'warehouse',
            'zone'
        ]
        read_only_fields = ('id', 'created_at', 'updated_at', 'created_by', 'updated_by')


class WarehouseStockCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para crear y actualizar stock de almacén."""
    
    class Meta:
        model = WarehouseStock
        fields = [
            'actual_exit_date',
            'blocked_reason',
            'column',
            'container',
            'created_at',
            'created_by',
            'entry_date',
            'expected_exit_date',
            'id',
            'is_active',
            'is_blocked',
            'notes',
            'row',
            'special_handling',
            'stack_position',
            'updated_at',
            'updated_by',
            'warehouse',
            'zone'
        ]
        read_only_fields = ('id', 'created_at', 'updated_at', 'created_by', 'updated_by')


class WarehouseOperationSerializer(serializers.ModelSerializer):
    warehouse = WarehouseSerializer(read_only=True)
    container = ContainerSerializer(read_only=True)
    from_zone = WarehouseZoneSerializer(read_only=True)
    to_zone = WarehouseZoneSerializer(read_only=True)
    operation_type_display = serializers.CharField(source='get_operation_type_display', read_only=True)
    duration_minutes = serializers.ReadOnlyField()

    class Meta:
        model = WarehouseOperation
        fields = [
            'container',
            'created_at',
            'created_by',
            'end_time',
            'equipment_used',
            'from_zone',
            'id',
            'is_active',
            'issues_found',
            'notes',
            'operation_date',
            'operation_type',
            'operator_name',
            'start_time',
            'to_zone',
            'updated_at',
            'updated_by',
            'warehouse'
        ]
        read_only_fields = ('id', 'created_at', 'updated_at', 'created_by', 'updated_by')


class WarehouseOperationCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para crear y actualizar operaciones de almacén."""
    
    class Meta:
        model = WarehouseOperation
        fields = [
            'container',
            'created_at',
            'created_by',
            'end_time',
            'equipment_used',
            'from_zone',
            'id',
            'is_active',
            'issues_found',
            'notes',
            'operation_date',
            'operation_type',
            'operator_name',
            'start_time',
            'to_zone',
            'updated_at',
            'updated_by',
            'warehouse'
        ]
        read_only_fields = ('id', 'created_at', 'updated_at', 'created_by', 'updated_by')


class WarehouseReservationSerializer(serializers.ModelSerializer):
    warehouse = WarehouseSerializer(read_only=True)
    zone = WarehouseZoneSerializer(read_only=True)
    client_company = CompanySerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = WarehouseReservation
        fields = [
            'client_company',
            'container_count',
            'container_types',
            'created_at',
            'created_by',
            'end_date',
            'id',
            'is_active',
            'notes',
            'reservation_code',
            'reservation_date',
            'special_requirements',
            'start_date',
            'status',
            'updated_at',
            'updated_by',
            'warehouse',
            'zone'
        ]
        read_only_fields = ('id', 'created_at', 'updated_at', 'created_by', 'updated_by')


class WarehouseReservationCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para crear y actualizar reservas de almacén."""
    
    class Meta:
        model = WarehouseReservation
        fields = [
            'client_company',
            'container_count',
            'container_types',
            'created_at',
            'created_by',
            'end_date',
            'id',
            'is_active',
            'notes',
            'reservation_code',
            'reservation_date',
            'special_requirements',
            'start_date',
            'status',
            'updated_at',
            'updated_by',
            'warehouse',
            'zone'
        ]
        read_only_fields = ('id', 'created_at', 'updated_at', 'created_by', 'updated_by')


class WarehouseSummarySerializer(serializers.ModelSerializer):
    """Serializer resumido para listados."""
    manager_company_name = serializers.CharField(source='manager_company.name', read_only=True)
    location_name = serializers.CharField(source='location.name', read_only=True)
    warehouse_type_display = serializers.CharField(source='get_warehouse_type_display', read_only=True)
    available_capacity = serializers.ReadOnlyField()
    occupancy_percentage = serializers.ReadOnlyField()
    
    class Meta:
        model = Warehouse
        fields = [
            'id', 'name', 'code', 'warehouse_type', 'warehouse_type_display',
            'total_capacity', 'current_occupancy', 'available_capacity',
            'occupancy_percentage', 'manager_company_name', 'location_name',
            'is_active', 'created_at'
        ]