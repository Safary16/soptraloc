"""
Serializers para el módulo de drivers
"""
from rest_framework import serializers
from .models import Location, Driver, Assignment, TimeMatrix, Alert, TrafficAlert


class LocationSerializer(serializers.ModelSerializer):
    """Serializer para ubicaciones"""
    class Meta:
        model = Location
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')


class DriverSerializer(serializers.ModelSerializer):
    """Serializer para conductores"""
    tipo_conductor_display = serializers.CharField(source='get_tipo_conductor_display', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    ubicacion_actual_display = serializers.CharField(source='get_ubicacion_actual_display', read_only=True)
    esta_disponible = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Driver
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')


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
        fields = '__all__'
        read_only_fields = ('fecha_asignacion',)


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
