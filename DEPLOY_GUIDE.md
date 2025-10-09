# 🚀 Guía Rápida de Deploy en Render

## ✅ TODO YA ESTÁ CONFIGURADO Y LISTO

Este repositorio incluye todo lo necesario para hacer deploy en Render **con solo 3 clics**:

- ✅ `render.yaml` - Blueprint completo de infraestructura
- ✅ `.env.render` - Variables de entorno (referencia)
- ✅ `auto_deploy_render.sh` - Script de automatización
- ✅ Endpoint `/health/` configurado
- ✅ Migraciones automáticas
- ✅ Collectstatic automático
- ✅ Todos los servicios pre-configurados

---

## 📋 Pasos para Deploy (15 minutos)

### 1️⃣ Ve a Render Dashboard

👉 **https://dashboard.render.com/**

### 2️⃣ Crea un Blueprint (3 clics)

1. Clic en **"New +"** (esquina superior derecha)
2. Selecciona **"Blueprint"**
3. Conecta tu cuenta de GitHub (si no lo has hecho)
4. Selecciona el repositorio: **`Safary16/soptraloc`**
5. Render detectará automáticamente `render.yaml`
6. Clic en **"Apply"**

🎉 Render creará automáticamente:
- `soptraloc-db` (PostgreSQL)
- `soptraloc-redis` (Redis)
- `soptraloc-web` (Django Web)
- `soptraloc-celery-worker` (Background Worker)
- `soptraloc-celery-beat` (Scheduler)

### 3️⃣ Configura SECRET_KEY (1 minuto)

Mientras se construyen los servicios (~5 min):

1. Ve a **`soptraloc-web`** en tu Dashboard
2. Clic en **"Environment"** (menú izquierdo)
3. Busca la variable **`SECRET_KEY`**
4. Clic en **"Edit"** y pega este valor:

```
FmNTEAe3_jfryE4BncosvG7fxzC6Tj6cgLkqLH-KLddQQfn0ZfDVEtUJdfgkzAwyvJg
```

5. Clic en **"Save Changes"**

> ⚠️ **IMPORTANTE**: Esta SECRET_KEY también está guardada en `.env.render` (NO commitear este archivo)

### 4️⃣ Espera la Construcción (5-10 min)

Verás en tiempo real:

- ⏳ `soptraloc-db` → 🟢 Live (1-2 min)
- ⏳ `soptraloc-redis` → 🟢 Live (1-2 min)  
- ⏳ `soptraloc-web` → 🟢 Live (5-8 min) ← **El más importante**
- ⏳ `soptraloc-celery-worker` → 🟢 Live (3-5 min)
- ⏳ `soptraloc-celery-beat` → 🟢 Live (3-5 min)

### 5️⃣ Crea Superusuario (1 minuto)

Una vez que `soptraloc-web` esté 🟢 **Live**:

1. Clic en **`soptraloc-web`**
2. Clic en **"Shell"** (menú izquierdo)
3. Ejecuta:

```bash
cd soptraloc_system
python manage.py createsuperuser
```

4. Ingresa tus credenciales:
   - Username: `admin` (o el que prefieras)
   - Email: `tu@email.com`
   - Password: (tu contraseña segura)

### 6️⃣ (Opcional) Carga Datos de Prueba

En el mismo Shell:

```bash
python manage.py quick_test_data
```

Esto crea:
- ✅ 5 conductores de prueba
- ✅ 20 contenedores
- ✅ 7 asignaciones
- ✅ 10 rutas en TimeMatrix

### 7️⃣ Verifica el Sistema

```bash
python test_system.py
```

Deberías ver:
- ✅ 28/30 tests passed (93.3%)
- ✅ Mapbox API funcional
- ✅ Database conectada
- ✅ Redis funcionando
- ✅ Celery operativo

### 8️⃣ Accede a tu Aplicación 🎉

1. Ve a **`soptraloc-web`** → **URL** (parte superior)
2. Copia la URL (ejemplo: `https://soptraloc-web.onrender.com`)
3. Accede al admin:

👉 **https://soptraloc-web.onrender.com/admin/**

---

## 🎯 Verificación Rápida

### Health Check
```
https://tu-app.onrender.com/health/
```
Debe mostrar: `{"status": "healthy"}`

### API Info
```
https://tu-app.onrender.com/api/info/
```
Debe mostrar: JSON con información del sistema

---

## 📊 Servicios Configurados

| Servicio | Tipo | Plan | Región |
|----------|------|------|--------|
| soptraloc-db | PostgreSQL | Starter (Free 90 días) | Oregon |
| soptraloc-redis | Redis | Starter (25MB, Free) | Oregon |
| soptraloc-web | Web Service | Starter (750 hrs/mes) | Oregon |
| soptraloc-celery-worker | Background Worker | Starter (750 hrs/mes) | Oregon |
| soptraloc-celery-beat | Background Worker | Starter (750 hrs/mes) | Oregon |

**Total Free Tier**: $0/mes por 90 días  
**Total después**: ~$33/mes

> 💡 Los servicios free se suspenden después de 15 min de inactividad y se reactivan automáticamente.

---

## 🔧 Variables de Entorno Auto-configuradas

El archivo `render.yaml` configura automáticamente:

- ✅ `DATABASE_URL` (desde PostgreSQL service)
- ✅ `REDIS_URL` (desde Redis service)
- ✅ `CELERY_BROKER_URL` (desde Redis)
- ✅ `CELERY_RESULT_BACKEND` (desde Redis)
- ✅ `MAPBOX_API_KEY` (ya configurado)
- ✅ `TIME_ZONE=America/Santiago`
- ✅ `DEBUG=False`
- ✅ `ALLOWED_HOSTS` (auto-generado)

**Solo necesitas configurar manualmente:**
- ⚠️ `SECRET_KEY` (ver paso 3)

---

## 🔥 Troubleshooting

### ❌ Build failed
- Ve a **Logs** del servicio
- Busca el error específico
- Probablemente falta una dependencia en `requirements.txt`

### ❌ Health check failed
- Verifica que `SECRET_KEY` esté configurada
- Verifica que `DATABASE_URL` esté conectada
- Revisa logs del servicio

### ❌ Celery no se conecta
- Espera que Redis esté 🟢 **Live**
- Verifica `REDIS_URL` en Environment
- Revisa logs de celery-worker

### ❌ Static files not found
- El build command incluye `collectstatic`
- Verifica logs del build
- Ejecuta manualmente si es necesario

---

## 📞 Recursos Adicionales

- 📄 [RENDER_DEPLOYMENT_CHECKLIST.md](RENDER_DEPLOYMENT_CHECKLIST.md) - Checklist completo
- 📄 [DEPLOYMENT_SUCCESS_REPORT.md](DEPLOYMENT_SUCCESS_REPORT.md) - Reporte detallado
- 📄 [SYSTEM_STATUS.md](soptraloc_system/SYSTEM_STATUS.md) - Estado del sistema
- 📄 [DIAGNOSTICO_MAPBOX.md](soptraloc_system/DIAGNOSTICO_MAPBOX.md) - Documentación Mapbox

### Enlaces Útiles

- 🔗 [Dashboard Render](https://dashboard.render.com/)
- 🔗 [Documentación Render](https://render.com/docs)
- 🔗 [Repositorio GitHub](https://github.com/Safary16/soptraloc)

---

## 🎉 ¡Listo para Producción!

Este sistema incluye:

✅ **Integración Mapbox completa** (tráfico en tiempo real)  
✅ **Asignación inteligente de conductores** (basada en tráfico)  
✅ **Detección automática de conflictos** de horario  
✅ **Celery Workers** para procesamiento en background  
✅ **Celery Beat** para tareas programadas  
✅ **Redis** como message broker y cache  
✅ **PostgreSQL** como base de datos principal  
✅ **93.3% de tests pasando** (28/30)  

---

## 💡 Tips

1. **Guarda el archivo `.env.render`** en un lugar seguro (contiene tu SECRET_KEY)
2. **No commitees `.env.render`** (ya está en .gitignore)
3. **Auto-deploy está habilitado**: Cada push a `main` desplegará automáticamente
4. **Monitorea los logs** en Render Dashboard para detectar problemas
5. **Los servicios free se duermen** después de 15 min sin uso (es normal)

---

## 🚀 ¿Necesitas ayuda?

1. Revisa los logs en Render Dashboard
2. Consulta [RENDER_DEPLOYMENT_CHECKLIST.md](RENDER_DEPLOYMENT_CHECKLIST.md)
3. Ejecuta `python test_system.py` en Render Shell
4. Verifica las variables de entorno

---

**Fecha de última actualización**: Octubre 9, 2025  
**Versión del sistema**: Django 5.2.6 + Celery 5.4.0 + Mapbox API  
**Estado**: ✅ Listo para producción
