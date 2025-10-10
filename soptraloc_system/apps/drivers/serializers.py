"""
Serializers para el módulo de drivers
"""
from rest_framework import serializers
from .models import Location, Driver, Assignment, TimeMatrix, Alert, TrafficAlert


class LocationSerializer(serializers.ModelSerializer):
    """Serializer para ubicaciones"""
    class Meta:
        model = Location
        # FASE 5: Campos explícitos (antes: fields='__all__')
        fields = [
            'id', 'name', 'code', 'address', 'latitude', 'longitude',
            'location_type', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ('created_at', 'updated_at')


class DriverSerializer(serializers.ModelSerializer):
    """Serializer para conductores"""
    tipo_conductor_display = serializers.CharField(source='get_tipo_conductor_display', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    ubicacion_actual_display = serializers.CharField(source='get_ubicacion_actual_display', read_only=True)
    esta_disponible = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Driver
        # FASE 5: Campos explícitos (antes: fields='__all__' - expone datos sensibles)
        fields = [
            'id', 'ppu', 'nombre', 'rut', 'telefono', 'email',
            'tipo_conductor', 'tipo_conductor_display',
            'estado', 'estado_display',
            'ubicacion_actual', 'ubicacion_actual_display',
            'esta_disponible',
            'avg_travel_time', 'avg_loading_time', 'avg_unloading_time',
            'learned_total_time',
            'created_at', 'updated_at'
        ]
        # EXCLUIDOS: salary, internal_notes, emergency_contact (datos sensibles)
        read_only_fields = ('created_at', 'updated_at', 'esta_disponible')


class TimeMatrixSerializer(serializers.ModelSerializer):
    """Serializer para matriz de tiempos"""
    from_location = LocationSerializer(read_only=True)
    to_location = LocationSerializer(read_only=True)
    
    class Meta:
        model = TimeMatrix
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'last_updated')


class AssignmentSerializer(serializers.ModelSerializer):
    """Serializer para asignaciones"""
    driver = DriverSerializer(read_only=True)
    origen = LocationSerializer(read_only=True)
    destino = LocationSerializer(read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    tipo_asignacion_display = serializers.CharField(source='get_tipo_asignacion_display', read_only=True)
    
    class Meta:
        model = Assignment
        # FASE 5: Campos explícitos (antes: fields='__all__')
        fields = [
            'id', 'driver', 'container', 'origen', 'destino',
            'tipo_asignacion', 'tipo_asignacion_display',
            'estado', 'estado_display',
            'scheduled_datetime', 'estimated_time_minutes',
            'actual_start_time', 'actual_end_time',
            'actual_travel_time', 'actual_loading_time', 'actual_unloading_time',
            'fecha_asignacion', 'created_by'
        ]
        # EXCLUIDOS: internal_notes, audit_trail (datos internos)
        read_only_fields = ('fecha_asignacion', 'actual_start_time', 'actual_end_time')


class AlertSerializer(serializers.ModelSerializer):
    """Serializer para alertas"""
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    prioridad_display = serializers.CharField(source='get_prioridad_display', read_only=True)
    
    class Meta:
        model = Alert
        fields = '__all__'
        read_only_fields = ('fecha_creacion',)


class TrafficAlertSerializer(serializers.ModelSerializer):
    """Serializer para alertas de tráfico"""
    driver = DriverSerializer(read_only=True)
    traffic_level_display = serializers.CharField(source='get_traffic_level_display', read_only=True)
    alert_type_display = serializers.CharField(source='get_alert_type_display', read_only=True)
    
    class Meta:
        model = TrafficAlert
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')
