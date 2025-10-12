# 📋 Estados del Contenedor - Ciclo de Vida Completo

## 🔄 Flujo de Estados

```
┌─────────────┐
│ POR ARRIBAR │ ─────────────────┐
└─────────────┘                  │
       │                         │
       │ Nave llega              │
       ▼                         │
┌─────────────┐                  │
│  ARRIBADO   │                  │
└─────────────┘                  │
       │                         │
       │ Aduana/Naviera libera   │
       ▼                         │
┌─────────────┐                  │
│  LIBERADO   │                  │
└─────────────┘                  │
       │                         │
       │ Marcado para entrega    │
       ▼                         │
┌─────────────┐                  │
│ SECUENCIADO │                  │ CONTENEDOR
└─────────────┘                  │   LLENO
       │                         │
       │ Asignado a fecha y CD   │
       ▼                         │
┌─────────────┐                  │
│ PROGRAMADO  │                  │
└─────────────┘                  │
       │                         │
       │ Asignado a conductor    │
       ▼                         │
┌─────────────┐                  │
│  ASIGNADO   │                  │
└─────────────┘                  │
       │                         │
       │ Conductor sale          │
       ▼                         │
┌─────────────┐                  │
│  EN RUTA    │                  │
└─────────────┘                  │
       │                         │
       │ Llega a CD              │
       ▼                         │
┌─────────────┐                  │
│ ENTREGADO   │                  │
└─────────────┘                  │
       │                         │
       │ Cliente descarga        │
       ▼                         │
┌─────────────┐                  │
│ DESCARGADO  │ ─────────────────┘
└─────────────┘
       │
       │ Contenedor vacío
       ▼
┌─────────────┐
│    VACÍO    │ ─────────────────┐
└─────────────┘                  │
       │                         │
       │ Iniciando retorno       │ CONTENEDOR
       ▼                         │   VACÍO
┌─────────────┐                  │
│VACÍO EN RUTA│                  │
└─────────────┘                  │
       │                         │
       │ Devuelto a naviera      │
       ▼                         │
┌─────────────┐                  │
│  DEVUELTO   │ ─────────────────┘
└─────────────┘
```

---

## 📊 Estados y Timestamps

| Estado | Timestamp | Descripción | Ubicación |
|--------|-----------|-------------|-----------|
| **por_arribar** | - | Nave en tránsito | En mar |
| **arribado** | `fecha_arribo` | Nave llegó a puerto | Puerto (TPS/STI/PCE/ZEAL) |
| **liberado** | `fecha_liberacion` | Liberado por aduana/naviera | Puerto |
| **secuenciado** | - | Marcado para próxima entrega | Puerto |
| **programado** | `fecha_programacion` | Asignado a fecha y CD | Puerto |
| **asignado** | `fecha_asignacion` | Asignado a conductor | Puerto |
| **en_ruta** | `fecha_inicio_ruta` | Conductor en camino | En tránsito |
| **entregado** | `fecha_entrega` | Llegó a CD cliente | CD Cliente |
| **descargado** | `fecha_descarga` | Cliente terminó descarga | CD Cliente |
| **vacio** | `fecha_vacio` | Vacío, esperando retiro | CD Cliente |
| **vacio_en_ruta** | `fecha_vacio_ruta` | Retornando a depósito | En tránsito |
| **devuelto** | `fecha_devolucion` | Devuelto a naviera | Depósito |

---

## 🏢 Centros de Distribución

### CDs Principales

#### 1️⃣ CD El Peñón
- **Código**: `PENON`
- **Dirección**: Avenida Presidente Jorge Alessandri Rodriguez 18899, San Bernardo
- **Comuna**: San Bernardo
- **Tipo**: Drop & Hook ✅
- **Tiempo descarga**: 30 minutos
- **Característica**: Conductor puede soltar contenedor y quedar libre inmediatamente

#### 2️⃣ CD Puerto Madero
- **Código**: `MADERO`
- **Dirección**: Puerto Madero 9710, Pudahuel
- **Comuna**: Pudahuel
- **Tipo**: Espera completa ❌
- **Tiempo descarga**: 90 minutos
- **Característica**: Conductor debe esperar descarga completa

#### 3️⃣ CD Campos de Chile
- **Código**: `CAMPOS`
- **Dirección**: Av. El Parque 1000, Pudahuel
- **Comuna**: Pudahuel
- **Tipo**: Espera completa ❌
- **Tiempo descarga**: 90 minutos
- **Característica**: Conductor debe esperar descarga completa

#### 4️⃣ CD Quilicura
- **Código**: `QUILICURA`
- **Dirección**: Eduardo Frei Montalva 8301, Quilicura
- **Comuna**: Quilicura
- **Tipo**: Espera completa ❌
- **Tiempo descarga**: 90 minutos
- **Característica**: Conductor debe esperar descarga completa

### Base de Operaciones

#### 🏭 CCTI (Centro de Consolidación y Transferencia Internacional)
- **Código**: `CCTI`
- **Dirección**: Camino Los Agricultores, Parcela 41, Maipú
- **Comuna**: Maipú
- **Tipo**: Base de operaciones
- **Capacidad vacíos**: 200 contenedores
- **Tiempo operación**: 20 minutos
- **Función**: Almacenamiento temporal, gestión de vacíos, punto de partida

---

## ⏱️ Tiempos de Tránsito Estimados

### Desde CCTI a CDs

| Origen | Destino | Distancia | Tiempo sin tráfico | Tiempo con tráfico |
|--------|---------|-----------|--------------------|--------------------|
| CCTI Maipú | CD El Peñón (San Bernardo) | 25 km | 30 min | 45-60 min |
| CCTI Maipú | CD Puerto Madero (Pudahuel) | 18 km | 25 min | 35-50 min |
| CCTI Maipú | CD Campos de Chile (Pudahuel) | 20 km | 27 min | 40-55 min |
| CCTI Maipú | CD Quilicura | 22 km | 28 min | 40-60 min |

### Desde Puerto a CDs (vía CCTI)

| Origen | Destino | Distancia | Tiempo sin tráfico | Tiempo con tráfico |
|--------|---------|-----------|--------------------|--------------------|
| Puerto Valparaíso | CCTI Maipú | 120 km | 90 min | 120-150 min |
| Puerto San Antonio | CCTI Maipú | 110 km | 85 min | 110-140 min |

---

## 🚛 Tipos de Operación

### Drop & Hook (Solo El Peñón)
1. Conductor llega con contenedor lleno
2. Suelta contenedor en yard del cliente
3. **Queda libre inmediatamente** → Puede tomar siguiente carga
4. Cliente descarga a su ritmo
5. Conductor retorna más tarde por vacío

**Ventaja**: Mayor rotación de conductores, más eficiencia

### Espera Completa (Madero, Campos, Quilicura)
1. Conductor llega con contenedor lleno
2. **Espera mientras cliente descarga** (60-90 min)
3. Retira contenedor vacío
4. Retorna a CCTI o depósito naviera

**Desventaja**: Conductor bloqueado durante descarga

---

## 📍 Coordenadas GPS

```json
{
  "CCTI": {
    "lat": -33.5104,
    "lng": -70.8284,
    "address": "Camino Los Agricultores, Parcela 41, Maipú"
  },
  "PENON": {
    "lat": -33.6223,
    "lng": -70.7089,
    "address": "Av. Pdte Jorge Alessandri Rodriguez 18899, San Bernardo"
  },
  "MADERO": {
    "lat": -33.3947,
    "lng": -70.7642,
    "address": "Puerto Madero 9710, Pudahuel"
  },
  "CAMPOS": {
    "lat": -33.3986,
    "lng": -70.7489,
    "address": "Av. El Parque 1000, Pudahuel"
  },
  "QUILICURA": {
    "lat": -33.3511,
    "lng": -70.7282,
    "address": "Eduardo Frei Montalva 8301, Quilicura"
  }
}
```

---

## 🔄 Transiciones de Estado (API)

### Cambiar estado manualmente
```bash
POST /api/containers/{id}/cambiar_estado/
{
  "nuevo_estado": "arribado"
}
```

### Transiciones automáticas disponibles:
- `marcar_arribado` - Nave llega a puerto
- `marcar_liberado` - Liberado por aduana
- `marcar_programado` - Programar entrega
- `marcar_asignado` - Asignar conductor
- `iniciar_ruta` - Conductor sale
- `marcar_entregado` - Llega a CD
- `marcar_descargado` - Cliente termina descarga
- `marcar_vacio` - Contenedor vacío
- `iniciar_retorno` - Iniciar retorno
- `marcar_devuelto` - Devuelto a naviera

---

## 🎯 Métricas Clave

### Tiempos por Estado
- **Puerto a Cliente**: ~3-4 horas totales
  - Retiro de puerto: 30 min
  - Tránsito a CCTI: 120 min
  - Espera en CCTI: 30 min
  - Tránsito a CD: 45 min
  - Descarga: 30-90 min

### Tiempo total ciclo completo:
- **Con Drop & Hook (El Peñón)**: ~5 horas
- **Con Espera (otros CDs)**: ~6-7 horas

### Demurrage
- Plazo típico: 5-7 días desde arribo
- Después del plazo: costos por día de almacenaje

---

## 📱 Dashboard Stats

Métricas a mostrar en dashboard:
- ✅ Total por estado (gráfico de barras)
- ✅ Urgencias críticas (< 24h para demurrage)
- ✅ En tránsito (en_ruta + vacio_en_ruta)
- ✅ Disponibles para programar (liberado + secuenciado)
- ✅ Conductor ocupado vs libre (asignado + en_ruta)
- ✅ Contenedores en CDs (entregado + descargado + vacio)
- ✅ Vacíos en CCTI (contador)
