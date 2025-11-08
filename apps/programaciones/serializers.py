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
    container_id_formatted = serializers.CharField(source='container.container_id_formatted', read_only=True)
    driver_nombre = serializers.CharField(source='driver.nombre', read_only=True, allow_null=True)
    cd_nombre = serializers.CharField(source='cd.nombre', read_only=True)
    horas_hasta_programacion = serializers.FloatField(read_only=True)
    
    class Meta:
        model = Programacion
        fields = [
            'id', 'container_id', 'container_id_formatted', 'fecha_programada', 'cliente', 'cd_nombre',
            'driver_nombre', 'requiere_alerta', 'horas_hasta_programacion'
        ]


class ProgramacionCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear programaciones"""
    
    class Meta:
        model = Programacion
        fields = ['container', 'cd', 'fecha_programada', 'cliente', 'direccion_entrega', 'observaciones']


class RutaManualSerializer(serializers.Serializer):
    """
    Serializer para crear rutas manuales (retiros desde puerto)
    """
    container_id = serializers.CharField(help_text='ID del contenedor a retirar')
    tipo_movimiento = serializers.ChoiceField(
        choices=['retiro_ccti', 'retiro_directo'],
        help_text='Tipo de movimiento: retiro_ccti (al CCTI) o retiro_directo (directo a cliente)'
    )
    cd_destino_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text='ID del CD destino (solo para retiro_directo)'
    )
    fecha_programacion = serializers.DateTimeField(help_text='Fecha y hora de la programación')
    cliente = serializers.CharField(required=False, allow_blank=True)
    observaciones = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data):
        """Validaciones personalizadas"""
        # Si es retiro_directo, debe tener cd_destino
        if data['tipo_movimiento'] == 'retiro_directo' and not data.get('cd_destino_id'):
            raise serializers.ValidationError({
                'cd_destino_id': 'cd_destino_id es requerido para retiro_directo'
            })
        
        # Verificar que el contenedor existe
        from apps.containers.models import Container
        try:
            container = Container.objects.get(container_id=data['container_id'])
            data['_container'] = container
        except Container.DoesNotExist:
            raise serializers.ValidationError({
                'container_id': f"Contenedor {data['container_id']} no encontrado"
            })
        
        # Verificar que el contenedor está liberado
        if container.estado not in ['liberado', 'por_arribar']:
            raise serializers.ValidationError({
                'container_id': f"Contenedor debe estar en estado 'liberado' o 'por_arribar'. Estado actual: {container.estado}"
            })
        
        # Verificar CD destino si es retiro_directo
        if data['tipo_movimiento'] == 'retiro_directo':
            from apps.cds.models import CD
            try:
                cd = CD.objects.get(id=data['cd_destino_id'])
                data['_cd_destino'] = cd
            except CD.DoesNotExist:
                raise serializers.ValidationError({
                    'cd_destino_id': f"CD {data['cd_destino_id']} no encontrado"
                })
        
        return data
