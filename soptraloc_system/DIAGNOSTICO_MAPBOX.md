# 🗺️ DIAGNÓSTICO MAPBOX - SOPTRALOC TMS
**Fecha:** 8 de Octubre, 2025  
**Estado:** ⚠️ PARCIALMENTE IMPLEMENTADO

---

## 📊 ESTADO ACTUAL

### ✅ **LO QUE ESTÁ IMPLEMENTADO**

1. **Servicio Mapbox (`apps/routing/mapbox_service.py`)**
   - ✅ Clase `MapboxService` completa
   - ✅ Método `get_travel_time_with_traffic()` con tráfico en tiempo real
   - ✅ Procesamiento de coordenadas y códigos de ubicación
   - ✅ Caché de 5 minutos para optimizar requests
   - ✅ Fallback a tiempos estáticos si falla API
   - ✅ Cálculo de niveles de tráfico (low/medium/high/very_high)
   - ✅ Detección de rutas alternativas
   - ✅ Integración con catálogo de ubicaciones

2. **Servicio de Inicio de Ruta (`apps/routing/route_start_service.py`)**
   - ✅ Clase `RouteStartService` completa
   - ✅ Método `start_route()` que usa Mapbox
   - ✅ Actualiza Assignment con tiempo estimado real
   - ✅ Genera alertas de tráfico automáticas
   - ✅ Calcula ETA considerando tráfico actual
   - ✅ Almacena información de rutas alternativas

3. **Modelo de Datos**
   - ✅ `Assignment.tiempo_estimado` - almacena tiempo con tráfico
   - ✅ `Assignment.fecha_inicio` - timestamp de inicio
   - ✅ `TrafficAlert` - alertas de tráfico generadas

---

### ⚠️ **LO QUE FALTA IMPLEMENTAR**

#### **CRÍTICO - INTEGRACIÓN EN ASIGNACIÓN DE CONDUCTORES**

**Problema:**  
El sistema de asignación de conductores (`apps/drivers/views.py` y `duration_predictor.py`) 
**NO ESTÁ USANDO MAPBOX** para calcular tiempos de ocupación.

**Ubicaciones del código:**

1. **`apps/drivers/views.py:_estimate_assignment_duration_minutes()`** (línea ~74)
   ```python
   # ❌ USA: DriverDurationPredictor (ML histórico) o TimeMatrix estática
   # ✅ DEBE USAR: MapboxService para tiempo real con tráfico
   ```

2. **`apps/drivers/services/duration_predictor.py`** (completo)
   ```python
   # ❌ Solo usa datos históricos + ML
   # ✅ DEBE INTEGRAR: Mapbox como fuente primaria
   ```

3. **`apps/drivers/views.py:_has_schedule_conflict()`** (línea ~97)
   ```python
   # ❌ Usa tiempo estimado estático
   # ✅ DEBE CONSIDERAR: Tráfico actual para conflictos reales
   ```

---

#### **CONFIGURACIÓN FALTANTE**

**Problema:**  
La API key de Mapbox **NO ESTÁ CONFIGURADA** en el entorno.

**Evidencia:**
```bash
$ grep -i "MAPBOX" .env
⚠️ No se encontró archivo .env o MAPBOX_API_KEY no configurado
```

**Configuración en código:**
```python
# config/settings.py línea 243
MAPBOX_API_KEY = config('MAPBOX_API_KEY', default=None)
```

**Resultado:**
- MapboxService retorna tiempos fallback estáticos
- No hay consultas reales a la API
- El tráfico en tiempo real NO se está usando

---

## 🎯 PLAN DE ACCIÓN

### FASE 1: CONFIGURAR MAPBOX API KEY ⚡

#### Paso 1.1: Obtener Token Mapbox
```bash
# 1. Ir a https://account.mapbox.com/
# 2. Sign Up con GitHub Student Pack (gratis)
# 3. Crear nuevo token con permisos:
#    - Navigation (Directions API)
#    - Styles (opcional)
# 4. Copiar token (comienza con pk.eyJ...)
```

#### Paso 1.2: Crear archivo .env
```bash
cd /workspaces/soptraloc/soptraloc_system
cat > .env << 'EOF'
# Django Settings
SECRET_KEY='tu-secret-key-aqui'
DEBUG=True

# Mapbox API
MAPBOX_API_KEY=pk.eyJ1IjoidHUtdXNlcm5hbWUiLCJhIjoiY2x0eDEyMzQ1In0.AbCdEfGhIjKlMn...

# Redis/Celery
REDIS_URL=redis://localhost:6379/0

# Database (si usas PostgreSQL en prod)
# DATABASE_URL=postgres://user:pass@host:5432/dbname
EOF
```

#### Paso 1.3: Verificar configuración
```bash
cd /workspaces/soptraloc/soptraloc_system
/workspaces/soptraloc/venv/bin/python manage.py shell
```
```python
from django.conf import settings
print(f"MAPBOX_API_KEY: {settings.MAPBOX_API_KEY[:20]}..." if settings.MAPBOX_API_KEY else "❌ NO CONFIGURADO")

# Probar servicio
from apps.routing.mapbox_service import mapbox_service
result = mapbox_service.get_travel_time_with_traffic('CCTI', 'CD_PENON')
print(f"Tiempo CCTI → CD El Peñón: {result['duration_in_traffic_minutes']} min")
print(f"Tráfico: {result['traffic_level']}")
print(f"Fuente: {result['source']}")  # Debe ser 'mapbox_api', no 'static'
```

---

### FASE 2: INTEGRAR MAPBOX EN ASIGNACIÓN DE CONDUCTORES 🔧

#### Paso 2.1: Modificar `duration_predictor.py`

**Agregar método para consultar Mapbox:**

```python
# En apps/drivers/services/duration_predictor.py

def _mapbox_estimate(
    self, 
    origin: Location, 
    destination: Location, 
    scheduled_datetime
) -> Optional[tuple[int, str]]:
    """
    Obtiene tiempo estimado desde Mapbox con tráfico real.
    
    Returns:
        Tuple de (minutos, nivel_trafico) o None si falla
    """
    try:
        from apps.routing.mapbox_service import mapbox_service
        
        result = mapbox_service.get_travel_time_with_traffic(
            origin=origin.code,
            destination=destination.code,
            departure_time=scheduled_datetime
        )
        
        if result.get('source') == 'mapbox_api':
            return (
                result['duration_in_traffic_minutes'],
                result['traffic_level']
            )
    except Exception as e:
        logger.warning(f"Error consultando Mapbox: {e}")
    
    return None
```

**Modificar método `predict()` para priorizar Mapbox:**

```python
def predict(
    self,
    *,
    origin: Optional[Location],
    destination: Optional[Location],
    assignment_type: str,
    scheduled_datetime,
) -> PredictionResult:
    if origin is None or destination is None:
        return PredictionResult(minutes=DEFAULT_FALLBACK_MINUTES, source='default', sample_size=0)

    assignment_type = assignment_type or 'ENTREGA'
    scheduled_datetime = scheduled_datetime or timezone.now()

    # 🆕 PRIORIDAD 1: MAPBOX (tráfico en tiempo real)
    mapbox_minutes = None
    traffic_level = 'unknown'
    mapbox_result = self._mapbox_estimate(origin, destination, scheduled_datetime)
    if mapbox_result:
        mapbox_minutes, traffic_level = mapbox_result
    
    # PRIORIDAD 2: Modelo ML histórico
    historical_avg, historical_count = self._historical_route_average(
        origin, destination, assignment_type
    )
    
    # PRIORIDAD 3: TimeMatrix estática
    matrix_minutes = self._time_matrix_estimate(origin, destination)
    
    # PRIORIDAD 4: Predicción ML
    model_minutes = self._predict_with_model(
        origin, destination, assignment_type, 
        scheduled_datetime, matrix_minutes
    )

    # Construir lista de estimaciones con pesos
    estimates: list[tuple[str, float, int]] = []
    
    if mapbox_minutes and mapbox_minutes > 0:
        # Mapbox tiene máxima prioridad (70%)
        estimates.append(('mapbox_realtime', mapbox_minutes, 1000))
    
    if model_minutes and model_minutes > 0:
        estimates.append(('ml', model_minutes, self._model_sample_size))
    
    if historical_avg and historical_avg > 0:
        estimates.append(('historical', historical_avg, historical_count))
    
    if matrix_minutes and matrix_minutes > 0:
        estimates.append(('matrix', matrix_minutes, 0))

    if not estimates:
        return PredictionResult(
            minutes=DEFAULT_FALLBACK_MINUTES, 
            source='default', 
            sample_size=0
        )

    # Promedio ponderado favoreciendo Mapbox
    weights = {
        'mapbox_realtime': 0.70,  # 🆕 Máxima prioridad
        'ml': 0.15,
        'historical': 0.10,
        'matrix': 0.05,
    }

    total_weight = 0.0
    weighted_sum = 0.0
    sample_size = 0
    
    for source, minutes, count in estimates:
        weight = weights.get(source, 0.1)
        weighted_sum += minutes * weight
        total_weight += weight
        sample_size = max(sample_size, count)

    final_minutes = weighted_sum / total_weight if total_weight else DEFAULT_FALLBACK_MINUTES
    final_minutes = max(int(round(final_minutes)), 30)
    primary_source = estimates[0][0]

    return PredictionResult(
        minutes=final_minutes, 
        source=primary_source, 
        sample_size=sample_size
    )
```

---

#### Paso 2.2: Modificar `views.py` para usar Mapbox

**En `_estimate_assignment_duration_minutes()`:**

```python
def _estimate_assignment_duration_minutes(
    origin, 
    destination, 
    assignment_type, 
    scheduled_datetime
):
    """Estima duración usando Mapbox (tráfico real) como prioridad."""
    
    if origin and destination:
        # 🆕 Intentar con Mapbox primero
        try:
            from apps.routing.mapbox_service import mapbox_service
            
            result = mapbox_service.get_travel_time_with_traffic(
                origin=origin.code,
                destination=destination.code,
                departure_time=scheduled_datetime
            )
            
            if result.get('source') == 'mapbox_api':
                duration = result['duration_in_traffic_minutes']
                
                # Log para debugging
                logger.info(
                    f"🗺️  Mapbox: {origin.code} → {destination.code} = "
                    f"{duration} min (tráfico: {result['traffic_level']})"
                )
                
                return duration
        except Exception as e:
            logger.warning(f"Mapbox falló, usando predictor: {e}")
        
        # Fallback: Usar DriverDurationPredictor
        try:
            from apps.drivers.services.duration_predictor import DriverDurationPredictor
            
            prediction = DriverDurationPredictor().predict(
                origin=origin,
                destination=destination,
                assignment_type=assignment_type,
                scheduled_datetime=scheduled_datetime,
            )
            
            if prediction and prediction.minutes:
                return prediction.minutes
        except ImportError:
            pass

        # Fallback final: TimeMatrix
        try:
            time_matrix = TimeMatrix.objects.get(
                from_location=origin, 
                to_location=destination
            )
            return time_matrix.get_total_time()
        except TimeMatrix.DoesNotExist:
            pass
    
    return DEFAULT_ASSIGNMENT_DURATION
```

---

#### Paso 2.3: Actualizar conflictos de horario

**En `_has_schedule_conflict()`:**

```python
def _has_schedule_conflict(driver, start_datetime, duration_minutes):
    """
    Verifica conflictos considerando tráfico real.
    
    🆕 Usa Mapbox para calcular duración real de asignaciones activas
    """
    if start_datetime is None:
        start_datetime = timezone.now()
    if duration_minutes is None or duration_minutes <= 0:
        duration_minutes = DEFAULT_ASSIGNMENT_DURATION

    buffer = timedelta(minutes=SCHEDULE_BUFFER_MINUTES)
    window_start = start_datetime - buffer
    window_end = start_datetime + timedelta(minutes=duration_minutes) + buffer

    active_assignments = Assignment.objects.filter(
        driver=driver,
        estado__in=['PENDIENTE', 'EN_CURSO']
    ).select_related('origen', 'destino')

    for assignment in active_assignments:
        assign_start = (
            assignment.fecha_programada or 
            assignment.fecha_inicio or 
            timezone.now()
        )
        
        if assignment.estado == 'EN_CURSO' and assignment.fecha_inicio:
            assign_start = assignment.fecha_inicio

        # 🆕 Calcular duración real con tráfico si es posible
        assign_duration = assignment.tiempo_estimado
        
        if assignment.origen and assignment.destino:
            try:
                from apps.routing.mapbox_service import mapbox_service
                
                result = mapbox_service.get_travel_time_with_traffic(
                    origin=assignment.origen.code,
                    destination=assignment.destino.code,
                    departure_time=assign_start
                )
                
                if result.get('source') == 'mapbox_api':
                    # Usar tiempo con tráfico real
                    assign_duration = result['duration_in_traffic_minutes']
            except Exception:
                pass  # Usar tiempo estimado original
        
        if assign_duration is None:
            assign_duration = DEFAULT_ASSIGNMENT_DURATION
        
        assign_end = assign_start + timedelta(minutes=assign_duration)

        # Verificar overlap
        if (assign_start - buffer) < window_end and window_start < (assign_end + buffer):
            return True

    return False
```

---

### FASE 3: AGREGAR CAMPO DE TRÁFICO A ASSIGNMENT 🗃️

**Migración Django:**

```python
# apps/drivers/migrations/0XXX_add_traffic_info.py

from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('drivers', '0XXX_previous_migration'),
    ]

    operations = [
        migrations.AddField(
            model_name='assignment',
            name='traffic_level_at_assignment',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('low', 'Tráfico Bajo'),
                    ('medium', 'Tráfico Medio'),
                    ('high', 'Tráfico Alto'),
                    ('very_high', 'Tráfico Muy Alto'),
                    ('unknown', 'Desconocido'),
                ],
                default='unknown',
                help_text='Nivel de tráfico al momento de crear la asignación'
            ),
        ),
        migrations.AddField(
            model_name='assignment',
            name='mapbox_data',
            field=models.JSONField(
                null=True,
                blank=True,
                help_text='Datos completos de Mapbox (rutas alternativas, etc.)'
            ),
        ),
    ]
```

**Modificar modelo Assignment:**

```python
# apps/drivers/models.py - Clase Assignment

class Assignment(models.Model):
    # ... campos existentes ...
    
    # 🆕 Información de tráfico
    traffic_level_at_assignment = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Tráfico Bajo'),
            ('medium', 'Tráfico Medio'),
            ('high', 'Tráfico Alto'),
            ('very_high', 'Tráfico Muy Alto'),
            ('unknown', 'Desconocido'),
        ],
        default='unknown',
        help_text='Nivel de tráfico al momento de crear la asignación'
    )
    
    mapbox_data = models.JSONField(
        null=True,
        blank=True,
        help_text='Datos completos de Mapbox (rutas alternativas, warnings, etc.)'
    )
    
    def get_traffic_emoji(self):
        """Retorna emoji según nivel de tráfico."""
        return {
            'low': '🟢',
            'medium': '🟡',
            'high': '🟠',
            'very_high': '🔴',
            'unknown': '⚪',
        }.get(self.traffic_level_at_assignment, '⚪')
```

---

### FASE 4: ACTUALIZAR AUTO-ASIGNACIÓN 🤖

**En `views.py:auto_assign_drivers()`:**

```python
@login_required
def auto_assign_drivers(request):
    """
    Auto-asigna conductores a contenedores considerando:
    - Disponibilidad del conductor
    - Ubicación actual
    - Tipo de conductor apropiado
    - 🆕 Tráfico en tiempo real (Mapbox)
    - Conflictos de horario
    """
    # ... código existente ...
    
    # Al crear asignación:
    scheduled_datetime = _compute_scheduled_datetime(container)
    origin, destination = _resolve_assignment_locations(driver, container)
    
    # 🆕 Obtener información de tráfico
    traffic_info = None
    if origin and destination:
        try:
            from apps.routing.mapbox_service import mapbox_service
            
            traffic_info = mapbox_service.get_travel_time_with_traffic(
                origin=origin.code,
                destination=destination.code,
                departure_time=scheduled_datetime
            )
        except Exception as e:
            logger.warning(f"Error obteniendo tráfico: {e}")
    
    # Estimar duración (ya usa Mapbox internamente)
    duration_minutes = _estimate_assignment_duration_minutes(
        origin, destination, 'ENTREGA', scheduled_datetime
    )
    
    # Crear asignación con información de tráfico
    assignment = Assignment.objects.create(
        container=container,
        driver=driver,
        fecha_programada=scheduled_datetime,
        estado='PENDIENTE',
        origen=origin,
        destino=destination,
        tiempo_estimado=duration_minutes,
        # 🆕 Agregar información de tráfico
        traffic_level_at_assignment=traffic_info.get('traffic_level', 'unknown') if traffic_info else 'unknown',
        mapbox_data=traffic_info if traffic_info else None,
        # ... resto de campos ...
    )
    
    # ... resto del código ...
```

---

## 📈 BENEFICIOS DE LA INTEGRACIÓN

### ✅ **Tiempos de Ocupación Reales**

**Antes:**
```
Asignación CCTI → CD El Peñón
Tiempo estimado: 90 min (TimeMatrix estática)
Conductor ocupado hasta: 10:30 AM
```

**Después (con Mapbox):**
```
Asignación CCTI → CD El Peñón
Tráfico actual: 🔴 Muy Alto
Tiempo estimado: 145 min (tráfico real)
Conductor ocupado hasta: 11:25 AM
Rutas alternativas: 2 disponibles
```

### ✅ **Evita Conflictos Reales**

**Sin Mapbox:**
- Asigna 2 viajes basándose en tiempos estáticos
- En realidad hay tráfico → conductor llega tarde
- Segunda asignación pierde su ventana horaria

**Con Mapbox:**
- Detecta tráfico al crear primera asignación
- Extiende tiempo de ocupación
- Evita segunda asignación que causaría conflicto

### ✅ **Optimiza Recursos**

**Escenario:**
- 3 conductores disponibles
- 5 contenedores por asignar
- Mapbox detecta:
  - Ruta 1: Tráfico bajo (60 min)
  - Ruta 2: Tráfico alto (120 min)
  - Ruta 3: Tráfico medio (85 min)

**Sistema inteligente:**
- Asigna Ruta 2 (lenta) a conductor con tiempo libre
- Rutas 1 y 3 a conductores con ventanas pequeñas
- **Resultado:** Todos completan a tiempo vs. retrasos en cadena

---

## 🧪 PRUEBAS POST-IMPLEMENTACIÓN

### Test 1: Verificar Mapbox en Asignación

```python
from django.utils import timezone
from apps.drivers.models import Driver, Assignment
from apps.containers.models import Container

# Crear asignación manual
driver = Driver.objects.filter(estado='OPERATIVO').first()
container = Container.objects.filter(status='PROGRAMADO').first()

from apps.drivers.views import _assign_driver_to_container

assignment = _assign_driver_to_container(
    container=container,
    driver=driver,
    user=request.user,
    scheduled_datetime=timezone.now()
)

print(f"✅ Assignment creado: {assignment.id}")
print(f"Tiempo estimado: {assignment.tiempo_estimado} min")
print(f"Tráfico: {assignment.get_traffic_emoji()} {assignment.traffic_level_at_assignment}")
print(f"Mapbox data: {assignment.mapbox_data is not None}")
```

### Test 2: Verificar Conflictos con Tráfico

```python
# Crear 2 asignaciones consecutivas
driver = Driver.objects.first()

# Primera asignación (CCTI → CD Peñón con tráfico)
assignment1 = Assignment.objects.create(...)
print(f"A1: {assignment1.tiempo_estimado} min")

# Intentar segunda asignación inmediata
from apps.drivers.views import _has_schedule_conflict

conflict = _has_schedule_conflict(
    driver=driver,
    start_datetime=assignment1.fecha_programada + timedelta(minutes=60),
    duration_minutes=90
)

print(f"¿Conflicto detectado? {conflict}")  # Debe ser True si hay tráfico
```

### Test 3: Auto-Asignación Inteligente

```python
# Crear 10 contenedores PROGRAMADOS
# Tener 3 conductores OPERATIVOS

from apps.drivers.views import auto_assign_drivers

# Simular request
class FakeRequest:
    user = User.objects.first()
    method = 'POST'

result = auto_assign_drivers(FakeRequest())

# Verificar que las asignaciones consideraron tráfico
assignments = Assignment.objects.filter(
    estado='PENDIENTE'
).order_by('-created_at')[:10]

for a in assignments:
    print(f"{a.container.container_number}: {a.tiempo_estimado} min - {a.get_traffic_emoji()}")
```

---

## 📝 CHECKLIST DE IMPLEMENTACIÓN

### CONFIGURACIÓN
- [ ] Obtener Mapbox API key (GitHub Student Pack)
- [ ] Crear archivo `.env` con `MAPBOX_API_KEY`
- [ ] Verificar configuración en Django shell
- [ ] Probar llamada a Mapbox API manualmente

### CÓDIGO
- [ ] Modificar `duration_predictor.py` - agregar `_mapbox_estimate()`
- [ ] Modificar `duration_predictor.predict()` - priorizar Mapbox
- [ ] Modificar `views._estimate_assignment_duration_minutes()` - usar Mapbox
- [ ] Modificar `views._has_schedule_conflict()` - considerar tráfico
- [ ] Crear migración para campos `traffic_level` y `mapbox_data`
- [ ] Aplicar migración: `python manage.py migrate`
- [ ] Modificar modelo `Assignment` - agregar campos
- [ ] Actualizar `views.auto_assign_drivers()` - guardar info tráfico

### PRUEBAS
- [ ] Test 1: Asignación manual con Mapbox
- [ ] Test 2: Detección de conflictos con tráfico
- [ ] Test 3: Auto-asignación inteligente
- [ ] Test 4: Verificar logs de Mapbox API calls
- [ ] Test 5: Simular fallo de Mapbox (fallback funciona)

### DOCUMENTACIÓN
- [ ] Actualizar `test_system.py` con verificación Mapbox
- [ ] Crear guía de uso para coordinadores
- [ ] Documentar niveles de tráfico y emojis
- [ ] Agregar sección en SYSTEM_STATUS.md

---

## 💡 CONCLUSIÓN

**Estado Actual:**
- ✅ Mapbox está implementado técnicamente
- ⚠️ NO está configurado (falta API key)
- ❌ NO está integrado en asignación de conductores
- ❌ Tiempos de ocupación usan estimaciones estáticas

**Después de implementar:**
- ✅ Tiempos con tráfico en tiempo real
- ✅ Asignaciones consideran condiciones actuales
- ✅ Evita conflictos causados por retrasos
- ✅ Optimiza uso de conductores
- ✅ 100% operacional con tráfico real

**Estimación:** 2-3 horas de implementación + pruebas
