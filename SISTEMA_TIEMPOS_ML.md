# 🚛 Sistema de Gestión de Tiempos y Machine Learning

## 📋 Descripción

Sistema híbrido que combina **tiempos manuales configurables** con **Machine Learning predictivo** para gestionar rutas de transporte de contenedores.

**Ventajas del sistema**:
- ✅ **Sin GPS (por ahora)**: Tiempos manuales basados en experiencia
- ✅ **Machine Learning**: Aprende de cada viaje real para mejorar predicciones
- ✅ **Horas pico**: Ajuste automático según horario
- ✅ **Operaciones detalladas**: Tiempos para enganchar chasis, bajar a piso, etc.
- ✅ **Optimización continua**: Actualización diaria de predicciones

---

## 🏗️ Arquitectura

### Modelos Principales

#### 1. **LocationPair** - Tiempos entre Ubicaciones
Define tiempos de viaje entre dos puntos:
- ⏱️ **Tiempo base** (manual): Lo configuras tú
- 📊 **Predicción ML** (automático): El sistema aprende
- 🚦 **Horas pico**: Multiplicador para tráfico
- 📏 **Distancia**: Kilómetros entre puntos

```python
# Ejemplo: Puerto Valparaíso → CCTI
base_travel_time = 105 min  # Manual
ml_predicted_time = 98 min  # Aprendido de 50 viajes reales
confidence = 85%  # Confianza del modelo
```

#### 2. **OperationTime** - Tiempos de Operaciones
Define tiempos de operaciones específicas en cada ubicación:
- 🚛 **Enganchar/desenganchar chasis**
- 📦 **Bajar/levantar contenedor a piso**
- 🔍 **Inspecciones**
- 📄 **Trámites/documentos**
- ⏳ **Esperas**

```python
# Ejemplo: Enganchar chasis en CCTI
min_time = 10 min
avg_time = 15 min  # Manual
max_time = 20 min
ml_predicted_time = 14 min  # ML
```

#### 3. **ActualTripRecord** - Registro de Viajes Reales
Cada vez que un contenedor completa un viaje, se guarda:
- 🕐 Hora de salida y llegada
- ⏱️ Duración real
- 🌤️ Condiciones (clima, día de semana, hora)
- 👨‍✈️ Conductor
- 📦 Características del contenedor

**Estos datos alimentan el ML** para mejorar predicciones.

#### 4. **Route** y **RouteStop** - Rutas Completas
Agrupa múltiples contenedores en una ruta para un conductor:
- 📍 Múltiples paradas ordenadas
- ⏱️ Tiempos estimados vs reales
- 📊 Seguimiento de progreso

---

## 🚀 Uso Básico

### 1. Cargar Tiempos Iniciales

Ya se cargaron **35 rutas** y **70 operaciones** de Chile:

```bash
python manage.py load_initial_times
```

Ubicaciones incluidas:
- ✅ CCTI - Base Maipú
- ✅ CD Quilicura, Campos, Puerto Madero, El Peñón
- ✅ Puertos: Valparaíso, San Antonio, TPS, TCVAL, STI
- ✅ Almacenes extraportuarios

### 2. Consultar Tiempo Estimado (API)

**Endpoint**: `POST /api/v1/routing/time-prediction/predict-route/`

```bash
curl -X POST http://localhost:8000/api/v1/routing/time-prediction/predict-route/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "origin_id": 1,
    "destination_id": 2,
    "departure_time": "2025-10-01T14:30:00Z"
  }'
```

**Respuesta**:
```json
{
  "estimated_time": 105,
  "confidence": 85.5,
  "source": "ml",
  "total_samples": 50,
  "base_time": 105,
  "ml_time": 98,
  "last_ml_update": "2025-10-01T10:00:00Z"
}
```

### 3. Registrar Viaje Real

Cuando un contenedor completa un trayecto:

```python
from apps.routing.models import ActualTripRecord

ActualTripRecord.objects.create(
    container=container,
    driver=driver,
    vehicle=vehicle,
    origin=origin_location,
    destination=destination_location,
    departure_time=datetime(2025, 10, 1, 8, 0),
    arrival_time=datetime(2025, 10, 1, 9, 35),
    # duration_minutes se calcula automáticamente (95 min)
    weather='CLEAR',
    had_delay=False
)
```

### 4. Actualizar Predicciones ML

**Diariamente** (automático con cron/Celery):

```bash
python manage.py update_time_predictions
```

**Con análisis completo**:
```bash
python manage.py update_time_predictions --analyze --suggestions
```

**Salida ejemplo**:
```
============================================================
🤖 ACTUALIZACIÓN DE PREDICCIONES ML
============================================================

Actualizando predicciones...
✅ Actualizadas 35 rutas y 70 operaciones
🕐 Timestamp: 2025-10-01 10:00:00

============================================================
📊 ANÁLISIS DE PRECISIÓN
============================================================

Total predicciones evaluadas: 120
Error promedio: 8.5 minutos
Tasa de precisión: 92%

Últimas comparaciones:
  Puerto Valparaíso → CCTI: Predicho=105min, Real=102min, Error=2.9%
  CCTI → CD Quilicura: Predicho=35min, Real=38min, Error=8.6%
  ...

============================================================
💡 SUGERENCIAS DE OPTIMIZACIÓN
============================================================

1. Puerto San Antonio → CCTI
   Problema: Variabilidad alta (35.2%)
   Sugerencia: Revisar factores externos (tráfico, horarios)

2. CCTI → CD El Peñón
   Problema: Tiempo base desactualizado (25% diferencia)
   Sugerencia: Actualizar tiempo base de 40 a 32 minutos

============================================================
✅ ACTUALIZACIÓN COMPLETADA
============================================================
```

---

## 📊 Admin Panel

### Gestión de Tiempos

**Admin** → **Routing** → **Pares de Ubicaciones**

![Admin Screenshot](https://via.placeholder.com/800x400?text=LocationPair+Admin)

Columnas visibles:
- 🚩 Origen → Destino
- ⏱️ Tiempo Base (manual)
- 🤖 ML Predicción
- 🎯 Confianza ML (color)
- 📊 Total Viajes
- ✅ Activo

**Acciones en masa**:
- 🤖 Actualizar predicciones ML

### Gestión de Operaciones

**Admin** → **Routing** → **Tiempos de Operaciones**

Configurar tiempos para cada ubicación:
- Min / Avg / Max tiempo
- Variables que afectan (tamaño contenedor, hora del día)
- Predicción ML automática

### Registro de Viajes Reales

**Admin** → **Routing** → **Registros de Viajes Reales**

Historial completo:
- 🕐 Salida / Llegada / Duración
- 📦 Contenedor y características
- 👨‍✈️ Conductor
- 🌤️ Condiciones
- ⚠️ Retrasos

**Filtros**:
- Por día de semana
- Por hora pico
- Con/sin retraso
- Por clima

---

## 🤖 Machine Learning

### ¿Cómo Funciona?

#### Fase 1: Datos Insuficientes (< 5 viajes)
```
Tiempo estimado = Tiempo base manual
Confianza = 60%
Fuente = "manual"
```

#### Fase 2: Datos Suficientes (≥ 5 viajes)
```python
# Promedio ponderado
prediccion = (
    promedio_ultimos_30_dias * 0.6 +
    promedio_historico * 0.4
)

# Confianza basada en:
- Cantidad de muestras (más = mejor)
- Variabilidad (menos = mejor)

confianza = (
    min(100, samples/50 * 100) +  # Cantidad
    max(0, 100 - std_dev/avg * 100)  # Variabilidad
) / 2
```

#### Fase 3: ML Confiable (>70% confianza)
```
Tiempo estimado = ML Predicción
Confianza = 85%
Fuente = "ml"
```

### Actualización Automática

**Recomendado**: Ejecutar diariamente a las 3 AM

**Con Celery Beat** (agregar a `celerybeat-schedule`):
```python
from celery.schedules import crontab

CELERYBEAT_SCHEDULE = {
    'update-time-predictions': {
        'task': 'apps.routing.tasks.update_predictions',
        'schedule': crontab(hour=3, minute=0),
    },
}
```

**Con cron** (Linux):
```bash
crontab -e

# Agregar:
0 3 * * * cd /path/to/soptraloc && python manage.py update_time_predictions
```

### Métricas de Calidad

**Endpoint**: `GET /api/v1/routing/time-prediction/accuracy-report/`

```json
{
  "total_predictions": 120,
  "avg_error_minutes": 8.5,
  "accuracy_rate": 92.0,
  "recent_comparisons": [...]
}
```

**Objetivo**: Error promedio < 10 minutos, Precisión > 90%

---

## 📍 Datos Iniciales de Chile

### Rutas Configuradas (35)

#### Puertos → Almacenes Extraportuarios
- Puerto Valparaíso → Almacén Extra Valparaíso: **25 min** (5 km)
- Puerto San Antonio → Almacén Extra San Antonio: **20 min** (3 km)

#### Almacenes → CCTI/CDs (Carretera)
- Almacén Extra Valparaíso → CCTI: **90 min** (110 km)
- Almacén Extra Valparaíso → CD Quilicura: **100 min** (120 km)
- Almacén Extra San Antonio → CCTI: **110 min** (130 km)

#### Puertos → CCTI/CDs (Directo)
- Puerto Valparaíso → CCTI: **105 min** (115 km)
- Puerto San Antonio → CCTI: **120 min** (135 km)

#### Entre CDs Santiago (Urbano)
- CCTI → CD Quilicura: **35 min** (25 km) - Hora pico +30%
- CCTI → CD Campos: **30 min** (20 km)
- CD Quilicura → CD Campos: **20 min** (12 km)
- CD Campos → CD Puerto Madero: **15 min** (8 km)

### Operaciones Configuradas (70)

#### CCTI - Base
- Enganchar chasis: 10-15-20 min
- Desenganchar chasis: 8-12-15 min
- Bajar a piso: 12-18-25 min
- Levantar de piso: 12-18-25 min
- Check-in/out almacén: 5-10-15 min
- Trámites: 10-20-30 min
- Inspección: 15-25-40 min

#### Centros de Distribución (Clientes)
- Entrega cliente: 20-30-45 min
- Retiro cliente: 15-25-35 min
- Descarga contenedor: 15-25-40 min
- Espera: 10-20-60 min
- Trámites: 5-15-25 min

#### Puertos
- Ingreso puerto: 15-25-45 min
- Salida puerto: 10-20-40 min
- Retiro: 20-35-60 min
- Entrega: 20-35-60 min
- Trámites: 15-30-60 min
- Inspección: 20-40-90 min

#### Almacenes Extraportuarios
- Almacenaje: 15-25-40 min
- Check-in: 10-20-35 min
- Check-out: 10-20-35 min
- Bajar/levantar: 12-18-25 min
- Trámites: 10-20-30 min

---

## 🔄 Flujo Completo de Uso

### Escenario: Contenedor desde Puerto Valparaíso a CD Quilicura

#### 1. **Planificación** (Sistema)
```python
# El sistema calcula ruta óptima
origin = Location.objects.get(name='Puerto Valparaíso')
destination = Location.objects.get(name='CD Quilicura')

# Consulta tiempo estimado
pair = LocationPair.objects.get(origin=origin, destination=destination)
estimated_time = pair.get_estimated_time(departure_time)
# Resultado: 115 min (o ML: 108 min si hay datos)

# Agregar operaciones
pickup_time = OperationTime.objects.get(
    location=origin,
    operation_type='PORT_PICKUP'
).avg_time  # 35 min

delivery_time = OperationTime.objects.get(
    location=destination,
    operation_type='CLIENT_DELIVERY'
).avg_time  # 30 min

# Tiempo total estimado
total_time = pickup_time + estimated_time + delivery_time
# = 35 + 115 + 30 = 180 minutos (3 horas)
```

#### 2. **Ejecución** (Conductor)
- 08:00 - Salida de base
- 08:35 - Arribo a puerto (retiro: 35 min)
- 10:25 - Inicio viaje (real: 118 min - 3 min más por tráfico)
- 12:23 - Arribo a CD Quilicura
- 12:53 - Entrega completada (30 min)

#### 3. **Registro** (Sistema)
```python
# Se crea automáticamente al cambiar estado del contenedor
ActualTripRecord.objects.create(
    container=container,
    origin=origin,
    destination=destination,
    departure_time=datetime(2025, 10, 1, 10, 25),
    arrival_time=datetime(2025, 10, 1, 12, 23),
    # duration_minutes = 118 (calculado automático)
    day_of_week=1,  # Martes
    hour_of_day=10,
    was_peak_hour=True,  # Salida en hora pico
    weather='CLEAR'
)
```

#### 4. **Aprendizaje** (ML)
Al día siguiente (3 AM):
```bash
python manage.py update_time_predictions
```

El sistema:
- Detecta nuevo viaje: Puerto Valparaíso → CD Quilicura
- Calcula nuevo promedio con todos los viajes
- Actualiza ML: 115 min → 116 min (ajusta por hora pico)
- Incrementa confianza: 75% → 77%

---

## 📚 API Completa

### Time Prediction

#### POST `/api/v1/routing/time-prediction/predict-route/`
Predice tiempo de viaje.

**Body**:
```json
{
  "origin_id": 1,
  "destination_id": 2,
  "departure_time": "2025-10-01T14:30:00Z"
}
```

#### GET `/api/v1/routing/time-prediction/accuracy-report/`
Reporte de precisión del modelo ML.

#### GET `/api/v1/routing/time-prediction/optimization-suggestions/`
Sugerencias de optimización basadas en datos históricos.

#### POST `/api/v1/routing/time-prediction/update-ml/`
Fuerza actualización de predicciones ML.

### Routes

#### GET `/api/v1/routing/routes/today/`
Rutas del día actual.

#### POST `/api/v1/routing/routes/{id}/start/`
Inicia una ruta.

#### POST `/api/v1/routing/routes/{id}/complete/`
Completa una ruta.

### Route Stops

#### POST `/api/v1/routing/route-stops/{id}/complete/`
Marca parada como completada.

**Body**:
```json
{
  "actual_departure": "2025-10-01T15:30:00Z",
  "notes": "Entrega sin problemas"
}
```

---

## 🎯 Próximos Pasos

### Fase 1: Aprendizaje (Actual) ✅
- ✅ Tiempos manuales configurables
- ✅ Registro de viajes reales
- ✅ ML básico (promedios ponderados)
- ✅ Actualización diaria

### Fase 2: Optimización (Próximo)
- ⏳ Algoritmo VRP (Vehicle Routing Problem)
- ⏳ Clustering geográfico
- ⏳ Optimización por ventanas de tiempo
- ⏳ Balance de carga entre conductores

### Fase 3: Integración GPS (Futuro)
- ⏳ Tracking en tiempo real
- ⏳ ETA dinámico
- ⏳ Detección automática de retrasos
- ⏳ Ajuste de rutas en tiempo real

### Fase 4: ML Avanzado (Futuro)
- ⏳ Random Forest / XGBoost
- ⏳ Predicción de demoras
- ⏳ Análisis de patrones climáticos
- ⏳ Optimización multiobjetivo

---

## 🤝 Contribuir

Para agregar nuevas ubicaciones o ajustar tiempos:

1. **Admin Panel**: Crear manualmente en `LocationPair` o `OperationTime`

2. **Comando**: Modificar `load_initial_times.py` y ejecutar con `--reset`

3. **API**: Próximamente endpoint para crear desde interfaz

---

## 📞 Soporte

Para preguntas o problemas:
- 📧 Email: contacto@soptraloc.com
- 📱 WhatsApp: +56 9 XXXX XXXX
- 🐛 Issues: GitHub repo

---

**Versión**: 1.0  
**Última actualización**: 1 de Octubre, 2025  
**Estado**: ✅ Producción (Sin GPS)
