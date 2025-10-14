# 🤖 Guía de Automatización para Render.com

## 📋 Descripción

Este documento describe los comandos de automatización creados para facilitar el deployment y mantenimiento en Render.com sin necesidad de acceso a shell.

---

## 🚀 Comandos Disponibles

### 1. `render_migrate` - Migraciones Seguras

Ejecuta migraciones de base de datos con logging detallado y manejo de errores.

**Uso en Render.com:**
```bash
python manage.py render_migrate
```

**Uso local con dry-run:**
```bash
python manage.py render_migrate --dry-run
```

**Características:**
- ✅ Verifica conexión a base de datos antes de migrar
- ✅ Muestra migraciones pendientes
- ✅ Logging detallado de cada paso
- ✅ Manejo de errores robusto
- ✅ Verificación post-migración con `check --deploy`

**Salida esperada:**
```
============================================================
🔄 RENDER MIGRATION MANAGER
============================================================
✅ Database connection: OK

📋 Checking for pending migrations...
[ ] containers.0001_initial
[X] containers.0002_auto_20250101_1200

🚀 Applying migrations...
Running migrations:
  Applying containers.0001_initial... OK

✅ All migrations applied successfully!

🔍 Running system checks...
✅ System checks passed!

============================================================
✅ MIGRATION COMPLETE
============================================================
```

---

### 2. `render_maintenance` - Tareas de Mantenimiento

Ejecuta tareas de limpieza y optimización de la base de datos.

**Uso en Render.com (todas las tareas):**
```bash
python manage.py render_maintenance --all
```

**Tareas individuales:**
```bash
# Limpiar datos GPS antiguos (>30 días)
python manage.py render_maintenance --cleanup-old-data

# Limpiar sesiones expiradas
python manage.py render_maintenance --cleanup-sessions

# Optimizar base de datos (VACUUM en PostgreSQL)
python manage.py render_maintenance --optimize-db
```

**Características:**
- 🗑️ **cleanup-old-data**: Limpia ubicaciones GPS de conductores mayores a 30 días
- 🗑️ **cleanup-sessions**: Elimina sesiones expiradas de Django
- ⚡ **optimize-db**: Ejecuta VACUUM ANALYZE en PostgreSQL para optimización
- ✅ Manejo seguro con transacciones
- ✅ Logging detallado de cada operación

**Salida esperada:**
```
============================================================
🔧 RENDER MAINTENANCE MANAGER
============================================================

🗑️  Cleaning old GPS tracking data...
✅ Cleaned GPS data from 15 drivers (older than 30 days)

🗑️  Cleaning expired sessions...
✅ Expired sessions cleaned

⚡ Optimizing database...
Running VACUUM ANALYZE...
✅ Database optimized (VACUUM ANALYZE)

============================================================
✅ MAINTENANCE COMPLETE
============================================================
```

---

## 📅 Automatización en Render.com

### Opción 1: Cron Jobs en Render

Render.com soporta Cron Jobs. Agregar en `render.yaml`:

```yaml
services:
  - type: web
    name: soptraloc
    # ... configuración existente ...

  - type: cron
    name: soptraloc-maintenance
    env: python
    schedule: "0 2 * * *"  # Todos los días a las 2 AM
    buildCommand: pip install -r requirements.txt
    startCommand: python manage.py render_maintenance --all
```

### Opción 2: Ejecutar Manualmente desde Render Dashboard

1. Ir al dashboard de Render: https://dashboard.render.com
2. Seleccionar el servicio "soptraloc"
3. Ir a la pestaña "Shell" (si está disponible) o usar "Manual Deploy"
4. Durante el deploy, `build.sh` ejecutará automáticamente las migraciones

### Opción 3: Agregar al Build Script

Ya está incluido en `build.sh`:
```bash
# En build.sh
python manage.py render_migrate
```

---

## 🔧 Configuración en `build.sh`

El archivo `build.sh` ya está configurado para usar el nuevo comando:

```bash
#!/usr/bin/env bash
set -o errexit

echo "=========================================="
echo "🚀 SOPTRALOC TMS - BUILD"
echo "=========================================="

# 1. Actualizar pip
echo "📦 Actualizando pip..."
pip install --upgrade pip

# 2. Instalar dependencias
echo "📦 Instalando dependencias..."
pip install -r requirements.txt

# 3. Colectar archivos estáticos
echo "📁 Colectando archivos estáticos..."
python manage.py collectstatic --no-input

# 4. Ejecutar migraciones con logging
echo "🔄 Ejecutando migraciones..."
python manage.py render_migrate

# 5. Crear superusuario admin
echo "👤 Creando superusuario admin..."
python manage.py reset_admin --username=admin --password=1234

echo "=========================================="
echo "✅ Build completado exitosamente"
echo "=========================================="
```

---

## 🎯 Casos de Uso

### Caso 1: Deploy Inicial
```bash
# Render ejecuta automáticamente build.sh que incluye:
# - Migraciones con render_migrate
# - Creación de superusuario
```

### Caso 2: Nuevo Deploy con Migraciones
```bash
# 1. Hacer push al repositorio
git push origin main

# 2. Render detecta cambios y ejecuta build.sh
# 3. render_migrate aplica nuevas migraciones automáticamente
```

### Caso 3: Mantenimiento Mensual
```bash
# Ejecutar manualmente o programar con cron:
python manage.py render_maintenance --all
```

### Caso 4: Verificar Migraciones sin Aplicar
```bash
python manage.py render_migrate --dry-run
```

---

## 📊 Monitoreo y Logs

### Ver logs en Render:
1. Dashboard de Render → Servicio "soptraloc"
2. Pestaña "Logs"
3. Buscar por:
   - `RENDER MIGRATION MANAGER`
   - `MAINTENANCE MANAGER`

### Logs importantes:
- `✅ All migrations applied successfully!` - Migraciones OK
- `❌ Migration failed:` - Error en migración
- `✅ Cleaned GPS data from X drivers` - Limpieza exitosa

---

## 🚨 Troubleshooting

### Problema: Migraciones fallan
**Solución:**
```bash
# 1. Verificar con dry-run
python manage.py render_migrate --dry-run

# 2. Verificar logs en Render Dashboard
# 3. Revisar estado de migraciones:
python manage.py showmigrations
```

### Problema: Base de datos lenta
**Solución:**
```bash
# Ejecutar optimización
python manage.py render_maintenance --optimize-db
```

### Problema: Muchos datos GPS antiguos
**Solución:**
```bash
# Limpiar datos >30 días
python manage.py render_maintenance --cleanup-old-data
```

---

## 📝 Notas Importantes

1. **Seguridad**: Los comandos están diseñados para ser seguros en producción
2. **Transacciones**: Todas las operaciones de mantenimiento usan transacciones atómicas
3. **Logging**: Todos los comandos generan logs detallados
4. **Errores**: Los comandos retornan códigos de salida apropiados (0=éxito, 1=error)
5. **PostgreSQL**: La optimización de DB solo funciona con PostgreSQL

---

## 🎓 Referencias

- [Render Cron Jobs](https://render.com/docs/cronjobs)
- [Django Management Commands](https://docs.djangoproject.com/en/5.1/howto/custom-management-commands/)
- [PostgreSQL VACUUM](https://www.postgresql.org/docs/current/sql-vacuum.html)

---

**Generado por**: GitHub Copilot  
**Fecha**: 2025-10-14  
**Sistema**: SoptraLoc TMS v1.0.0
