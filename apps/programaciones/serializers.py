from rest_framework import serializers
from .models import Programacion
from apps.containers.serializers import ContainerListSerializer
from apps.drivers.serializers import DriverListSerializer
from apps.cds.serializers import CDListSerializer


class ProgramacionSerializer(serializers.ModelSerializer):
    container_detail = ContainerListSerializer(source='container', read_only=True)
    driver_detail = DriverListSerializer(source='driver', read_only=True)
    cd_detail = CDListSerializer(source='cd', read_only=True)
    horas_hasta_programacion = serializers.FloatField(read_only=True)
    requiere_conductor_urgente = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Programacion
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'alerta_48h_enviada']


class ProgramacionListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listas"""
    container_id = serializers.CharField(source='container.container_id', read_only=True)
    driver_nombre = serializers.CharField(source='driver.nombre', read_only=True, allow_null=True)
    cd_nombre = serializers.CharField(source='cd.nombre', read_only=True)
    horas_hasta_programacion = serializers.FloatField(read_only=True)
    
    class Meta:
        model = Programacion
        fields = [
            'id', 'container_id', 'fecha_programada', 'cliente', 'cd_nombre',
            'driver_nombre', 'requiere_alerta', 'horas_hasta_programacion'
        ]


class ProgramacionCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear programaciones"""
    
    class Meta:
        model = Programacion
        fields = ['container', 'cd', 'fecha_programada', 'cliente', 'direccion_entrega', 'observaciones']
