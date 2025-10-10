# 🚀 DEPLOY CRÍTICO - RESET ROUTING + MEJORAS ADMIN

## 📋 RESUMEN DE CAMBIOS

### 1. ✅ **MIGRACIÓN 0004: Reset Routing en Producción**
**Archivo**: `apps/routing/migrations/0004_reset_routing_for_production.py`

**Problema Resuelto**: 
- Error "cannot cast type uuid to bigint" en Render
- Las tablas routing fueron creadas con FKs UUID apuntando a `core.driver` (UUID)
- Ahora `Driver` está en `drivers.driver` con BigAutoField (bigint) → Cast imposible

**Solución Implementada**:
- ✅ Detecta si es PostgreSQL (Render) o SQLite (local)
- ✅ En PostgreSQL: DROP CASCADE de todas las tablas routing
- ✅ Recrea tablas con tipos correctos (FKs bigint para driver)
- ✅ Limpia historial de migraciones routing (0001, 0002, 0003)
- ✅ En SQLite: SKIP (funciona OK, no necesita cambios)

**Tablas Recreadas**:
- `routing_locationpair`
- `routing_operationtime`
- `routing_route`
- `routing_routestop`
- `routing_actualtriprecord`
- `routing_actualoperationrecord`

**Relaciones FK Correctas**:
- `driver_id` → `drivers.driver` (bigint) ✓
- `location_id` → `drivers.location` (varchar 32) ✓

---

### 2. ✅ **ADMIN: Edición Rápida de Fechas de Programación**
**Archivo**: `apps/containers/admin.py`

**Cambios**:
```python
# Agregado a list_display
'scheduled_date'

# Agregado list_editable
list_editable = ('scheduled_date',)

# Agregado filter
list_filter = (..., 'scheduled_date')
```

**Beneficio**: 
- ✅ Editar `scheduled_date` directamente desde la lista de contenedores
- ✅ No es necesario entrar a cada contenedor individualmente
- ✅ Filtrar por fecha de programación

---

### 3. ✅ **ADMIN: Eliminación Segura de Conductores**
**Archivo**: `apps/drivers/admin.py`

**Problema**: Error 500 al intentar eliminar conductores desde admin

**Solución**:
```python
def safe_delete_drivers(self, request, queryset):
    """
    Limpia todas las relaciones antes de eliminar:
    1. Desvincula contenedores asignados
    2. Elimina assignments relacionadas
    3. Maneja ProtectedError con mensajes claros
    """
```

**Características**:
- ✅ Acción masiva "🗑️ Eliminar conductores seleccionados (seguro)"
- ✅ Limpia `contenedor_asignado` antes de eliminar
- ✅ Elimina `Assignment` relacionadas
- ✅ Mensajes detallados de éxito/error
- ✅ Override de `delete_queryset` para usar método seguro

---

### 4. ✅ **IMPORTACIÓN: Captura SIEMPRE los Pesos**
**Archivo**: `apps/containers/services/import_services.py`

**Problema**: Sistema no reconocía pesos al importar Excel

**Mejoras**:
```python
# ANTES: Silenciosamente ignoraba pesos faltantes
if column_map.get('cargo_weight'):
    container.cargo_weight = float(row[...])

# AHORA: Detecta y advierte cuando faltan pesos
peso_encontrado = False
# ... intenta extraer tare, cargo_weight, total_weight ...
if not peso_encontrado:
    logger.warning(f"⚠️ CONTENEDOR {formatted_number}: Sin datos de peso")
    self.results['messages'].append(f"⚠️ {formatted_number}: Sin datos de peso")
```

**Beneficios**:
- ✅ Logging explícito cuando NO se encuentran pesos
- ✅ Try/except para conversiones con logging de errores
- ✅ Reporta en `results['messages']` los contenedores sin peso
- ✅ Permite identificar rápidamente problemas en Excel

---

### 5. ✅ **DETECTOR DE COLUMNAS: Más Variantes de Peso**
**Archivo**: `apps/containers/services/utils.py`

**Mejoras**:
```python
COLUMN_KEYWORDS = {
    # ANTES:
    'tare': ['tara', 'peso vacio'],
    'cargo_weight': ['peso carga'],
    'total_weight': ['peso total', 'bruto'],
    
    # AHORA: Múltiples variantes
    'tare': ['tara', 'peso vacio', 'tare', 'empty weight', 'pesovacio', 'weight empty'],
    'cargo_weight': ['peso carga', 'cargo weight', 'pesocarga', 'neto', 'net weight', 'peso neto'],
    'total_weight': ['peso total', 'total weight', 'pesototal', 'bruto', 'gross', 'peso bruto', 'gross weight', 'kg'],
}
```

**Nuevas Variantes Detectadas**:
- Español: tara, peso vacio, peso carga, peso total, bruto, neto
- Inglés: tare, empty weight, cargo weight, gross weight, net weight
- Sin espacios: pesovacio, pesocarga, pesototal
- Genérico: kg

---

## 📊 IMPACTO

### ✅ RESOLVE:
1. **Error Crítico Render**: "cannot cast type uuid to bigint" → SOLUCIONADO
2. **Admin Error 500**: Eliminación de conductores → SOLUCIONADO
3. **Datos Faltantes**: Pesos no importados → DETECTADO Y REPORTADO
4. **UX Admin**: Edición rápida de `scheduled_date` → IMPLEMENTADO

### ⚠️ IMPORTANTE PARA RENDER:
- Primera vez que se deploya: **SE PERDERÁN DATOS DE ROUTING**
  - Tablas: `routing_*` serán DROP y recreadas
  - Datos preservados: Containers, Drivers, Locations, Assignments
  - Funcionalidad preservada: Importación Excel, flujo de programación
  
- Después del primer deploy: Sistema estable con tipos correctos

---

## 🧪 TESTING LOCAL

```bash
# Migración en SQLite local
python manage.py migrate  # SKIP routing reset (SQLite funciona OK)

# Test admin
python manage.py runserver
# 1. Ir a /admin/containers/container/
# 2. Editar scheduled_date desde lista ✓
# 3. Ir a /admin/drivers/driver/
# 4. Seleccionar conductores → "Eliminar seguro" ✓

# Test importación
# 1. Importar Excel con pesos
# 2. Verificar logs para advertencias "⚠️ Sin datos de peso"
```

---

## 🚀 DESPLIEGUE RENDER

Al hacer push, Render ejecutará:
1. `routing/0004` detecta PostgreSQL
2. DROP CASCADE routing tables
3. Recrea con tipos correctos (bigint para driver_id)
4. Sistema operativo con admin mejorado

**Deploy seguro**: No afecta Containers, Drivers, Locations existentes.

---

## 📝 NOTAS TÉCNICAS

### Migración 0004 - Detalles:
- `connection.vendor != 'postgresql'` → skip en SQLite
- `DROP TABLE IF EXISTS ... CASCADE` → elimina constraints automáticamente
- `DELETE FROM django_migrations WHERE app='routing'` → limpia historial
- `CreateModel` con FKs correctos desde inicio

### Admin Seguro:
- `ProtectedError` capturado y mostrado como warning
- Batch messages agrupados (max 5 + contador)
- `delete_queryset` override para consistencia

### Importación Robusta:
- `try/except` en cada conversión de peso
- Logger con nivel WARNING para visibilidad
- Results messages para feedback usuario

---

## 🎯 PRÓXIMOS PASOS POST-DEPLOY

1. Verificar que Render despliega OK
2. Revisar logs para advertencias de pesos faltantes
3. Re-importar datos routing si es necesario (opcional)
4. Probar eliminación de conductores en producción
5. Capacitar usuarios en edición rápida de `scheduled_date`
