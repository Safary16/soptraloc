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
            'city', 'region', 'country', 'is_active', 'created_at', 'updated_at'
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
            'id', 'ppu', 'nombre', 'rut', 'telefono',
            'tipo_conductor', 'tipo_conductor_display',
            'estado', 'estado_display',
            'ubicacion_actual', 'ubicacion_actual_display',
            'esta_disponible',
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
        fields = [
            'avg_travel_time',
            'created_at',
            'from_location',
            'last_updated',
            'loading_time',
            'max_travel_time',
            'min_travel_time',
            'to_location',
            'total_trips',
            'travel_time',
            'unloading_time',
            'updated_at'
        ]
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
            'fecha_programada', 'tiempo_estimado',
            'fecha_inicio', 'fecha_completada',
            'tiempo_real', 'ruta_minutos_real', 'descarga_minutos_real',
            'fecha_asignacion'
        ]
        # EXCLUIDOS: internal_notes, audit_trail (datos internos)
        read_only_fields = ('fecha_asignacion', 'fecha_inicio', 'fecha_completada')


class AlertSerializer(serializers.ModelSerializer):
    """Serializer para alertas"""
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    prioridad_display = serializers.CharField(source='get_prioridad_display', read_only=True)
    
    class Meta:
        model = Alert
        fields = [
            'container',
            'driver',
            'fecha_creacion',
            'fecha_resolucion',
            'is_active',
            'mensaje',
            'prioridad',
            'resuelto_por',
            'tipo',
            'titulo'
        ]
        read_only_fields = ('fecha_creacion',)


class TrafficAlertSerializer(serializers.ModelSerializer):
    """Serializer para alertas de tráfico"""
    driver = DriverSerializer(read_only=True)
    traffic_level_display = serializers.CharField(source='get_traffic_level_display', read_only=True)
    alert_type_display = serializers.CharField(source='get_alert_type_display', read_only=True)
    
    class Meta:
        model = TrafficAlert
        fields = [
            'acknowledged',
            'acknowledged_at',
            'actual_time_minutes',
            'alert_type',
            'alternative_routes',
            'assignment',
            'created_at',
            'delay_minutes',
            'departure_time',
            'destination_name',
            'driver',
            'estimated_arrival',
            'estimated_time_minutes',
            'has_alternatives',
            'is_active',
            'message',
            'origin_name',
            'raw_data',
            'traffic_level',
            'updated_at',
            'warnings'
        ]
        read_only_fields = ('created_at', 'updated_at')
