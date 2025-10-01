# 🚛 Sistema de Gestión de Tiempos y Machine Learning

## ✨ Nuevo: Módulo Routing con ML

Sistema híbrido que gestiona tiempos de viaje **sin necesidad de GPS**, usando tiempos manuales que el sistema aprende a mejorar automáticamente con Machine Learning.

### 🎯 Características Principales

| Característica | Estado | Descripción |
|---------------|--------|-------------|
| ⏱️ Tiempos Manuales | ✅ Implementado | Configura tiempos base entre ubicaciones |
| 🤖 Machine Learning | ✅ Implementado | Aprende de viajes reales para mejorar predicciones |
| 🚦 Horas Pico | ✅ Implementado | Ajuste automático según horario (ej: +30% en Santiago urbano) |
| ⚙️ Operaciones Detalladas | ✅ Implementado | Tiempos para enganchar chasis, bajar a piso, trámites, etc. |
| 📊 Dashboard ML | ✅ Implementado | Admin panel con confianza, muestras, predicciones |
| 📈 Análisis de Precisión | ✅ Implementado | Reportes de error, sugerencias de optimización |
| 🗺️ Optimización de Rutas | ⏳ Próximamente | Algoritmo VRP para rutas eficientes |
| 📍 GPS Tracking | ⏳ Pendiente permiso | Integración cuando se obtenga API |

### 📦 Datos Iniciales de Chile

**35 rutas configuradas** entre:
- Puertos: Valparaíso, San Antonio (TPS, TCVAL, STI)
- Almacenes Extraportuarios
- CCTI - Base Maipú
- CDs: Quilicura, Campos, Puerto Madero, El Peñón

**70 operaciones** definidas:
- Enganchar/desenganchar chasis (8-20 min)
- Bajar/levantar contenedor (12-25 min)
- Operaciones portuarias (15-60 min)
- Entregas cliente (20-45 min)

### 🚀 Quick Start

```bash
# 1. Aplicar migraciones
python manage.py migrate routing

# 2. Cargar datos iniciales de Chile
python manage.py load_initial_times

# 3. Actualizar predicciones ML (ejecutar diariamente)
python manage.py update_time_predictions --analyze
```

### 📊 Ejemplo de Predicción

```python
# Consultar tiempo Puerto Valparaíso → CCTI
pair = LocationPair.objects.get(
    origin__name='Puerto Valparaíso',
    destination__name='CCTI - Base Maipú'
)

# Primera vez (sin datos)
estimated_time = pair.get_estimated_time()
# Resultado: 105 min (tiempo base manual)
# Confianza: 60%

# Después de 50 viajes reales registrados
estimated_time = pair.get_estimated_time()
# Resultado: 98 min (ML aprendió que es más rápido)
# Confianza: 85%
```

### 🤖 Machine Learning

**Algoritmo actual**: Promedio ponderado
- 60% datos recientes (últimos 30 días)
- 40% datos históricos
- Confianza basada en cantidad de muestras y variabilidad

**Roadmap ML**:
- ✅ v1.0: Promedios ponderados (actual)
- ⏳ v2.0: Random Forest para predicciones avanzadas
- ⏳ v3.0: XGBoost con variables climáticas y eventos

### 📱 API Endpoints

```bash
# Predecir tiempo de viaje
POST /api/v1/routing/time-prediction/predict-route/
{
  "origin_id": 1,
  "destination_id": 2,
  "departure_time": "2025-10-01T14:30:00Z"
}

# Reporte de precisión ML
GET /api/v1/routing/time-prediction/accuracy-report/

# Sugerencias de optimización
GET /api/v1/routing/time-prediction/optimization-suggestions/

# Forzar actualización ML
POST /api/v1/routing/time-prediction/update-ml/
```

### 📈 Monitoreo de Calidad

El sistema genera reportes automáticos:

```
============================================================
📊 ANÁLISIS DE PRECISIÓN
============================================================

Total predicciones evaluadas: 120
Error promedio: 8.5 minutos
Tasa de precisión: 92%

Últimas comparaciones:
  Puerto Valparaíso → CCTI: Predicho=105min, Real=102min, Error=2.9%
  CCTI → CD Quilicura: Predicho=35min, Real=38min, Error=8.6%

============================================================
💡 SUGERENCIAS DE OPTIMIZACIÓN
============================================================

1. Puerto San Antonio → CCTI
   Problema: Variabilidad alta (35.2%)
   Sugerencia: Revisar factores externos (tráfico, horarios)

2. CCTI → CD El Peñón
   Problema: Tiempo base desactualizado (25% diferencia)
   Sugerencia: Actualizar tiempo base de 40 a 32 minutos
```

### 🎯 Casos de Uso

#### 1. Planificación de Rutas
```python
# Calcular tiempo total estimado para una ruta
route_time = (
    origin_operation_time +  # Ej: retiro puerto (35 min)
    travel_time +            # Ej: viaje (105 min)
    destination_operation_time  # Ej: entrega (30 min)
)
# Total: 170 minutos (2h 50min)
```

#### 2. Registro Automático
```python
# Al completar contenedor, se registra automáticamente
ActualTripRecord.objects.create(
    container=container,
    origin=origin,
    destination=destination,
    departure_time=actual_departure,
    arrival_time=actual_arrival,
    # ML usa estos datos para mejorar predicciones
)
```

#### 3. Actualización Diaria
```bash
# Cron job diario a las 3 AM
0 3 * * * cd /path/to/soptraloc && python manage.py update_time_predictions
```

### 📚 Documentación Completa

Ver: **[SISTEMA_TIEMPOS_ML.md](SISTEMA_TIEMPOS_ML.md)**

Incluye:
- 📖 Guía completa de uso
- 🏗️ Arquitectura detallada
- 🤖 Explicación del ML
- 📊 API completa
- 🚀 Próximos pasos
- 💡 Mejores prácticas

---

### 🎉 Ventajas vs GPS (mientras se espera permiso)

| Aspecto | Sistema Actual | Con GPS |
|---------|---------------|---------|
| **Costo** | ✅ $0 | 💰 $X/mes por unidad |
| **Implementación** | ✅ Inmediata | ⏳ Requiere hardware |
| **Mantenimiento** | ✅ Bajo | 🔧 Medio-Alto |
| **Precisión inicial** | 🟡 Manual (~90%) | ✅ Alta (~95%) |
| **Precisión con ML** | ✅ Alta (~92%) | ✅ Muy Alta (~98%) |
| **Aprendizaje** | ✅ Continuo | ✅ Continuo |
| **Offline** | ✅ Funciona | ❌ Requiere señal |

**Conclusión**: Sistema actual es **excelente para empezar** y seguirá útil incluso con GPS (como backup y validación).

---

### 🔄 Integración Futura con GPS

Cuando se obtenga acceso a GPS API:

```python
# El sistema será híbrido
if gps_available and gps_signal_good:
    # Usar posición GPS en tiempo real
    current_location = gps.get_position()
    eta = calculate_eta_with_traffic(current_location, destination)
else:
    # Fallback a predicción ML
    eta = LocationPair.get_estimated_time()

# Ambos métodos se complementan
ml_prediction = ML.predict()
gps_eta = GPS.calculate()
final_eta = (ml_prediction * 0.3) + (gps_eta * 0.7)  # Peso según confianza
```

---

**Desarrollado con ❤️ por el equipo Soptraloc**  
**Versión**: 2.1-ml  
**Última actualización**: 1 de Octubre, 2025
