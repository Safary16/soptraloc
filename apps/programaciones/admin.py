from django.contrib import admin
from .models import Programacion, TiempoOperacion, TiempoViaje


@admin.register(Programacion)
class ProgramacionAdmin(admin.ModelAdmin):
    list_display = ['container', 'fecha_programada', 'cliente', 'cd', 'driver', 'requiere_alerta', 'horas_restantes']
    list_filter = ['fecha_programada', 'requiere_alerta', 'alerta_48h_enviada', 'cd']
    search_fields = ['container__container_id', 'cliente', 'driver__nombre']
    readonly_fields = ['created_at', 'updated_at', 'horas_restantes', 'requiere_conductor_urgente']
    autocomplete_fields = ['container', 'driver', 'cd']
    
    fieldsets = (
        ('Contenedor y Destino', {
            'fields': ('container', 'cd', 'cliente', 'direccion_entrega')
        }),
        ('Programación', {
            'fields': ('fecha_programada', 'driver')
        }),
        ('Datos de Ruta (Mapbox)', {
            'fields': ('eta_minutos', 'distancia_km', 'ruta_geojson'),
            'classes': ('collapse',)
        }),
        ('Alertas', {
            'fields': ('requiere_alerta', 'alerta_48h_enviada', 'horas_restantes', 'requiere_conductor_urgente')
        }),
        ('Observaciones', {
            'fields': ('observaciones',),
            'classes': ('collapse',)
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def horas_restantes(self, obj):
        horas = obj.horas_hasta_programacion
        if horas is None:
            return "-"
        if horas < 0:
            return f"Venció hace {abs(horas):.1f}h"
        return f"{horas:.1f}h"
    horas_restantes.short_description = 'Tiempo Restante'


@admin.register(TiempoOperacion)
class TiempoOperacionAdmin(admin.ModelAdmin):
    list_display = ['cd', 'tipo_operacion', 'tiempo_real_min', 'tiempo_estimado_min', 'desviacion_porcentaje', 'conductor', 'fecha', 'anomalia']
    list_filter = ['tipo_operacion', 'anomalia', 'fecha', 'cd']
    search_fields = ['cd__nombre', 'conductor__nombre', 'container__container_id']
    readonly_fields = ['fecha', 'desviacion_porcentaje']
    autocomplete_fields = ['cd', 'conductor', 'container']
    date_hierarchy = 'fecha'
    
    fieldsets = (
        ('Operación', {
            'fields': ('cd', 'tipo_operacion', 'conductor', 'container')
        }),
        ('Tiempos', {
            'fields': ('tiempo_estimado_min', 'tiempo_real_min', 'desviacion_porcentaje', 'hora_inicio', 'hora_fin')
        }),
        ('Control de Calidad', {
            'fields': ('anomalia', 'observaciones')
        }),
    )
    
    def desviacion_porcentaje(self, obj):
        """Muestra desviación como porcentaje con color"""
        desv = obj.calcular_desviacion()
        if desv > 50:
            return f"🔴 +{desv:.0f}%"
        elif desv > 20:
            return f"🟡 +{desv:.0f}%"
        elif desv < -20:
            return f"🟢 {desv:.0f}%"
        else:
            return f"⚪ {desv:.0f}%"
    desviacion_porcentaje.short_description = 'Desviación'


@admin.register(TiempoViaje)
class TiempoViajeAdmin(admin.ModelAdmin):
    list_display = ['origen_nombre', 'destino_nombre', 'tiempo_real_min', 'tiempo_mapbox_min', 'factor_correccion_display', 'conductor', 'fecha', 'hora_del_dia', 'anomalia']
    list_filter = ['anomalia', 'fecha', 'dia_semana', 'hora_del_dia']
    search_fields = ['origen_nombre', 'destino_nombre', 'conductor__nombre']
    readonly_fields = ['fecha', 'hora_del_dia', 'dia_semana', 'factor_correccion_display']
    autocomplete_fields = ['conductor', 'programacion']
    date_hierarchy = 'fecha'
    
    fieldsets = (
        ('Ruta', {
            'fields': (
                ('origen_nombre', 'destino_nombre'),
                ('origen_lat', 'origen_lon'),
                ('destino_lat', 'destino_lon'),
                'distancia_km'
            )
        }),
        ('Tiempos', {
            'fields': (
                'tiempo_mapbox_min',
                'tiempo_real_min',
                'factor_correccion_display',
                ('hora_salida', 'hora_llegada')
            )
        }),
        ('Contexto', {
            'fields': ('conductor', 'programacion', 'hora_del_dia', 'dia_semana')
        }),
        ('Control de Calidad', {
            'fields': ('anomalia', 'observaciones')
        }),
    )
    
    def factor_correccion_display(self, obj):
        """Muestra factor de corrección con interpretación"""
        factor = obj.calcular_factor_correccion()
        if factor > 1.5:
            return f"🔴 {factor:.2f}x (Muy lento)"
        elif factor > 1.2:
            return f"🟡 {factor:.2f}x (Lento)"
        elif factor < 0.8:
            return f"🟢 {factor:.2f}x (Rápido)"
        else:
            return f"⚪ {factor:.2f}x (Normal)"
    factor_correccion_display.short_description = 'Factor Corrección'
