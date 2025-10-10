from django.contrib import admin
from django.utils.html import format_html
from .models import Container, ContainerMovement, ContainerDocument, ContainerInspection


@admin.register(Container)
class ContainerAdmin(admin.ModelAdmin):
    list_display = (
        'container_number', 'container_type', 'status_colored', 'position_status', 
        'client', 'vessel', 'eta', 'scheduled_date', 'conductor_asignado', 'is_active'
    )
    list_filter = (
        'container_type', 'status', 'position_status', 'client', 
        'vessel', 'is_active', 'created_at', 'scheduled_date'
    )
    search_fields = ('container_number', 'seal_number', 'customs_document', 'client__name', 'vessel__name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    list_editable = ('scheduled_date',)  # Permite edición rápida desde lista
    list_per_page = 25
    date_hierarchy = 'eta'
    
    def status_colored(self, obj):
        """Muestra el estado con color"""
        colors = {
            'DISPONIBLE': '#28a745',
            'ASIGNADO': '#007bff',
            'EN_RUTA': '#ffc107',
            'ENTREGADO': '#6c757d',
            'DEVUELTO': '#17a2b8',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_colored.short_description = 'Estado'
    
    actions = ['mark_as_disponible', 'mark_as_entregado']
    
    def mark_as_disponible(self, request, queryset):
        updated = queryset.update(status='DISPONIBLE')
        self.message_user(request, f'{updated} contenedor(es) marcado(s) como disponible.')
    mark_as_disponible.short_description = "Marcar como disponible"
    
    def mark_as_entregado(self, request, queryset):
        updated = queryset.update(status='ENTREGADO')
        self.message_user(request, f'{updated} contenedor(es) marcado(s) como entregado.')
    mark_as_entregado.short_description = "Marcar como entregado"
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('container_number', 'container_type', 'status', 'position_status')
        }),
        ('Información de Importación', {
            'fields': ('sequence_id', 'client', 'port', 'eta', 'vessel', 'cargo_description',
                      'shipping_line', 'agency', 'terminal')
        }),
        ('Liberación y Programación', {
            'fields': ('release_date', 'release_time', 'scheduled_date', 'scheduled_time', 
                      'cd_location', 'demurrage_alert')
        }),
        ('Asignación y Transporte', {
            'fields': ('conductor_asignado', 'current_position', 'position_updated_at')
        }),
        ('Pesos y Especificaciones', {
            'fields': ('cargo_weight', 'total_weight', 'weight_empty', 'max_weight')
        }),
        ('Ubicación Actual', {
            'fields': ('current_location', 'current_vehicle', 'owner_company')
        }),
        ('Información Adicional', {
            'fields': ('seal_number', 'customs_document', 'special_requirements', 
                      'observation_1', 'observation_2', 'additional_service')
        }),
        ('Devolución', {
            'fields': ('deposit_return', 'return_date'),
            'classes': ('collapse',)
        }),
        ('Auditoría', {
            'fields': ('is_active', 'created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        })
    )
    
    def get_readonly_fields(self, request, obj=None):
        """Make container_number readonly after creation"""
        if obj:  # Editing existing object
            return self.readonly_fields + ('container_number',)
        return self.readonly_fields
    
    class Meta:
        verbose_name = "Contenedor"
        verbose_name_plural = "Contenedores"


@admin.register(ContainerMovement)
class ContainerMovementAdmin(admin.ModelAdmin):
    list_display = (
        'container', 'movement_type', 'movement_date', 'movement_code', 
        'from_location', 'to_location', 'created_at'
    )
    list_filter = ('movement_type', 'movement_date', 'created_at')
    search_fields = ('container__container_number', 'movement_code__code', 'notes')
    readonly_fields = ('id', 'created_at', 'updated_at')
    date_hierarchy = 'movement_date'
    list_per_page = 25
    
    fieldsets = (
        ('Información del Movimiento', {
            'fields': ('container', 'movement_type', 'movement_code', 'movement_date')
        }),
        ('Ubicaciones', {
            'fields': ('from_location', 'to_location')
        }),
        ('Vehículos', {
            'fields': ('from_vehicle', 'to_vehicle')
        }),
        ('Detalles', {
            'fields': ('weight_at_movement', 'notes')
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        })
    )
    
    class Meta:
        verbose_name = "Movimiento de Contenedor"
        verbose_name_plural = "Movimientos de Contenedores"


@admin.register(ContainerDocument)
class ContainerDocumentAdmin(admin.ModelAdmin):
    list_display = (
        'container', 'document_type', 'document_number', 'document_date', 
        'created_at'
    )
    list_filter = ('document_type', 'document_date', 'created_at')
    search_fields = ('container__container_number', 'document_number', 'description')
    readonly_fields = ('id', 'created_at', 'updated_at')
    date_hierarchy = 'document_date'
    list_per_page = 25
    
    class Meta:
        verbose_name = "Documento de Contenedor"
        verbose_name_plural = "Documentos de Contenedores"


@admin.register(ContainerInspection)
class ContainerInspectionAdmin(admin.ModelAdmin):
    list_display = (
        'container', 'inspection_type', 'inspection_date', 'inspector_name',
        'overall_condition', 'repair_required', 'created_at'
    )
    list_filter = (
        'inspection_type', 'overall_condition', 'repair_required', 
        'inspection_date', 'created_at'
    )
    search_fields = ('container__container_number', 'inspector_name', 'observations')
    readonly_fields = ('id', 'created_at', 'updated_at')
    date_hierarchy = 'inspection_date'
    list_per_page = 25
    
    fieldsets = (
        ('Información de la Inspección', {
            'fields': ('container', 'inspection_type', 'inspection_date', 'inspector_name')
        }),
        ('Condiciones', {
            'fields': ('overall_condition', 'exterior_condition', 'interior_condition')
        }),
        ('Observaciones', {
            'fields': ('observations', 'damage_description')
        }),
        ('Reparaciones', {
            'fields': ('repair_required', 'repair_notes')
        }),
        ('Archivos', {
            'fields': ('photos',)
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        })
    )
    
    class Meta:
        verbose_name = "Inspección de Contenedor"
        verbose_name_plural = "Inspecciones de Contenedores"