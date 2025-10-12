# 🎉 Nuevas Funcionalidades - SoptraLoc TMS

## 📋 Resumen de Implementación

Se han implementado **5 nuevas funcionalidades principales** que mejoran significativamente la gestión operativa, eficiencia y control del sistema TMS.

---

## 1. 🔒 Validación de Pre-Asignación con Tiempos Mapbox

### Descripción
Sistema de validación que previene conflictos de doble asignación utilizando cálculos de tiempo reales de Mapbox. Considera el tiempo total de cada entrega incluyendo viaje, descarga y retorno.

### Componentes

#### Servicio: `PreAssignmentValidationService`
**Ubicación:** `apps/core/services/validation.py`

**Métodos principales:**
- `validar_disponibilidad_temporal(driver, programacion_nueva, buffer_minutos=30)` - Valida si un conductor está libre en la ventana de tiempo requerida
- `obtener_proxima_ventana_disponible(driver, duracion_minutos, fecha_minima=None)` - Encuentra el próximo horario disponible

**Lógica de cálculo de tiempo:**
```python
# Drop & Hook (El Peñón)
if cd.permite_soltar_contenedor:
    tiempo_total = tiempo_viaje + 15  # Solo 15 min para soltar

# Truck Discharge (Puerto Madero, Campos, etc.)
else:
    tiempo_total = tiempo_viaje + tiempo_descarga_cd
    if cd.requiere_espera_carga:
        tiempo_total += 30  # Tiempo adicional de espera
```

### Endpoints

#### `POST /api/programaciones/{id}/validar_asignacion/`
Valida si un conductor puede ser asignado a una programación.

**Request:**
```json
{
    "driver_id": 1
}
```

**Response:**
```json
{
    "success": true,
    "disponible": true,
    "conflictos": [],
    "tiempo_requerido": 75,
    "ventana_ocupada": null,
    "nueva_ventana": {
        "inicio": "2025-10-15T10:00:00Z",
        "fin": "2025-10-15T11:15:00Z"
    },
    "conductor": "Juan Pérez"
}
```

**Respuesta con conflicto:**
```json
{
    "success": true,
    "disponible": false,
    "conflictos": [
        "Conflicto con ABCD1234567: 09:00-10:30"
    ],
    "tiempo_requerido": 75,
    "ventana_ocupada": [
        {
            "programacion_id": 45,
            "container_id": "ABCD1234567",
            "inicio": "2025-10-15T09:00:00Z",
            "fin": "2025-10-15T10:30:00Z",
            "duracion_minutos": 90
        }
    ],
    "conductor": "Juan Pérez"
}
```

### Uso
```javascript
// Validar antes de asignar
$.ajax({
    url: `/api/programaciones/${programacionId}/validar_asignacion/`,
    method: 'POST',
    contentType: 'application/json',
    data: JSON.stringify({ driver_id: driverId }),
    success: function(data) {
        if (data.disponible) {
            // Proceder con asignación
        } else {
            alert('Conflictos: ' + data.conflictos.join(', '));
        }
    }
});
```

---

## 2. 📬 Sistema de Notificaciones de Arribo con ETA

### Descripción
Sistema completo de notificaciones que alerta sobre el inicio de rutas, actualizaciones de ETA, proximidad de arribo y llegadas confirmadas.

### Modelos

#### `Notification`
**Ubicación:** `apps/notifications/models.py`

**Campos principales:**
- `tipo`: ruta_iniciada, eta_actualizado, arribo_proximo, llegada, demurrage_alerta, asignacion
- `prioridad`: baja, media, alta, critica
- `estado`: pendiente, enviada, leida, archivada
- `eta_minutos`: Tiempo estimado de arribo
- `eta_timestamp`: Timestamp de arribo estimado
- `distancia_km`: Distancia restante
- `lat_actual`, `lng_actual`: Posición actual del conductor

#### `NotificationPreference`
Configuración de preferencias de notificación por usuario (email, SMS, push, sistema).

### Servicio: `NotificationService`
**Ubicación:** `apps/notifications/services.py`

**Métodos principales:**
- `crear_notificacion_inicio_ruta(programacion, driver, eta_minutos, distancia_km)` - Crea notificación cuando inicia ruta
- `actualizar_eta(programacion, driver, nueva_posicion_lat, nueva_posicion_lng)` - Actualiza ETA con nueva posición
- `crear_alerta_arribo_proximo(programacion, minutos_anticipacion=15)` - Alerta cuando está cerca (< 15 min)
- `crear_notificacion_llegada(programacion)` - Confirma llegada al destino

### Endpoints

#### `GET /api/notifications/activas/`
Lista notificaciones activas (pendientes y enviadas).

**Response:**
```json
{
    "success": true,
    "total": 5,
    "notificaciones": [
        {
            "id": 1,
            "container_id": "ABCD1234567",
            "driver_nombre": "Juan Pérez",
            "tipo": "ruta_iniciada",
            "tipo_display": "Ruta Iniciada",
            "prioridad": "alta",
            "titulo": "Ruta iniciada - ABCD1234567",
            "mensaje": "Conductor Juan Pérez ha iniciado ruta hacia El Peñón. ETA: 45 minutos",
            "eta_minutos": 45,
            "eta_timestamp": "2025-10-15T11:30:00Z",
            "distancia_km": "35.5",
            "created_at": "2025-10-15T10:45:00Z"
        }
    ]
}
```

#### `GET /api/notifications/recientes/`
Notificaciones de los últimos 30 minutos.

#### `GET /api/notifications/por_prioridad/`
Agrupa notificaciones activas por nivel de prioridad.

**Response:**
```json
{
    "success": true,
    "total": 8,
    "por_prioridad": {
        "critica": [...],
        "alta": [...],
        "media": [...],
        "baja": [...]
    },
    "resumen": {
        "critica": 2,
        "alta": 3,
        "media": 2,
        "baja": 1
    }
}
```

#### `POST /api/notifications/{id}/marcar_leida/`
Marca una notificación como leída.

#### `POST /api/notifications/marcar_todas_leidas/`
Marca todas las notificaciones activas como leídas.

#### `POST /api/notifications/limpiar_antiguas/`
Archiva notificaciones antiguas.

**Request:**
```json
{
    "dias": 7
}
```

### Integración con Rutas

#### `POST /api/programaciones/{id}/iniciar_ruta/`
Inicia una ruta y crea notificación automáticamente.

**Request:**
```json
{
    "lat": -33.4372,
    "lng": -70.6506
}
```

**Response:**
```json
{
    "success": true,
    "mensaje": "Ruta iniciada por conductor Juan Pérez",
    "programacion": {...},
    "notificacion": {
        "id": 1,
        "titulo": "Ruta iniciada - ABCD1234567",
        "mensaje": "Conductor Juan Pérez ha iniciado ruta hacia El Peñón. ETA: 45 minutos",
        "eta_minutos": 45,
        "eta_timestamp": "2025-10-15T11:30:00Z",
        "distancia_km": "35.5"
    }
}
```

#### `POST /api/programaciones/{id}/actualizar_posicion/`
Actualiza posición GPS y recalcula ETA.

**Request:**
```json
{
    "lat": -33.4500,
    "lng": -70.6400
}
```

**Response:**
```json
{
    "success": true,
    "mensaje": "Posición actualizada y ETA recalculado",
    "eta_minutos": 30,
    "distancia_km": "22.3",
    "eta_timestamp": "2025-10-15T11:15:00Z",
    "notificacion": {
        "id": 2,
        "titulo": "ETA Actualizado - ABCD1234567",
        "mensaje": "Nuevo ETA: 30 minutos. Distancia restante: 22.3 km."
    }
}
```

#### `GET /api/programaciones/{id}/eta/`
Obtiene el ETA actual sin actualizar posición.

---

## 3. 🚛 Diferenciación Drop & Hook vs Truck Discharge

### Descripción
Implementación completa de workflows diferenciados para entregas Drop & Hook (dejar contenedor y retirarse) vs Truck Discharge (esperar descarga completa).

### Configuración en CD

El modelo `CD` ya tiene los campos necesarios:

```python
class CD(models.Model):
    # ...
    
    # Drop & Hook
    permite_soltar_contenedor = models.BooleanField(
        'Permite Drop & Hook',
        default=False,
        help_text='Si True: conductor puede soltar contenedor y quedar libre inmediatamente'
    )
    
    # Truck Discharge
    requiere_espera_carga = models.BooleanField(
        'Requiere Espera para Carga',
        default=False,
        help_text='Si True: conductor espera descarga sobre camión'
    )
    
    tiempo_promedio_descarga_min = models.IntegerField(
        'Tiempo Promedio Descarga (minutos)',
        default=60
    )
```

### Ejemplos de Configuración

#### Drop & Hook (El Peñón)
```python
cd_penon = CD.objects.create(
    nombre='El Peñón',
    permite_soltar_contenedor=True,   # ✅ Drop & Hook
    requiere_espera_carga=False,
    tiempo_promedio_descarga_min=15   # Solo 15 min para soltar
)
```

#### Truck Discharge (Puerto Madero)
```python
cd_madero = CD.objects.create(
    nombre='Puerto Madero',
    permite_soltar_contenedor=False,  # ❌ No Drop & Hook
    requiere_espera_carga=True,       # ✅ Espera completa
    tiempo_promedio_descarga_min=90   # 90 min descarga
)
```

### Impacto en Validación

```python
# En PreAssignmentValidationService._calcular_tiempo_total_asignacion()

if cd.permite_soltar_contenedor:
    # DROP & HOOK
    # Conductor queda libre rápidamente
    tiempo_total = tiempo_viaje + 15
else:
    # TRUCK DISCHARGE
    # Conductor bloqueado durante descarga
    tiempo_total = tiempo_viaje + tiempo_descarga
    if cd.requiere_espera_carga:
        tiempo_total += 30  # Tiempo adicional
```

### Flujo de Trabajo

#### Escenario 1: Drop & Hook (El Peñón)
```
1. Conductor llega a El Peñón
2. Suelta contenedor (15 minutos)
3. ✅ Conductor queda LIBRE inmediatamente
4. Puede recibir nueva asignación
5. Cliente descarga a su ritmo (no afecta al conductor)
```

#### Escenario 2: Truck Discharge (Puerto Madero)
```
1. Conductor llega a Puerto Madero
2. Espera descarga completa (90 minutos)
3. ❌ Conductor BLOQUEADO durante descarga
4. Solo queda libre después de descarga
5. Recién entonces puede recibir nueva asignación
```

---

## 4. 📱 Dashboard Móvil para Conductores

### Descripción
Interfaz móvil optimizada para conductores con funcionalidad completa de gestión de entregas, GPS y confirmaciones.

### Acceso
**URL:** `/driver/dashboard/?driver_id={id}`

Ejemplo: `/driver/dashboard/?driver_id=1`

El sistema guarda el driver_id en localStorage para sesiones futuras.

### Funcionalidades

#### 1. Vista General
- Información del conductor (nombre, entregas del día, disponibilidad)
- Estado de ubicación GPS en tiempo real
- Lista de entregas asignadas con estados

#### 2. Gestión de Entregas

**Estados soportados:**
- **Asignado**: Botón "Iniciar Ruta"
- **En Ruta**: Botones "Actualizar GPS", "Ver ETA", "Marcar Entregado"
- **Entregado**: Botón "Confirmar Descarga"
- **Descargado**: Completado

#### 3. Funciones GPS

**Actualización Automática:**
```javascript
// Al iniciar ruta
navigator.geolocation.getCurrentPosition(function(position) {
    $.ajax({
        url: `/api/programaciones/${programacionId}/iniciar_ruta/`,
        method: 'POST',
        data: JSON.stringify({
            lat: position.coords.latitude,
            lng: position.coords.longitude
        })
    });
});
```

**Botón Flotante de Ubicación:**
- Ubicado en esquina inferior derecha
- Actualiza posición en el servidor
- Muestra toast de confirmación

#### 4. Auto-actualización
El dashboard se actualiza automáticamente cada 30 segundos para mostrar cambios en entregas y estado.

### Capturas de Pantalla

#### Vista Principal
```
┌─────────────────────────────┐
│ 👤 Juan Pérez               │
│ Entregas: 2/3 • 📍 Ubicación│
├─────────────────────────────┤
│                             │
│ 📦 Mis Entregas             │
│                             │
│ ┌─────────────────────────┐ │
│ │ ABCD1234567             │ │
│ │ En Ruta                 │ │
│ │ Cliente: Walmart        │ │
│ │ ⏰ ETA: 30 min          │ │
│ │ [Actualizar GPS]        │ │
│ │ [Ver ETA] [Entregado]   │ │
│ └─────────────────────────┘ │
│                             │
│ ┌─────────────────────────┐ │
│ │ EFGH5678901             │ │
│ │ Asignado                │ │
│ │ Cliente: Jumbo          │ │
│ │ [Iniciar Ruta]          │ │
│ └─────────────────────────┘ │
│                             │
└─────────────────────────────┘
          [🌍] ← Botón flotante
```

### Uso en Producción

1. **Distribuir URL** a conductores con su ID
2. **Primera carga**: Sistema solicita ID si no está en URL
3. **Navegación**: Compatible con cualquier dispositivo móvil
4. **Offline**: Guarda ID localmente para acceso rápido
5. **Permisos GPS**: Solicita permiso automáticamente

---

## 5. 📊 Dashboard Ejecutivo y Reportes

### Descripción
Dashboard completo con métricas operacionales, análisis de conductores, eficiencia y tendencias históricas.

### Acceso
**URL:** `/executive/`

### Endpoints de Analytics

#### `GET /api/dashboard/stats/`
Estadísticas generales del sistema.

**Response:**
```json
{
    "success": true,
    "stats": {
        "contenedores_total": 44,
        "conductores": 6,
        "conductores_disponibles": 4,
        "programados_hoy": 5,
        "con_demurrage": 8,
        "liberados": 12,
        "en_ruta": 3,
        "sin_asignar": 2,
        "por_arribar": 3,
        "programados": 7,
        "asignados": 5,
        "entregados": 2,
        "descargados": 18,
        "vacios": 4,
        "total_activos": 43,
        "notificaciones_activas": 6
    }
}
```

#### `GET /api/dashboard/alertas/`
Alertas activas priorizadas.

**Response:**
```json
{
    "success": true,
    "total": 5,
    "alertas": [
        {
            "tipo": "demurrage",
            "prioridad": "critica",
            "container_id": "ABCD1234567",
            "mensaje": "Demurrage vencido",
            "dias_restantes": -2
        },
        {
            "tipo": "sin_conductor",
            "prioridad": "alta",
            "container_id": "EFGH5678901",
            "mensaje": "Sin conductor asignado - Faltan 18 horas",
            "horas_restantes": 18
        }
    ]
}
```

#### `GET /api/analytics/conductores/`
Análisis de rendimiento de conductores.

**Response:**
```json
{
    "success": true,
    "total": 6,
    "conductores": [
        {
            "driver_id": 1,
            "nombre": "Juan Pérez",
            "esta_disponible": true,
            "entregas_dia": 2,
            "max_entregas_dia": 3,
            "total_entregas": 145,
            "entregas_a_tiempo": 138,
            "cumplimiento_porcentaje": 95.17,
            "ocupacion_porcentaje": 66.67,
            "programaciones_completadas": 140
        }
    ]
}
```

#### `GET /api/analytics/eficiencia/`
Métricas de eficiencia operacional.

**Response:**
```json
{
    "success": true,
    "tiempo_promedio_operacion_min": 65,
    "tiempo_promedio_viaje_min": 42,
    "tasa_cumplimiento_porcentaje": 94.5,
    "entregas_ultimos_7_dias": 28,
    "distribucion_estados": [
        {"estado": "liberado", "count": 12},
        {"estado": "en_ruta", "count": 3},
        {"estado": "descargado", "count": 18}
    ]
}
```

#### `GET /api/analytics/tendencias/?dias=30`
Tendencias históricas.

**Parameters:**
- `dias`: Número de días a analizar (default: 30)

**Response:**
```json
{
    "success": true,
    "periodo_dias": 30,
    "entregas_por_dia": [
        {"fecha": "2025-09-15", "entregas": 5},
        {"fecha": "2025-09-16", "entregas": 7},
        ...
    ],
    "entregas_por_dia_semana": [
        {"dia": "Lunes", "entregas": 22},
        {"dia": "Martes", "entregas": 25},
        {"dia": "Miércoles", "entregas": 23},
        {"dia": "Jueves", "entregas": 21},
        {"dia": "Viernes", "entregas": 20},
        {"dia": "Sábado", "entregas": 8},
        {"dia": "Domingo", "entregas": 3}
    ]
}
```

### Secciones del Dashboard

#### 1. Métricas Principales
Tarjetas con KPIs principales:
- Total de contenedores
- Contenedores en ruta
- Programados para hoy
- Sin asignar (próximas 48h)

#### 2. Tab Operaciones
- **Gráfico**: Contenedores por estado (pie chart)
- **Gráfico**: Entregas por día (últimos 7 días)
- **Tabla**: Programaciones próximas con nivel de urgencia

#### 3. Tab Conductores
- **Tabla completa** con:
  - Estado (disponible/no disponible)
  - Entregas del día vs máximo
  - Total de entregas históricas
  - Porcentaje de cumplimiento
  - Barra de ocupación visual

#### 4. Tab Eficiencia
- Tiempo promedio de entrega
- Tasa de cumplimiento general
- Métricas operacionales

#### 5. Tab Alertas
- Lista de alertas activas por prioridad
- Códigos de color según criticidad
- Información de contenedor y tiempo restante

### Exportación de Reportes (Preparado)
```javascript
function exportarReporte(tipo) {
    // Preparado para implementar exportación a Excel/PDF
    // tipos: 'programaciones', 'conductores', 'eficiencia'
}
```

---

## 🔧 Configuración y Despliegue

### 1. Migraciones
```bash
python manage.py makemigrations notifications
python manage.py migrate
```

### 2. Configuración de Settings

Ya está configurado en `config/settings.py`:
```python
INSTALLED_APPS = [
    ...
    'apps.notifications',
]

# Mapbox API Key (necesaria)
MAPBOX_API_KEY = config('MAPBOX_API_KEY', default=None)
```

### 3. Variables de Entorno

Crear archivo `.env`:
```bash
# Mapbox (REQUERIDO para funcionalidades de ETA)
MAPBOX_API_KEY=pk.tu_clave_aqui

# Database
DATABASE_URL=postgres://...

# Debug
DEBUG=True
SECRET_KEY=tu-secret-key-aqui
```

### 4. URLs Configuradas

Todas las rutas ya están agregadas en `config/urls.py`:
- `/driver/dashboard/` - Dashboard móvil
- `/executive/` - Dashboard ejecutivo
- `/api/notifications/*` - Endpoints de notificaciones
- `/api/programaciones/{id}/validar_asignacion/` - Validación
- `/api/programaciones/{id}/iniciar_ruta/` - Iniciar ruta
- `/api/programaciones/{id}/actualizar_posicion/` - GPS
- `/api/programaciones/{id}/eta/` - ETA
- `/api/dashboard/*` - Estadísticas
- `/api/analytics/*` - Analíticas

---

## 📱 Guía de Uso Rápido

### Para Operadores

1. **Validar antes de asignar:**
   ```
   Operaciones → Seleccionar programación → 
   Validar Asignación → Elegir conductor →
   Ver conflictos (si hay) → Asignar
   ```

2. **Monitorear notificaciones:**
   ```
   Dashboard → Ver notificaciones activas →
   Filtrar por prioridad → Marcar como leídas
   ```

3. **Ver analytics:**
   ```
   Dashboards → Ejecutivo → 
   Explorar tabs (Operaciones, Conductores, Eficiencia, Alertas)
   ```

### Para Conductores

1. **Acceder al dashboard:**
   ```
   Abrir navegador móvil →
   Ir a: https://tudominio.com/driver/dashboard/?driver_id=TU_ID
   ```

2. **Iniciar entrega:**
   ```
   Ver lista de entregas → 
   Seleccionar "Iniciar Ruta" →
   Permitir ubicación GPS →
   Sistema calcula ETA automáticamente
   ```

3. **Actualizar posición:**
   ```
   Durante el viaje →
   Presionar botón flotante (🌍) →
   Sistema recalcula ETA automáticamente
   ```

4. **Confirmar entrega:**
   ```
   Al llegar → "Marcar Entregado" →
   Después de descarga → "Confirmar Descarga" →
   ¡Entrega completada!
   ```

### Para Ejecutivos

1. **Ver métricas:**
   ```
   Dashboards → Ejecutivo →
   Métricas principales en tarjetas superiores
   ```

2. **Analizar rendimiento:**
   ```
   Tab Conductores →
   Ver cumplimiento y ocupación →
   Identificar mejores performers
   ```

3. **Revisar alertas:**
   ```
   Tab Alertas →
   Priorizar críticas y altas →
   Tomar acción según necesidad
   ```

---

## 🧪 Testing

### Probar Validación
```bash
curl -X POST http://localhost:8000/api/programaciones/1/validar_asignacion/ \
  -H "Content-Type: application/json" \
  -d '{"driver_id": 1}'
```

### Probar Inicio de Ruta
```bash
curl -X POST http://localhost:8000/api/programaciones/1/iniciar_ruta/ \
  -H "Content-Type: application/json" \
  -d '{"lat": -33.4372, "lng": -70.6506}'
```

### Probar Dashboard Stats
```bash
curl http://localhost:8000/api/dashboard/stats/
```

---

## 📚 Documentación Adicional

- **API REST**: `/api/` - Django REST Framework browsable API
- **Admin Panel**: `/admin/` - Gestión completa de modelos
- **Código fuente**: Revisar comentarios inline en cada archivo

---

## 🎯 Próximas Mejoras Sugeridas

1. **Exportación real de reportes** (Excel/PDF)
2. **Notificaciones push** reales (Firebase/OneSignal)
3. **Mapas interactivos** con trazado de rutas
4. **Alertas SMS** automáticas
5. **Integración con WhatsApp** Business API
6. **Dashboard en tiempo real** con WebSockets
7. **Machine Learning** para predicción de demoras

---

## ✅ Checklist de Implementación

- [x] Pre-asignación con validación de tiempos
- [x] Sistema de notificaciones con ETA
- [x] Diferenciación Drop & Hook vs Truck Discharge
- [x] Dashboard móvil para conductores
- [x] Dashboard ejecutivo con analytics
- [x] Endpoints API completos
- [x] Migraciones de base de datos
- [x] Documentación completa
- [x] Pruebas de integración
- [x] Navegación actualizada

---

**Versión:** 1.0  
**Fecha:** Octubre 2025  
**Desarrollado por:** SoptraLoc Team
