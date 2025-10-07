# 🚀 Guía Rápida: Ubicaciones y Disponibilidad de Conductores

**5 minutos para empezar a usar el nuevo sistema**

---

## ✅ Paso 1: Cargar Ubicaciones (Una vez)

```bash
cd soptraloc_system
python manage.py load_locations
```

**Resultado:** 6 ubicaciones cargadas:
- ✅ CD El Peñón (San Bernardo)
- ✅ CD Quilicura
- ✅ CD Puerto Madero (Pudahuel)
- ✅ CD Campos de Chile (Pudahuel)
- ✅ CCTI (Maipú)
- ✅ CLEP San Antonio (V Región)

> **Nota:** En producción (Render) esto se ejecuta automáticamente en cada deploy.

---

## 📍 Paso 2: Usar Códigos de Ubicación

### Antes (solo coordenadas):
```python
traffic_data = gmaps_service.get_travel_time_with_traffic(
    origin_lat=-33.5167,
    origin_lng=-70.8667,
    dest_lat=-33.6370,
    dest_lng=-70.7050,
    departure_time=datetime.now()
)
```

### Ahora (códigos simples):
```python
traffic_data = gmaps_service.get_travel_time_with_traffic(
    origin='CCTI',
    destination='CD_PENON',
    departure_time=datetime.now()
)
```

**Ventajas:**
- ✅ Más simple y legible
- ✅ Usa direcciones completas = más preciso
- ✅ Soporta aliases ('QUILICURA', 'CD_QL', etc.)
- ✅ Fallback automático si API no disponible

---

## 🚗 Paso 3: Verificar Disponibilidad de Conductores

### En Python:

```python
from apps.routing.driver_availability_service import driver_availability

# ¿Está disponible el conductor #45?
status = driver_availability.get_driver_status(driver_id=45)

if status['is_available']:
    print(f"✅ Disponible: {status['message']}")
else:
    print(f"❌ Ocupado: {status['message']}")
    print(f"   Disponible a las: {status['available_at']}")
```

### Vía API REST:

```bash
curl -X GET "https://tu-app.onrender.com/api/v1/routing/route-tracking/driver-status/?driver_id=45" \
  -H "Authorization: Token TU_TOKEN"
```

---

## 📋 Paso 4: Ver Horario del Día

### En Python:

```python
from datetime import datetime

# Ver horario del conductor #45 para hoy
schedule = driver_availability.get_driver_schedule(
    driver_id=45,
    date=datetime.now()
)

print(f"Rutas hoy: {len(schedule)}")
for item in schedule:
    print(f"- Asignación #{item['assignment_id']}")
    print(f"  Inicio: {item['start_time']}")
    print(f"  ETA: {item['estimated_arrival']}")
    print(f"  Estado: {item['status']}")
```

### Vía API REST:

```bash
curl -X GET "https://tu-app.onrender.com/api/v1/routing/route-tracking/driver-schedule/?driver_id=45&date=2025-10-07" \
  -H "Authorization: Token TU_TOKEN"
```

---

## 🔍 Paso 5: Encontrar Conductores Disponibles

### En Python:

```python
from datetime import datetime, timedelta

# Ahora
disponibles_ahora = driver_availability.get_available_drivers()
print(f"{len(disponibles_ahora)} conductores disponibles ahora")

# En 2 horas
en_2_horas = datetime.now() + timedelta(hours=2)
disponibles_luego = driver_availability.get_available_drivers(at_time=en_2_horas)
print(f"{len(disponibles_luego)} conductores disponibles en 2 horas")

# Para ubicación específica (prioriza cercanos)
para_ccti = driver_availability.get_available_drivers(for_location='CCTI')
```

### Vía API REST:

```bash
# Ahora
curl -X GET "https://tu-app.onrender.com/api/v1/routing/route-tracking/available-drivers/" \
  -H "Authorization: Token TU_TOKEN"

# En 2 horas
curl -X GET "https://tu-app.onrender.com/api/v1/routing/route-tracking/available-drivers/?at_time=2025-10-07T17:00:00Z" \
  -H "Authorization: Token TU_TOKEN"
```

---

## 🎯 Casos de Uso Comunes

### Caso 1: Asignar Ruta sin Conflictos

```python
from apps.routing.driver_availability_service import driver_availability
from datetime import datetime, timedelta

# 1. Verificar disponibilidad
driver_id = 45
start_time = datetime.now() + timedelta(minutes=15)

can_assign, message = driver_availability.can_assign_route(
    driver_id=driver_id,
    start_time=start_time,
    estimated_duration_minutes=60
)

if can_assign:
    # 2. Asignar ruta
    from apps.routing.route_start_service import RouteStartService
    
    result = RouteStartService.start_route(
        assignment_id=123,
        driver_id=driver_id,
        origin_name='CCTI',
        destination_name='CD_PENON',
        origin_lat=-33.5167,
        origin_lng=-70.8667,
        dest_lat=-33.6370,
        dest_lng=-70.7050
    )
    
    print(f"✅ Ruta asignada")
    print(f"   ETA: {result['time']['eta']}")
else:
    print(f"❌ No se puede asignar: {message}")
```

### Caso 2: Sugerir Mejor Conductor

```python
# Encontrar el mejor conductor disponible para ruta desde CCTI
best = driver_availability.suggest_next_driver(
    origin_location='CCTI',
    for_time=datetime.now()
)

if best:
    print(f"Sugerencia: {best['nombre']} (ID: {best['driver_id']})")
else:
    print("No hay conductores disponibles")
```

### Caso 3: Dashboard de Operaciones

```python
from apps.drivers.models import Driver

# Ver estado de todos los conductores
conductores = Driver.objects.filter(is_active=True)

for conductor in conductores:
    status = driver_availability.get_driver_status(conductor.id)
    
    emoji = "🟢" if status['is_available'] else "🔴"
    print(f"{emoji} {conductor.nombre}: {status['estimated_location']}")
```

---

## 📍 Ubicaciones Disponibles

### Códigos que Puedes Usar:

| Código Principal | Aliases Aceptados |
|-----------------|-------------------|
| `CCTI` | ccti, CCTI |
| `CD_PENON` | el_penon, penon, CD EL PENON |
| `CD_QUILICURA` | cd_ql, quilicura, CD QUILICURA |
| `CD_PUERTO_MADERO` | cd_puerto_stgo, puerto_madero, PUERTO MADERO |
| `CD_CAMPOS_CHILE` | cd_cdch, campos_chile, CD CAMPOS DE CHILE |
| `CLEP_SAI` | sai, san_antonio, clep, liberado |

**Ejemplos válidos:**
```python
get_location('CCTI')           # ✅
get_location('cd el penon')    # ✅ (case-insensitive)
get_location('QUILICURA')      # ✅ (alias)
get_location('CD_QL')          # ✅ (alias)
```

---

## 🌐 Endpoints API

### 1. **Listar Ubicaciones**
```
GET /api/v1/routing/route-tracking/locations/
```

### 2. **Estado de Conductor**
```
GET /api/v1/routing/route-tracking/driver-status/?driver_id=45
```

### 3. **Conductores Disponibles**
```
GET /api/v1/routing/route-tracking/available-drivers/
GET /api/v1/routing/route-tracking/available-drivers/?at_time=2025-10-07T17:00:00Z
```

### 4. **Horario de Conductor**
```
GET /api/v1/routing/route-tracking/driver-schedule/?driver_id=45&date=2025-10-07
```

### 5. **Iniciar Ruta (ahora acepta códigos)**
```
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

---

## ⚡ Tips Rápidos

### 1. Verificar antes de asignar
```python
status = driver_availability.get_driver_status(driver_id)
if not status['is_available']:
    print(f"Conductor ocupado hasta: {status['available_at']}")
    # Buscar alternativa
```

### 2. Ver tráfico actual entre ubicaciones
```python
from apps.routing.google_maps_service import gmaps_service

data = gmaps_service.get_travel_time_with_traffic('CCTI', 'CD_PENON')
print(f"Tiempo: {data['duration_in_traffic_minutes']} min")
print(f"Tráfico: {data['traffic_level']}")
```

### 3. Detectar conflictos
```python
conflicts = driver_availability.check_conflicts(
    driver_id=45,
    start_time=start,
    estimated_end_time=end
)

if conflicts:
    print(f"⚠️ {len(conflicts)} conflictos detectados")
```

---

## 🔧 Comandos Útiles

```bash
# Cargar ubicaciones
python manage.py load_locations

# Actualizar ubicaciones existentes
python manage.py load_locations --force

# Ver ubicaciones en shell
python manage.py shell
>>> from apps.routing.locations_catalog import list_all_locations
>>> list_all_locations()

# Probar disponibilidad
python manage.py shell
>>> from apps.routing.driver_availability_service import driver_availability
>>> driver_availability.get_available_drivers()
```

---

## 📚 Documentación Completa

Para información detallada, ver:
- `SISTEMA_UBICACIONES_CONDUCTORES_OCT_2025.md` - Documentación completa (400+ líneas)
- `SISTEMA_TRAFICO_TIEMPO_REAL_OCT_2025.md` - Sistema de tráfico
- `INICIO_RAPIDO_TRAFICO.md` - Activación de Google Maps API

---

## ✅ Checklist de Implementación

- [x] Cargar ubicaciones con `load_locations`
- [x] Probar consulta de ubicaciones
- [x] Verificar disponibilidad de conductores
- [x] Ver horarios del día
- [x] Listar conductores disponibles
- [x] Probar endpoints REST
- [x] Iniciar ruta con códigos de ubicación

---

**¿Problemas?**
- Verifica que las ubicaciones estén cargadas: `python manage.py load_locations`
- Revisa logs: `tail -f logs/soptraloc.log`
- Consulta documentación completa: `SISTEMA_UBICACIONES_CONDUCTORES_OCT_2025.md`

---

**Última actualización:** Octubre 7, 2025  
**Versión:** 1.0
