# 🚦 Sistema de Estimación de Tiempos en Tiempo Real con Google Maps

## 📋 Resumen

Sistema que obtiene información de tráfico en tiempo real usando Google Maps Distance Matrix API para calcular ETAs (Estimated Time of Arrival) precisas y generar alertas automáticas cuando un conductor inicia una ruta.

**Características principales:**
- ✅ Tráfico en tiempo real considerando condiciones actuales
- ✅ Detección de accidentes, cierres de carretera y obras
- ✅ Sugerencias de rutas alternativas
- ✅ Alertas automáticas para conductores
- ✅ Sin necesidad de GPS en los vehículos
- ✅ Usa API gratuita de GitHub Student Pack ($200 crédito)

---

## 🎯 Problema Resuelto

**Antes:**
- ❌ Tiempos estáticos que no consideran tráfico actual
- ❌ No se detectaban accidentes o cierres
- ❌ Conductores sin información de condiciones de ruta
- ❌ ETAs imprecisos

**Ahora:**
- ✅ Tiempos dinámicos con tráfico en tiempo real
- ✅ Alertas automáticas de problemas en la ruta
- ✅ Conductores informados antes de salir
- ✅ ETAs precisos considerando condiciones actuales
- ✅ Sugerencias de rutas alternativas más rápidas

---

## 🏗️ Arquitectura del Sistema

### 1. **Google Maps Service** (`apps/routing/google_maps_service.py`)

Servicio que se comunica con Google Maps Distance Matrix API.

**Métodos principales:**
```python
# Obtener tiempo de viaje con tráfico
gmaps_service.get_travel_time_with_traffic(
    origin_lat=-33.5089,
    origin_lng=-70.7593,
    dest_lat=-33.6297,
    dest_lng=-70.7045,
    departure_time=None  # None = ahora
)

# Retorna:
{
    'duration_minutes': 25,              # Sin tráfico
    'duration_in_traffic_minutes': 35,   # Con tráfico actual
    'distance_km': 15.2,
    'traffic_level': 'high',             # low/medium/high/very_high
    'delay_minutes': 10,
    'warnings': ['Accidente en Ruta 5'],
    'alternative_routes': [...]
}

# Calcular ETA directamente
eta, traffic_data = gmaps_service.get_eta(
    origin_lat=-33.5089,
    origin_lng=-70.7593,
    dest_lat=-33.6297,
    dest_lng=-70.7045
)
# eta = datetime con hora estimada de llegada
```

**Caché inteligente:**
- Los datos se cachean por 5 minutos
- Evita consultas repetidas innecesarias
- Reduce costos de API

**Fallback automático:**
- Si la API no responde, usa tiempos estáticos
- El sistema sigue funcionando sin interrupciones

### 2. **Traffic Alert Model** (`apps/drivers/models.py`)

Modelo para almacenar alertas de tráfico generadas automáticamente.

```python
class TrafficAlert(models.Model):
    # Relaciones
    assignment = ForeignKey(Assignment)
    driver = ForeignKey(Driver)
    
    # Información de ruta
    origin_name = CharField(max_length=200)
    destination_name = CharField(max_length=200)
    
    # Datos de tráfico
    traffic_level = CharField(choices=[
        ('low', 'Tráfico Bajo'),
        ('medium', 'Tráfico Medio'),
        ('high', 'Tráfico Alto'),
        ('very_high', 'Tráfico Muy Alto'),
    ])
    
    alert_type = CharField(choices=[
        ('TRAFFIC', 'Tráfico Denso'),
        ('ACCIDENT', 'Accidente'),
        ('ROAD_CLOSURE', 'Carretera Cerrada'),
        ('CONSTRUCTION', 'Obras en Ruta'),
        ('DELAY', 'Retraso Estimado'),
        ('ALTERNATIVE', 'Ruta Alternativa'),
    ])
    
    # Tiempos
    estimated_time_minutes = IntegerField()
    actual_time_minutes = IntegerField()
    delay_minutes = IntegerField()
    departure_time = DateTimeField()
    estimated_arrival = DateTimeField()  # ETA
    
    # Mensaje para el conductor
    message = TextField()
    warnings = JSONField(default=list)
    
    # Rutas alternativas
    has_alternatives = BooleanField(default=False)
    alternative_routes = JSONField(default=list)
    
    # Estado
    is_active = BooleanField(default=True)
    acknowledged = BooleanField(default=False)
```

### 3. **Route Start Service** (`apps/routing/route_start_service.py`)

Servicio que procesa el inicio de una ruta.

**Flujo:**
1. Conductor reporta inicio de ruta
2. Consulta Google Maps API con origen y destino
3. Calcula ETA con tráfico actual
4. Genera alertas automáticas según condiciones
5. Actualiza asignación con tiempos calculados
6. Retorna información al conductor

```python
from apps.routing.route_start_service import route_start_service

result = route_start_service.start_route(
    assignment_id=123,
    driver_id=45,
    origin_name="CCTI Maipú",
    destination_name="CD El Peñón",
    origin_lat=-33.5089,
    origin_lng=-70.7593,
    dest_lat=-33.6297,
    dest_lng=-70.7045
)
```

### 4. **API Endpoints** (`apps/routing/api_views.py`)

#### 📍 Iniciar Ruta
```http
POST /api/v1/routing/route-tracking/start-route/
Content-Type: application/json

{
    "assignment_id": 123,
    "driver_id": 45,
    "origin": {
        "name": "CCTI Maipú",
        "latitude": -33.5089,
        "longitude": -70.7593
    },
    "destination": {
        "name": "CD El Peñón - San Bernardo",
        "latitude": -33.6297,
        "longitude": -70.7045
    }
}
```

**Respuesta:**
```json
{
    "success": true,
    "assignment_id": 123,
    "driver_name": "Juan Pérez",
    "route": {
        "origin": "CCTI Maipú",
        "destination": "CD El Peñón",
        "distance_km": 15.2
    },
    "time": {
        "departure": "2025-10-07T15:15:00Z",
        "eta": "2025-10-07T15:50:00Z",
        "duration_no_traffic": 25,
        "duration_with_traffic": 35,
        "delay": 10
    },
    "traffic": {
        "level": "high",
        "ratio": 1.4
    },
    "alerts": [
        {
            "id": 1,
            "type": "TRAFFIC",
            "message": "⚠️ TRÁFICO ALTO DETECTADO\n\nRuta: CCTI Maipú → CD El Peñón\nRetraso estimado: +10 minutos\nTiempo total: 35 minutos\nETA: 15:50\n\n⚠️ ADVERTENCIAS:\n• Tráfico denso en Ruta 5 Sur",
            "traffic_level": "high",
            "emoji": "🟠"
        }
    ],
    "warnings": [
        "Tráfico denso en Ruta 5 Sur"
    ],
    "alternative_routes": [
        {
            "duration_minutes": 32,
            "distance_km": 17.5,
            "summary": "Vía Camino a Melipilla"
        }
    ]
}
```

#### 📍 Ver Alertas Activas
```http
GET /api/v1/routing/route-tracking/alerts/active/?driver_id=45
```

#### 📍 Reconocer Alerta
```http
POST /api/v1/routing/route-tracking/alerts/123/acknowledge/
```

#### 📍 Resumen de Tráfico
```http
GET /api/v1/routing/route-tracking/traffic-summary/
```

---

## 🔧 Configuración

### 1. **Obtener API Key de Google Maps**

Con GitHub Student Pack tienes $200 de crédito en Google Cloud:

1. Ve a https://console.cloud.google.com/
2. Crea un proyecto nuevo
3. Habilita las APIs:
   - Distance Matrix API
   - Directions API
4. Crea una API Key
5. Restringe la key (opcional pero recomendado):
   - Restricción de API: Solo Distance Matrix y Directions
   - Restricción de HTTP: Tu dominio

**Costos:**
- Distance Matrix API: $0.005 por elemento
- Con $200 de crédito = 40,000 consultas gratis
- Para este sistema: ~5 consultas/ruta iniciada
- Capacidad: ~8,000 rutas con el crédito gratuito

### 2. **Configurar Variable de Entorno**

```bash
# .env
GOOGLE_MAPS_API_KEY=AIzaSyC... (tu key aquí)
```

### 3. **Aplicar Migraciones**

```bash
cd soptraloc_system
python manage.py migrate drivers
```

### 4. **Configurar en Render**

En el dashboard de Render, agregar variable de entorno:
- Key: `GOOGLE_MAPS_API_KEY`
- Value: Tu API key de Google Maps

---

## 💻 Uso del Sistema

### Escenario 1: Conductor Inicia Ruta desde CCTI a CD El Peñón

```python
# El sistema registra:
# - Origen: CCTI Maipú (-33.5089, -70.7593)
# - Destino: CD El Peñón (-33.6297, -70.7045)
# - Hora: 15:15

POST /api/v1/routing/route-tracking/start-route/
{
    "assignment_id": 123,
    "driver_id": 45,
    "origin": {
        "name": "CCTI Maipú",
        "latitude": -33.5089,
        "longitude": -70.7593
    },
    "destination": {
        "name": "CD El Peñón",
        "latitude": -33.6297,
        "longitude": -70.7045
    }
}

# Google Maps consulta tráfico actual y responde:
# - Distancia: 15.2 km
# - Tiempo sin tráfico: 25 minutos
# - Tiempo con tráfico: 35 minutos (tráfico alto)
# - ETA: 15:50
# - Advertencia: "Tráfico denso en Ruta 5 Sur"

# Sistema genera automáticamente:
✅ Alerta de tráfico alto
✅ ETA actualizado en la asignación
✅ Notificación al conductor
✅ Sugerencia de ruta alternativa (si ahorra >5 min)
```

### Escenario 2: Accidente Detectado en la Ruta

```python
# Google Maps detecta accidente y lo reporta
# Sistema genera alerta automática:

TrafficAlert {
    driver: "Juan Pérez",
    origin: "CCTI Maipú",
    destination: "CD El Peñón",
    alert_type: "ACCIDENT",
    traffic_level: "very_high",
    message: "⚠️ Accidente reportado en Ruta 5 Sur km 25",
    delay_minutes: 25,
    alternative_routes: [
        {
            "duration_minutes": 32,
            "summary": "Vía Camino a Melipilla",
            "distance_km": 17.5
        }
    ]
}

# El conductor ve la alerta antes de salir
# Puede decidir usar la ruta alternativa
```

### Escenario 3: Dashboard de Operaciones

```python
# El sistema muestra en tiempo real:

GET /api/v1/routing/route-tracking/traffic-summary/
{
    "success": true,
    "summary": {
        "traffic_levels": [
            {"traffic_level": "low", "count": 5},
            {"traffic_level": "medium", "count": 8},
            {"traffic_level": "high", "count": 3},
            {"traffic_level": "very_high", "count": 1}
        ],
        "average_delay_minutes": 8.5,
        "alerts_by_type": [
            {"alert_type": "TRAFFIC", "count": 12},
            {"alert_type": "ACCIDENT", "count": 1},
            {"alert_type": "ALTERNATIVE", "count": 4}
        ]
    }
}
```

---

## 📊 Admin de Django

En `/admin/drivers/trafficalert/` puedes ver todas las alertas:

**Lista de Alertas:**
```
🟠 TRAFFIC    Juan Pérez    CCTI → CD Peñón    Alto    +10 min    15:50    ✅
🔴 ACCIDENT   María López   Puerto → CCTI      Muy Alto +25 min  16:30    ❌
🟡 ALTERNATIVE Pedro Ruiz   CD → Puerto        Medio   +0 min     17:15    ✅
```

**Acciones disponibles:**
- Marcar como reconocida por conductor
- Desactivar alertas
- Ver detalles completos de Google Maps API

---

## 🎯 Ventajas del Sistema

### vs GPS Tradicional:
- ✅ **Costo:** No requiere hardware GPS en vehículos
- ✅ **Simplicidad:** Solo coordenadas de origen/destino
- ✅ **Información:** Más datos que solo ubicación (accidentes, cierres, etc.)
- ✅ **Proactividad:** Alertas ANTES de iniciar ruta, no durante

### vs Tiempos Estáticos:
- ✅ **Precisión:** Considera tráfico real actual
- ✅ **Adaptabilidad:** Se ajusta a condiciones cambiantes
- ✅ **Alertas:** Informa problemas específicos
- ✅ **Optimización:** Sugiere rutas alternativas

### GitHub Student Pack:
- ✅ **Gratis:** $200 de crédito = ~8,000 rutas
- ✅ **Confiable:** API de Google Maps (99.9% uptime)
- ✅ **Actualizado:** Datos de tráfico en tiempo real
- ✅ **Global:** Funciona en cualquier país

---

## 📈 Métricas y Estadísticas

El sistema almacena:
- ✅ Tiempos estimados vs reales
- ✅ Nivel de tráfico por horario
- ✅ Rutas más problemáticas
- ✅ Efectividad de rutas alternativas
- ✅ Tiempos de respuesta de Google Maps API

**Reportes disponibles:**
- Rutas con mayor tráfico
- Horarios pico por ruta
- Promedio de retraso por conductor
- Uso de rutas alternativas

---

## 🔐 Seguridad y Mejores Prácticas

### API Key Protection:
```python
# ✅ Bueno - Variable de entorno
GOOGLE_MAPS_API_KEY = config('GOOGLE_MAPS_API_KEY', default=None)

# ❌ Malo - Hardcoded
GOOGLE_MAPS_API_KEY = "AIzaSyC..."
```

### Restricciones Recomendadas:
1. **API Restrictions:**
   - Solo Distance Matrix API
   - Solo Directions API

2. **Application Restrictions:**
   - HTTP referrers: `https://tu-dominio.com/*`
   - IP addresses: IP de tu servidor

3. **Quota Management:**
   - Límite diario: 1,000 consultas/día (ajustable)
   - Alertas de uso

---

## 🚀 Roadmap Futuro

### Fase 1: ✅ Completado
- [x] Integración con Google Maps API
- [x] Modelo de alertas de tráfico
- [x] API para inicio de ruta
- [x] Admin de Django

### Fase 2: En Progreso
- [ ] Dashboard visual de tráfico en tiempo real
- [ ] Notificaciones push a conductores
- [ ] Integración con WhatsApp Business API

### Fase 3: Planeado
- [ ] Machine Learning para predecir tráfico
- [ ] Optimización de rutas multi-parada
- [ ] Integración con Waze API (complementario)
- [ ] App móvil para conductores

---

## 📚 Archivos Creados

```
soptraloc_system/
├── apps/
│   ├── routing/
│   │   ├── google_maps_service.py    ← Servicio Google Maps API
│   │   ├── route_start_service.py    ← Lógica de inicio de ruta
│   │   ├── api_views.py              ← API endpoints
│   │   └── urls.py                    ← URLs actualizadas
│   │
│   └── drivers/
│       ├── models.py                  ← Modelo TrafficAlert agregado
│       ├── admin.py                   ← Admin de TrafficAlert
│       └── migrations/
│           └── 0007_trafficalert.py   ← Nueva migración
│
├── config/
│   └── settings.py                    ← GOOGLE_MAPS_API_KEY agregado
│
└── .env.example                       ← Variable de ejemplo agregada
```

---

## 🎓 Recursos Adicionales

### GitHub Student Pack:
- https://education.github.com/pack

### Google Maps APIs:
- Distance Matrix: https://developers.google.com/maps/documentation/distance-matrix
- Directions: https://developers.google.com/maps/documentation/directions

### Documentación:
- Esta documentación: `/SISTEMA_TRAFICO_TIEMPO_REAL_OCT_2025.md`

---

**Fecha:** 7 de octubre de 2025  
**Versión:** SoptraLoc TMS v3.1  
**Estado:** ✅ Implementado y listo para usar  
**Costo:** $0 con GitHub Student Pack ($200 crédito incluido)
