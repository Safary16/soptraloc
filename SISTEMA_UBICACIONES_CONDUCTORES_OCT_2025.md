# 🗺️ Sistema de Ubicaciones y Disponibilidad de Conductores

**Fecha:** Octubre 7, 2025  
**Versión:** SOPTRALOC TMS v3.1  
**Autor:** GitHub Copilot  

---

## 📋 Resumen Ejecutivo

Se ha implementado un **sistema completo de gestión de ubicaciones** y **seguimiento de disponibilidad de conductores** que permite:

1. ✅ **Catálogo de ubicaciones fijas** con direcciones completas de todos los CDs
2. ✅ **Consultas a Mapbox Directions usando direcciones** en lugar de solo coordenadas
3. ✅ **Tracking de disponibilidad de conductores** en tiempo real
4. ✅ **Prevención de asignaciones duplicadas**
5. ✅ **Horarios y programación** de conductores por día
6. ✅ **API REST completa** para integración con apps móviles

---

## 🏢 Ubicaciones Configuradas

### Centros de Distribución (CDs)

| Código | Nombre | Dirección Completa |
|--------|--------|-------------------|
| **CD_PENON** | CD El Peñón | Av. Presidente Jorge Alessandri 18899, San Bernardo, RM |
| **CD_QUILICURA** | CD Quilicura | Eduardo Frei Montalva 8301, Quilicura, RM |
| **CD_PUERTO_MADERO** | CD Puerto Madero (Puerto Santiago) | Puerto Madero 9710, Pudahuel, RM |
| **CD_CAMPOS_CHILE** | CD Campos de Chile | Av. El Parque 1000, Pudahuel, RM |
| **CCTI** | Centro de Contenedores Terrestres Internacionales | Camino Los Agricultores, Parcela 41, Maipú, RM |
| **CLEP_SAI** | CLEP San Antonio (Todo lo liberado) | Av. Las Factorías 7373, San Antonio, V Región |

### Aliases Soportados

El sistema reconoce múltiples formas de referirse a las ubicaciones:

```python
# Quilicura
'CD_QL', 'QUILICURA', 'CD QUILICURA' → 'CD_QUILICURA'

# Puerto Madero
'CD_PUERTO_STGO', 'PUERTO_MADERO', 'CD PUERTO STGO' → 'CD_PUERTO_MADERO'

# Campos de Chile
'CD_CDCH', 'CAMPOS_CHILE', 'CD CAMPOS DE CHILE' → 'CD_CAMPOS_CHILE'

# El Peñón
'EL_PENON', 'PENON', 'CD EL PEÑON' → 'CD_PENON'

# San Antonio
'SAI', 'SAN_ANTONIO', 'CLEP', 'LIBERADO' → 'CLEP_SAI'
```

---

## 🚗 Sistema de Disponibilidad de Conductores

### Conceptos Clave

El sistema ahora calcula **automáticamente**:

1. **Estado actual** de cada conductor (disponible, en ruta, ocupado)
2. **Ubicación estimada** en cualquier momento
3. **Hora de disponibilidad** basada en ETAs reales
4. **Conflictos de horario** para prevenir doble asignación
5. **Horario diario** completo con todas las rutas

### Estados de Conductores

| Estado | Descripción | Color |
|--------|-------------|-------|
| `available` | Conductor disponible para asignación | 🟢 |
| `on_route` | Conductor en ruta activa | 🟡 |
| `will_be_busy` | Conductor ocupado en el horario consultado | 🔴 |

---

## 🔧 Uso del Sistema

### 1. Consultar Estado de un Conductor

**API Endpoint:**
```bash
GET /api/v1/routing/route-tracking/driver-status/?driver_id=45
```

**Respuesta:**
```json
{
  "success": true,
  "driver_id": 45,
  "driver_name": "Juan Pérez",
  "is_available": false,
  "status": "on_route",
  "estimated_location": "En ruta (llegará en 25 min)",
  "available_at": "2025-10-07T16:00:00Z",
  "estimated_arrival": "2025-10-07T16:00:00Z",
  "current_assignment": {
    "id": 123,
    "container_number": "CMAU1234567"
  },
  "message": "Juan Pérez llegará a destino a las 16:00"
}
```

**Consultar disponibilidad futura:**
```bash
GET /api/v1/routing/route-tracking/driver-status/?driver_id=45&check_time=2025-10-07T17:00:00Z
```

---

### 2. Listar Conductores Disponibles

**API Endpoint:**
```bash
GET /api/v1/routing/route-tracking/available-drivers/
```

**Parámetros opcionales:**
- `at_time`: ISO datetime para verificar disponibilidad futura
- `for_location`: Código de ubicación para priorizar cercanos

**Respuesta:**
```json
{
  "success": true,
  "at_time": "2025-10-07T15:00:00Z",
  "for_location": "CCTI",
  "count": 12,
  "drivers": [
    {
      "driver_id": 45,
      "nombre": "Juan Pérez",
      "rut": "12345678-9",
      "status": {...},
      "priority": 1
    }
  ]
}
```

---

### 3. Ver Horario de un Conductor

**API Endpoint:**
```bash
GET /api/v1/routing/route-tracking/driver-schedule/?driver_id=45&date=2025-10-07
```

**Respuesta:**
```json
{
  "success": true,
  "driver_id": 45,
  "driver_name": "Juan Pérez",
  "date": "2025-10-07",
  "schedule": [
    {
      "assignment_id": 123,
      "start_time": "2025-10-07T08:00:00Z",
      "estimated_arrival": "2025-10-07T08:45:00Z",
      "actual_arrival": null,
      "duration_minutes": 45,
      "status": "in_progress"
    },
    {
      "assignment_id": 124,
      "start_time": "2025-10-07T10:00:00Z",
      "estimated_arrival": "2025-10-07T11:30:00Z",
      "actual_arrival": "2025-10-07T11:35:00Z",
      "duration_minutes": 90,
      "status": "completed"
    }
  ]
}
```

---

### 4. Listar Todas las Ubicaciones

**API Endpoint:**
```bash
GET /api/v1/routing/route-tracking/locations/
```

**Respuesta:**
```json
{
  "success": true,
  "count": 6,
  "locations": [
    {
      "code": "CD_PENON",
      "name": "CD El Peñón",
      "full_name": "Centro de Distribución El Peñón",
      "address": "Avenida Presidente Jorge Alessandri 18899, San Bernardo",
      "city": "San Bernardo",
      "region": "Región Metropolitana",
      "latitude": -33.6370,
      "longitude": -70.7050
    }
  ]
}
```

---

### 5. Iniciar Ruta con Códigos de Ubicación

**Nueva funcionalidad:** Ahora puedes usar códigos de ubicación en lugar de coordenadas:

```bash
POST /api/v1/routing/route-tracking/start-route/

{
  "assignment_id": 123,
  "driver_id": 45,
  "origin": {
    "name": "CCTI",
    "latitude": -33.5167,
    "longitude": -70.8667
  },
  "destination": {
    "name": "CD_PENON",
    "latitude": -33.6370,
    "longitude": -70.7050
  }
}
```

El sistema **automáticamente**:
1. Reconoce "CCTI" y "CD_PENON" como códigos del catálogo
2. Usa las direcciones completas para consultar Mapbox Directions
3. Calcula ETA considerando tráfico real
4. Actualiza el estado del conductor a "ocupado"
5. Genera alertas si hay tráfico o problemas

---

## 🐍 Uso en Python

### Importar Servicios

```python
from apps.routing.locations_catalog import get_location, format_route_name
from apps.routing.driver_availability_service import driver_availability
from apps.routing.mapbox_service import mapbox_service
```

### Obtener Información de Ubicación

```python
# Por código
location = get_location('CD_PENON')
print(location.full_name)  # "Centro de Distribución El Peñón"
print(location.get_mapbox_query())  # Dirección completa

# Por alias
location = get_location('QUILICURA')  # También funciona
location = get_location('cd el penon')  # Case-insensitive
```

### Consultar Tráfico entre Ubicaciones

```python
from datetime import datetime

# Usando códigos de ubicación
traffic_data = mapbox_service.get_travel_time_with_traffic(
    origin='CCTI',
    destination='CD_PENON',
    departure_time=datetime.now()
)

print(f"Distancia: {traffic_data['distance_km']} km")
print(f"Tiempo con tráfico: {traffic_data['duration_in_traffic_minutes']} min")
print(f"Nivel de tráfico: {traffic_data['traffic_level']}")
print(f"Origen: {traffic_data['origin_name']}")
print(f"Destino: {traffic_data['destination_name']}")
```

### Verificar Disponibilidad de Conductor

```python
from django.utils import timezone
from datetime import timedelta

# Estado actual
status = driver_availability.get_driver_status(driver_id=45)
print(f"Disponible: {status['is_available']}")
print(f"Estado: {status['status']}")
print(f"Ubicación estimada: {status['estimated_location']}")

# Disponibilidad futura (ej: en 2 horas)
future_time = timezone.now() + timedelta(hours=2)
status = driver_availability.get_driver_status(
    driver_id=45,
    check_time=future_time
)
```

### Obtener Conductores Disponibles

```python
# Ahora
available_now = driver_availability.get_available_drivers()
print(f"{len(available_now)} conductores disponibles")

# A las 17:00
from datetime import datetime
at_5pm = datetime.now().replace(hour=17, minute=0)
available_at_5pm = driver_availability.get_available_drivers(at_time=at_5pm)
```

### Verificar si se Puede Asignar una Ruta

```python
from datetime import datetime, timedelta

start_time = datetime.now() + timedelta(hours=1)
duration = 45  # minutos

can_assign, message = driver_availability.can_assign_route(
    driver_id=45,
    start_time=start_time,
    estimated_duration_minutes=duration
)

if can_assign:
    print(f"✅ {message}")
    # Proceder con asignación
else:
    print(f"❌ {message}")
    # Buscar otro conductor
```

### Detectar Conflictos de Horario

```python
from datetime import datetime, timedelta

start = datetime.now()
end = start + timedelta(minutes=60)

conflicts = driver_availability.check_conflicts(
    driver_id=45,
    start_time=start,
    estimated_end_time=end
)

if conflicts:
    print(f"⚠️ {len(conflicts)} conflictos detectados:")
    for conflict in conflicts:
        print(f"  - Asignación #{conflict['assignment_id']}")
        print(f"    Inicio: {conflict['start']}")
        print(f"    Fin estimado: {conflict['estimated_end']}")
```

---

## 📁 Archivos Creados/Modificados

### Nuevos Archivos

1. **`apps/routing/locations_catalog.py`** (272 líneas)
   - Catálogo completo de ubicaciones con direcciones
   - Funciones helper para búsqueda y formateo
   - Tiempos estáticos de fallback
   - Aliases y normalización

2. **`apps/routing/driver_availability_service.py`** (322 líneas)
   - Servicio de disponibilidad de conductores
   - Cálculo de estados y ubicaciones estimadas
   - Detección de conflictos
   - Sugerencias de asignación

3. **`apps/core/management/commands/load_locations.py`** (93 líneas)
   - Comando para cargar ubicaciones a BD
   - Soporte para actualización con `--force`
   - Resumen detallado de operaciones

### Archivos Modificados

1. **`apps/routing/mapbox_service.py`**
   - ✅ Ahora acepta códigos de ubicación O coordenadas
   - ✅ Usa direcciones completas para consultas más precisas
   - ✅ Retorna nombres de origen/destino en respuesta
   - ✅ Fallback con tiempos estáticos del catálogo

2. **`apps/routing/route_start_service.py`**
   - ✅ Detecta automáticamente si usar código o coordenadas
   - ✅ Usa nombres del catálogo para mejor logging

3. **`apps/routing/api_views.py`**
   - ✅ **+200 líneas** de nuevos endpoints:
     - `driver-status/` - Estado de conductor
     - `available-drivers/` - Lista de disponibles
     - `driver-schedule/` - Horario del día
     - `locations/` - Catálogo de ubicaciones

4. **`post_deploy.sh`**
   - ✅ Agregado PASO 6: Cargar ubicaciones automáticamente
   - ✅ Actualizado resumen con 6 ubicaciones

---

## 🎯 Casos de Uso

### Caso 1: Asignar Ruta Considerando Disponibilidad

```python
from apps.routing.driver_availability_service import driver_availability
from apps.routing.route_start_service import RouteStartService
from datetime import datetime, timedelta

# 1. Determinar hora de inicio
start_time = datetime.now() + timedelta(minutes=30)

# 2. Encontrar conductor disponible
available = driver_availability.get_available_drivers(
    at_time=start_time,
    for_location='CCTI'
)

if not available:
    print("❌ No hay conductores disponibles")
else:
    driver = available[0]['driver']
    
    # 3. Verificar que no haya conflictos
    can_assign, msg = driver_availability.can_assign_route(
        driver_id=driver.id,
        start_time=start_time,
        estimated_duration_minutes=45
    )
    
    if can_assign:
        # 4. Iniciar ruta
        result = RouteStartService.start_route(
            assignment_id=assignment.id,
            driver_id=driver.id,
            origin_name='CCTI',
            destination_name='CD_PENON',
            origin_lat=-33.5167,
            origin_lng=-70.8667,
            dest_lat=-33.6370,
            dest_lng=-70.7050
        )
        
        print(f"✅ Ruta asignada a {driver.nombre}")
        print(f"   ETA: {result['time']['eta']}")
        print(f"   Tráfico: {result['traffic']['level']}")
```

### Caso 2: Evitar Doble Asignación

```python
# Verificar estado actual
status = driver_availability.get_driver_status(driver_id=45)

if status['is_available']:
    # Asignar inmediatamente
    assign_route(driver_id=45)
else:
    # Mostrar cuándo estará disponible
    available_at = status['available_at']
    print(f"Conductor disponible a las {available_at.strftime('%H:%M')}")
    
    # Sugerir alternativa
    alternative = driver_availability.suggest_next_driver(
        origin_location='CCTI'
    )
    
    if alternative:
        print(f"Conductor alternativo sugerido: {alternative['nombre']}")
```

### Caso 3: Dashboard de Operaciones

```python
from django.utils import timezone

# Ver todos los conductores y su estado
all_drivers = Driver.objects.filter(is_active=True)

for driver in all_drivers:
    status = driver_availability.get_driver_status(driver.id)
    
    print(f"\n{driver.nombre} ({driver.id})")
    print(f"  Estado: {status['status']}")
    print(f"  Ubicación: {status['estimated_location']}")
    
    if status['current_assignment']:
        assignment = status['current_assignment']
        print(f"  Asignación activa: #{assignment.id}")
        print(f"  ETA: {status['estimated_arrival']}")
    
    # Ver horario del día
    schedule = driver_availability.get_driver_schedule(driver.id)
    print(f"  Rutas hoy: {len(schedule)}")
```

---

## 🧪 Testing

### Pruebas Manuales

```bash
# 1. Cargar ubicaciones
python manage.py load_locations

# 2. Verificar en shell
python manage.py shell
```

```python
from apps.routing.locations_catalog import get_location, list_all_locations

# Probar búsqueda
ccti = get_location('CCTI')
print(ccti.get_mapbox_query())

# Probar aliases
quilicura = get_location('CD_QL')
print(quilicura.name)  # "CD Quilicura"

# Listar todas
locations = list_all_locations()
print(f"{len(locations)} ubicaciones")
```

### Probar API

```bash
# Obtener ubicaciones
curl -X GET "http://localhost:8000/api/v1/routing/route-tracking/locations/" \
  -H "Authorization: Token YOUR_TOKEN"

# Estado de conductor
curl -X GET "http://localhost:8000/api/v1/routing/route-tracking/driver-status/?driver_id=1" \
  -H "Authorization: Token YOUR_TOKEN"

# Conductores disponibles
curl -X GET "http://localhost:8000/api/v1/routing/route-tracking/available-drivers/" \
  -H "Authorization: Token YOUR_TOKEN"
```

---

## 💡 Ventajas del Sistema

### 1. Prevención de Conflictos
- ✅ No se puede asignar el mismo conductor a dos rutas simultáneas
- ✅ Sistema advierte si hay conflictos de horario
- ✅ Sugiere conductores alternativos automáticamente

### 2. Optimización de Tiempos
- ✅ Saber dónde estará cada conductor a X hora
- ✅ Asignar rutas desde ubicación más cercana
- ✅ Minimizar tiempos muertos

### 3. Planificación Mejorada
- ✅ Ver horario completo del día por conductor
- ✅ Identificar períodos de alta demanda
- ✅ Balancear carga de trabajo

### 4. Tráfico en Tiempo Real
- ✅ ETAs precisos considerando condiciones actuales
- ✅ Direcciones completas = consultas más precisas
- ✅ Fallback automático si API no disponible

---

## 📊 Métricas y Reportes

### Ejemplo: Reporte de Disponibilidad

```python
from django.utils import timezone
from datetime import timedelta

# Hora actual y próximas 4 horas
now = timezone.now()
hours = [now + timedelta(hours=i) for i in range(5)]

print("REPORTE DE DISPONIBILIDAD - Próximas 4 horas")
print("=" * 70)

for hour in hours:
    available = driver_availability.get_available_drivers(at_time=hour)
    print(f"{hour.strftime('%H:%M')}: {len(available)} conductores disponibles")
```

### Ejemplo: Reporte de Utilización

```python
from datetime import date

today = date.today()
all_drivers = Driver.objects.filter(is_active=True)

total_time = 0
total_routes = 0

for driver in all_drivers:
    schedule = driver_availability.get_driver_schedule(
        driver.id,
        datetime.combine(today, datetime.min.time())
    )
    
    driver_time = sum(item['duration_minutes'] or 0 for item in schedule)
    total_time += driver_time
    total_routes += len(schedule)
    
    print(f"{driver.nombre}: {len(schedule)} rutas, {driver_time} min")

print(f"\nTOTAL: {total_routes} rutas, {total_time} minutos")
print(f"Promedio: {total_time / len(all_drivers):.1f} min/conductor")
```

---

## 🚀 Próximos Pasos Sugeridos

### Mejoras Futuras

1. **Priorización Inteligente**
   - Calcular distancia real del conductor a ubicación de pickup
   - Considerar historial de rendimiento
   - Optimizar por tipo de vehículo

2. **Notificaciones Automáticas**
   - Alertar a conductor cuando quede disponible
   - Notificar sobre próxima asignación
   - Recordatorios de inicio de ruta

3. **Integración con App Móvil**
   - Conductor ve su horario del día
   - Acepta/rechaza asignaciones
   - Reporta problemas en ruta

4. **Analytics Avanzados**
   - Heatmap de disponibilidad por hora
   - Predicción de demanda
   - Optimización de rutas

5. **Geocoding Automático**
  - Actualizar coordenadas desde Mapbox o servicio equivalente
  - Validar direcciones al crear ubicaciones
  - Cache de geocoding results

---

## 📞 Soporte

**Documentación relacionada:**
- `CONFIGURAR_MAPBOX_PASO_A_PASO.md` - Configuración y buenas prácticas con Mapbox
- `ROUTING_ML_QUICKSTART.md` - Uso del motor de rutas y predicciones
- `COORDENADAS_CHILE_EJEMPLOS.md` - Ejemplos de coordenadas reales

**Archivos importantes:**
- `apps/routing/locations_catalog.py` - Catálogo de ubicaciones
- `apps/routing/driver_availability_service.py` - Servicio de disponibilidad
- `apps/routing/api_views.py` - Endpoints REST

---

## ✅ Checklist de Implementación

- [x] Crear catálogo de ubicaciones con 6 CDs
- [x] Implementar servicio de disponibilidad de conductores
- [x] Integrar Mapbox service para uso de direcciones y tráfico
- [x] Crear 4 nuevos endpoints REST
- [x] Crear comando `load_locations`
- [x] Actualizar `post_deploy.sh`
- [x] Probar carga de ubicaciones
- [x] Crear documentación completa

**Estado:** ✅ **IMPLEMENTACIÓN COMPLETA**

---

**Fecha de creación:** Octubre 7, 2025  
**Última actualización:** Octubre 7, 2025  
**Versión del documento:** 1.0
