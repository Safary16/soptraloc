# 🚀 Guía de Deployment en Render.com

## 📋 Requisitos Previos

- ✅ Cuenta en [Render.com](https://render.com) (gratuita)
- ✅ Repositorio GitHub actualizado
- ✅ Código optimizado y testeado localmente

---

## 🔧 Preparación del Proyecto

### 1. Archivos de Configuración Necesarios

El proyecto ya incluye todos los archivos necesarios:

```
soptraloc/
├── render.yaml              # Configuración de Render
├── build.sh                 # Script de build
├── requirements.txt         # Dependencias Python
└── soptraloc_system/
    └── config/
        ├── settings_production.py  # Settings de producción
        └── wsgi.py                 # WSGI application
```

### 2. Variables de Entorno Automáticas

Render configurará automáticamente desde `render.yaml`:

- `SECRET_KEY` - Generada automáticamente
- `DATABASE_URL` - Conectada a PostgreSQL
- `ALLOWED_HOSTS` - Configurado para *.onrender.com
- `DEBUG` - False en producción
- `TZ` - America/Santiago

---

## 🚀 Pasos de Deployment

### Opción 1: Deployment Automático (Recomendado)

#### 1. **Conectar Repositorio GitHub**

1. Ir a [Render Dashboard](https://dashboard.render.com/)
2. Click en **"New +"** → **"Blueprint"**
3. Conectar tu cuenta de GitHub
4. Seleccionar repositorio: `Safary16/soptraloc`
5. Render detectará automáticamente `render.yaml`

#### 2. **Aprobar Configuración**

Render mostrará:
- ✅ Web Service: `soptraloc-production`
- ✅ PostgreSQL Database: `soptraloc-production-db`

Click en **"Apply"**

#### 3. **Monitorear Build**

El proceso tomará ~5-10 minutos:

```bash
# Paso 1: Instalación de dependencias
📦 Installing dependencies...
✅ Dependencies installed

# Paso 2: Collectstatic
📁 Collecting static files...
✅ Static files collected

# Paso 3: Migraciones
🗄️ Running migrations...
✅ Database migrated

# Paso 4: Datos iniciales
🌱 Setting up initial data...
✅ 10 test containers created

# Paso 5: Inicio del servidor
🚀 Starting gunicorn...
✅ Server running on port 10000
```

#### 4. **Acceder a la Aplicación**

URL automática: `https://soptraloc-production.onrender.com`

---

### Opción 2: Deployment Manual

#### 1. **Crear Web Service**

1. Dashboard → **"New +"** → **"Web Service"**
2. Conectar GitHub → Seleccionar repo `soptraloc`
3. Configurar:
   - **Name**: `soptraloc-production`
   - **Region**: Oregon (US West)
   - **Branch**: `main`
   - **Runtime**: Python 3
   - **Build Command**: `./build.sh`
   - **Start Command**: 
     ```bash
     cd soptraloc_system && gunicorn --bind=0.0.0.0:$PORT --timeout 600 --workers 2 config.wsgi:application
     ```

#### 2. **Crear Base de Datos PostgreSQL**

1. Dashboard → **"New +"** → **"PostgreSQL"**
2. Configurar:
   - **Name**: `soptraloc-production-db`
   - **Database**: `soptraloc_prod`
   - **User**: `soptraloc_prod_user`
   - **Plan**: Free

#### 3. **Conectar Database a Web Service**

1. En Web Service → **Environment**
2. Agregar variable:
   ```
   DATABASE_URL = [internal connection string from database]
   ```

#### 4. **Agregar Variables de Entorno**

En Web Service → **Environment**:

```bash
DEBUG=False
DJANGO_SETTINGS_MODULE=config.settings_production
SECRET_KEY=[generate random key]
ALLOWED_HOSTS=*.onrender.com,localhost
RENDER_EXTERNAL_HOSTNAME=soptraloc-production.onrender.com
TZ=America/Santiago
```

#### 5. **Deploy Manual**

Click en **"Manual Deploy"** → **"Deploy latest commit"**

---

## 🔍 Verificación Post-Deployment

### 1. **Health Check**

```bash
curl https://soptraloc-production.onrender.com/health/
```

Respuesta esperada:
```json
{
  "status": "healthy",
  "timestamp": "2025-10-01T12:00:00Z"
}
```

### 2. **API Info**

```bash
curl https://soptraloc-production.onrender.com/api/info/
```

Respuesta esperada:
```json
{
  "system": "SOPTRALOC",
  "version": "v2.0-optimized",
  "environment": "production"
}
```

### 3. **Admin Panel**

Ir a: `https://soptraloc-production.onrender.com/admin/`

- Usuario: `admin`
- Password: `admin123` (cambiar en producción)

### 4. **Dashboard**

Ir a: `https://soptraloc-production.onrender.com/dashboard/`

Verificar:
- ✅ Reloj en tiempo real funcionando
- ✅ 10 contenedores cargados
- ✅ Alertas de proximidad activas
- ✅ Estilos CSS aplicados correctamente

---

## 📊 Características en Producción

### Sistema Completo Funcional

#### 1. **Reloj en Tiempo Real**
- Visible en navbar de todas las páginas
- Actualización cada segundo
- Timezone: America/Santiago

#### 2. **Alertas de Proximidad**
- Detección automática de contenedores < 2h
- 3 niveles de urgencia (crítico/alto/medio)
- Badge con contador en navbar
- Modal interactivo

#### 3. **Dashboard Optimizado**
- 10 contenedores de prueba
- Ordenamiento por urgencia
- Filas destacadas según prioridad
- Import/Export Excel

#### 4. **API REST**
- Endpoint: `/api/v1/containers/urgent/`
- Swagger docs: `/swagger/`
- ReDoc: `/redoc/`

#### 5. **Gestión de Conductores**
- Pase de lista
- Asignaciones
- Alertas operativas

---

## 🔧 Configuración Adicional (Opcional)

### 1. **Dominio Personalizado**

En Render Web Service → **Settings** → **Custom Domain**:

```
soptraloc.tudominio.com
```

Agregar DNS CNAME:
```
CNAME: soptraloc
Target: soptraloc-production.onrender.com
```

### 2. **Variables de Entorno Adicionales**

```bash
# Email (para notificaciones futuras)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=tu-email@gmail.com
EMAIL_HOST_PASSWORD=tu-app-password

# Sentry (para monitoreo de errores)
SENTRY_DSN=https://your-sentry-dsn

# Redis (para caché futuro)
REDIS_URL=redis://your-redis-url
```

### 3. **Escalado (Plan Paid)**

Si necesitas más recursos:

**Starter Plan** ($7/mes):
- 512 MB RAM → 2 GB RAM
- Shared CPU → Dedicated CPU
- Sin sleep automático

**Professional Plan** ($25/mes):
- 4 GB RAM
- 2 vCPU dedicados
- Autoscaling

---

## 🐛 Troubleshooting

### Error: "Application failed to start"

**Causa**: Falta DATABASE_URL

**Solución**:
```bash
# Verificar en Environment que DATABASE_URL existe
# Si no existe, conectar manualmente la database
```

### Error: "Static files not loading"

**Causa**: STATIC_ROOT no configurado

**Solución**:
```bash
# Re-run build
render deploy --service soptraloc-production
```

### Error: "Database connection refused"

**Causa**: Database no está creada o no está conectada

**Solución**:
1. Verificar que PostgreSQL database existe
2. Verificar DATABASE_URL en Environment
3. Re-deploy

### Error: "ModuleNotFoundError"

**Causa**: Falta dependencia en requirements.txt

**Solución**:
```bash
# Agregar dependencia a requirements.txt
pip freeze > requirements.txt
git commit -am "Add missing dependency"
git push
```

### Logs en Tiempo Real

```bash
# Ver logs del servicio
render logs --service soptraloc-production --tail
```

---

## 📈 Monitoreo

### Render Dashboard

Métricas automáticas disponibles:

- 📊 **CPU Usage**
- 💾 **Memory Usage**
- 🌐 **Request Count**
- ⚡ **Response Time**
- 🔴 **Error Rate**

### Health Checks

Render ejecuta health checks automáticos cada 30s:

```
GET /health/
Timeout: 5 seconds
Expected: 200 OK
```

---

## 🔄 Actualizaciones

### Deployment Automático

Con cada push a `main`:

```bash
git add .
git commit -m "feat: Nueva funcionalidad"
git push origin main

# Render detecta el push y re-deploya automáticamente
```

### Deployment Manual

En Render Dashboard:

1. Click en servicio `soptraloc-production`
2. **Manual Deploy** → **Deploy latest commit**
3. Monitorear logs en tiempo real

### Rollback

Si algo sale mal:

1. Dashboard → **Events**
2. Seleccionar deployment anterior exitoso
3. Click en **"Rollback to this deploy"**

---

## ✅ Checklist Final

Antes de considerar el deployment completo:

- [ ] URL pública funcional
- [ ] Health check retorna 200
- [ ] Admin panel accesible
- [ ] Dashboard carga correctamente
- [ ] Reloj en tiempo real funcionando
- [ ] Alertas de proximidad activas
- [ ] API endpoints respondiendo
- [ ] Swagger docs accesible
- [ ] Static files cargando (CSS/JS)
- [ ] Database con datos iniciales
- [ ] Logs sin errores críticos

---

## 🎯 URLs de Producción

Una vez deployado:

- **Home**: `https://soptraloc-production.onrender.com/`
- **Dashboard**: `https://soptraloc-production.onrender.com/dashboard/`
- **Admin**: `https://soptraloc-production.onrender.com/admin/`
- **API Root**: `https://soptraloc-production.onrender.com/api/v1/`
- **Swagger**: `https://soptraloc-production.onrender.com/swagger/`
- **ReDoc**: `https://soptraloc-production.onrender.com/redoc/`
- **Health**: `https://soptraloc-production.onrender.com/health/`

---

## 🎓 Próximos Pasos

Después del deployment exitoso:

1. **Cambiar credenciales de admin**
   ```bash
   python manage.py changepassword admin
   ```

2. **Cargar datos reales**
   - Subir manifiestos de nave
   - Importar liberaciones
   - Aplicar programación

3. **Configurar backups**
   - Render hace backups automáticos del database
   - Configurar backups adicionales si es necesario

4. **Monitorear logs**
   - Revisar logs diarios
   - Configurar alertas de errores

5. **Optimizar performance**
   - Agregar índices de database si es necesario
   - Implementar caché con Redis
   - Optimizar queries N+1

---

## 📞 Soporte

- **Render Docs**: https://render.com/docs
- **Django Docs**: https://docs.djangoproject.com/
- **GitHub Issues**: https://github.com/Safary16/soptraloc/issues

---

**Última actualización**: Octubre 2025  
**Versión del sistema**: v2.0-optimized  
**Estado**: ✅ Listo para producción
