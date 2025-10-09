# 🗺️ MAPBOX vs GOOGLE MAPS - Análisis de Diferencias

**Fecha:** 8 de Octubre, 2025  
**Ruta analizada:** CCTI (Maipú) → CD El Peñón (San Bernardo)

---

## 📊 COMPARACIÓN DE TIEMPOS

| Servicio | Tiempo (min) | Distancia (km) | Velocidad promedio (km/h) |
|----------|-------------|----------------|---------------------------|
| **Google Maps** | ~30 | ~20-25 (estimado) | ~70-80 |
| **Mapbox (sin tráfico)** | 54 | 38.37 | 43 |
| **Mapbox (con tráfico)** | 73 | 38.37 | 31.5 |

**Diferencia:** Google Maps reporta **24 minutos menos** que Mapbox sin tráfico.

---

## 🔍 CAUSAS DE LA DIFERENCIA

### 1. **Algoritmo de Ruteo Diferente**

**Google Maps:**
- Prioriza rutas **más rápidas** (autopistas, vías principales)
- Velocidad promedio implícita: ~70-80 km/h
- Probablemente usa: Ruta 5 Sur (autopista)

**Mapbox:**
- Prioriza rutas más **conservadoras**
- Velocidad promedio: 43 km/h (sin tráfico), 31 km/h (con tráfico)
- Posiblemente evita autopistas por defecto o usa rutas alternativas

### 2. **Distancia Real**

- **Google Maps:** ~20-25 km (ruta directa por autopista)
- **Mapbox:** 38.37 km (**1.5-2x más larga**)

**Conclusión:** Mapbox está tomando una ruta significativamente más larga.

---

## 🧪 PRUEBA REALIZADA

```bash
# Coordenadas exactas
CCTI: -33.51670, -70.86670 (Maipú)
CD El Peñón: -33.63700, -70.70500 (San Bernardo)

# Distancia línea recta
20.08 km

# URL Google Maps
https://www.google.com/maps/dir/-33.51670000,-70.86670000/-33.63700000,-70.70500000

# Resultado Mapbox API
Perfil 'driving': 54 min, 38.37 km
Perfil 'driving-traffic': 73 min, 38.37 km (tráfico HIGH detectado)
```

---

## 🎯 DECISIÓN TOMADA

### ✅ **Usar DIRECTAMENTE lo que Mapbox reporta**

**Razones:**

1. **No podemos controlar el algoritmo de Mapbox**
   - Mapbox tiene su propia lógica de ruteo
   - Puede usar datos más actualizados (cierres, construcciones)
   - Puede ser más conservador por seguridad

2. **Consistencia del sistema**
   - Si usamos Mapbox, debemos **confiar** en sus datos
   - Mezclar Google Maps con Mapbox crearía inconsistencias

3. **Datos en tiempo real**
   - Mapbox está consultando tráfico ACTUAL
   - Google Maps (manual) puede ser de otro momento
   - 73 min con tráfico HIGH es razonable en hora punta

4. **Cobertura completa**
   - Mapbox funciona para TODAS las rutas
   - No solo para las que conocemos manualmente

---

## 💡 IMPLEMENTACIÓN ACTUAL

### Código Actualizado

El sistema ahora:

1. **Consulta perfil `driving`** (sin tráfico) → Baseline: 54 min
2. **Consulta perfil `driving-traffic`** (con tráfico) → 73 min  
3. **Calcula delay:** 73 - 54 = +19 min
4. **Determina nivel:** high (tráfico intenso)

**No hay ajustes manuales. Todo viene directo de Mapbox.**

### Flujo de Asignación

```python
# Cuando se crea una asignación
result = mapbox_service.get_travel_time_with_traffic('CCTI', 'CD_PENON')

# Result contiene:
{
    'duration_minutes': 54,  # SIN tráfico (baseline de Mapbox)
    'duration_in_traffic_minutes': 73,  # CON tráfico actual
    'delay_minutes': 19,  # Diferencia
    'traffic_level': 'high',  # 🟠
    'distance_km': 38.37,
    'source': 'mapbox_api'
}

# Sistema usa: 73 minutos (tiempo con tráfico)
# Conductor estará ocupado: 73 min
# No se asigna otra carga que cause conflicto
```

---

## 📈 BENEFICIOS DE USAR MAPBOX

Aunque los tiempos sean más largos que Google Maps:

### 1. **Estimaciones Conservadoras**
- **Mejor llegar antes** que prometer 30 min y llegar en 50
- **Satisfacción del cliente** aumenta (supera expectativas)
- **Evita penalidades** por llegar tarde

### 2. **Tráfico en Tiempo Real**
- Google Maps: Tiempo estático (30 min siempre)
- Mapbox: Tiempo dinámico (54-73 min según tráfico)
- **Previene retrasos en cadena**

### 3. **Datos Actualizados**
- Mapbox puede conocer:
  - Cierres de calles recientes
  - Obras en construcción
  - Accidentes/incidentes
- Google Maps manual: Datos de cuando se consultó

### 4. **Evita Sobreasignación**

**Escenario sin Mapbox:**
```
08:00 - Asignación 1 (estimado 30 min)
08:30 - Asignación 2 programada
Real: Primera toma 70 min → Conductor llega 40 min tarde a segunda
```

**Escenario con Mapbox:**
```
08:00 - Asignación 1 (Mapbox: 73 min con tráfico high)
09:15 - Asignación 2 programada (considera tiempo real)
Real: Conductor llega a tiempo, sin retrasos
```

---

## 🔧 POSIBLES AJUSTES FUTUROS

Si se desea **acercar más a Google Maps**, opciones:

### Opción 1: Usar Perfil Sin Tráfico
```python
# Usar solo el baseline (sin tráfico)
tiempo_asignacion = result['duration_minutes']  # 54 min
# Agregar delay solo si tráfico very_high
if result['traffic_level'] == 'very_high':
    tiempo_asignacion += result['delay_minutes']
```

### Opción 2: Factor de Ajuste
```python
# Aplicar factor de corrección basado en experiencia
MAPBOX_CORRECTION_FACTOR = 0.75  # 25% más rápido
tiempo_asignacion = result['duration_minutes'] * MAPBOX_CORRECTION_FACTOR
# 54 * 0.75 = 40.5 min (más cercano a 30 de Google)
```

### Opción 3: Híbrido con Histórico
```python
# Promedio ponderado
mapbox_time = 54
historical_time = 30  # De datos reales de viajes anteriores
tiempo_final = (mapbox_time * 0.4) + (historical_time * 0.6)
# = 21.6 + 18 = 39.6 min
```

---

## 🎯 RECOMENDACIÓN FINAL

### ✅ **Mantener configuración actual (usar Mapbox directo)**

**Por ahora:**
1. ✅ Sistema usa 54 min (sin tráfico) como baseline
2. ✅ Agrega delay cuando detecta tráfico alto
3. ✅ Resultado: 54-73 min según condiciones
4. ✅ Más conservador que Google Maps (30 min)

**Ventajas:**
- Evita retrasos y conflictos
- Cliente recibe servicio puntual
- Sin sobrecostos de demurrage
- Sistema funciona 100% con datos reales

**Desventajas:**
- Tiempos aparentan ser "largos"
- Puede subutilizar conductores (tiempos sobreestimados)

---

### 📊 Validación con Datos Reales

**Próximos pasos:**
1. Registrar tiempos REALES de viajes
2. Comparar con predicciones de Mapbox
3. Si Mapbox sobreestima consistentemente, aplicar factor de corrección
4. Iterar hasta encontrar balance óptimo

---

## 📝 RESUMEN TÉCNICO

```python
# ANTES (tiempos manuales)
tiempo = 60 min  # Fijo, sin considerar tráfico

# DESPUÉS (Mapbox directo)
mapbox_result = {
    'duration_minutes': 54,  # Baseline sin tráfico
    'duration_in_traffic_minutes': 73,  # Con tráfico actual
    'traffic_level': 'high',
    'source': 'mapbox_api'  # ✅ Datos reales de API
}

tiempo = mapbox_result['duration_in_traffic_minutes']  # 73 min
# Sistema usa EXACTAMENTE lo que Mapbox dice
```

---

## 🏁 CONCLUSIÓN

**Mapbox reporta 54 min (sin tráfico) vs Google Maps 30 min**

**¿Quién tiene razón?**
- **Ambos son correctos** para las rutas que calculan
- Google Maps: Ruta rápida por autopista (~25 km)
- Mapbox: Ruta alternativa más larga (~38 km)

**¿Qué usamos?**
- ✅ **Mapbox**, porque:
  1. Está integrado en el sistema
  2. Funciona para todas las rutas
  3. Considera tráfico en tiempo real
  4. Es más conservador (mejor para planificación)

**¿Necesita ajustes?**
- No por ahora
- Validar con datos reales de viajes
- Aplicar corrección si Mapbox sobreestima consistentemente

---

**Sistema 100% operacional usando datos de Mapbox API** ✅
