# Deploy - Octubre 2025

## Cambios implementados

### 1. Sistema de Testing Optimizado
- **Comando:** `python manage.py reset_test_data --keep-containers 30`
- Reduce base de datos para testing ágil
- Mantiene datos esenciales (naves, agencias, clientes)

### 2. Servicios de Importación Completos

#### VesselImportService
- Importa manifiestos de nave desde Excel
- Formato automático de contenedores: `AAAU1234561` → `AAAU 123456-1`
- Estado inicial: **POR_ARRIBAR**
- Detecta columnas flexiblemente (español e inglés)

#### ReleaseScheduleImportService  
- Importa horarios de liberación (WALMART TTS.xls)
- Actualiza `release_date`, `release_time`
- Cambia estado a **LIBERADO**

#### ProgrammingImportService
- Importa programación del cliente
- Actualiza `scheduled_date`, `scheduled_time`, `cd_location`, `demurrage_date`
- Determina posición automáticamente:
  - **SAN ANTONIO** → `CLEP`
  - **VALPARAÍSO** → `ZEAL`
- Cambia estado a **PROGRAMADO**

### 3. Dashboard Mejorado
- Formularios de carga para:
  1. Manifiestos de nave
  2. Liberaciones
  3. Programación
- Botón "Exportar Liberados" → genera Excel para cliente
- Alertas informativas del flujo de trabajo
- Auto-submit al seleccionar archivos

### 4. Documentación del Flujo
- `FLUJO_TRABAJO.md`: Guía completa paso a paso
- Estados del contenedor documentados
- Tipos de conductor (TRONCAL vs LOCAL)
- Reglas de asignación según posición

### 5. Frontend Unificado
- `container-actions.js`: Módulo compartido
- Templates harmonizados (`dashboard.html`, `resueltos.html`)
- Acciones consistentes en todas las vistas
- Modals para arribo con selección de destino

## Archivos Clave

```
/workspaces/soptraloc/
├── FLUJO_TRABAJO.md                                    # Documentación completa
├── soptraloc_system/
│   ├── apps/containers/
│   │   ├── management/commands/
│   │   │   ├── reset_test_data.py                      # Reducir datos testing
│   │   │   └── setup_testing_cycle.py                  # Crear escenario prueba
│   │   └── services/
│   │       └── import_services.py                      # Servicios importación
│   ├── static/js/
│   │   └── container-actions.js                        # Módulo JS compartido
│   └── templates/core/
│       ├── dashboard.html                              # Dashboard mejorado
│       └── resueltos.html                              # Vista resueltos armonizada
```

## Verificación Pre-Deploy

### 1. Base de Datos
```bash
python manage.py reset_test_data --keep-containers 30
python manage.py collectstatic --noinput
```

### 2. Migraciones
```bash
python manage.py makemigrations
python manage.py migrate
```

### 3. Variables de Entorno (.env)
```
DEBUG=False
ALLOWED_HOSTS=soptraloc.onrender.com,*.onrender.com
DATABASE_URL=postgresql://...
SECRET_KEY=...
```

## Comandos para Testing Local

### Reducir contenedores
```bash
python manage.py reset_test_data --keep-containers 30
```

### Crear escenario completo
```bash
python manage.py setup_testing_cycle --replicas 2 --purge
```

### Iniciar servidor
```bash
python manage.py runserver
```

## Endpoints API

### Importación
- `POST /api/v1/containers/import-manifest/` - Manifiesto nave
- `POST /api/v1/containers/import-release/` - Liberaciones
- `POST /api/v1/containers/import-programming/` - Programación

### Exportación
- `GET /api/v1/containers/export-liberated/` - Excel contenedores liberados

### Actualización de Estado
- `POST /containers/{id}/update-status/` - Cambiar estado
- `POST /containers/{id}/update-position/` - Cambiar posición

## Flujo de Trabajo en Producción

1. **Subir Manifiesto** → Contenedores en POR_ARRIBAR
2. **Aplicar Liberaciones** → Contenedores en LIBERADO
3. **Exportar Liberados** → Enviar Excel al cliente
4. **Subir Programación** → Contenedores en PROGRAMADO (posición auto-determinada)
5. **Asignar Conductores** → Manual o automático
6. **Seguimiento Operativo** → EN_RUTA → ARRIBADO → FINALIZADO

## Mejoras Machine Learning (Futuro)
- Predicción de tiempos de ruta
- Optimización automática de asignaciones
- Alertas predictivas de demurrage
- Análisis de patrones operativos

## Deploy a Render

### Opción 1: Auto-Deploy desde GitHub
Render detectará el push y desplegará automáticamente.

### Opción 2: Deploy Manual
```bash
# Desde Render Dashboard
1. Ir a https://dashboard.render.com
2. Seleccionar el servicio soptraloc
3. Hacer clic en "Manual Deploy" → "Deploy latest commit"
```

### Verificación Post-Deploy
1. Abrir https://soptraloc.onrender.com/dashboard/
2. Verificar que los formularios de carga estén visibles
3. Probar subida de archivo de prueba
4. Verificar botón "Exportar Liberados"
5. Confirmar que el módulo SoptralocActions funcione

## Notas Importantes

### Base de Datos
- Actualmente: **30 contenedores** (post reset)
- Producción: Escalar según carga real
- Backup recomendado antes de importaciones masivas

### Archivos Excel
- Formato flexible (español/inglés)
- Detección automática de columnas
- Logging de errores por fila

### Performance
- Auto-refresh deshabilitado por defecto
- Alertas con auto-dismiss (5 segundos)
- Carga asíncrona de formularios

## Próximos Pasos

1. **Testing en Staging:** Probar flujo completo con datos reales
2. **Capacitación:** Entrenar usuarios en nuevo flujo
3. **Monitoreo:** Configurar alertas de errores
4. **Optimización:** Ajustar según feedback operativo

---

**Última actualización:** Octubre 2025  
**Versión:** 2.0  
**Branch:** main  
**Commit:** 48759d2
