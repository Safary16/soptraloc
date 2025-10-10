# ⚙️ AUDITORÍA - FASE 3: LÓGICA DE NEGOCIO Y SERVICIOS

**Fecha**: 2025-01-10  
**Auditor**: GitHub Copilot  
**Alcance**: Análisis exhaustivo de servicios, reglas de negocio, validaciones, importadores, ML, y flujos operativos

---

## 📊 RESUMEN EJECUTIVO

### Estadísticas de Servicios
- **Servicios de negocio**: 8 archivos principales
- **Líneas de lógica**: ~2,500 líneas (servicios + views con lógica)
- **Servicios críticos**:
  - `excel_importers.py` (800 líneas) - Importación de manifiestos
  - `ml_service.py` (434 líneas) - Machine Learning de tiempos
  - `demurrage.py` (140 líneas) - Alertas de sobrestadía
  - `status_utils.py` (138 líneas) - Normalización de estados
- **Funciones de negocio**: 40+ funciones de servicios
- **Validaciones**: Dispersas (sin centralizar)

### Veredicto General de Lógica de Negocio
🟡 **MODERADO/BUENO** - Lógica funcional y bien organizada en servicios, pero con **validaciones débiles**, **manejo de errores mejorable**, y **falta de tests unitarios críticos**.

---

## 1️⃣ ANÁLISIS POR DOMINIO DE NEGOCIO

### 🟢 **DOMINIO: Importación de Contenedores (BIEN DISEÑADO)**

#### Archivo: `apps/containers/services/excel_importers.py` (800 líneas)

**✅ BUENAS PRÁCTICAS DETECTADAS**:

```python
# ✅ 1. Uso de dataclasses para resultados
@dataclass
class ImportSummary:
    """Resultado estructurado de importación"""
    file_name: str
    created: int
    updated: int
    errors: int
    messages: List[str]
    
    def as_dict(self) -> dict:
        return {...}

# ✅ 2. Transacciones atómicas
@transaction.atomic
def import_vessel_manifest(files: Iterable[BytesIO], user: User) -> List[ImportSummary]:
    """Importa manifiestos con rollback automático en errores"""
    ...

# ✅ 3. Normalización centralizada
MANIFEST_COLUMN_MAP = {
    "naveconfirmado": "vessel_name",
    "containernumbers": "container_number",
    ...
}

# ✅ 4. Type hints completos
def _get_or_create_vessel(
    name: Optional[str], 
    shipping_line: ShippingLine, 
    user: User
) -> Optional[Vessel]:
    ...
```

**Fortalezas**:
- ✅ Manejo robusto de variaciones de columnas Excel
- ✅ Transacciones para integridad de datos
- ✅ Logging detallado de operaciones
- ✅ Retorno de resultados estructurados

---

**🔴 PROBLEMAS CRÍTICOS**:

```python
# ❌ 1. FUNCIÓN DEMASIADO LARGA (líneas 331-530 = 200 líneas)
def import_vessel_manifest(files: Iterable[BytesIO], user: User) -> List[ImportSummary]:
    """❌ Función monolítica con múltiples responsabilidades"""
    # Línea 331-400: Procesamiento de archivos
    # Línea 400-450: Normalización de datos
    # Línea 450-500: Creación/actualización de modelos
    # Línea 500-530: Generación de resumen
    # ← Debería dividirse en 4-5 funciones más pequeñas
```

**Refactorización sugerida**:
```python
# ✅ SOLUCIÓN: Dividir en funciones cohesivas

def import_vessel_manifest(files: Iterable[BytesIO], user: User) -> List[ImportSummary]:
    """Orquestador principal"""
    summaries = []
    for file in files:
        summary = _process_single_manifest_file(file, user)
        summaries.append(summary)
    return summaries

@transaction.atomic
def _process_single_manifest_file(file: BytesIO, user: User) -> ImportSummary:
    """Procesa un solo archivo"""
    df = _load_and_validate_manifest(file)
    normalized_df = _normalize_manifest_columns(df)
    results = _import_manifest_rows(normalized_df, user)
    return _build_import_summary(file.name, results)

def _import_manifest_rows(df: pd.DataFrame, user: User) -> Dict:
    """Importa filas del dataframe"""
    for _, row in df.iterrows():
        _import_single_container_from_manifest(row, user)
```

---

```python
# ❌ 2. LÓGICA DE ASIGNACIÓN AUTOMÁTICA EN IMPORTADOR
def assign_driver_by_location(container: Container, user: User) -> Optional[Driver]:
    """❌ Mezclando responsabilidades: importación + asignación"""
    # ← Esta función debería estar en drivers/services/assignment_service.py
    ...
```

**Impacto**: Violación de Single Responsibility Principle.

**Solución**:
```python
# ✅ Mover a drivers/services/assignment_service.py
class DriverAssignmentService:
    @staticmethod
    def assign_by_location(container: Container, user: User) -> Optional[Driver]:
        """Asigna conductor según ubicación del contenedor"""
        ...
```

---

```python
# ❌ 3. VALIDACIONES DÉBILES
def _attach_operational_location(container: Container, user: User) -> None:
    """❌ Sin validación de ubicación nula o inválida"""
    location_code = _infer_location_code_from_container(container)
    location = Location.objects.filter(code=location_code).first()
    
    container.current_location = location  # ← ¿Qué pasa si location es None?
    container.save()

# ✅ SOLUCIÓN: Validar y manejar casos edge
def _attach_operational_location(container: Container, user: User) -> None:
    location_code = _infer_location_code_from_container(container)
    
    if not location_code:
        logger.warning(f"No se pudo inferir ubicación para {container.container_number}")
        return
    
    location = Location.objects.filter(code=location_code).first()
    if not location:
        logger.error(f"Ubicación {location_code} no existe en BD")
        raise ValueError(f"Ubicación inválida: {location_code}")
    
    container.current_location = location
    container.save()
```

---

### 🟢 **DOMINIO: Machine Learning (BIEN IMPLEMENTADO)**

#### Archivo: `apps/routing/ml_service.py` (434 líneas)

**✅ EXCELENTE DISEÑO**:

```python
class TimePredictionML:
    """
    ✅ Clase bien estructurada con métodos claros
    """
    
    # ✅ Constantes configurables
    RECENT_DATA_WEIGHT = 0.6
    HISTORICAL_DATA_WEIGHT = 0.4
    MIN_SAMPLES_FOR_ML = 5
    RECENT_DAYS = 30
    
    @classmethod
    def update_all_predictions(cls):
        """✅ API pública clara"""
        ...
    
    @classmethod
    def _update_single_location_pair(cls, pair: LocationPair) -> bool:
        """✅ Método privado para detalle de implementación"""
        # 1. Obtener datos reales
        all_trips = ActualTripRecord.objects.filter(...)
        
        # 2. Verificar cantidad mínima
        if total_count < cls.MIN_SAMPLES_FOR_ML:
            return False
        
        # 3. Separar reciente vs histórico
        recent_trips = all_trips.filter(departure_time__gte=recent_cutoff)
        
        # 4. Calcular promedio ponderado
        predicted_time = int(
            (recent_avg * cls.RECENT_DATA_WEIGHT) +
            (historical_avg * cls.HISTORICAL_DATA_WEIGHT)
        )
        
        # 5. Calcular confianza
        confidence = ...
        
        # 6. Actualizar modelo
        pair.ml_predicted_time = predicted_time
        pair.save()
        
        return True
```

**Fortalezas**:
- ✅ Algoritmo simple pero efectivo (promedio ponderado)
- ✅ Cálculo de confianza basado en cantidad y variabilidad
- ✅ Logging informativo
- ✅ Manejo de casos sin datos suficientes

---

**🟡 MEJORAS POSIBLES**:

```python
# ⚠️ 1. ALGORITMO BÁSICO (no es error, pero puede mejorar)
# Actual: Promedio ponderado
predicted_time = int(
    (recent_avg * 0.6) + (historical_avg * 0.4)
)

# ✅ MEJORA FUTURA: Considerar factores adicionales
# - Hora del día (hora pico vs normal)
# - Día de la semana (lunes vs domingo)
# - Clima (si disponible)
# - Tráfico en tiempo real (Mapbox)

# ✅ PROPUESTA: Modelo de regresión lineal simple
from sklearn.linear_model import LinearRegression

def _train_ml_model(trips: QuerySet) -> LinearRegression:
    """Entrena modelo con características adicionales"""
    X = []  # Features: [hora, día_semana, histórico_avg]
    y = []  # Target: duration_minutes
    
    for trip in trips:
        X.append([
            trip.departure_time.hour,
            trip.departure_time.weekday(),
            historical_avg,
        ])
        y.append(trip.duration_minutes)
    
    model = LinearRegression()
    model.fit(X, y)
    return model
```

---

```python
# ⚠️ 2. NO HAY MÉTRICAS DE PRECISIÓN DEL MODELO
# ✅ AGREGAR: Evaluación de performance

def _evaluate_ml_accuracy(pair: LocationPair) -> Dict:
    """Calcula precisión del modelo"""
    recent_trips = ActualTripRecord.objects.filter(
        origin=pair.origin,
        destination=pair.destination,
        departure_time__gte=timezone.now() - timedelta(days=30)
    )
    
    errors = []
    for trip in recent_trips:
        predicted = pair.ml_predicted_time
        actual = trip.duration_minutes
        error_pct = abs(predicted - actual) / actual * 100
        errors.append(error_pct)
    
    return {
        'mean_error_pct': sum(errors) / len(errors) if errors else 0,
        'samples': len(errors),
        'confidence': pair.ml_confidence,
    }
```

---

### 🟢 **DOMINIO: Alertas de Demurrage (CORRECTO)**

#### Archivo: `apps/containers/services/demurrage.py` (140 líneas)

**✅ BUENAS PRÁCTICAS**:

```python
# ✅ 1. Constantes configurables
DEMURRAGE_ALERT_THRESHOLD_DAYS = 2

# ✅ 2. Función pura y predecible
def create_demurrage_alert_if_needed(
    container, 
    *, 
    resolved_by=None
) -> Optional[DemurrageAlertResult]:
    """
    ✅ Nombre descriptivo
    ✅ Keyword-only argument (resolved_by)
    ✅ Retorno tipado
    ✅ Idempotente (puede llamarse múltiples veces sin efectos secundarios)
    """
    if not container.demurrage_date:
        _resolve_existing_alerts(container, resolved_by=resolved_by)
        return None  # ← Caso edge manejado
    
    days_until = (container.demurrage_date - today).days
    
    # Lógica clara de severidad
    if days_until >= 0:
        alert_type = "DEMURRAGE_PROXIMO"
        prioridad = "ALTA" if days_until <= 1 else "MEDIA"
    else:
        alert_type = "DEMURRAGE_VENCIDO"
        prioridad = "CRITICA"
    
    # ✅ get_or_create con defaults
    alert, created = Alert.objects.get_or_create(
        container=container,
        tipo=alert_type,
        defaults={...}
    )
    
    return DemurrageAlertResult(alert=alert, ...)
```

**Fortalezas**:
- ✅ Lógica clara y legible
- ✅ Manejo correcto de casos edge
- ✅ Actualización idempotente de alertas
- ✅ Resolución automática de alertas obsoletas

---

**🟡 MEJORA MENOR**:

```python
# ⚠️ CONSTANTE HARDCODEADA
DEMURRAGE_ALERT_THRESHOLD_DAYS = 2  # ← ¿Debería ser configurable por cliente?

# ✅ MEJORA: Mover a settings.py o modelo de configuración
# settings.py
DEMURRAGE_THRESHOLD_DAYS = int(os.getenv('DEMURRAGE_THRESHOLD_DAYS', 2))

# O crear modelo SystemConfig
class SystemConfig(models.Model):
    demurrage_threshold_days = models.IntegerField(default=2)
    class Meta:
        db_table = 'system_config'
```

---

### 🟡 **DOMINIO: Normalización de Estados (FUNCIONAL CON ISSUES)**

#### Archivo: `apps/containers/services/status_utils.py` (138 líneas)

**✅ BUENA PRÁCTICA: Diccionario centralizado**

```python
# ✅ Mapeo de aliases a estados canónicos
STATUS_ALIASES: Dict[str, str] = {
    "": "PROGRAMADO",  # ← Default para strings vacíos
    "AVAILABLE": "PROGRAMADO",
    "DISPONIBLE": "PROGRAMADO",
    "IN_TRANSIT": "EN_TRANSITO",
    "EN TRANSITO": "EN_TRANSITO",
    ...
}

def normalize_status(raw_status: str | None) -> str:
    """✅ Función simple y clara"""
    if not raw_status:
        return DEFAULT_STATUS
    cleaned = raw_status.strip().upper()
    return STATUS_ALIASES.get(cleaned, cleaned)
```

---

**🔴 PROBLEMA: ESTADOS NO SINCRONIZADOS CON MODELO**

```python
# ❌ DUPLICACIÓN: Container.CONTAINER_STATUS vs STATUS_ALIASES
# apps/containers/models.py
class Container(BaseModel):
    CONTAINER_STATUS = [
        ('POR_ARRIBAR', 'Por Arribar'),
        ('LIBERADO', 'Liberado'),
        ('PROGRAMADO', 'Programado'),
        ...
        ('FINALIZADO', 'Finalizado'),
        ('TRG', 'TRG'),  # ← ¿Qué significa TRG?
        ('SECUENCIADO', 'Secuenciado'),
    ]

# apps/containers/services/status_utils.py
CANONICAL_STATUSES: Dict[str, str] = {
    "PROGRAMADO": "PROGRAMADO",
    "LIBERADO": "LIBERADO",
    ...
    "TRG": "TRG",  # ← Sin documentación
}
```

**Impacto**:
- 🔴 Riesgo de inconsistencias si se agregan estados en un lugar y no en otro
- 🔴 `TRG` no está documentado (¿qué significa?)

**Solución**:
```python
# ✅ UNIFICAR: Generar CANONICAL_STATUSES desde Container.CONTAINER_STATUS

# apps/containers/models.py
class Container(BaseModel):
    CONTAINER_STATUS = [
        ('POR_ARRIBAR', 'Por Arribar', 'Contenedor en tránsito marítimo'),
        ('LIBERADO', 'Liberado', 'Liberado por aduana'),
        ('TRG', 'TRG', 'Transferencia en gestión'),  # ← Documentado
        ...
    ]
    
    @classmethod
    def get_status_choices(cls):
        """Retorna lista de tuplas (code, display)"""
        return [(code, display) for code, display, _ in cls.CONTAINER_STATUS]
    
    @classmethod
    def get_status_descriptions(cls) -> Dict[str, str]:
        """Retorna mapa {code: descripción}"""
        return {code: desc for code, _, desc in cls.CONTAINER_STATUS}

# apps/containers/services/status_utils.py
from apps.containers.models import Container

CANONICAL_STATUSES = {
    code: code for code, _, _ in Container.CONTAINER_STATUS
}  # ← Generado automáticamente
```

---

## 2️⃣ ANÁLISIS DE VALIDACIONES

### 🔴 **PROBLEMA CRÍTICO: Validaciones Dispersas y Débiles**

```python
# ❌ 1. VALIDACIONES EN VIEWS (debería estar en servicios o modelos)

# apps/drivers/views.py
def _assign_driver_to_container(container, driver, user, ...):
    """❌ Validaciones mezcladas con lógica de vista"""
    
    # Validación 1: Asistencia
    if driver.ultimo_registro_asistencia != today or not driver.hora_ingreso_hoy:
        raise ValueError(f'El conductor no ha registrado asistencia hoy')
        # ← Debería estar en Driver.can_be_assigned()
    
    # Validación 2: Conflictos de horario
    if _has_schedule_conflict(driver, scheduled_datetime, duration_minutes):
        raise ValueError(f'Conductor tiene conflicto de horario')
        # ← Debería estar en AssignmentService.validate_availability()

# ❌ 2. SIN VALIDACIÓN DE REGLAS DE NEGOCIO

# apps/containers/services/excel_importers.py
def _process_container_row(row):
    """❌ No valida pesos, fechas, ni campos requeridos"""
    container = Container(
        cargo_weight=row.get('weight'),  # ← ¿Y si weight es negativo?
        eta=row.get('eta'),               # ← ¿Y si eta es pasado?
    )
    container.save()  # ← Sin validación
```

---

### ✅ **SOLUCIÓN PROPUESTA: Capa de Validación Unificada**

```python
# ✅ apps/containers/services/validators.py

from django.core.exceptions import ValidationError
from datetime import date

class ContainerValidator:
    """Validador centralizado para contenedores"""
    
    @staticmethod
    def validate_weights(container):
        """Valida coherencia de pesos"""
        if container.weight_empty and container.cargo_weight:
            total_calculated = container.weight_empty + container.cargo_weight
            if container.total_weight and abs(total_calculated - container.total_weight) > 100:
                raise ValidationError(
                    f"Peso total ({container.total_weight}) no coincide con "
                    f"suma de vacío + carga ({total_calculated})"
                )
        
        if container.max_weight and container.total_weight:
            if container.total_weight > container.max_weight:
                raise ValidationError(
                    f"Peso total ({container.total_weight}) excede "
                    f"peso máximo permitido ({container.max_weight})"
                )
    
    @staticmethod
    def validate_dates(container):
        """Valida coherencia de fechas"""
        today = date.today()
        
        if container.eta and container.eta < today:
            raise ValidationError(f"ETA no puede ser en el pasado: {container.eta}")
        
        if container.release_date and container.eta:
            if container.release_date < container.eta:
                raise ValidationError(
                    "Fecha de liberación no puede ser antes del ETA"
                )
        
        if container.demurrage_date and container.release_date:
            if container.demurrage_date < container.release_date:
                raise ValidationError(
                    "Fecha de demurrage no puede ser antes de liberación"
                )
    
    @staticmethod
    def validate_status_transition(container, new_status):
        """Valida transiciones de estado permitidas"""
        if not container.can_transition_to(container.status, new_status):
            raise ValidationError(
                f"Transición inválida: {container.status} → {new_status}"
            )
    
    @classmethod
    def validate_all(cls, container):
        """Ejecuta todas las validaciones"""
        cls.validate_weights(container)
        cls.validate_dates(container)

# ✅ Uso en servicios
def import_vessel_manifest(...):
    ...
    container = Container(...)
    ContainerValidator.validate_all(container)  # ← Validación centralizada
    container.save()
```

---

## 3️⃣ ANÁLISIS DE MANEJO DE ERRORES

### 🔴 **PROBLEMA: Manejo inconsistente de excepciones**

```python
# ❌ 1. EXCEPCIONES GENÉRICAS
def _assign_driver_to_container(...):
    if condition:
        raise ValueError('Error genérico')  # ← Poco específico
    
    try:
        assignment = Assignment.objects.create(...)
    except Exception as e:  # ← ❌ Catch-all demasiado amplio
        logger.error(f"Error: {e}")
        raise

# ❌ 2. SIN CLASIFICACIÓN DE ERRORES
# - Errores de validación (400)
# - Errores de lógica de negocio (422)
# - Errores de sistema (500)
```

---

### ✅ **SOLUCIÓN: Jerarquía de Excepciones Personalizadas**

```python
# ✅ apps/core/exceptions.py

class SoptralocException(Exception):
    """Excepción base del sistema"""
    default_message = "Error en el sistema"
    http_status = 500
    
    def __init__(self, message=None, **kwargs):
        self.message = message or self.default_message
        self.extra_data = kwargs
        super().__init__(self.message)

class ValidationException(SoptralocException):
    """Error de validación de datos"""
    http_status = 400

class BusinessRuleException(SoptralocException):
    """Violación de regla de negocio"""
    http_status = 422

class ResourceNotFoundException(SoptralocException):
    """Recurso no encontrado"""
    http_status = 404

# ✅ Excepciones específicas
class DriverNotAvailableException(BusinessRuleException):
    default_message = "Conductor no disponible para asignación"

class InvalidStatusTransitionException(BusinessRuleException):
    default_message = "Transición de estado inválida"

class DemurrageDatePassedException(BusinessRuleException):
    default_message = "Fecha de demurrage vencida"

# ✅ Uso en servicios
def _assign_driver_to_container(container, driver, ...):
    if not driver.esta_disponible:
        raise DriverNotAvailableException(
            f"Conductor {driver.nombre} no está disponible",
            driver_id=driver.id,
            reason=driver.estado
        )
    
    if _has_schedule_conflict(driver, ...):
        raise DriverNotAvailableException(
            "Conductor tiene conflicto de horario",
            driver_id=driver.id,
            conflicting_assignments=[...]
        )
```

---

## 4️⃣ ANÁLISIS DE REGLAS DE NEGOCIO COMPLEJAS

### 🟢 **REGLA: Asignación Automática de Conductores (BIEN DISEÑADA)**

#### Archivo: `apps/drivers/views.py` (líneas 60-180)

**Flujo complejo bien estructurado**:

```python
def _assign_driver_to_container(container, driver, user, ...):
    """
    ✅ Flujo de asignación con múltiples validaciones
    """
    # 1. Validar asistencia del conductor
    if driver.ultimo_registro_asistencia != today:
        raise ValueError('Conductor sin asistencia')
    
    # 2. Resolver ubicaciones origen/destino
    origin, destination = _resolve_assignment_locations(driver, container)
    
    # 3. Estimar duración (integra Mapbox + ML + TimeMatrix)
    duration = _estimate_assignment_duration_minutes(
        origin, destination, assignment_type, scheduled_datetime
    )
    
    # 4. Verificar conflictos de horario (con tráfico en tiempo real)
    if _has_schedule_conflict(driver, scheduled_datetime, duration):
        raise ValueError('Conflicto de horario')
    
    # 5. Crear asignación
    assignment = Assignment.objects.create(...)
    
    # 6. Actualizar estados
    container.status = 'ASIGNADO'
    driver.contenedor_asignado = container
    
    # 7. Actualizar ubicación del conductor
    driver.ubicacion_actual = origin.code
    
    # 8. Guardar cambios
    assignment.save()
    container.save()
    driver.save()
    
    return assignment
```

**Fortalezas**:
- ✅ Validaciones secuenciales claras
- ✅ Integración con múltiples sistemas (Mapbox, ML, TimeMatrix)
- ✅ Actualización consistente de estados

---

**🔴 PROBLEMA: NO USA TRANSACCIONES**

```python
# ❌ RIESGO: Si falla driver.save(), container queda inconsistente
assignment.save()
container.save()  # ← Si falla aquí...
driver.save()     # ← ...driver.contenedor_asignado apunta a assignment que no tiene container actualizado
```

**Solución**:
```python
# ✅ USAR TRANSACCIÓN ATÓMICA
from django.db import transaction

@transaction.atomic
def _assign_driver_to_container(container, driver, user, ...):
    """✅ Todo o nada (rollback automático en error)"""
    ...
    assignment.save()
    container.save()
    driver.save()
    # Si cualquier save() falla, se hace rollback completo
```

---

### 🟡 **REGLA: Detección de Conflictos de Horario (MEJORABLE)**

```python
# ⚠️ ACTUAL: Recalcula tiempo con tráfico solo para asignaciones EN_CURSO
def _has_schedule_conflict(driver, start_datetime, duration_minutes):
    for assignment in active_assignments:
        if assignment.estado == 'EN_CURSO':
            # Recalcular tiempo con tráfico actual
            recalculated_duration = _estimate_assignment_duration_minutes(...)
            assign_duration = recalculated_duration
        else:
            assign_duration = assignment.tiempo_estimado
        
        # Verificar overlap
        if (assign_start - buffer) < window_end and window_start < (assign_end + buffer):
            return True
    return False
```

**Problema**:
- ⚠️ Solo recalcula para estado `EN_CURSO`, no para `PENDIENTE`
- ⚠️ Si hay tráfico imprevisto en ruta `PENDIENTE`, puede haber conflicto no detectado

**Mejora**:
```python
# ✅ Recalcular para TODOS los estados activos
def _has_schedule_conflict(driver, start_datetime, duration_minutes):
    for assignment in active_assignments:
        # Recalcular SIEMPRE con tráfico actual
        if assignment.origen and assignment.destino:
            recalculated = _estimate_assignment_duration_minutes(
                assignment.origen, 
                assignment.destino,
                assignment.tipo_asignacion,
                timezone.now()  # Tráfico actual
            )
            assign_duration = recalculated if recalculated else assignment.tiempo_estimado
        else:
            assign_duration = assignment.tiempo_estimado
        
        # Verificar overlap con buffer
        ...
```

---

## 5️⃣ ANÁLISIS DE INTEGRACIÓN CON APIS EXTERNAS

### 🟢 **INTEGRACIÓN: Mapbox (Tráfico en tiempo real)**

**Archivo**: `apps/drivers/services/duration_predictor.py`

```python
class DriverDurationPredictor:
    """✅ Predictor con fallbacks en cascada"""
    
    def predict(self, origin, destination, ...) -> DurationPrediction:
        # 1. Intentar Mapbox (tráfico real)
        result = self._mapbox_duration(origin, destination, scheduled_datetime)
        if result:
            return DurationPrediction(minutes=result, source='mapbox')
        
        # 2. Fallback a ML
        result = self._ml_duration(origin, destination)
        if result:
            return DurationPrediction(minutes=result, source='ml')
        
        # 3. Fallback a histórico
        result = self._historical_duration(origin, destination)
        if result:
            return DurationPrediction(minutes=result, source='historical')
        
        # 4. Fallback a matriz estática
        result = self._matrix_duration(origin, destination)
        if result:
            return DurationPrediction(minutes=result, source='time_matrix')
        
        # 5. Default conservador
        return DurationPrediction(minutes=120, source='default')
```

**Fortalezas**:
- ✅ Múltiples fallbacks (resiliente a fallos de API)
- ✅ Source tracking (para debugging)
- ✅ Default conservador

---

**🟡 MEJORA: Cache de resultados Mapbox**

```python
# ⚠️ ACTUAL: Cada predicción llama a Mapbox
result = self._mapbox_duration(origin, destination, scheduled_datetime)
# ← Si se consulta 100 veces la misma ruta, hace 100 llamadas API

# ✅ MEJORA: Cache con Redis (TTL 5 minutos)
import redis
from django.core.cache import cache

def _mapbox_duration_cached(self, origin, destination, scheduled_datetime):
    # Clave de cache incluye hora (redondear a 5 min)
    rounded_time = scheduled_datetime.replace(minute=(scheduled_datetime.minute // 5) * 5)
    cache_key = f"mapbox:{origin.code}:{destination.code}:{rounded_time.isoformat()}"
    
    # Buscar en cache
    cached = cache.get(cache_key)
    if cached:
        logger.debug(f"✅ Cache hit: {cache_key}")
        return cached
    
    # Llamar a Mapbox
    result = self._mapbox_duration(origin, destination, scheduled_datetime)
    
    # Guardar en cache (5 min)
    if result:
        cache.set(cache_key, result, timeout=300)
    
    return result
```

---

## 6️⃣ PUNTUACIÓN POR CATEGORÍA

| Categoría                      | Puntuación | Comentario                                    |
|--------------------------------|------------|-----------------------------------------------|
| **Organización de servicios**  | 8/10       | Bien estructurados, funciones claras          |
| **Validaciones**               | 4/10       | Dispersas, débiles, sin centralizar           |
| **Manejo de errores**          | 5/10       | Funcional pero inconsistente                  |
| **Reglas de negocio**          | 7/10       | Lógica correcta, pero sin transacciones       |
| **Integración APIs**           | 8/10       | Mapbox bien integrado con fallbacks           |
| **Machine Learning**           | 7/10       | Algoritmo simple pero efectivo                |
| **Testing**                    | 2/10       | Muy pocos tests unitarios                     |
| **Documentación**              | 6/10       | Docstrings presentes, pero incompletos        |

**PROMEDIO**: **5.9/10** 🟡 **BUENO CON MEJORAS NECESARIAS**

---

## 7️⃣ RECOMENDACIONES PRIORIZADAS

### 🔴 **CRÍTICO (Hacer AHORA)**

1. **Agregar transacciones atómicas en funciones críticas**
   ```python
   # Todas las funciones que modifican múltiples modelos
   @transaction.atomic
   def _assign_driver_to_container(...):
       ...
   ```

2. **Crear capa de validación centralizada**
   ```python
   # apps/containers/services/validators.py
   class ContainerValidator:
       @staticmethod
       def validate_all(container):
           ...
   ```

3. **Implementar excepciones personalizadas**
   ```python
   # apps/core/exceptions.py
   class BusinessRuleException(SoptralocException):
       ...
   ```

---

### 🟡 **IMPORTANTE (Próximas 2-4 semanas)**

4. **Refactorizar `import_vessel_manifest` (función de 200 líneas)**
   - Dividir en 5-6 funciones más pequeñas
   - Cada función con responsabilidad única

5. **Agregar tests unitarios para servicios críticos**
   ```python
   # tests/test_demurrage_service.py
   def test_create_demurrage_alert_proximo():
       ...
   
   def test_create_demurrage_alert_vencido():
       ...
   ```

6. **Implementar cache Redis para Mapbox**
   - Reducir llamadas API
   - TTL de 5 minutos

7. **Unificar estados entre modelo y utils**
   - Generar `CANONICAL_STATUSES` desde `Container.CONTAINER_STATUS`
   - Documentar significado de `TRG`

---

### 🟢 **MEJORAS (Backlog)**

8. Mejorar algoritmo ML (regresión lineal con más features)
9. Agregar métricas de precisión del modelo ML
10. Implementar circuit breaker para APIs externas
11. Agregar observabilidad (métricas, trazas distribuidas)

---

## 8️⃣ PRÓXIMOS PASOS (FASE 4)

Con el análisis de lógica de negocio completo, ahora procederé a:

1. ✅ **FASE 1 COMPLETADA**: Arquitectura y dependencias
2. ✅ **FASE 2 COMPLETADA**: Modelos y base de datos
3. ✅ **FASE 3 COMPLETADA**: Lógica de negocio y servicios
4. ⏳ **FASE 4**: Views y controladores
5. ⏳ **FASE 5**: APIs y serializers
6. ⏳ **FASE 6**: Seguridad profunda
7. ⏳ **FASE 7**: Performance y optimización
8. ⏳ **FASE 8**: Tests y cobertura
9. ⏳ **FASE 9**: Documentación
10. ⏳ **FASE 10**: Deployment e integración

---

**FIN DE FASE 3 - LÓGICA DE NEGOCIO**  
**Próximo paso**: Análisis exhaustivo de Views, ViewSets y controladores.