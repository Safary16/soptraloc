# 📍 Coordenadas de Ubicaciones Principales - Chile

## Ubicaciones de SoptraLoc

### Puertos
```python
PUERTOS = {
    'VALPARAISO': {
        'name': 'Puerto Valparaíso',
        'latitude': -33.0279,
        'longitude': -71.6293
    },
    'SAN_ANTONIO': {
        'name': 'Puerto San Antonio',
        'latitude': -33.5958,
        'longitude': -71.6116
    }
}
```

### Centros de Distribución
```python
CENTROS_DISTRIBUCION = {
    'CCTI_MAIPU': {
        'name': 'CCTI Maipú - Base',
        'latitude': -33.5089,
        'longitude': -70.7593
    },
    'CD_QUILICURA': {
        'name': 'CD Quilicura',
        'latitude': -33.3563,
        'longitude': -70.7302
    },
    'CD_PUDAHUEL_CAMPOS': {
        'name': 'CD Campos de Chile - Pudahuel',
        'latitude': -33.3991,
        'longitude': -70.7644
    },
    'CD_PUDAHUEL_MADERO': {
        'name': 'CD Puerto Madero - Pudahuel',
        'latitude': -33.3914,
        'longitude': -70.7585
    },
    'CD_PENON': {
        'name': 'CD El Peñón - San Bernardo',
        'latitude': -33.6297,
        'longitude': -70.7045
    },
    'CD_WALMART_QUILICURA': {
        'name': 'CD Walmart Quilicura',
        'latitude': -33.3528,
        'longitude': -70.7312
    },
    'CD_FALABELLA_QUILICURA': {
        'name': 'CD Falabella Quilicura',
        'latitude': -33.3575,
        'longitude': -70.7298
    }
}
```

## Ejemplos de Uso de la API

### Ejemplo 1: CCTI Maipú → CD El Peñón

```bash
curl -X POST http://localhost:8000/api/v1/routing/route-tracking/start-route/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
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
}'
```

**Ruta Real:**
- Distancia: ~15 km
- Tiempo sin tráfico: ~20-25 minutos
- Tiempo con tráfico (hora pico): ~30-40 minutos
- Ruta: Ruta 68 → Américo Vespucio Sur

---

### Ejemplo 2: Puerto San Antonio → CCTI Maipú

```bash
curl -X POST http://localhost:8000/api/v1/routing/route-tracking/start-route/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "assignment_id": 124,
    "driver_id": 46,
    "origin": {
        "name": "Puerto San Antonio",
        "latitude": -33.5958,
        "longitude": -71.6116
    },
    "destination": {
        "name": "CCTI Maipú",
        "latitude": -33.5089,
        "longitude": -70.7593
    }
}'
```

**Ruta Real:**
- Distancia: ~105 km
- Tiempo sin tráfico: ~1 hora 20 minutos
- Tiempo con tráfico: ~1 hora 45 minutos
- Ruta: Ruta 78

---

### Ejemplo 3: CCTI Maipú → CD Quilicura

```bash
curl -X POST http://localhost:8000/api/v1/routing/route-tracking/start-route/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "assignment_id": 125,
    "driver_id": 47,
    "origin": {
        "name": "CCTI Maipú",
        "latitude": -33.5089,
        "longitude": -70.7593
    },
    "destination": {
        "name": "CD Quilicura",
        "latitude": -33.3563,
        "longitude": -70.7302
    }
}'
```

**Ruta Real:**
- Distancia: ~18 km
- Tiempo sin tráfico: ~22 minutos
- Tiempo con tráfico (hora pico): ~35-45 minutos
- Ruta: Ruta 68 → Américo Vespucio Norte

---

### Ejemplo 4: Puerto Valparaíso → CD Walmart Quilicura

```bash
curl -X POST http://localhost:8000/api/v1/routing/route-tracking/start-route/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "assignment_id": 126,
    "driver_id": 48,
    "origin": {
        "name": "Puerto Valparaíso",
        "latitude": -33.0279,
        "longitude": -71.6293
    },
    "destination": {
        "name": "CD Walmart Quilicura",
        "latitude": -33.3528,
        "longitude": -70.7312
    }
}'
```

**Ruta Real:**
- Distancia: ~120 km
- Tiempo sin tráfico: ~1 hora 30 minutos
- Tiempo con tráfico: ~2 horas
- Ruta: Ruta 68

---

## Respuesta Esperada (Ejemplo)

```json
{
    "success": true,
    "assignment_id": 123,
    "driver_name": "Juan Pérez",
    "route": {
        "origin": "CCTI Maipú",
        "destination": "CD El Peñón - San Bernardo",
        "distance_km": 15.2
    },
    "time": {
        "departure": "2025-10-07T08:15:00-03:00",
        "eta": "2025-10-07T08:50:00-03:00",
        "duration_no_traffic": 22,
        "duration_with_traffic": 35,
        "delay": 13
    },
    "traffic": {
        "level": "high",
        "ratio": 1.59
    },
    "alerts": [
        {
            "id": 1,
            "type": "TRAFFIC",
            "message": "⚠️ TRÁFICO ALTO DETECTADO\n\nRuta: CCTI Maipú → CD El Peñón\nRetraso estimado: +13 minutos\nTiempo total: 35 minutos\nETA: 08:50\n\n⚠️ ADVERTENCIAS:\n• Tráfico denso en Américo Vespucio Sur (hora pico matinal)",
            "traffic_level": "high",
            "emoji": "🟠"
        },
        {
            "id": 2,
            "type": "ALTERNATIVE",
            "message": "💡 RUTA ALTERNATIVA RECOMENDADA\n\nRuta actual: 35 minutos\nRuta alternativa: 30 minutos\nAhorro: 5 minutos\n\nDescripción: Vía Gran Avenida",
            "traffic_level": "high",
            "emoji": "🟠"
        }
    ],
    "warnings": [
        "Tráfico denso en Américo Vespucio Sur (hora pico matinal)"
    ],
    "alternative_routes": [
        {
            "duration_minutes": 30,
            "distance_km": 16.8,
            "summary": "Vía Gran Avenida"
        }
    ]
}
```

---

## Script Python de Ejemplo

```python
import requests
from datetime import datetime

class SoptralocTrafficAPI:
    """Cliente para API de tráfico de SoptraLoc"""
    
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
    
    def start_route(self, assignment_id, driver_id, origin, destination):
        """Inicia una ruta y obtiene información de tráfico"""
        endpoint = f"{self.base_url}/api/v1/routing/route-tracking/start-route/"
        
        payload = {
            'assignment_id': assignment_id,
            'driver_id': driver_id,
            'origin': origin,
            'destination': destination
        }
        
        response = requests.post(endpoint, json=payload, headers=self.headers)
        return response.json()
    
    def get_active_alerts(self, driver_id=None):
        """Obtiene alertas activas"""
        endpoint = f"{self.base_url}/api/v1/routing/route-tracking/alerts/active/"
        params = {'driver_id': driver_id} if driver_id else {}
        
        response = requests.get(endpoint, params=params, headers=self.headers)
        return response.json()
    
    def acknowledge_alert(self, alert_id):
        """Marca una alerta como reconocida"""
        endpoint = f"{self.base_url}/api/v1/routing/route-tracking/alerts/{alert_id}/acknowledge/"
        response = requests.post(endpoint, headers=self.headers)
        return response.json()

# Uso
api = SoptralocTrafficAPI('http://localhost:8000', 'YOUR_TOKEN')

# Iniciar ruta
result = api.start_route(
    assignment_id=123,
    driver_id=45,
    origin={
        'name': 'CCTI Maipú',
        'latitude': -33.5089,
        'longitude': -70.7593
    },
    destination={
        'name': 'CD El Peñón',
        'latitude': -33.6297,
        'longitude': -70.7045
    }
)

print(f"ETA: {result['time']['eta']}")
print(f"Tráfico: {result['traffic']['level']}")
print(f"Retraso: +{result['time']['delay']} minutos")

# Ver alertas
for alert in result['alerts']:
    print(f"\n{alert['emoji']} {alert['type']}")
    print(alert['message'])

# Reconocer alerta
if result['alerts']:
    alert_id = result['alerts'][0]['id']
    api.acknowledge_alert(alert_id)
    print(f"\n✅ Alerta {alert_id} reconocida")
```

---

## Script Shell de Ejemplo

```bash
#!/bin/bash
# start_route.sh - Inicia ruta y muestra información

API_URL="http://localhost:8000"
TOKEN="your-token-here"

ASSIGNMENT_ID=123
DRIVER_ID=45

# Coordenadas de ejemplo: CCTI Maipú → CD El Peñón
ORIGIN_NAME="CCTI Maipú"
ORIGIN_LAT=-33.5089
ORIGIN_LNG=-70.7593

DEST_NAME="CD El Peñón"
DEST_LAT=-33.6297
DEST_LNG=-70.7045

# Hacer request
response=$(curl -s -X POST "${API_URL}/api/v1/routing/route-tracking/start-route/" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d @- <<EOF
{
    "assignment_id": ${ASSIGNMENT_ID},
    "driver_id": ${DRIVER_ID},
    "origin": {
        "name": "${ORIGIN_NAME}",
        "latitude": ${ORIGIN_LAT},
        "longitude": ${ORIGIN_LNG}
    },
    "destination": {
        "name": "${DEST_NAME}",
        "latitude": ${DEST_LAT},
        "longitude": ${DEST_LNG}
    }
}
EOF
)

# Mostrar resultado
echo "==================================="
echo "🚚 INFORMACIÓN DE RUTA"
echo "==================================="
echo "$response" | jq -r '"Conductor: \(.driver_name)"'
echo "$response" | jq -r '"Origen: \(.route.origin)"'
echo "$response" | jq -r '"Destino: \(.route.destination)"'
echo "$response" | jq -r '"Distancia: \(.route.distance_km) km"'
echo ""
echo "⏱️  TIEMPOS"
echo "$response" | jq -r '"Sin tráfico: \(.time.duration_no_traffic) minutos"'
echo "$response" | jq -r '"Con tráfico: \(.time.duration_with_traffic) minutos"'
echo "$response" | jq -r '"Retraso: +\(.time.delay) minutos"'
echo "$response" | jq -r '"ETA: \(.time.eta)"'
echo ""
echo "🚦 TRÁFICO"
traffic_level=$($response | jq -r '.traffic.level')
case $traffic_level in
    "low") echo "🟢 Tráfico Bajo" ;;
    "medium") echo "🟡 Tráfico Medio" ;;
    "high") echo "🟠 Tráfico Alto" ;;
    "very_high") echo "🔴 Tráfico Muy Alto" ;;
esac

# Mostrar alertas
echo ""
echo "⚠️  ALERTAS"
echo "$response" | jq -r '.alerts[] | "\(.emoji) \(.type): \(.message)"'
```

---

## Matriz de Distancias y Tiempos (Estimados)

| Origen | Destino | Distancia | Sin Tráfico | Hora Pico |
|--------|---------|-----------|-------------|-----------|
| Puerto Valparaíso | CCTI Maipú | ~115 km | 1h 25min | 1h 50min |
| Puerto San Antonio | CCTI Maipú | ~105 km | 1h 20min | 1h 45min |
| CCTI Maipú | CD Quilicura | ~18 km | 22min | 35-45min |
| CCTI Maipú | CD El Peñón | ~15 km | 20min | 30-40min |
| CCTI Maipú | CD Pudahuel | ~12 km | 18min | 25-35min |
| Puerto Valparaíso | CD Quilicura | ~120 km | 1h 30min | 2h |
| Puerto San Antonio | CD El Peñón | ~110 km | 1h 25min | 1h 55min |

**Nota:** Los tiempos reales varían según tráfico actual. El sistema utiliza Mapbox Directions API para obtener tiempos con tráfico en tiempo real.

---

## Horarios de Mayor Tráfico (Santiago)

### Hora Pico Matinal (Lunes-Viernes)
- **07:00 - 09:30:** Tráfico muy alto
- **Rutas afectadas:** Acceso a Santiago desde puertos, Américo Vespucio, Costanera Norte

### Hora Pico Vespertina (Lunes-Viernes)
- **18:00 - 20:30:** Tráfico muy alto
- **Rutas afectadas:** Salida de Santiago, Ruta 68, Américo Vespucio

### Fines de Semana
- **Sábados:** Tráfico moderado (10:00 - 14:00)
- **Domingos:** Tráfico bajo en general

---

**Fecha:** 7 de octubre de 2025  
**Para usar con:** Sistema de Tráfico en Tiempo Real de SoptraLoc  
**Referencia:** CONFIGURAR_MAPBOX_PASO_A_PASO.md
