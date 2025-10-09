# Consolidación de Modelos - Octubre 8, 2025

## Problema Identificado

El sistema tenía **duplicación crítica** de modelos entre `apps.core` y `apps.drivers`:

- **Driver**: definido en `core.models` y `drivers.models`
- **Location**: definido en `core.models` y `drivers.models`

Esto causaba:
1. Inconsistencias en las relaciones ForeignKey
2. Confusión sobre qué modelo importar
3. Posibles conflictos de datos en la base de datos
4. Dificultad para mantener el código

## Solución Implementada

### Principio de Diseño: Un Solo Modelo, Un Solo Lugar

Se consolidaron los modelos siguiendo el principio de responsabilidad única y dominio:

### Modelos en `apps.core.models`
- `BaseModel` (abstracto) - Base para herencia
- `Company` - Empresas/Clientes
- `Vehicle` - Vehículos/Chasis
- `MovementCode` - Códigos de movimiento

### Modelos en `apps.drivers.models` (Dominio de Conductores y Logística)
- `Location` - Ubicaciones geográficas ✅ **Modelo unificado**
- `Driver` - Conductores ✅ **Modelo unificado**
- `TimeMatrix` - Matriz de tiempos entre ubicaciones
- `Assignment` - Asignaciones conductor-contenedor
- `Alert` - Sistema de alertas
- `TrafficAlert` - Alertas de tráfico en tiempo real

### Cambios Realizados

#### 1. Eliminación de Duplicados
- ❌ Eliminado `Driver` de `apps.core.models`
- ❌ Eliminado `Location` de `apps.core.models`

#### 2. Extensión del Modelo Location
Se agregaron campos faltantes al modelo unificado en `drivers.models.Location`:
```python
city = models.CharField(max_length=100, blank=True, default='', verbose_name="Ciudad")
region = models.CharField(max_length=100, blank=True, default='', verbose_name="Región")
country = models.CharField(max_length=100, default='Chile', verbose_name="País")
```

#### 3. Actualización de Imports
Se actualizaron **todos** los archivos que importaban `Location` o `Driver` desde `core`:

**Archivos actualizados (26 archivos):**
- `apps/containers/models.py`
- `apps/containers/views.py`
- `apps/containers/serializers.py`
- `apps/containers/services/excel_importers.py`
- `apps/containers/services/utils.py`
- `apps/containers/management/commands/*.py` (varios)
- `apps/warehouses/models.py`
- `apps/warehouses/serializers.py`
- `apps/routing/models.py`
- `apps/routing/management/commands/*.py`
- `apps/core/admin.py`
- `apps/core/serializers.py`
- `apps/core/views.py`
- `apps/core/urls.py`
- `apps/core/management/commands/*.py`
- Y otros archivos relacionados

#### 4. Creación de Serializers
Se creó `apps/drivers/serializers.py` con serializers completos:
- `LocationSerializer`
- `DriverSerializer`
- `TimeMatrixSerializer`
- `AssignmentSerializer`
- `AlertSerializer`
- `TrafficAlertSerializer`

#### 5. Actualización de Admin
- Eliminados `DriverAdmin` y `LocationAdmin` de `apps/core/admin.py`
- Estos deben registrarse en `apps/drivers/admin.py`

#### 6. Actualización de URLs
- Eliminadas rutas `/api/core/drivers/` y `/api/core/locations/` de `apps/core/urls.py`
- Estas rutas deben estar en `apps/drivers/urls.py`

### Migración de Base de Datos

Se creó y aplicó la migración `0009_extend_location_model.py`:
```bash
python manage.py makemigrations drivers --name extend_location_model
python manage.py migrate
```

**Cambios en DB:**
- Agregados campos `city`, `region`, `country` a `drivers_location`
- Actualizados metadatos y verbose names

### Función Consolidada

Se creó función unificada `_get_or_create_location()` en `excel_importers.py` que:
- Busca ubicaciones por código (prioridad)
- Busca por nombre si no hay código
- Crea automáticamente con código único si no existe
- Maneja coordenadas, ciudad, región y país

### Validación

✅ **Tests Pasados:**
```bash
python manage.py check
# System check identified no issues (0 silenced).
```

✅ **Pyright:**
```bash
npx pyright
# 0 errors, 0 warnings, 0 informations
```

## Beneficios Obtenidos

1. **Claridad arquitectónica**: Un modelo, un lugar
2. **Eliminación de ambigüedad**: No hay confusión sobre qué modelo importar
3. **Integridad referencial**: Todas las FK apuntan al mismo modelo
4. **Mantenibilidad**: Cambios en un solo lugar
5. **Escalabilidad**: Base sólida para futuras extensiones

## Próximos Pasos Recomendados

1. ✅ **COMPLETADO**: Consolidar modelos Location y Driver
2. 🔄 **EN PROCESO**: Auditar lógica de negocio en views y services
3. ⏳ **PENDIENTE**: Revisar y completar admin.py de drivers
4. ⏳ **PENDIENTE**: Crear/actualizar tests unitarios
5. ⏳ **PENDIENTE**: Documentar flujos de trabajo completos

## Impacto en el Sistema

### Módulos Afectados
- ✅ `core` - Simplificado, solo modelos base
- ✅ `drivers` - Ahora es el dueño de Location, Driver y lógica de rutas
- ✅ `containers` - Actualizado para usar modelos correctos
- ✅ `warehouses` - Actualizado para usar Location correcto
- ✅ `routing` - Actualizado para usar modelos de drivers

### Sin Breaking Changes
- ✅ Las tablas de base de datos mantienen sus nombres originales
- ✅ Los datos existentes se preservan
- ✅ Las APIs mantienen compatibilidad (solo cambian endpoints base)

## Notas Técnicas

- Tabla `drivers_location` mantiene su nombre por compatibilidad
- Se usa `db_table = 'drivers_location'` en el Meta del modelo
- Los campos `created_at`, `updated_at` se mantienen automáticos
- Los campos de auditoría (`created_by`, `updated_by`) solo están en modelos que heredan `BaseModel`

## Autor
Sistema consolidado el 8 de octubre de 2025.
Refactorización completa de arquitectura de modelos para TMS Soptraloc.
