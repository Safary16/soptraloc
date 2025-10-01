from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import (
    LocationPair,
    OperationTime,
    ActualTripRecord,
    ActualOperationRecord,
    Route,
    RouteStop
)


@admin.register(LocationPair)
class LocationPairAdmin(admin.ModelAdmin):
    list_display = [
        'origin',
        'destination',
        'base_travel_time',
        'ml_status',
        'total_trips',
        'confidence_badge',
        'route_type',
        'is_active'
    ]
    list_filter = ['route_type', 'is_active', 'origin', 'destination']
    search_fields = ['origin__name', 'destination__name']
    readonly_fields = [
        'ml_predicted_time',
        'ml_confidence',
        'ml_last_update',
        'total_trips',
        'avg_actual_time',
        'created_at',
        'updated_at'
    ]
    
    fieldsets = (
        ('Ubicaciones', {
            'fields': ('origin', 'destination', 'route_type', 'distance_km')
        }),
        ('Tiempos Base (Manual)', {
            'fields': (
                'base_travel_time',
                'peak_hour_multiplier',
                'peak_hours_start',
                'peak_hours_end',
                'peak_hours_2_start',
                'peak_hours_2_end',
            )
        }),
        ('Machine Learning (Automático)', {
            'fields': (
                'ml_predicted_time',
                'ml_confidence',
                'ml_last_update',
            ),
            'classes': ('collapse',)
        }),
        ('Estadísticas', {
            'fields': (
                'total_trips',
                'avg_actual_time',
            ),
            'classes': ('collapse',)
        }),
        ('Otros', {
            'fields': ('notes', 'is_active')
        })
    )
    
    def ml_status(self, obj):
        if obj.ml_predicted_time:
            return f"{obj.ml_predicted_time} min"
        return "Sin datos"
    ml_status.short_description = "ML Predicción"
    
    def confidence_badge(self, obj):
        if not obj.ml_confidence:
            return format_html('<span style="color: gray;">-</span>')
        
        confidence = float(obj.ml_confidence)
        if confidence >= 80:
            color = 'green'
        elif confidence >= 60:
            color = 'orange'
        else:
            color = 'red'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.1f}%</span>',
            color,
            confidence
        )
    confidence_badge.short_description = "Confianza ML"
    
    actions = ['update_ml_predictions']
    
    def update_ml_predictions(self, request, queryset):
        from .ml_service import TimePredictionML
        
        updated = 0
        for pair in queryset:
            if TimePredictionML._update_single_location_pair(pair):
                updated += 1
        
        self.message_user(
            request,
            f"✅ Actualizadas {updated} predicciones ML de {queryset.count()} rutas."
        )
    update_ml_predictions.short_description = "🤖 Actualizar predicciones ML"


@admin.register(OperationTime)
class OperationTimeAdmin(admin.ModelAdmin):
    list_display = [
        'location',
        'operation_type',
        'time_range',
        'ml_prediction',
        'confidence_badge',
        'total_operations',
        'is_active'
    ]
    list_filter = ['operation_type', 'location', 'is_active']
    search_fields = ['location__name', 'operation_type']
    readonly_fields = [
        'ml_predicted_time',
        'ml_confidence',
        'ml_last_update',
        'total_operations',
        'created_at',
        'updated_at'
    ]
    
    fieldsets = (
        ('Operación', {
            'fields': ('location', 'operation_type')
        }),
        ('Tiempos (Manual)', {
            'fields': ('min_time', 'avg_time', 'max_time')
        }),
        ('Variables', {
            'fields': (
                'depends_on_container_size',
                'depends_on_cargo_type',
                'depends_on_time_of_day',
            )
        }),
        ('Machine Learning', {
            'fields': (
                'ml_predicted_time',
                'ml_confidence',
                'ml_last_update',
                'total_operations',
            ),
            'classes': ('collapse',)
        }),
        ('Otros', {
            'fields': ('notes', 'is_active')
        })
    )
    
    def time_range(self, obj):
        return f"{obj.min_time}-{obj.max_time} min (avg: {obj.avg_time})"
    time_range.short_description = "Rango de Tiempo"
    
    def ml_prediction(self, obj):
        if obj.ml_predicted_time:
            return f"{obj.ml_predicted_time} min"
        return "-"
    ml_prediction.short_description = "ML"
    
    def confidence_badge(self, obj):
        if not obj.ml_confidence:
            return format_html('<span style="color: gray;">-</span>')
        
        confidence = float(obj.ml_confidence)
        if confidence >= 80:
            color = 'green'
        elif confidence >= 60:
            color = 'orange'
        else:
            color = 'red'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.1f}%</span>',
            color,
            confidence
        )
    confidence_badge.short_description = "Confianza"
    
    actions = ['update_ml_predictions']
    
    def update_ml_predictions(self, request, queryset):
        from .ml_service import TimePredictionML
        
        updated = 0
        for op_time in queryset:
            if TimePredictionML._update_single_operation(op_time):
                updated += 1
        
        self.message_user(
            request,
            f"✅ Actualizadas {updated} predicciones ML de {queryset.count()} operaciones."
        )
    update_ml_predictions.short_description = "🤖 Actualizar predicciones ML"


@admin.register(ActualTripRecord)
class ActualTripRecordAdmin(admin.ModelAdmin):
    list_display = [
        'container',
        'origin',
        'destination',
        'departure_time',
        'duration_minutes',
        'day_name',
        'had_delay'
    ]
    list_filter = [
        'day_of_week',
        'was_peak_hour',
        'had_delay',
        'weather',
        'origin',
        'destination'
    ]
    search_fields = ['container__number', 'driver__first_name', 'driver__last_name']
    readonly_fields = [
        'duration_minutes',
        'day_of_week',
        'hour_of_day',
        'container_size',
        'container_type',
        'cargo_weight',
        'created_at'
    ]
    date_hierarchy = 'departure_time'
    
    fieldsets = (
        ('Viaje', {
            'fields': (
                'container',
                'driver',
                'vehicle',
                'origin',
                'destination',
            )
        }),
        ('Tiempos', {
            'fields': (
                'departure_time',
                'arrival_time',
                'duration_minutes',
            )
        }),
        ('Contexto (Auto)', {
            'fields': (
                'day_of_week',
                'hour_of_day',
                'was_peak_hour',
                'weather',
            ),
            'classes': ('collapse',)
        }),
        ('Contenedor (Auto)', {
            'fields': (
                'container_size',
                'container_type',
                'cargo_weight',
            ),
            'classes': ('collapse',)
        }),
        ('Retrasos', {
            'fields': (
                'had_delay',
                'delay_reason',
            )
        }),
        ('Notas', {
            'fields': ('notes',)
        })
    )
    
    def day_name(self, obj):
        days = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
        return days[obj.day_of_week] if obj.day_of_week is not None else '-'
    day_name.short_description = "Día"


@admin.register(ActualOperationRecord)
class ActualOperationRecordAdmin(admin.ModelAdmin):
    list_display = [
        'container',
        'location',
        'operation_type',
        'start_time',
        'duration_minutes',
        'had_issues'
    ]
    list_filter = ['operation_type', 'location', 'had_issues', 'day_of_week']
    search_fields = ['container__number', 'location__name']
    readonly_fields = [
        'duration_minutes',
        'day_of_week',
        'hour_of_day',
        'container_size',
        'created_at'
    ]
    date_hierarchy = 'start_time'


class RouteStopInline(admin.TabularInline):
    model = RouteStop
    extra = 1
    fields = [
        'stop_order',
        'container',
        'location',
        'action_type',
        'planned_arrival',
        'actual_arrival',
        'is_completed'
    ]
    readonly_fields = ['actual_arrival']


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'driver',
        'route_date',
        'status_badge',
        'progress',
        'total_containers',
        'duration_display'
    ]
    list_filter = ['status', 'route_date', 'driver']
    search_fields = ['name', 'driver__first_name', 'driver__last_name']
    readonly_fields = [
        'total_containers',
        'completed_stops',
        'actual_duration',
        'created_at',
        'updated_at'
    ]
    date_hierarchy = 'route_date'
    
    inlines = [RouteStopInline]
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('name', 'driver', 'vehicle', 'route_date', 'status')
        }),
        ('Tiempos Estimados', {
            'fields': (
                'estimated_start',
                'estimated_end',
                'estimated_duration',
            )
        }),
        ('Tiempos Reales', {
            'fields': (
                'actual_start',
                'actual_end',
                'actual_duration',
            )
        }),
        ('Estadísticas', {
            'fields': (
                'total_containers',
                'completed_stops',
                'total_distance_km',
            )
        }),
        ('Notas', {
            'fields': ('notes',)
        })
    )
    
    def status_badge(self, obj):
        colors = {
            'DRAFT': 'gray',
            'PLANNED': 'blue',
            'IN_PROGRESS': 'orange',
            'COMPLETED': 'green',
            'CANCELLED': 'red',
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.status, 'black'),
            obj.get_status_display()
        )
    status_badge.short_description = "Estado"
    
    def progress(self, obj):
        if obj.total_containers == 0:
            return "0%"
        
        percentage = (obj.completed_stops / obj.total_containers) * 100
        return format_html(
            '<div style="width: 100px; background: #f0f0f0; border-radius: 3px;">'
            '<div style="width: {}px; background: green; height: 20px; border-radius: 3px; text-align: center; color: white;">'
            '{:.0f}%'
            '</div></div>',
            percentage,
            percentage
        )
    progress.short_description = "Progreso"
    
    def duration_display(self, obj):
        if obj.actual_duration:
            return f"{obj.actual_duration} min (real)"
        elif obj.estimated_duration:
            return f"{obj.estimated_duration} min (est.)"
        return "-"
    duration_display.short_description = "Duración"
    
    actions = ['mark_as_in_progress', 'mark_as_completed']
    
    def mark_as_in_progress(self, request, queryset):
        updated = queryset.update(status='IN_PROGRESS')
        self.message_user(request, f"{updated} rutas marcadas como En Progreso")
    mark_as_in_progress.short_description = "▶️ Marcar como En Progreso"
    
    def mark_as_completed(self, request, queryset):
        updated = queryset.update(status='COMPLETED')
        self.message_user(request, f"{updated} rutas marcadas como Completadas")
    mark_as_completed.short_description = "✅ Marcar como Completadas"


@admin.register(RouteStop)
class RouteStopAdmin(admin.ModelAdmin):
    list_display = [
        'route',
        'stop_order',
        'container',
        'location',
        'action_type',
        'planned_arrival',
        'actual_arrival',
        'status_icon'
    ]
    list_filter = ['action_type', 'is_completed', 'location']
    search_fields = ['route__name', 'container__number']
    readonly_fields = [
        'delay_minutes',
        'actual_operation_time',
        'created_at',
        'updated_at'
    ]
    
    def status_icon(self, obj):
        if obj.is_completed:
            return format_html('<span style="color: green; font-size: 18px;">✅</span>')
        return format_html('<span style="color: gray; font-size: 18px;">⏳</span>')
    status_icon.short_description = "Estado"
