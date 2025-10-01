# 🔄 Actualización del Servicio Existente en Render

## 🎯 Objetivo
Actualizar el servicio existente en `https://soptraloc.onrender.com/` con las nuevas funcionalidades:
- ⏰ Reloj en tiempo real
- 🚨 Alertas de proximidad
- 📊 Dashboard optimizado
- 🔧 Código refactorizado

---

## ⚡ Método 1: Auto-Deploy desde GitHub (RECOMENDADO)

### Render detecta automáticamente los cambios en GitHub

**Paso 1: Verificar Auto-Deploy está activado**

1. Ir a: https://dashboard.render.com/
2. Click en servicio: **`soptraloc`**
3. Ir a **Settings** → **Build & Deploy**
4. Verificar: **Auto-Deploy** = `Yes` (branch: `main`)

**Paso 2: El deploy se hace automáticamente**

✅ Ya hiciste `git push origin main`  
✅ Render detectó el cambio  
✅ Iniciará el build automáticamente  

**Paso 3: Monitorear el deployment**

En el dashboard verás:

```
🔨 Building...
   - Installing dependencies
   - Running ./build.sh
   - Collecting static files

🚀 Deploying...
   - Running migrations
   - Starting gunicorn

✅ Live (en ~5-7 minutos)
```

---

## 🔧 Método 2: Manual Deploy

Si Auto-Deploy está desactivado:

### Paso 1: Ir al Dashboard de Render

```
https://dashboard.render.com/
```

### Paso 2: Seleccionar el Servicio

Click en: **`soptraloc`**

### Paso 3: Manual Deploy

1. Click en **"Manual Deploy"** (botón arriba a la derecha)
2. Seleccionar: **"Deploy latest commit"**
3. Click en **"Deploy"**

### Paso 4: Monitorear Logs

Ver en tiempo real:
- Click en **"Logs"** tab
- Verás el progreso del build y deploy

---

## 📊 Verificación Post-Deploy

### 1. Health Check (Automático)

Render hace health check automático:
```
GET https://soptraloc.onrender.com/health/
Expected: 200 OK
```

### 2. Verificar Nuevas Funcionalidades

#### Reloj en Tiempo Real
```bash
# Abrir en navegador
open https://soptraloc.onrender.com/dashboard/

# Verificar:
✅ Reloj en navbar (HH:MM:SS)
✅ Fecha actual visible
✅ Se actualiza cada segundo
```

#### Alertas de Proximidad
```bash
# Endpoint de urgentes
curl https://soptraloc.onrender.com/api/v1/containers/urgent/

# Respuesta esperada:
{
  "urgent_containers": [...],
  "total_urgent": 0,
  "critical_count": 0,
  "high_count": 0,
  "medium_count": 0
}
```

#### Dashboard Optimizado
```bash
# Verificar en navegador:
✅ Contenedores con badges de urgencia
✅ Filas destacadas si hay urgentes
✅ Badge en navbar si hay alertas
✅ Modal de urgentes funcional
```

### 3. Verificar Static Files

```bash
# CSS cargado
open https://soptraloc.onrender.com/static/css/

# JavaScript cargado
open https://soptraloc.onrender.com/static/js/realtime-clock.js
```

### 4. API Endpoints

```bash
# Swagger docs
open https://soptraloc.onrender.com/swagger/

# API info
curl https://soptraloc.onrender.com/api/info/
```

---

## 🔐 Configuración de Variables de Entorno

### Variables Existentes (Mantener)

No tocar estas variables (ya existen):

```bash
SECRET_KEY=<mantener el existente>
DATABASE_URL=<mantener el existente>
```

### Variables Nuevas (Agregar si no existen)

En Dashboard → **`soptraloc`** → **Environment**:

Agregar SOLO si no existen:

```bash
# Timezone
TZ=America/Santiago

# Version
SYSTEM_VERSION=v2.0-optimized

# Django Settings
DJANGO_SETTINGS_MODULE=config.settings_production

# Hostname
RENDER_EXTERNAL_HOSTNAME=soptraloc.onrender.com
```

**Nota**: Si ya existen, NO las cambies. Render las preserva entre deploys.

---

## 🔄 Proceso de Actualización (Detalles Técnicos)

### Build Process

```bash
# 1. Git pull
git pull origin main

# 2. Install dependencies
pip install -r requirements.txt

# 3. Collect static files
cd soptraloc_system
python manage.py collectstatic --noinput
```

### Pre-Deploy Process

```bash
# Solo migraciones (NO resetea datos)
python manage.py migrate --settings=config.settings_production

# ⚠️ NO ejecuta reset_test_data
# ⚠️ Conserva todos los datos existentes
```

### Start Process

```bash
# Gunicorn con configuración optimizada
cd soptraloc_system
gunicorn --bind=0.0.0.0:$PORT \
         --timeout 600 \
         --workers 2 \
         --threads 4 \
         config.wsgi:application
```

---

## 🛡️ Seguridad de Datos

### ✅ Datos Preservados

El deployment NO afectará:
- ✅ Contenedores existentes
- ✅ Conductores registrados
- ✅ Asignaciones activas
- ✅ Usuarios del sistema
- ✅ Configuraciones

### ⚠️ Solo se Actualiza

- Código fuente (nuevas funcionalidades)
- Static files (CSS/JS)
- Migraciones de base de datos (si hay nuevas)

---

## 📈 Monitoreo del Deployment

### Logs en Tiempo Real

```bash
# En Dashboard → soptraloc → Logs

🔨 Build started...
📦 Installing dependencies from requirements.txt
   - Django==5.2.6 ✓
   - djangorestframework==3.16.1 ✓
   - gunicorn==23.0.0 ✓
   - psycopg2-binary==2.9.9 ✓
   - pandas==2.2.3 ✓
   - openpyxl==3.1.2 ✓
   - (todas las demás) ✓

📁 Collecting static files
   - 156 static files copied ✓

🚀 Pre-deploy commands
   - Running migrations... ✓
   - 0 new migrations applied ✓

✅ Build complete

🌐 Starting service...
   - Gunicorn workers: 2 ✓
   - Port: 10000 ✓
   - Timeout: 600s ✓

✅ Live at https://soptraloc.onrender.com
```

### Métricas Disponibles

Dashboard → **Metrics**:
- CPU Usage
- Memory Usage
- Response Time
- Request Count
- Error Rate

---

## 🐛 Troubleshooting

### Error: "Build Failed"

**Causa**: Error en requirements.txt o build.sh

**Solución**:
```bash
# Ver logs completos
Dashboard → Logs → Ver línea exacta del error

# Comunes:
- Dependencia faltante → Agregar a requirements.txt
- Script no ejecutable → chmod +x build.sh
```

### Error: "Health Check Failed"

**Causa**: Aplicación no responde en /health/

**Solución**:
```bash
# Verificar que /health/ existe
# Verificar logs de gunicorn
# Verificar DATABASE_URL está configurado
```

### Error: "Static Files 404"

**Causa**: Collectstatic no ejecutado

**Solución**:
```bash
# Manual re-build
Dashboard → Manual Deploy → Clear build cache
```

### Cambios no se Reflejan

**Causa**: Caché de navegador

**Solución**:
```bash
# Hard refresh en navegador
Ctrl + Shift + R (Windows/Linux)
Cmd + Shift + R (Mac)

# O borrar caché del navegador
```

---

## ⏱️ Tiempos Estimados

| Proceso | Duración |
|---------|----------|
| Build | 2-3 minutos |
| Deploy | 1-2 minutos |
| Health Check | 30 segundos |
| **Total** | **~5 minutos** |

---

## ✅ Checklist Post-Deploy

Después del deployment exitoso:

- [ ] URL responde: https://soptraloc.onrender.com/
- [ ] Health check OK: /health/
- [ ] Dashboard carga: /dashboard/
- [ ] Reloj visible en navbar
- [ ] Reloj actualizándose cada segundo
- [ ] Admin accesible: /admin/
- [ ] API funcionando: /api/v1/
- [ ] Swagger docs: /swagger/
- [ ] Static files cargando (CSS/JS)
- [ ] Sin errores en logs
- [ ] Datos existentes intactos

---

## 🔄 Rollback (Si es Necesario)

Si algo sale mal:

### Opción 1: Rollback Automático

1. Dashboard → **`soptraloc`**
2. Click en **"Events"**
3. Buscar último deployment exitoso
4. Click en **"Rollback to this deploy"**

### Opción 2: Revert en Git

```bash
# Ver commits recientes
git log --oneline -5

# Revertir al commit anterior
git revert HEAD

# Push
git push origin main

# Render re-deployará automáticamente
```

---

## 📞 Soporte

Si tienes problemas:

1. **Ver logs**: Dashboard → Logs
2. **Verificar status**: Dashboard → Events
3. **Contactar Render**: support@render.com
4. **Community**: https://community.render.com/

---

## 🎯 Resultado Final

Después del deployment exitoso tendrás:

✅ **Sistema actualizado** a v2.0-optimized  
✅ **Reloj en tiempo real** funcionando  
✅ **Alertas de proximidad** activas  
✅ **Dashboard optimizado** con priorización  
✅ **Código refactorizado** (~400 líneas menos)  
✅ **Datos existentes** preservados  
✅ **Sin downtime** (deploy zero-downtime)  

---

## 🚀 Siguiente Deploy

Para futuros deployments:

```bash
# 1. Hacer cambios localmente
git add .
git commit -m "feat: Nueva funcionalidad"

# 2. Push a GitHub
git push origin main

# 3. Render auto-deploya
# (monitorear en dashboard)
```

**¡Simple como eso!** 🎉

---

**Última actualización**: Octubre 2025  
**Versión objetivo**: v2.0-optimized  
**Tiempo estimado**: 5 minutos  
**Riesgo**: Bajo (datos preservados)
