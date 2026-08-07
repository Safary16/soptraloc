from django.contrib import admin
from .models import Container


@admin.register(Container)
class ContainerAdmin(admin.ModelAdmin):
    list_display = ['container_id', 'tipo', 'estado', 'nave', 'posicion_fisica', 'fecha_liberacion', 'secuenciado', 'updated_at']
    list_filter = ['estado', 'tipo', 'tipo_carga', 'secuenciado', 'puerto', 'tipo_movimiento']
    search_fields = ['container_id', 'nave', 'vendor', 'sello', 'comuna', 'booking', 'referencia']
    readonly_fields = ['created_at', 'updated_at', 'peso_total', 'peso_total_tons', 'dias_para_demurrage', 'urgencia_demurrage']
    
    fieldsets = (
        ('Identificación', {
            'fields': ('container_id', 'tipo', 'tipo_carga', 'nave', 'viaje', 'booking', 'referencia')
        }),
        ('Detalles del Embarque', {
            'fields': ('peso_carga', 'tara', 'peso_total', 'peso_total_tons', 'contenido', 'vendor', 'sello', 'puerto')
        }),
        ('Estado y Ubicación', {
            'fields': ('estado', 'posicion_fisica', 'tipo_movimiento', 'secuenciado')
        }),
        ('Información de Entrega', {
            'fields': ('cliente', 'comuna', 'cd_entrega', 'deposito_devolucion')
        }),
        ('Fechas Importantes', {
            'fields': ('fecha_eta', 'fecha_liberacion', 'fecha_demurrage', 'dias_para_demurrage', 'urgencia_demurrage')
        }),
        ('Ciclo de Vida (Timestamps)', {
            'fields': (
                'fecha_arribo', 'fecha_programacion',
                'fecha_asignacion', 'fecha_inicio_ruta', 'fecha_entrega',
                'fecha_descarga', 'fecha_vacio', 'fecha_vacio_ruta', 'fecha_devolucion'
            ),
            'classes': ('collapse',)
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['marcar_secuenciado', 'desmarcar_secuenciado']
    
    def marcar_secuenciado(self, request, queryset):
        updated = queryset.update(secuenciado=True)
        self.message_user(request, f'{updated} contenedores marcados como secuenciados.')
    marcar_secuenciado.short_description = 'Marcar como secuenciado'
    
    def desmarcar_secuenciado(self, request, queryset):
        updated = queryset.update(secuenciado=False)
        self.message_user(request, f'{updated} contenedores desmarcados como secuenciados.')
    desmarcar_secuenciado.short_description = 'Desmarcar secuenciado'
