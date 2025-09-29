from django.contrib import admin
from .models import Driver, Assignment, Alert

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