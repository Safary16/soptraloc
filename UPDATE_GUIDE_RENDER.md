# 🔄 Guía de Actualización para Deploy Existente en Render

## ⚠️ IMPORTANTE: Ya tienes servicios en Render

Esta guía es para **ACTUALIZAR** tu deploy existente, NO para crear uno nuevo desde cero.

---

## 📊 Estado Actual de tu Deploy

Basándome en tu historial de commits, tu deploy actual en Render incluye:

### ✅ Lo que ya tienes funcionando:
- 🗺️ Mapbox API integrada (commit `aca5566`)
- 📍 Sistema de ubicaciones y disponibilidad (commit `7ab997f`)
- 🚦 Sistema de tráfico en tiempo real (commit `221637c`)
- 🚚 82 conductores cargados (commit `e49fe1f`)
- 📊 Panel de administración mejorado
- 🎯 Sistema base de asignaciones

### 🆕 Lo que acabamos de agregar:
- ✅ Integración Mapbox mejorada (70% prioridad en predicción)
- ✅ Campos `traffic_level_at_assignment` y `mapbox_data` en Assignment
- ✅ Migraciones 0011 y 0012 (traffic fields)
- ✅ Sistema de optimización (`optimize_system.py`)
- ✅ Scripts de servicios (`start_services.sh`, `stop_services.sh`)
- ✅ Suite de tests completa (`test_system.py`)
- ✅ Documentación exhaustiva (8 archivos)

---

## 🚀 Estrategia de Actualización Segura

### Opción 1: Actualización Automática (RECOMENDADA) ⭐

Ya que tienes `autoDeploy: true` en tu Web Service, **Render desplegará automáticamente** al hacer push:

```bash
# Los cambios ya están en GitHub (commit a4a5821)
# Render los detectará y desplegará automáticamente
```

**Lo que pasará:**
1. ✅ Render detecta el push a `main`
2. ✅ Ejecuta build: `pip install -r requirements.txt && collectstatic && migrate`
3. ✅ Aplica migraciones 0011 y 0012 automáticamente
4. ✅ Reinicia el servicio con código actualizado
5. ✅ Celery Worker y Beat también se actualizarán

**Tiempo estimado:** 5-8 minutos

---

### Opción 2: Actualización Manual Controlada

Si prefieres más control:

#### Paso 1: Verificar en Render Dashboard

Ve a https://dashboard.render.com/ y verifica:

1. **Web Service (`soptraloc-web`)**:
   - ¿Está en estado "Live"? ✅
   - ¿Última build exitosa?
   - ¿Auto-deploy habilitado?

2. **Celery Worker** (si existe):
   - ¿Está corriendo?
   - ¿Redis conectado?

3. **Database**:
   - ¿Qué plan tienes? (Free/Paid)
   - ¿Cuántas migraciones aplicadas?

#### Paso 2: Verificar Variables de Entorno

Asegúrate de que tienes configuradas:

```bash
SECRET_KEY=<tu-key-actual>  # ⚠️ NO cambies la que ya tienes
DEBUG=False
MAPBOX_API_KEY=pk.eyJ1Ijoic2FmYXJ5MTYiLCJhIjoiY200cTN6MGY5MGlqMDJpb2o5a3RvYTh2dSJ9.B0A7Nw0nDCXzjUBBN0i4aQ
DATABASE_URL=<auto-configurado>
REDIS_URL=<si-tienes-redis>
TIME_ZONE=America/Santiago
```

#### Paso 3: Deploy Manual

Si auto-deploy NO está habilitado:

1. Ve a tu Web Service en Render
2. Clic en "Manual Deploy"
3. Selecciona branch `main`
4. Clic en "Deploy"

---

## 🔍 Verificación Post-Actualización

### 1. Verificar Migraciones

En Render Shell (`soptraloc-web` → Shell):

```bash
cd soptraloc_system
python manage.py showmigrations drivers
```

Deberías ver:
```
[X] 0011_add_traffic_info_to_assignment
[X] 0012_add_traffic_fields
```

### 2. Verificar Mapbox API

```bash
cd soptraloc_system
python -c "
from apps.routing.mapbox_service import mapbox_service
result = mapbox_service.get_travel_time_with_traffic('CCTI', 'CD_PENON', None)
print(f'Mapbox funcionando: {result.get(\"source\") == \"mapbox_api\"}')
print(f'Duración con tráfico: {result.get(\"duration_in_traffic_minutes\")} min')
"
```

### 3. Ejecutar Suite de Tests

```bash
cd soptraloc_system
python test_system.py
```

Deberías ver: `28/30 tests passed (93.3%)`

### 4. Verificar Campos Nuevos

En Django Admin:
- Ve a una Asignación existente
- Verifica que aparezcan:
  - `Traffic level at assignment` (campo nuevo)
  - `Mapbox data` (campo nuevo)

---

## ⚠️ Precauciones Importantes

### 🛑 NO HAGAS ESTO:

1. ❌ **NO apliques `render.yaml` si ya tienes servicios creados manualmente**
   - `render.yaml` es para crear servicios NUEVOS
   - Si aplicas el Blueprint, Render intentará crear servicios duplicados
   - Resultado: Nombres conflictivos y servicios duplicados

2. ❌ **NO elimines servicios existentes para "empezar de nuevo"**
   - Perderás tu base de datos
   - Perderás tus 82 conductores
   - Perderás todas las asignaciones

3. ❌ **NO cambies SECRET_KEY en producción**
   - Invalidará todas las sesiones
   - Puede romper tokens y cookies

### ✅ SÍ PUEDES HACER:

1. ✅ **Dejar que auto-deploy actualice el código**
   - Es seguro
   - Las migraciones se aplican automáticamente
   - Los datos se mantienen

2. ✅ **Agregar nuevas variables de entorno**
   - `MAPBOX_API_KEY` (si no la tienes)
   - Cualquier variable que falte

3. ✅ **Actualizar comandos de build/start**
   - Si necesitas cambiar el comando de Gunicorn
   - Si quieres ajustar workers

---

## 📋 Checklist de Actualización

```
□ Los commits están en GitHub (main branch)
□ Auto-deploy está habilitado en Render
□ Variables de entorno verificadas
□ Backup de DB hecho (opcional pero recomendado)
□ Esperé a que el deploy termine (~5-8 min)
□ Verifiqué que el servicio está "Live"
□ Verifiqué migraciones con showmigrations
□ Probé Mapbox API desde Shell
□ Ejecuté test_system.py
□ Verifiqué que el admin funciona
□ Verifiqué que las asignaciones tienen los campos nuevos
```

---

## 🆕 ¿Qué pasa con `render.yaml`?

### Si NO tienes Redis ni Celery en Render:

Puedes usar `render.yaml` para **agregar solo** esos servicios:

1. **Opción A: Agregar servicios individualmente en Dashboard**
   - Más control
   - No afecta servicios existentes
   - Recomendado si ya tienes Web Service

2. **Opción B: Editar render.yaml**
   - Elimina la sección de Web Service
   - Deja solo Redis, Celery Worker, Celery Beat
   - Aplica el Blueprint

### Si YA tienes todos los servicios:

**Ignora `render.yaml` completamente**. Ya no lo necesitas.

Los archivos útiles para ti son:
- ✅ `optimize_system.py` - Úsalo para mantenimiento
- ✅ `test_system.py` - Úsalo para verificar el sistema
- ✅ `start_services.sh` / `stop_services.sh` - Para desarrollo local
- ✅ Documentación (DIAGNOSTICO_MAPBOX.md, etc.)

---

## 🔧 Comandos Útiles Post-Actualización

### Ver logs en tiempo real:
```bash
# En Render Dashboard → tu servicio → Logs
# O desde CLI si tienes render CLI instalado:
render logs soptraloc-web
```

### Ejecutar comando en producción:
```bash
# En Render Dashboard → Shell
cd soptraloc_system
python manage.py <comando>
```

### Ver estado de Celery:
```bash
cd soptraloc_system
celery -A config inspect active
celery -A config inspect stats
```

---

## 📊 Monitoreo Post-Actualización

### Primeras 24 horas:

1. **Monitorea logs de errores:**
   ```bash
   # En Render logs, busca:
   ERROR
   CRITICAL
   Exception
   ```

2. **Verifica métricas de Mapbox:**
   - Ve a https://account.mapbox.com/
   - Revisa "API Usage"
   - Asegúrate de estar dentro de cuota (200k requests/mes gratis)

3. **Verifica asignaciones:**
   - En Django Admin → Assignments
   - Verifica que nuevas asignaciones tengan `traffic_level`
   - Verifica que `mapbox_data` se llene correctamente

---

## 🚨 Rollback (si algo sale mal)

Si el deploy falla o algo se rompe:

### Opción 1: Rollback en Render Dashboard

1. Ve a tu Web Service
2. Clic en "Rollback" (aparece después de un deploy)
3. Selecciona el deploy anterior
4. Confirma

### Opción 2: Rollback manual con Git

```bash
# Volver al commit anterior
git revert HEAD
git push origin main

# O volver a un commit específico
git reset --hard <commit-hash-anterior>
git push --force origin main
```

**Commits importantes para rollback:**
- `9d2ad2e` - Última versión antes de Mapbox upgrade
- `7ab997f` - Sistema de ubicaciones estable
- `e49fe1f` - Con 82 conductores cargados

---

## ✅ Resumen: ¿Qué Debes Hacer?

### SI tienes auto-deploy habilitado (recomendado):

**Respuesta corta:** Nada. Espera 5-8 minutos y verifica que todo funcione.

**Pasos:**
1. Espera a que Render termine el deploy automático
2. Ve a tu app y verifica que funciona
3. Ejecuta `test_system.py` desde Shell
4. Listo ✅

### SI NO tienes auto-deploy:

1. Ve a Render Dashboard
2. Clic en "Manual Deploy" → "Deploy latest commit"
3. Espera 5-8 minutos
4. Verifica que funciona
5. Listo ✅

### SI quieres agregar Redis/Celery (y no los tienes):

1. Lee la sección "¿Qué pasa con render.yaml?"
2. Decide si agregas servicios manualmente o con Blueprint
3. Configura variables de entorno
4. Verifica conexión

---

## 📞 Soporte

Si algo sale mal:

1. **Revisa logs en Render:** Dashboard → Logs
2. **Ejecuta diagnóstico:** `python test_system.py` en Shell
3. **Verifica migraciones:** `python manage.py showmigrations`
4. **Revisa variables:** Dashboard → Environment
5. **Consulta docs:** DIAGNOSTICO_MAPBOX.md, SYSTEM_STATUS.md

---

**Última actualización:** Octubre 9, 2025  
**Commit base:** a4a5821 (docs: Agregar DEPLOY_GUIDE.md)  
**Cambios principales:** Mapbox upgrade, traffic fields, optimización
