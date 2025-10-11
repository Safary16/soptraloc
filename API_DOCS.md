# 📡 Documentación de API - SoptraLoc TMS

## Base URL

- **Desarrollo**: `http://localhost:8000/api/`
- **Producción**: `https://tu-app.onrender.com/api/`

## Autenticación

Actualmente la API está abierta para desarrollo. Se puede agregar JWT en producción si es necesario.

---

## 📦 Endpoints de Contenedores

### Listar contenedores
```http
GET /api/containers/
```

**Filtros disponibles**:
- `estado`: por_arribar, liberado, programado, asignado, en_ruta, entregado, etc.
- `tipo`: 20, 40, 40HC, 45
- `secuenciado`: true/false
- `puerto`: Valparaíso
- `posicion_fisica`: ZEAL, CLEP, TPS, STI, PCE

**Búsqueda**: `?search=CONT001` (busca en container_id, nave, vendor, comuna)

### Importar Excel de Embarque
```http
POST /api/containers/import_embarque/
Content-Type: multipart/form-data

file: archivo.xlsx
```

**Respuesta**:
```json
{
  "success": true,
  "mensaje": "Importación completada",
  "creados": 10,
  "actualizados": 2,
  "errores": 0,
  "detalles": [...]
}
```

### Importar Excel de Liberación
```http
POST /api/containers/import_liberacion/
Content-Type: multipart/form-data

file: archivo.xlsx
```

### Importar Excel de Programación
```http
POST /api/containers/import_programacion/
Content-Type: multipart/form-data

file: archivo.xlsx
```

### Exportar Stock
```http
GET /api/containers/export_stock/
```

Retorna contenedores en estado `liberado` y `por_arribar` con flag `secuenciado`.

### Cambiar Estado Manual
```http
POST /api/containers/{id}/cambiar_estado/
Content-Type: application/json

{
  "estado": "liberado"
}
```

---

## 👷 Endpoints de Conductores

### Listar conductores
```http
GET /api/drivers/
```

**Filtros**:
- `presente`: true/false
- `activo`: true/false

### Listar solo disponibles
```http
GET /api/drivers/disponibles/
```

Retorna solo conductores activos, presentes y con capacidad.

### Actualizar posición
```http
POST /api/drivers/{id}/actualizar_posicion/
Content-Type: application/json

{
  "lat": -33.4489,
  "lng": -70.6693
}
```

### Registrar entrega
```http
POST /api/drivers/{id}/registrar_entrega/
Content-Type: application/json

{
  "a_tiempo": true
}
```

### Marcar presente/ausente
```http
POST /api/drivers/{id}/marcar_presente/
POST /api/drivers/{id}/marcar_ausente/
```

### Resetear entregas del día (batch)
```http
POST /api/drivers/resetear_entregas_dia/
```

Resetea el contador `num_entregas_dia` para todos los conductores. Útil para ejecutar diariamente.

---

## 📅 Endpoints de Programaciones

### Listar programaciones
```http
GET /api/programaciones/
```

**Filtros**:
- `fecha_programada`: YYYY-MM-DD
- `requiere_alerta`: true/false
- `driver`: ID del conductor
- `cd`: ID del CD

### Ver alertas (< 48h sin conductor)
```http
GET /api/programaciones/alertas/
```

### Asignar conductor manual
```http
POST /api/programaciones/{id}/asignar_conductor/
Content-Type: application/json

{
  "driver_id": 1
}
```

### Asignar conductor automático
```http
POST /api/programaciones/{id}/asignar_automatico/
```

**Respuesta**:
```json
{
  "success": true,
  "mensaje": "Conductor Juan Pérez asignado automáticamente",
  "score": 87.5,
  "desglose": {
    "disponibilidad": 100.0,
    "ocupacion": 66.67,
    "cumplimiento": 95.5,
    "proximidad": 82.3
  },
  "programacion": {...}
}
```

### Ver conductores disponibles con scores
```http
GET /api/programaciones/{id}/conductores_disponibles/
```

Retorna todos los conductores disponibles ordenados por score de asignación.

### Asignar múltiples programaciones
```http
POST /api/programaciones/asignar_multiples/
Content-Type: application/json

{
  "programacion_ids": [1, 2, 3, 4]
}
```

**Respuesta**:
```json
{
  "success": true,
  "asignadas": 3,
  "fallidas": 1,
  "detalles": [...]
}
```

---

## 📍 Endpoints de CDs (Centros de Distribución)

### Listar CDs
```http
GET /api/cds/
```

**Filtros**:
- `tipo`: cliente, ccti
- `activo`: true/false
- `comuna`: nombre de la comuna

### Listar solo CCTIs
```http
GET /api/cds/cctis/
```

### Listar solo clientes
```http
GET /api/cds/clientes/
```

### Recibir contenedor vacío en CCTI
```http
POST /api/cds/{id}/recibir_vacio/
```

Incrementa el contador de vacíos en el CCTI.

### Retirar contenedor vacío de CCTI
```http
POST /api/cds/{id}/retirar_vacio/
```

Decrementa el contador de vacíos en el CCTI.

---

## 🔍 Ejemplos de Uso

### 1. Flujo completo de importación

```bash
# 1. Importar embarque
curl -X POST http://localhost:8000/api/containers/import_embarque/ \
  -F "file=@embarque.xlsx"

# 2. Importar liberación
curl -X POST http://localhost:8000/api/containers/import_liberacion/ \
  -F "file=@liberacion.xlsx"

# 3. Importar programación
curl -X POST http://localhost:8000/api/containers/import_programacion/ \
  -F "file=@programacion.xlsx"

# 4. Ver alertas
curl http://localhost:8000/api/programaciones/alertas/

# 5. Asignar automáticamente
curl -X POST http://localhost:8000/api/programaciones/1/asignar_automatico/
```

### 2. Consultar stock actual

```bash
curl http://localhost:8000/api/containers/export_stock/
```

### 3. Actualizar posición del conductor

```bash
curl -X POST http://localhost:8000/api/drivers/1/actualizar_posicion/ \
  -H "Content-Type: application/json" \
  -d '{"lat": -33.4489, "lng": -70.6693}'
```

### 4. Ver conductores disponibles para una programación

```bash
curl http://localhost:8000/api/programaciones/1/conductores_disponibles/
```

---

## 📊 Códigos de Estado

- `200 OK`: Solicitud exitosa
- `201 Created`: Recurso creado exitosamente
- `400 Bad Request`: Error en los datos enviados
- `404 Not Found`: Recurso no encontrado
- `500 Internal Server Error`: Error del servidor

---

## 🔧 Comandos de Management

### Cargar datos de prueba
```bash
python manage.py cargar_datos_prueba
```

Crea:
- 2 CCTIs (ZEAL, CLEP)
- 3 Clientes
- 4 Conductores
- 8 Contenedores
- 3 Programaciones

---

## 🚀 Para Producción

1. Configurar variables de entorno en Render
2. Ejecutar migraciones
3. Crear superusuario
4. (Opcional) Agregar autenticación JWT
5. (Opcional) Configurar límites de rate limiting

---

## 📝 Notas

- Los importadores de Excel son tolerantes a diferentes formatos de columnas
- El algoritmo de asignación usa Mapbox para calcular distancias reales
- Las alertas de 48h se generan automáticamente al importar programaciones
- Los eventos se registran automáticamente para auditoría
