from rest_framework import serializers
from .models import Driver, DriverLocation
from .access import asegurar_acceso


class DriverLocationSerializer(serializers.ModelSerializer):
    """Serializer para ubicaciones GPS"""
    
    class Meta:
        model = DriverLocation
        fields = ['id', 'driver', 'lat', 'lng', 'accuracy', 'timestamp']
        read_only_fields = ['id', 'timestamp']


class DriverSerializer(serializers.ModelSerializer):
    """Serializer para conductores"""
    
    esta_disponible = serializers.BooleanField(read_only=True)
    ubicacion_actual = serializers.SerializerMethodField()
    
    class Meta:
        model = Driver
        fields = [
            'id', 'nombre', 'rut', 'telefono', 'patente', 'presente', 'activo',
            'cumplimiento_porcentaje', 'num_entregas_dia', 'max_entregas_dia',
            'ultima_posicion_lat', 'ultima_posicion_lng', 'ultima_actualizacion_posicion',
            'total_entregas', 'entregas_a_tiempo', 'esta_disponible', 'ubicacion_actual',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'esta_disponible']

    def validate_rut(self, value):
        """La ausencia de RUT debe ser NULL; '' chocaría con el índice unique."""
        return value.strip() or None if value is not None else None

    def validate_patente(self, value):
        return value.strip().upper() or None if value is not None else None

    def validate_max_entregas_dia(self, value):
        if value < 1:
            raise serializers.ValidationError('Debe ser al menos 1.')
        return value

    def create(self, validated_data):
        driver = super().create(validated_data)
        # La clave temporal se adjunta en la vista y nunca se persiste en texto plano.
        self._temporary_access = asegurar_acceso(driver)
        return driver

    def update(self, instance, validated_data):
        driver = super().update(instance, validated_data)
        if driver.user_id:
            user = driver.user
            changed = []
            if user.is_active != driver.activo:
                user.is_active = driver.activo
                changed.append('is_active')
            names = driver.nombre.split()
            first_name = names[0] if names else ''
            last_name = ' '.join(names[1:])
            if user.first_name != first_name:
                user.first_name = first_name
                changed.append('first_name')
            if user.last_name != last_name:
                user.last_name = last_name
                changed.append('last_name')
            if changed:
                user.save(update_fields=changed)
        return driver
    
    def get_ubicacion_actual(self, obj):
        """Retorna la ubicación más reciente"""
        if obj.ultima_posicion_lat and obj.ultima_posicion_lng:
            return {
                'lat': float(obj.ultima_posicion_lat),
                'lng': float(obj.ultima_posicion_lng),
                'ultima_actualizacion': obj.ultima_actualizacion_posicion
            }
        return None


class DriverDetailSerializer(DriverSerializer):
    """Serializer detallado para conductores con programaciones asignadas"""
    
    programaciones_asignadas = serializers.SerializerMethodField()
    
    class Meta(DriverSerializer.Meta):
        fields = DriverSerializer.Meta.fields + ['programaciones_asignadas']
    
    def get_programaciones_asignadas(self, obj):
        """Retorna programaciones asignadas al conductor con información de ETA"""
        from apps.programaciones.models import Programacion
        from django.utils import timezone
        from datetime import timedelta
        
        # Get all programaciones for this driver
        programaciones = Programacion.objects.filter(
            driver=obj
        ).select_related('container', 'cd')
        
        resultado = []
        for prog in programaciones:
            # Filter by estado after retrieval since it's a property
            estado = prog.estado
            if estado in ['programado', 'asignado', 'en_ruta', 'entregado', 'soltado', 'descargado', 'vacio']:
                item = {
                    'id': prog.id,
                    'contenedor': prog.container.container_id_formatted if prog.container else None,
                    'cliente': prog.cliente,
                    'cd': prog.cd.nombre if prog.cd else None,
                    'cd_direccion': prog.cd.direccion if prog.cd else None,
                    'cd_permite_soltar': prog.cd.permite_soltar_contenedor if prog.cd else False,
                    'estado': estado,
                    'fecha_asignacion': prog.fecha_asignacion,
                    'fecha_programada': prog.fecha_programada,
                    'fecha_inicio_ruta': prog.fecha_inicio_ruta,
                    'fecha_arribo_cd': prog.fecha_arribo_cd,
                    'gps_arribo_lat': prog.gps_arribo_lat,
                    'gps_arribo_lng': prog.gps_arribo_lng,
                    'origen_arribo': prog.origen_arribo,
                    # Información de ETA
                    'eta_minutos': prog.eta_minutos,
                    'distancia_km': float(prog.distancia_km) if prog.distancia_km else None,
                }
                
                # El ETA original se ancla al inicio real de ruta. Usar now() aquí
                # desplazaría artificialmente la llegada estimada en cada recarga.
                if estado == 'en_ruta' and prog.fecha_inicio_ruta and prog.eta_minutos is not None:
                    item['eta_timestamp'] = prog.fecha_inicio_ruta + timedelta(minutes=prog.eta_minutos)
                    transcurrido = max(
                        0,
                        int((timezone.now() - prog.fecha_inicio_ruta).total_seconds() / 60),
                    )
                    item['eta_restante_minutos'] = max(0, prog.eta_minutos - transcurrido)
                else:
                    item['eta_timestamp'] = None
                    item['eta_restante_minutos'] = None
                
                resultado.append(item)
        
        return resultado


class DriverListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listas de conductores"""
    
    class Meta:
        model = Driver
        fields = [
            'id', 'nombre', 'rut', 'telefono', 'patente', 'activo', 'presente',
            'num_entregas_dia', 'max_entregas_dia', 'cumplimiento_porcentaje',
        ]


class DriverDisponibleSerializer(serializers.ModelSerializer):
    """Serializer para conductores disponibles con scores"""
    
    score_total = serializers.FloatField(read_only=True)
    esta_disponible = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Driver
        fields = [
            'id', 'nombre', 'rut', 'telefono', 'cumplimiento_porcentaje',
            'num_entregas_dia', 'max_entregas_dia', 'esta_disponible', 'score_total'
        ]
