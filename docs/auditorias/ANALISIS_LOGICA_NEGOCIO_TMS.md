# Análisis de Lógica de Negocio - TMS Soptraloc

## Fecha: Octubre 8, 2025

---

## 1. CICLO DE VIDA DEL CONTENEDOR (Import Lifecycle)

### Estados Definidos en Container.CONTAINER_STATUS

```python
CONTAINER_STATUS = [
    # === Estados Básicos ===
    ('available', 'Disponible'),
    ('in_transit', 'En Tránsito'),
    ('loading', 'Cargando'),
    ('unloading', 'Descargando'),
    ('maintenance', 'Mantenimiento'),
    ('damaged', 'Dañado'),
    ('out_of_service', 'Fuera de Servicio'),
    
    # === Estados Específicos de Importación (Ciclo Completo) ===
    ('POR_ARRIBAR', 'Por Arribar'),                    # 1. Nave viene con contenedor
    ('EN_SECUENCIA', 'En Secuencia'),                  # Intermedio
    ('DESCARGADO', 'Descargado'),                      # Descargado en puerto
    ('LIBERADO', 'Liberado'),                          # 2. Liberado por aduana
    ('PROGRAMADO', 'Programado'),                      # 3. Programado para CD
    ('ASIGNADO', 'Asignado'),                          # 4. Con conductor asignado
    ('EN_RUTA', 'En Ruta'),                            # 5. En camino a CD
    ('ARRIBADO', 'Arribado'),                          # 6. Arribado a CD
    ('DESCARGADO_CD', 'Descargado en CD'),             # 7. Descargado en CD
    ('DISPONIBLE_DEVOLUCION', 'Disponible Devolución'), # 8. Listo para devolver
    ('EN_RUTA_DEVOLUCION', 'En Ruta Devolución'),     # 9. Devolviendo a puerto/CCTI
    ('FINALIZADO', 'Finalizado'),                      # 10. Ciclo completo
    ('TRG', 'TRG'),
    ('SECUENCIADO', 'Secuenciado'),
]
```

### Flujo Estándar (Happy Path)

```
POR_ARRIBAR → LIBERADO → PROGRAMADO → ASIGNADO → EN_RUTA → 
ARRIBADO → DESCARGADO_CD → DISPONIBLE_DEVOLUCION → 
EN_RUTA_DEVOLUCION → FINALIZADO
```

### Transiciones de Estado Implementadas

#### 📍 Ubicación: `apps/containers/views.py` - Acción `update_status`

**ASIGNADO → EN_RUTA** (Línea 480-498)
```python
if container.status == 'ASIGNADO' and container.conductor_asignado:
    position_stats = _apply_container_position_update(container, 'EN_RUTA', request.user)
    container.status = 'EN_RUTA'
    container.tiempo_inicio_ruta = timezone.now()
    container.save()
    
    # Actualizar Assignment
    assignment = Assignment.objects.filter(
        container=container,
        driver=container.conductor_asignado,
        estado='PENDIENTE'
    ).first()
    if assignment:
        assignment.estado = 'EN_CURSO'
        assignment.fecha_inicio = timezone.now()
        assignment.save()
```

**EN_RUTA → ARRIBADO** (Línea 524-546)
```python
if container.status == 'EN_RUTA':
    position_stats = _apply_container_position_update(container, cd_location, request.user)
    
    container.status = 'ARRIBADO'
    container.tiempo_llegada = timezone.now()
    container.save()
    
    # Actualizar Assignment con tiempo de ruta real
    assignment = Assignment.objects.filter(
        container=container,
        driver=container.conductor_asignado,
        estado='EN_CURSO'
    ).first()
    if assignment and assignment.fecha_inicio:
        route_minutes = int((timezone.now() - assignment.fecha_inicio).total_seconds() / 60)
        assignment.ruta_minutos_real = route_minutes
        assignment.save()
```

**ARRIBADO → FINALIZADO** (Línea 667-688 en `update_status`)
```python
if new_status == 'FINALIZADO':
    container.tiempo_finalizacion = now
    # Calcular duración de descarga
    if container.tiempo_llegada:
        delta = now - container.tiempo_llegada
        container.duracion_descarga = int(delta.total_seconds() / 60)
    # Calcular duración total
    if container.tiempo_asignacion:
        delta_total = now - container.tiempo_asignacion
        container.duracion_total = int(delta_total.total_seconds() / 60)
    
    # Completar Assignment y alimentar matriz de tiempos
    assignment = Assignment.objects.filter(
        container=container,
        driver=container.conductor_asignado,
        estado__in=['PENDIENTE', 'EN_CURSO']
    ).first()
    if assignment:
        assignment.record_actual_times(
            total_minutes=total_minutes,
            route_minutes=route_recorded,
            unloading_minutes=unloading_minutes,
        )
```

---

## 2. SISTEMA DE ASIGNACIÓN (Driver Assignment)

### Estados de Assignment

```python
ESTADO_ASIGNACION_CHOICES = [
    ('PENDIENTE', 'Pendiente'),      # Asignación creada, conductor notificado
    ('EN_CURSO', 'En Curso'),        # Conductor en camino/trabajando
    ('COMPLETADA', 'Completada'),    # Ciclo finalizado
    ('CANCELADA', 'Cancelada'),      # Asignación cancelada
]
```

### Tipos de Asignación

```python
TIPO_ASIGNACION_CHOICES = [
    ('ENTREGA', 'Entrega a cliente'),              # Terminal → CD
    ('DEVOLUCION', 'Devolución a depósito/CCTI'),  # CD → Terminal
]
```

### Flujo de Asignación

1. **Creación de Assignment** (Estado: PENDIENTE)
   - Se asigna conductor disponible a contenedor PROGRAMADO
   - Se calcula `tiempo_estimado` usando matriz de tiempos o predictor ML
   - Se vincula origen y destino (Location)

2. **Inicio de Ruta** (Estado: EN_CURSO)
   - Container cambia de ASIGNADO → EN_RUTA
   - Assignment cambia de PENDIENTE → EN_CURSO
   - Se registra `fecha_inicio` para medir tiempo real

3. **Finalización** (Estado: COMPLETADA)
   - Container cambia a FINALIZADO
   - Se llama a `assignment.record_actual_times()` que:
     - Guarda `tiempo_real`, `ruta_minutos_real`, `descarga_minutos_real`
     - **Alimenta la matriz de tiempos** con datos reales
     - Marca assignment como COMPLETADA

### Validación de Disponibilidad

📍 `apps/drivers/models.py` - Método `is_available_for_new_assignment()`

```python
def is_available_for_new_assignment(self, start_time, duration_minutes):
    """Verifica si el conductor está disponible para una nueva asignación"""
    end_time = start_time + timedelta(minutes=duration_minutes)
    
    # Buscar asignaciones que se solapen en el tiempo
    overlapping = Assignment.objects.filter(
        driver=self.driver,
        estado__in=['PENDIENTE', 'EN_CURSO'],
        fecha_programada__lt=end_time,
        fecha_programada__gte=start_time - timedelta(minutes=self.tiempo_estimado)
    ).exclude(id=self.id if self.id else None)
    
    return not overlapping.exists()
```

**PROBLEMA IDENTIFICADO:** Este método está en `Assignment`, pero valida disponibilidad de `self.driver`. Debería ser un método de `Driver` o un servicio externo.

---

## 3. MATRIZ DE TIEMPOS Y APRENDIZAJE AUTOMÁTICO

### TimeMatrix - Sistema de Predicción

📍 `apps/drivers/models.py` - Clase `TimeMatrix`

#### Campos Clave

```python
class TimeMatrix:
    # Tiempos base (manual)
    travel_time = IntegerField(help_text="Tiempo de viaje en minutos")
    loading_time = IntegerField(default=0, help_text="Tiempo de carga en minutos")
    unloading_time = IntegerField(default=0, help_text="Tiempo de descarga en minutos")
    
    # Tiempos aprendidos (históricos)
    avg_travel_time = FloatField(null=True, help_text="Tiempo promedio histórico")
    min_travel_time = IntegerField(null=True)
    max_travel_time = IntegerField(null=True)
    
    # Estadísticas
    total_trips = IntegerField(default=0)
    last_updated = DateTimeField(auto_now=True)
```

#### Cálculo de Tiempo Total

```python
def get_total_time(self, use_learned: bool = True) -> int:
    """Tiempo total estimado incluyendo viaje, carga y descarga."""
    travel_component = self.travel_time
    if use_learned and self.avg_travel_time is not None:
        travel_component = int(round(self.avg_travel_time))

    total = travel_component + self.loading_time + self.unloading_time
    return max(int(round(total)), 15)  # Mínimo 15 minutos
```

#### Actualización con Datos Reales

```python
def update_historical_data(self, actual_total_minutes: int, 
                          route_minutes: int | None = None, 
                          unloading_minutes: int | None = None):
    """Actualiza la matriz de tiempos con datos reales recibidos."""
    
    # Inferir tiempo de ruta si no se proporciona
    inferred_route = route_minutes
    if inferred_route is None:
        inferred_route = max(actual_total_minutes - (self.loading_time + self.unloading_time), 0)
    
    # Suavizado exponencial (smoothing = 0.6)
    smoothing = 0.6
    if self.avg_travel_time is None:
        self.avg_travel_time = inferred_route
    else:
        self.avg_travel_time = (self.avg_travel_time * smoothing) + 
                                (inferred_route * (1 - smoothing))
    
    # Actualizar límites observados
    if self.min_travel_time is None or inferred_route < self.min_travel_time:
        self.min_travel_time = inferred_route
    
    if self.max_travel_time is None or inferred_route > self.max_travel_time:
        self.max_travel_time = inferred_route
    
    # Actualizar tiempos manuales con promedio aprendido
    if inferred_route > 0:
        self.travel_time = max(int(round(self.avg_travel_time)), 1)
    
    # Actualizar tiempo de descarga si se proporciona
    if unloading_minutes is not None:
        self.unloading_time = max(unloading_minutes, self.unloading_time)
    
    self.total_trips += 1
    self.save()
```

**EVALUACIÓN:**
- ✅ **Excelente:** Sistema de aprendizaje incremental con suavizado exponencial
- ✅ **Robusto:** Maneja casos donde faltan datos
- ⚠️ **Mejora posible:** Considerar día de la semana y hora del día para mejor predicción

---

## 4. CAMPOS DE SEGUIMIENTO TEMPORAL

### Container - Tracking Fields

```python
# Tiempos de seguimiento operativo
tiempo_asignacion = DateTimeField(null=True, blank=True)
tiempo_inicio_ruta = DateTimeField(null=True, blank=True)
tiempo_llegada = DateTimeField(null=True, blank=True)
tiempo_descarga = DateTimeField(null=True, blank=True)
tiempo_finalizacion = DateTimeField(null=True, blank=True)
tiempo_inicio_devolucion = DateTimeField(null=True, blank=True)
tiempo_arribo_devolucion = DateTimeField(null=True, blank=True)

# Duración calculada (en minutos)
duracion_total = IntegerField(null=True, blank=True)
duracion_ruta = IntegerField(null=True, blank=True)
duracion_descarga = IntegerField(null=True, blank=True)
duracion_devolucion = IntegerField(null=True, blank=True)
```

**FLUJO DE REGISTRO DE TIEMPOS:**

1. **ASIGNADO**: Se registra `tiempo_asignacion = now()`
2. **EN_RUTA**: Se registra `tiempo_inicio_ruta = now()`
3. **ARRIBADO**: Se registra `tiempo_llegada = now()` + se calcula `duracion_ruta`
4. **FINALIZADO**: Se registra `tiempo_finalizacion = now()` + se calculan `duracion_descarga` y `duracion_total`

---

## 5. SISTEMA DE ALERTAS Y DEMURRAGE

### Campos Relacionados con Demurrage

```python
free_days = IntegerField(default=0, verbose_name="Días libres")
demurrage_date = DateField(blank=True, null=True, verbose_name="Demurrage")
overtime_2h = IntegerField(default=0, verbose_name="Sobreestadía región (x ciclo 2 horas)")
overtime_4h = IntegerField(default=0, verbose_name="Sobreestadía (x ciclo de 4 horas)")
extra_storage_days = IntegerField(default=0, verbose_name="Días extras de almacenaje")
```

### Métodos de Validación

```python
def days_since_release(self):
    """Calcula días desde la liberación."""
    if self.release_date:
        return (timezone.now().date() - self.release_date).days
    return 0

def is_overdue(self):
    """Verifica si está en sobreestadía."""
    if self.demurrage_date:
        return timezone.now().date() > self.demurrage_date
    return False
```

**PROBLEMA IDENTIFICADO:** No se encontró lógica automática de alertas en views.py o servicios. Las alertas deberían generarse proactivamente.

---

## 6. MOVIMIENTOS DE CONTENEDORES

### ContainerMovement - Registro Histórico

```python
MOVEMENT_TYPES = [
    # Tipos básicos
    ('load_chassis', 'Cargar en Chasis'),
    ('unload_chassis', 'Descargar de Chasis'),
    ('transfer_warehouse', 'Transferir a Almacén'),
    ('transfer_location', 'Transferir Ubicación'),
    ('maintenance_in', 'Ingreso a Mantenimiento'),
    ('maintenance_out', 'Salida de Mantenimiento'),
    ('import', 'Importación'),
    ('export', 'Exportación'),
    
    # Tipos específicos de importación
    ('PICKUP', 'Retiro'),
    ('DELIVERY', 'Entrega'),
    ('STORAGE_IN', 'Ingreso a almacén'),
    ('STORAGE_OUT', 'Salida de almacén'),
    ('CHASSIS_MOUNT', 'Montaje en chasis'),
    ('CHASSIS_DISMOUNT', 'Desmontaje de chasis'),
    ('TRANSFER', 'Transferencia'),
]
```

### Actualización Automática en save()

```python
def save(self, *args, **kwargs):
    """Actualiza la posición del contenedor al guardar el movimiento."""
    super().save(*args, **kwargs)
    
    # Actualizar posición del contenedor
    if self.movement_type in ['load_chassis', 'CHASSIS_MOUNT']:
        self.container.position_status = 'chassis'
        self.container.current_vehicle = self.to_vehicle
        self.container.current_location = None
    elif self.movement_type in ['unload_chassis', 'CHASSIS_DISMOUNT']:
        self.container.position_status = 'floor'
        self.container.current_location = self.to_location
        self.container.current_vehicle = None
    # ... más lógica
    self.container.save()
```

**EVALUACIÓN:**
- ✅ **Excelente:** Registro automático de historial de movimientos
- ✅ **Robusto:** Sincronización automática de posición del contenedor
- ⚠️ **Mejora posible:** Validar que no haya movimientos duplicados o inconsistentes

---

## 7. POSICIONAMIENTO Y UBICACIÓN ACTUAL

### current_position vs current_location

```python
# Container tiene DOS sistemas de posición:

# 1. Campo de posición específica (choices limitadas)
current_position = CharField(
    max_length=30,
    choices=[
        ('EN_PISO', 'En Piso'),
        ('EN_CHASIS', 'En Chasis'),
        ('CCTI', 'CCTI'),
        ('ZEAL', 'ZEAL'),
        ('CLEP', 'CLEP'),
        ('EN_RUTA', 'En Ruta'),
        ('CD_QUILICURA', 'CD Quilicura'),
        ('CD_CAMPOS', 'CD Campos'),
        ('CD_MADERO', 'CD Puerto Madero'),
        ('CD_PENON', 'CD El Peñón'),
        ('DEPOSITO_DEVOLUCION', 'Depósito Devolución'),
    ],
    blank=True,
)

# 2. Ubicación mediante ForeignKey (escalable)
current_location = ForeignKey(Location, on_delete=SET_NULL, null=True, blank=True)
current_vehicle = ForeignKey(Vehicle, on_delete=SET_NULL, null=True, blank=True)
```

**PROBLEMA IDENTIFICADO:** Dualidad de sistemas de ubicación causa confusión. Se recomienda usar exclusivamente `current_location` (ForeignKey) y eliminar `current_position`.

---

## 8. EVALUACIÓN GENERAL DEL SISTEMA

### ✅ Fortalezas

1. **Modelo de Datos Robusto:**
   - Container tiene todos los campos necesarios para ciclo completo
   - Tracking temporal completo con timestamps
   - Sistema de devolución bien modelado

2. **Sistema de Aprendizaje:**
   - TimeMatrix con actualización incremental
   - Suavizado exponencial para promedios
   - Alimentación automática desde Assignment.record_actual_times()

3. **Historial de Movimientos:**
   - ContainerMovement registra todo
   - Sincronización automática de posición

4. **Asignación de Conductores:**
   - Validación de disponibilidad
   - Tracking de tiempos reales
   - Integración con matriz de tiempos

### ⚠️ Áreas de Mejora Críticas

1. **Transiciones de Estado Incompletas:**
   - ❌ No hay transición PROGRAMADO → ASIGNADO (debe implementarse)
   - ❌ No hay transición DESCARGADO_CD → DISPONIBLE_DEVOLUCION
   - ❌ No hay transición DISPONIBLE_DEVOLUCION → EN_RUTA_DEVOLUCION
   - ⚠️ Falta validación de transiciones permitidas (máquina de estados)

2. **Sistema de Alertas Incompleto:**
   - ❌ No hay generación automática de alertas de demurrage
   - ❌ No hay alertas por retrasos en ruta
   - ❌ No hay notificaciones proactivas
   - ⚠️ Modelo Alert existe pero no se usa en lógica de negocio

3. **Duplicidad de Ubicación:**
   - ⚠️ `current_position` (CharField) vs `current_location` (FK)
   - ⚠️ Inconsistencias posibles entre ambos sistemas

4. **Validación de Asignaciones:**
   - ⚠️ `is_available_for_new_assignment()` está en Assignment, debería ser método de Driver
   - ❌ No hay validación de que conductor no esté en PANNE o AUSENTE

5. **Predicción de Tiempos:**
   - ⚠️ No considera hora del día ni día de la semana
   - ⚠️ No hay integración con tráfico en tiempo real (aunque existe TrafficAlert model)

### 🔧 Recomendaciones de Implementación

#### Prioridad Alta (Crítico para TMS funcional)

1. **Implementar Máquina de Estados:**
   ```python
   ALLOWED_TRANSITIONS = {
       'LIBERADO': ['PROGRAMADO'],
       'PROGRAMADO': ['ASIGNADO', 'CANCELADO'],
       'ASIGNADO': ['EN_RUTA', 'CANCELADO'],
       'EN_RUTA': ['ARRIBADO'],
       'ARRIBADO': ['DESCARGADO_CD'],
       'DESCARGADO_CD': ['DISPONIBLE_DEVOLUCION'],
       'DISPONIBLE_DEVOLUCION': ['EN_RUTA_DEVOLUCION'],
       'EN_RUTA_DEVOLUCION': ['FINALIZADO'],
   }
   
   def can_transition_to(self, new_status):
       return new_status in ALLOWED_TRANSITIONS.get(self.status, [])
   ```

2. **Sistema de Alertas Automático:**
   - Celery task que corra cada hora
   - Detectar contenedores cerca de demurrage_date
   - Crear registros en Alert model
   - Enviar notificaciones

3. **Servicio de Asignación Automática:**
   - Método en Driver: `get_available_drivers(start_time, duration)`
   - Algoritmo de asignación óptima (nearest available driver)
   - Validación de estado del conductor

#### Prioridad Media (Mejoras operativas)

1. **Consolidar Sistema de Ubicación:**
   - Eliminar `current_position` CharField
   - Usar solo `current_location` FK
   - Migrar datos existentes

2. **Mejorar Predicción de Tiempos:**
   - Agregar campos hour_of_day, day_of_week a TimeMatrix
   - Usar regresión por intervalos horarios
   - Integrar con TrafficAlert para ajustes en tiempo real

3. **Dashboard de Métricas:**
   - KPIs: Tiempo promedio por ruta
   - Tasa de sobreestadía
   - Eficiencia de conductores

#### Prioridad Baja (Optimizaciones)

1. **Tests Automatizados:**
   - Tests de flujo completo (LIBERADO → FINALIZADO)
   - Tests de Assignment
   - Tests de TimeMatrix learning

2. **API Documentation:**
   - Swagger/OpenAPI
   - Ejemplos de uso

---

## 9. CÓDIGO FALTANTE CRÍTICO

### A. Transición PROGRAMADO → ASIGNADO

**Ubicación recomendada:** `apps/containers/views.py` - nueva acción `assign_driver`

```python
@action(detail=True, methods=['post'])
def assign_driver(self, request, pk=None):
    """
    Asigna un conductor a un contenedor PROGRAMADO.
    
    POST /api/containers/{id}/assign_driver/
    Body: {
        "driver_id": 123,
        "scheduled_datetime": "2025-10-08T10:00:00Z",
        "origin_id": 5,
        "destination_id": 12
    }
    """
    container = self.get_object()
    
    # Validar estado
    if container.status != 'PROGRAMADO':
        return JsonResponse({
            'success': False,
            'message': 'El contenedor debe estar en estado PROGRAMADO'
        }, status=400)
    
    # Obtener datos
    driver_id = request.data.get('driver_id')
    scheduled_datetime = request.data.get('scheduled_datetime')
    origin_id = request.data.get('origin_id')
    destination_id = request.data.get('destination_id')
    
    # Validar conductor
    try:
        driver = Driver.objects.get(id=driver_id, is_active=True)
    except Driver.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Conductor no encontrado'
        }, status=404)
    
    # Validar disponibilidad
    if not driver.esta_disponible:
        return JsonResponse({
            'success': False,
            'message': f'Conductor {driver.nombre} no está disponible. Estado: {driver.get_estado_display()}'
        }, status=400)
    
    # Crear asignación
    try:
        origin = Location.objects.get(id=origin_id)
        destination = Location.objects.get(id=destination_id)
    except Location.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Ubicación origen o destino no encontrada'
        }, status=404)
    
    assignment = Assignment.objects.create(
        container=container,
        driver=driver,
        fecha_programada=scheduled_datetime,
        origen=origin,
        destino=destination,
        tipo_asignacion='ENTREGA',
        estado='PENDIENTE',
        created_by=request.user
    )
    
    # Calcular tiempo estimado
    assignment.calculate_estimated_time(refresh=True)
    assignment.save()
    
    # Actualizar container
    container.status = 'ASIGNADO'
    container.conductor_asignado = driver
    container.tiempo_asignacion = timezone.now()
    container.save()
    
    # Actualizar driver
    driver.contenedor_asignado = container
    driver.save()
    
    return JsonResponse({
        'success': True,
        'message': f'Contenedor asignado a {driver.nombre}',
        'assignment_id': assignment.id,
        'estimated_duration': assignment.tiempo_estimado
    })
```

### B. Sistema de Alertas Automático

**Ubicación:** `apps/containers/tasks.py` (nuevo archivo)

```python
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from apps.containers.models import Container
from apps.drivers.models import Alert

@shared_task
def generate_demurrage_alerts():
    """
    Tarea programada para generar alertas de demurrage.
    Ejecutar cada hora.
    """
    now = timezone.now().date()
    
    # Contenedores cerca de demurrage (3 días antes)
    warning_date = now + timedelta(days=3)
    
    containers_at_risk = Container.objects.filter(
        demurrage_date__lte=warning_date,
        demurrage_date__gt=now,
        status__in=['LIBERADO', 'PROGRAMADO', 'ASIGNADO', 'EN_RUTA', 'ARRIBADO']
    )
    
    for container in containers_at_risk:
        days_remaining = (container.demurrage_date - now).days
        
        # Verificar si ya existe alerta
        existing_alert = Alert.objects.filter(
            container=container,
            alert_type='DEMURRAGE_WARNING',
            is_resolved=False
        ).exists()
        
        if not existing_alert:
            Alert.objects.create(
                container=container,
                alert_type='DEMURRAGE_WARNING',
                priority='HIGH' if days_remaining <= 1 else 'MEDIUM',
                message=f'Contenedor {container.container_number} tiene {days_remaining} días hasta demurrage',
                expires_at=container.demurrage_date + timedelta(days=1)
            )
    
    # Contenedores ya en demurrage
    containers_overdue = Container.objects.filter(
        demurrage_date__lt=now,
        status__in=['LIBERADO', 'PROGRAMADO', 'ASIGNADO', 'EN_RUTA', 'ARRIBADO']
    )
    
    for container in containers_overdue:
        days_overdue = (now - container.demurrage_date).days
        
        existing_alert = Alert.objects.filter(
            container=container,
            alert_type='DEMURRAGE_OVERDUE',
            is_resolved=False
        ).exists()
        
        if not existing_alert:
            Alert.objects.create(
                container=container,
                alert_type='DEMURRAGE_OVERDUE',
                priority='CRITICAL',
                message=f'URGENTE: Contenedor {container.container_number} lleva {days_overdue} días en demurrage',
                expires_at=now + timedelta(days=30)
            )
    
    return {
        'warnings_generated': containers_at_risk.count(),
        'overdue_alerts': containers_overdue.count()
    }


@shared_task
def check_delayed_deliveries():
    """
    Detecta contenedores que deberían haber arribado pero no lo han hecho.
    """
    now = timezone.now()
    
    # Assignments en curso que excedieron tiempo estimado
    delayed = Assignment.objects.filter(
        estado='EN_CURSO',
        fecha_inicio__isnull=False
    )
    
    alerts_created = 0
    
    for assignment in delayed:
        elapsed_minutes = (now - assignment.fecha_inicio).total_seconds() / 60
        
        if elapsed_minutes > (assignment.tiempo_estimado * 1.5):  # 50% de retraso
            existing_alert = Alert.objects.filter(
                container=assignment.container,
                alert_type='DELIVERY_DELAYED',
                is_resolved=False
            ).exists()
            
            if not existing_alert:
                Alert.objects.create(
                    container=assignment.container,
                    driver=assignment.driver,
                    alert_type='DELIVERY_DELAYED',
                    priority='HIGH',
                    message=f'Entrega retrasada: {assignment.driver.nombre} lleva {int(elapsed_minutes)} minutos (estimado: {assignment.tiempo_estimado} min)'
                )
                alerts_created += 1
    
    return {'delayed_alerts_created': alerts_created}
```

---

## 10. PRÓXIMOS PASOS RECOMENDADOS

### Fase Actual: Validación de Lógica de Negocio

1. ✅ **COMPLETADO**: Analizar ciclo de vida del contenedor
2. ✅ **COMPLETADO**: Revisar sistema de asignaciones
3. ✅ **COMPLETADO**: Evaluar matriz de tiempos
4. 🔄 **SIGUIENTE**: Implementar transiciones faltantes
5. 🔄 **SIGUIENTE**: Crear sistema de alertas automático
6. ⏳ **PENDIENTE**: Tests end-to-end del flujo completo

### Orden de Implementación Sugerido

```
Día 1:
- Implementar máquina de estados (ALLOWED_TRANSITIONS)
- Agregar validación en Container.save()
- Tests de transiciones

Día 2:
- Implementar assign_driver endpoint
- Tests de asignación
- UI para asignar conductores

Día 3:
- Configurar Celery
- Implementar generate_demurrage_alerts task
- Implementar check_delayed_deliveries task
- Schedule tasks (hourly)

Día 4:
- Consolidar sistema de ubicación (eliminar current_position)
- Migración de datos
- Tests

Día 5:
- Dashboard de alertas
- API para consultar alertas activas
- Notificaciones por email/SMS
```

---

## 11. MÉTRICAS DE SALUD DEL SISTEMA

### KPIs Sugeridos

```python
# apps/containers/services/metrics.py

def get_system_health_metrics():
    """Retorna métricas clave del TMS."""
    from django.db.models import Avg, Count, Q
    from datetime import datetime, timedelta
    
    now = timezone.now()
    last_week = now - timedelta(days=7)
    
    return {
        # Eficiencia operativa
        'avg_delivery_time': Assignment.objects.filter(
            estado='COMPLETADA',
            fecha_completada__gte=last_week
        ).aggregate(Avg('tiempo_real'))['tiempo_real__avg'],
        
        'on_time_percentage': calculate_on_time_percentage(last_week),
        
        # Estado de contenedores
        'containers_in_demurrage': Container.objects.filter(
            demurrage_date__lt=now.date(),
            status__in=['LIBERADO', 'PROGRAMADO', 'ASIGNADO']
        ).count(),
        
        'containers_at_risk': Container.objects.filter(
            demurrage_date__lte=now.date() + timedelta(days=3),
            demurrage_date__gt=now.date()
        ).count(),
        
        # Conductores
        'active_drivers': Driver.objects.filter(
            estado='OPERATIVO',
            is_active=True
        ).count(),
        
        'drivers_with_assignment': Driver.objects.filter(
            contenedor_asignado__isnull=False
        ).count(),
        
        # Alertas
        'critical_alerts': Alert.objects.filter(
            is_resolved=False,
            priority='CRITICAL'
        ).count(),
        
        'high_priority_alerts': Alert.objects.filter(
            is_resolved=False,
            priority='HIGH'
        ).count(),
    }
```

---

## CONCLUSIÓN

El sistema **Soptraloc TMS** tiene una **base arquitectónica sólida** tras la consolidación de modelos. Los componentes principales están bien diseñados:

✅ Modelo de datos completo y robusto
✅ Sistema de aprendizaje automático (TimeMatrix) funcional
✅ Tracking temporal detallado
✅ Historial de movimientos automático

Sin embargo, para ser un **TMS production-ready**, requiere:

🔴 **CRÍTICO:**
- Implementar transiciones de estado faltantes
- Sistema de alertas automático
- Validación de asignaciones

🟡 **IMPORTANTE:**
- Consolidar sistema de ubicación
- Mejorar predicción de tiempos
- Dashboard de métricas

Con estas implementaciones, el sistema estará completo y listo para operación en producción.

---

**Documento generado:** Octubre 8, 2025
**Autor:** GitHub Copilot (Análisis profundo)
**Estado:** Fase 2 - Auditoría de Lógica de Negocio
