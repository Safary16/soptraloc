from rest_framework import serializers
from .models import Driver, DriverLocation


class DriverSerializer(serializers.ModelSerializer):
    ocupacion_porcentaje = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    esta_disponible = serializers.BooleanField(read_only=True)
    username = serializers.CharField(source='user.username', read_only=True, allow_null=True)
    
    class Meta:
        model = Driver
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'total_entregas', 'entregas_a_tiempo', 'user']


class DriverListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listas"""
    ocupacion_porcentaje = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    esta_disponible = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Driver
        fields = [
            'id', 'nombre', 'presente', 'activo', 'num_entregas_dia',
            'max_entregas_dia', 'ocupacion_porcentaje', 'esta_disponible',
            'cumplimiento_porcentaje'
        ]


class DriverDisponibleSerializer(serializers.ModelSerializer):
    """Serializer para drivers disponibles con score de asignación"""
    ocupacion_porcentaje = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    score = serializers.DecimalField(max_digits=5, decimal_places=2, required=False)
    distancia_km = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    
    class Meta:
        model = Driver
        fields = [
            'id', 'nombre', 'presente', 'num_entregas_dia', 'max_entregas_dia',
            'ocupacion_porcentaje', 'cumplimiento_porcentaje', 'score', 'distancia_km'
        ]


class DriverLocationSerializer(serializers.ModelSerializer):
    """Serializer para ubicaciones GPS del conductor"""
    driver_name = serializers.CharField(source='driver.nombre', read_only=True)
    
    class Meta:
        model = DriverLocation
        fields = ['id', 'driver', 'driver_name', 'lat', 'lng', 'accuracy', 'timestamp']
        read_only_fields = ['timestamp']
