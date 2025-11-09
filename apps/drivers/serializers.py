from rest_framework import serializers
from .models import Driver, DriverLocation


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
            if estado in ['programado', 'asignado', 'en_ruta', 'entregado', 'descargado', 'vacio']:
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
                    # Información de ETA
                    'eta_minutos': prog.eta_minutos,
                    'distancia_km': float(prog.distancia_km) if prog.distancia_km else None,
                }
                
                # Calcular ETA timestamp si está en ruta y tenemos ETA
                if estado == 'en_ruta' and prog.eta_minutos:
                    eta_timestamp = timezone.now() + timedelta(minutes=prog.eta_minutos)
                    item['eta_timestamp'] = eta_timestamp
                else:
                    item['eta_timestamp'] = None
                
                resultado.append(item)
        
        return resultado


class DriverListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listas de conductores"""
    
    class Meta:
        model = Driver
        fields = ['id', 'nombre', 'rut', 'telefono', 'activo', 'presente', 'num_entregas_dia', 'max_entregas_dia']


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
