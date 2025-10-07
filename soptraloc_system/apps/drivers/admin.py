from django.contrib import admin
from .models import Driver, Assignment, Alert, TrafficAlert

@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'ppu', 'tipo_conductor', 'estado', 'ubicacion_actual', 'contenedor_asignado', 'coordinador']
    list_filter = ['tipo_conductor', 'estado', 'ubicacion_actual', 'coordinador', 'is_active']
    search_fields = ['nombre', 'rut', 'ppu', 'telefono']
    list_editable = ['estado', 'ubicacion_actual']
    
    fieldsets = (
        ('Información Personal', {
            'fields': ('nombre', 'rut', 'telefono')
        }),
        ('Vehículo', {
            'fields': ('ppu', 'tracto')
        }),
        ('Clasificación', {
            'fields': ('tipo_conductor', 'estado', 'coordinador', 'faena')
        }),
        ('Ubicación y Asignación', {
            'fields': ('ubicacion_actual', 'tiempo_en_ubicacion', 'contenedor_asignado')
        }),
        ('Observaciones', {
            'fields': ('observaciones', 'ingresa_agy')
        }),
        ('Estado del Registro', {
            'fields': ('is_active',)
        })
    )
    
    readonly_fields = ['tiempo_en_ubicacion', 'created_at', 'updated_at']

@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ['container', 'driver', 'estado', 'fecha_programada', 'origen', 'destino', 'created_by']
    list_filter = ['estado', 'fecha_programada', 'origen', 'destino']
    search_fields = ['container__container_number', 'driver__nombre', 'driver__ppu']
    date_hierarchy = 'fecha_programada'
    
    fieldsets = (
        ('Asignación', {
            'fields': ('container', 'driver', 'estado')
        }),
        ('Programación', {
            'fields': ('fecha_programada', 'fecha_inicio', 'fecha_completada')
        }),
        ('Ruta', {
            'fields': ('origen', 'destino')
        }),
        ('Observaciones', {
            'fields': ('observaciones', 'created_by')
        })
    )
    
    readonly_fields = ['fecha_asignacion']

@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'tipo', 'prioridad', 'is_active', 'fecha_creacion', 'container', 'driver']
    list_filter = ['tipo', 'prioridad', 'is_active', 'fecha_creacion']
    search_fields = ['titulo', 'mensaje', 'container__container_number', 'driver__nombre']
    date_hierarchy = 'fecha_creacion'
    
    actions = ['marcar_como_resuelto']
    
    def marcar_como_resuelto(self, request, queryset):
        from django.utils import timezone
        queryset.update(
            is_active=False, 
            fecha_resolucion=timezone.now(),
            resuelto_por=request.user
        )
        self.message_user(request, f"{queryset.count()} alertas marcadas como resueltas.")
    marcar_como_resuelto.short_description = "Marcar alertas seleccionadas como resueltas"


@admin.register(TrafficAlert)
class TrafficAlertAdmin(admin.ModelAdmin):
    list_display = [
        'get_traffic_emoji', 'alert_type', 'driver', 'origin_name', 'destination_name', 
        'traffic_level', 'delay_minutes', 'estimated_arrival', 'acknowledged', 'is_active'
    ]
    list_filter = ['traffic_level', 'alert_type', 'is_active', 'acknowledged', 'created_at']
    search_fields = ['driver__nombre', 'origin_name', 'destination_name', 'message']
    date_hierarchy = 'created_at'
    readonly_fields = [
        'assignment', 'driver', 'origin_name', 'destination_name', 'traffic_level',
        'alert_type', 'estimated_time_minutes', 'actual_time_minutes', 'delay_minutes',
        'departure_time', 'estimated_arrival', 'message', 'warnings', 'has_alternatives',
        'alternative_routes', 'raw_data', 'acknowledged_at', 'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('🚦 Información de Tráfico', {
            'fields': (
                ('get_traffic_emoji', 'traffic_level', 'alert_type'),
                ('delay_minutes', 'get_delay_text'),
            )
        }),
        ('🚚 Conductor y Ruta', {
            'fields': (
                'driver',
                'assignment',
                ('origin_name', 'destination_name'),
            )
        }),
        ('⏱️ Tiempos', {
            'fields': (
                'departure_time',
                'estimated_arrival',
                ('estimated_time_minutes', 'actual_time_minutes'),
            )
        }),
        ('📋 Mensaje y Advertencias', {
            'fields': (
                'message',
                'warnings',
            )
        }),
        ('🔀 Rutas Alternativas', {
            'fields': (
                'has_alternatives',
                'alternative_routes',
            ),
            'classes': ('collapse',)
        }),
        ('📊 Datos Completos de API', {
            'fields': ('raw_data',),
            'classes': ('collapse',)
        }),
        ('✅ Estado', {
            'fields': (
                'is_active',
                ('acknowledged', 'acknowledged_at'),
            )
        }),
    )
    
    actions = ['marcar_como_reconocida', 'desactivar_alertas']
    
    def get_traffic_emoji(self, obj):
        return obj.get_traffic_emoji()
    get_traffic_emoji.short_description = ''
    
    def get_delay_text(self, obj):
        return obj.get_delay_text()
    get_delay_text.short_description = 'Descripción del retraso'
    
    def marcar_como_reconocida(self, request, queryset):
        from django.utils import timezone
        queryset.update(acknowledged=True, acknowledged_at=timezone.now())
        self.message_user(request, f"{queryset.count()} alertas marcadas como reconocidas.")
    marcar_como_reconocida.short_description = "Marcar como reconocida por conductor"
    
    def desactivar_alertas(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"{queryset.count()} alertas desactivadas.")
    desactivar_alertas.short_description = "Desactivar alertas seleccionadas"