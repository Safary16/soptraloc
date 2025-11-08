# SoptraLoc TMS - URL Structure and Functionality

## Frontend Pages (User Interface)

### Core Operations
- **`/`** - Dashboard Principal
  - Muestra KPIs y estadísticas generales
  - Programaciones prioritarias
  - Enlaces rápidos a funciones principales

- **`/operaciones/`** - Panel de Operaciones (Gestión de Ciclo de Vida)
  - **Tab: Ciclo de Vida** - Ver y gestionar transiciones de estado de contenedores
  - **Tab: Liberación** - Liberar contenedores (Por Arribar → Liberado)
  - **Tab: Programación** - Programar entregas (asignar CD y fecha a contenedores liberados)

- **`/asignacion/`** - Asignación de Conductores
  - Asignar conductores a contenedores programados
  - Asignación manual o automática (ML)
  - Vista de conductores disponibles y contenedores sin asignar

- **`/estados/`** - Dashboard de Estados
  - Visualización del ciclo de vida completo
  - Enlaces de acción rápida para cada estado
  - Estadísticas por fase (Puerto, Entrega, Retorno)

### Gestión y Consulta
- **`/containers/`** - Listado de Contenedores
  - Lista completa con filtros por estado, urgencia, búsqueda
  - Hasta 100 contenedores por página

- **`/container/<container_id>/`** - Detalle de Contenedor
  - Información completa de un contenedor específico

- **`/drivers/`** - Listado de Conductores
  - Vista de todos los conductores con filtros

- **`/importar/`** - Importación de Excel
  - Subir archivos Excel para importar datos
  - Embarques, liberaciones, programaciones

### Monitoreo
- **`/monitoring/`** - Monitoreo GPS
  - Tracking en tiempo real de contenedores en ruta
  - Mapa con posiciones de conductores

- **`/executive/`** - Dashboard Ejecutivo
  - Métricas y análisis de alto nivel
  - KPIs y tendencias

### Portal de Conductores
- **`/driver/login/`** - Login de Conductores
- **`/driver/dashboard/`** - Dashboard de Conductor
- **`/driver/logout/`** - Logout de Conductor

### Administración
- **`/admin/`** - Panel de Administración Django
  - Gestión completa de modelos
  - Usuarios, permisos, configuración

---

## API Endpoints (REST API)

### Contenedores
- **`GET /api/containers/`** - Listar contenedores
  - Filtros: estado, tipo, secuenciado, puerto, posicion_fisica
  - Búsqueda: container_id, nave, vendor, comuna

- **`GET /api/containers/<id>/`** - Detalle de contenedor
- **`POST /api/containers/<id>/cambiar_estado/`** - Cambiar estado de contenedor
  - Body: `{"estado": "liberado"}`

- **`POST /api/containers/import-embarque/`** - Importar embarques (Excel)
- **`POST /api/containers/import-liberacion/`** - Importar liberaciones (Excel)
- **`GET /api/containers/export-liberacion-excel/`** - Exportar a Excel

### Conductores (Drivers)
- **`GET /api/drivers/`** - Listar conductores
  - Filtros: activo, presente
  
- **`GET /api/drivers/<id>/`** - Detalle de conductor
- **`POST /api/drivers/<id>/actualizar_posicion/`** - Actualizar posición GPS
  - Body: `{"lat": -33.4372, "lng": -70.6506}`

### Programaciones
- **`GET /api/programaciones/`** - Listar programaciones
  - Filtros: fecha_programada, requiere_alerta, driver, cd
  
- **`POST /api/programaciones/`** - Crear programación
  - Body: `{"container": <id>, "cd": <id>, "fecha_programada": "...", "cliente": "..."}`

- **`GET /api/programaciones/<id>/`** - Detalle de programación

- **`POST /api/programaciones/<id>/asignar_conductor/`** - Asignación manual
  - Body: `{"driver_id": <id>}`

- **`POST /api/programaciones/<id>/asignar_automatico/`** - Asignación automática (ML)
  - Selecciona el mejor conductor disponible

- **`GET /api/programaciones/<id>/conductores_disponibles/`** - Lista conductores con scores ML

- **`POST /api/programaciones/asignar_multiples/`** - Asignar múltiples programaciones
  - Body: `{"programacion_ids": [1, 2, 3]}`

- **`POST /api/programaciones/<id>/iniciar_ruta/`** - Iniciar ruta
  - Body: `{"patente": "ABC123", "lat": -33.4372, "lng": -70.6506}`

- **`POST /api/programaciones/<id>/notificar_arribo/`** - Notificar llegada a CD

- **`GET /api/programaciones/alertas/`** - Programaciones que requieren alerta
- **`GET /api/programaciones/alertas_demurrage/`** - Contenedores con demurrage crítico
- **`GET /api/programaciones/dashboard/`** - Dashboard con priorización inteligente

### Centros de Distribución (CDs)
- **`GET /api/cds/`** - Listar CDs
  - Filtros: tipo, activo, comuna
  
- **`GET /api/cds/<id>/`** - Detalle de CD
- **`GET /api/cds/cctis/`** - Listar solo CCTIs activos
- **`GET /api/cds/clientes/`** - Listar solo clientes activos
- **`POST /api/cds/<id>/recibir_vacio/`** - Registrar recepción de vacío
- **`POST /api/cds/<id>/retirar_vacio/`** - Registrar retiro de vacío

### Autenticación
- **`/api-auth/`** - Django REST Framework authentication
- **`/api/`** - API Root (navegable en browser)

---

## Flujo de Trabajo Típico

### 1. Importación y Liberación
1. Importar embarques → `/importar/` (Excel) → Contenedores en estado "Por Arribar"
2. Liberar contenedores → `/operaciones/` (Tab: Liberación) → Estado "Liberado"

### 2. Programación y Asignación
3. Programar entregas → `/operaciones/` (Tab: Programación) → Asignar CD y fecha → Estado "Programado"
4. Asignar conductores → `/asignacion/` → Manual o automático → Estado "Asignado"

### 3. Ejecución y Tracking
5. Conductor inicia ruta → App móvil o API → Estado "En Ruta"
6. Monitoreo GPS → `/monitoring/` → Ver ubicación en tiempo real
7. Arribo a CD → Estado "Entregado"
8. Descarga completa → Estado "Descargado"

### 4. Retorno
9. Contenedor vacío → Estado "Vacío"
10. Retorno a depósito → Estado "Vacío en Ruta"
11. Devolución completa → Estado "Devuelto"

---

## Estados del Contenedor (Ciclo de Vida)

### Fase 1: Puerto (Contenedor Lleno)
- **por_arribar**: Nave en tránsito
- **liberado**: Liberado por aduana/naviera
- **secuenciado**: Marcado para próxima entrega
- **programado**: Asignado a fecha y CD
- **asignado**: Asignado a conductor

### Fase 2: Entrega (Contenedor Lleno)
- **en_ruta**: Conductor en camino a CD
- **entregado**: Llegó a CD cliente
- **descargado**: Cliente terminó de descargar

### Fase 3: Retorno (Contenedor Vacío)
- **vacio**: Descargado, esperando retiro
- **vacio_en_ruta**: Retornando a depósito
- **devuelto**: Devuelto a depósito naviera

---

## Acciones por Estado

| Estado | Acción Disponible | URL |
|--------|-------------------|-----|
| Por Arribar | Liberar | `/operaciones/` → Tab Liberación |
| Liberado | Programar | `/operaciones/` → Tab Programación |
| Programado | Asignar Conductor | `/asignacion/` |
| Asignado | Iniciar Ruta | API o App Móvil |
| En Ruta | Ver en Mapa | `/monitoring/` |
| Entregado | Marcar Descargado | `/operaciones/` → Tab Ciclo de Vida |
| Descargado | Marcar Vacío | `/operaciones/` → Tab Ciclo de Vida |
| Vacío | Iniciar Retorno | API o gestión manual |
| Vacío en Ruta | Marcar Devuelto | `/operaciones/` → Tab Ciclo de Vida |

---

## Notas de Implementación

### Cambios Realizados
1. **`/asignacion/`**: Ahora tiene funcionalidad real de asignación (antes solo mostraba info ML)
2. **`/operaciones/`**: Refocado en gestión del ciclo de vida (liberación, programación, transiciones)
3. **`/estados/`**: Agregados enlaces de acción para cada estado
4. **API `/api/cds/`**: Agregado al router para soportar operaciones de programación

### URLs Eliminadas/Consolidadas
- Eliminado tab "Asignación" duplicado en `/operaciones/`
- Eliminado tab "Pre-Asignación" (funcionalidad movida a programación normal)
- Asignación de conductores ahora es exclusiva de `/asignacion/`

### Sin Cambios
- Todas las demás URLs permanecen funcionales
- No se eliminaron URLs existentes, solo se consolidó funcionalidad
- Compatibilidad total con API existente
