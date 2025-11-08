# Mejoras al Portal de Operaciones y Conductores

## Resumen de Cambios

Este documento describe las mejoras implementadas en el sistema SoptraLoc TMS para mejorar la experiencia de operaciones y conductores.

## Cambios Implementados

### 1. Dashboard Principal - Tarjeta "Sin Asignar" Clickeable

**Ubicación:** `templates/home.html`

**Cambios:**
- La tarjeta de estadísticas "Sin Asignar (48h)" ahora es clickeable
- Al hacer clic, redirige automáticamente a `/operaciones/`
- Incluye efectos hover para mejor UX (escala 1.05)
- Mantiene el esquema de colores existente (warning si hay sin asignar)

**Beneficios:**
- Acceso rápido desde el dashboard a la sección de operaciones
- Flujo de trabajo más intuitivo para asignar contenedores

### 2. Programación Manual en Operaciones

**Ubicación:** `templates/operaciones.html`

**Cambios:**
- Nueva pestaña "Programación Manual" en el panel de operaciones
- Formulario completo para crear programaciones sin necesidad de Excel
- Campos incluidos:
  - Contenedor Liberado (selector dinámico)
  - Centro de Distribución (selector dinámico)
  - Fecha Programada (datetime picker)
  - Cliente
  - Dirección de Entrega
  - Observaciones
- Muestra información del contenedor seleccionado (nave, tipo, posición, demurrage)
- Panel de programaciones recientes (últimas 10)
- Validación de datos antes de enviar

**Endpoints API:**
- `GET /api/containers/?estado=liberado` - Lista contenedores disponibles
- `GET /api/cds/` - Lista centros de distribución
- `POST /api/programaciones/` - Crea nueva programación

**Beneficios:**
- No es necesario importar Excel para casos individuales
- Más rápido para programaciones urgentes
- Mayor flexibilidad operacional

### 3. Visualización de Asignaciones del Conductor

**Ubicación:** `templates/operaciones.html`

**Cambios:**
- Los conductores en la lista ahora son clickeables
- Al hacer clic en un conductor, se muestra un modal con:
  - Todas las asignaciones actuales
  - Estado de cada contenedor (badges de colores)
  - Información del CD y cliente
  - Fecha programada
- Efectos hover con cambio de borde y sombra

**Beneficios:**
- Visibilidad completa de la carga de trabajo de cada conductor
- Facilita la toma de decisiones de asignación
- Mejor seguimiento de asignaciones activas

### 4. Flujo de Aceptación del Conductor

**Ubicación:** 
- Backend: `apps/programaciones/models.py`, `apps/programaciones/views.py`
- Frontend: `templates/driver_dashboard.html`

**Cambios Backend:**

**Modelo (Programacion):**
```python
aceptada_por_conductor = models.BooleanField(default=False)
fecha_aceptacion = models.DateTimeField(null=True, blank=True)
```

**Nuevo Endpoint:**
```
POST /api/programaciones/{id}/aceptar_asignacion/
Body: { "lat": -33.4372, "lng": -70.6506 }  # Opcional
Response: { "success": true, "mensaje": "...", "programacion": {...} }
```

**Cambios Frontend:**
- Nuevo botón "Aceptar Asignación" para asignaciones pendientes
- Alerta visual destacando asignaciones no aceptadas
- Flujo secuencial claro:
  1. **Aceptar Asignación** (nuevo)
  2. Iniciar Ruta
  3. Notificar Arribo
  4. Marcar Vacío

**Validación:**
- El conductor debe aceptar la asignación antes de poder iniciar la ruta
- Se registra la posición GPS al momento de aceptar
- Se crea evento de auditoría

**Beneficios:**
- El conductor confirma explícitamente que recibió y acepta la asignación
- Mejor rastreabilidad del flujo de trabajo
- Reduce confusiones sobre asignaciones activas vs. pendientes

### 5. Mejoras en Serializers

**Ubicación:** `apps/drivers/serializers.py`

**Cambios:**
- `DriverDetailSerializer` ahora incluye:
  - `aceptada_por_conductor`
  - `fecha_aceptacion`
- Estos campos se envían al portal del conductor para determinar el estado

### 6. Migración de Base de Datos

**Ubicación:** `apps/programaciones/migrations/0005_programacion_aceptada_por_conductor.py`

**Campos Agregados:**
- `aceptada_por_conductor` (BooleanField, default=False)
- `fecha_aceptacion` (DateTimeField, nullable)

**Ejecutar:**
```bash
python manage.py migrate
```

## Flujo de Trabajo Completo

### Para Operador

1. **Dashboard**: Ver "Sin Asignar (48h)" y hacer clic para ir a Operaciones
2. **Operaciones - Programación Manual**: 
   - Crear programación para contenedor liberado
   - Seleccionar CD y fecha
3. **Operaciones - Asignación**:
   - Ver contenedores sin asignar
   - Asignar automáticamente o manualmente
   - Hacer clic en conductor para ver su carga actual
4. **Seguimiento**:
   - Ver estado de todas las asignaciones
   - Monitorear aceptaciones pendientes

### Para Conductor

1. **Login**: Ingresar al portal del conductor
2. **Ver Asignaciones**: 
   - Asignaciones aparecen con alerta si no están aceptadas
3. **Aceptar**: 
   - Hacer clic en "Aceptar Asignación"
   - Confirmar aceptación
   - GPS se registra automáticamente
4. **Iniciar Ruta**:
   - Botón aparece solo después de aceptar
   - Ingresar patente del vehículo
   - Iniciar navegación
5. **Notificar Arribo**: Al llegar al CD
6. **Marcar Vacío**: Cuando el contenedor está descargado

## Estados del Flujo

| Estado | Descripción | Acción Disponible |
|--------|-------------|-------------------|
| Programado | Sin conductor asignado | - |
| Asignado (no aceptado) | Conductor asignado, esperando aceptación | **Aceptar Asignación** |
| Asignado (aceptado) | Conductor aceptó | **Iniciar Ruta** |
| En Ruta | Conductor en camino | **Notificar Arribo** |
| Entregado | Llegó a destino | **Marcar Vacío** |
| Vacío | Descargado y listo | - |

## Eventos de Auditoría

Se crean los siguientes eventos automáticamente:

- `asignacion_aceptada` - Cuando conductor acepta
- `inicio_ruta` - Cuando conductor inicia ruta
- `arribo_cd` - Cuando conductor notifica arribo
- `contenedor_vacio` - Cuando se marca como vacío

## Testing

**Ubicación:** `apps/programaciones/tests.py`

**Nuevo Test:**
- `test_aceptar_asignacion_workflow` - Valida el flujo de aceptación

**Ejecutar tests:**
```bash
python manage.py test apps.programaciones.tests.ProgramacionAsignacionTests.test_aceptar_asignacion_workflow
```

## Compatibilidad hacia Atrás

- **100% compatible**: Todas las funcionalidades existentes siguen funcionando
- Los contenedores ya asignados **no** requieren aceptación retroactiva
- El campo `aceptada_por_conductor` es opcional (default=False)
- Los endpoints existentes no se modificaron

## Notas Técnicas

### Frontend

- Bootstrap 5 para modales y UI
- Fetch API para llamadas AJAX
- CSRF tokens en todas las peticiones POST
- Geolocalización HTML5 para GPS

### Backend

- Django REST Framework para API
- Signals para eventos automáticos
- Transacciones atómicas en asignaciones
- Validaciones de estado antes de cambios

## Próximas Mejoras Sugeridas

1. Notificaciones push en tiempo real para nuevas asignaciones
2. Exportar programaciones a Excel desde la UI
3. Filtros avanzados en programación manual
4. Vista de calendario para programaciones
5. Estadísticas de aceptación de conductores

## Soporte

Para preguntas o problemas:
1. Revisar este documento
2. Revisar logs: `/var/log/django/`
3. Revisar eventos de auditoría en admin
4. Contactar equipo de desarrollo

---

**Versión:** 1.0  
**Fecha:** Noviembre 2025  
**Autor:** Equipo SoptraLoc
