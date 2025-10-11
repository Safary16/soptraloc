from django.contrib import admin
from .models import CD


@admin.register(CD)
class CDAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'codigo', 'tipo', 'comuna', 'activo', 'vacios_display', 'espacios_disponibles']
    list_filter = ['tipo', 'activo', 'comuna']
    search_fields = ['nombre', 'codigo', 'direccion', 'comuna']
    readonly_fields = ['created_at', 'updated_at', 'espacios_disponibles']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'codigo', 'tipo', 'activo')
        }),
        ('Ubicación', {
            'fields': ('direccion', 'comuna', 'lat', 'lng')
        }),
        ('Gestión de Vacíos (CCTI)', {
            'fields': ('capacidad_vacios', 'vacios_actuales', 'espacios_disponibles'),
            'classes': ('collapse',)
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def vacios_display(self, obj):
        if obj.tipo == 'ccti':
            return f"{obj.vacios_actuales}/{obj.capacidad_vacios}"
        return "-"
    vacios_display.short_description = 'Vacíos (actual/capacidad)'
