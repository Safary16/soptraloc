# 🚀 GUÍA COMPLETA DE DEPLOY EN RENDER - DESDE CERO

## 📋 Checklist Pre-Deploy

Antes de empezar, asegúrate de tener:
- [ ] Cuenta en Render.com
- [ ] Repositorio GitHub con el código
- [ ] Rama `main` actualizada
- [ ] Este archivo `render.yaml` en la raíz del proyecto

## 🎯 Paso 1: Crear Nuevo Servicio en Render

### 1.1 Accede a Render Dashboard
```
https://dashboard.render.com
```

### 1.2 Crear Nuevo Web Service
1. Click en **"New +"** → **"Web Service"**
2. Selecciona **"Build and deploy from a Git repository"**
3. Click **"Next"**

### 1.3 Conectar Repositorio
1. Si no está conectado, click en **"Connect GitHub"**
2. Busca tu repositorio: `Safary16/soptraloc`
3. Click **"Connect"**

### 1.4 Configuración del Servicio

**IMPORTANTE:** Render detectará automáticamente el `render.yaml`, pero verifica:

```yaml
Name: soptraloc  # ⚠️ SIN -tms
Region: Oregon (US West)
Branch: main
Runtime: Python 3
```

### 1.5 Click en "Create Web Service"

Render comenzará a:
1. Detectar `render.yaml`
2. Crear la base de datos PostgreSQL automáticamente
3. Configurar variables de entorno
4. Iniciar el build

## 🗄️ Paso 2: Verificar Base de Datos

La base de datos se crea automáticamente según `render.yaml`:

```yaml
Database Name: soptraloc-db  # ⚠️ Nuevo nombre
Database: soptraloc
User: soptraloc
Region: Oregon
Plan: Free
```

Para verificar:
1. En Dashboard → Databases
2. Deberías ver `soptraloc-db`
3. Status debe ser "Available"

## ⚙️ Paso 3: Variables de Entorno (Auto-configuradas)

El `render.yaml` configura automáticamente:

| Variable | Valor | Descripción |
|----------|-------|-------------|
| `PYTHON_VERSION` | 3.12.6 | Versión de Python |
| `SECRET_KEY` | Auto-generada | Clave secreta Django |
| `DATABASE_URL` | Auto-conectada | Conexión a PostgreSQL |
| `DJANGO_SETTINGS_MODULE` | config.settings_production | Settings de producción |

**NO necesitas configurar nada manualmente** ✅

## 📊 Paso 4: Monitorear el Deploy

### 4.1 Ver Logs en Tiempo Real
```
Dashboard → soptraloc → Logs
```

### 4.2 Etapas del Deploy

**Build Phase (3-5 min):**
```
🔨 Building...
📦 Installing dependencies
✅ Build succeeded
```

**Pre-Deploy Phase (1-2 min):**
```
🔄 Running migrations...
✅ Migrations completed
```

**Post-Deploy Phase (2-3 min):**
```
🚀 POST-DEPLOY SOPTRALOC TMS
📋 PASO 1: Verificando entorno
✅ Entorno verificado

🗄️ PASO 2: Verificando PostgreSQL
✅ Conexión a PostgreSQL exitosa

👤 PASO 3: Creando superusuario
✅ Superusuario creado

🔐 PASO 4: Verificación final
✅ Verificación completa exitosa

📊 PASO 5: Cargando datos
✅ Datos de Chile cargados

✅ POST-DEPLOY COMPLETADO EXITOSAMENTE
```

**Start Phase (1 min):**
```
🚀 Starting server...
✅ Live
```

### 4.3 Señales de Éxito

Busca estas líneas en los logs:

```
✅ Superusuario creado
✅ AUTENTICACIÓN EXITOSA
✅ POST-DEPLOY COMPLETADO EXITOSAMENTE
Deploy live at https://soptraloc.onrender.com
```

## 🔗 Paso 5: Acceder al Sistema

Una vez que el deploy esté en estado **"Live"** (verde):

### 5.1 URL del Admin
```
https://soptraloc.onrender.com/admin/
```

### 5.2 Credenciales Iniciales
```
Usuario:  admin
Password: 1234
```

### 5.3 Dashboard Principal
```
https://soptraloc.onrender.com/dashboard/
```

### 5.4 API
```
https://soptraloc.onrender.com/api/v1/
```

### 5.5 Documentación API
```
https://soptraloc.onrender.com/swagger/
```

## ✅ Paso 6: Verificación Post-Deploy

### 6.1 Verificar Login
1. Ve a `https://soptraloc.onrender.com/admin/`
2. Ingresa `admin` / `1234`
3. Deberías entrar al panel de Django admin
4. ✅ Si entras = Deploy exitoso

### 6.2 Verificar Dashboard
1. Ve a `https://soptraloc.onrender.com/dashboard/`
2. Deberías ver el dashboard de contenedores
3. ✅ Si carga = Frontend funciona

### 6.3 Verificar API
1. Ve a `https://soptraloc.onrender.com/api/v1/`
2. Deberías ver el API root
3. ✅ Si responde = API funciona

## 🔧 Paso 7: Configuración de Seguridad

### 7.1 Cambiar Contraseña (IMPORTANTE)

1. Login en el admin
2. Click en tu usuario (esquina superior derecha)
3. Click en "Change password"
4. Ingresa contraseña nueva segura
5. Save

### 7.2 Crear Usuarios Adicionales

En el admin:
1. Users → Add user
2. Ingresa username y password
3. Marca permisos según necesites
4. Save

## 📊 Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────┐
│                    RENDER.COM                           │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Web Service: soptraloc                          │  │
│  │  ├─ Runtime: Python 3.12.6                       │  │
│  │  ├─ Framework: Django 5.2.6                      │  │
│  │  ├─ Server: Gunicorn                             │  │
│  │  └─ Workers: 2 (threads: 4)                      │  │
│  └──────────────────────────────────────────────────┘  │
│                          ⬇️  ⬆️                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Database: soptraloc-db                          │  │
│  │  ├─ Engine: PostgreSQL                           │  │
│  │  ├─ Version: Latest                              │  │
│  │  └─ Plan: Free                                   │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
└─────────────────────────────────────────────────────────┘
                          ⬇️
┌─────────────────────────────────────────────────────────┐
│              URLS PÚBLICAS                              │
│  https://soptraloc.onrender.com                         │
└─────────────────────────────────────────────────────────┘
```

## 🐛 Troubleshooting

### Problema: Build Falla

**Síntomas:**
```
❌ Build failed
Error installing requirements
```

**Solución:**
1. Verifica `requirements.txt`
2. Revisa logs de build
3. Confirma Python version (3.12.6)

### Problema: Migrations Fallan

**Síntomas:**
```
❌ Error running migrations
django.db.utils.OperationalError
```

**Solución:**
1. Verifica que la base de datos esté "Available"
2. Revisa que `DATABASE_URL` esté configurada
3. Check logs de la base de datos

### Problema: Post-Deploy Falla

**Síntomas:**
```
❌ ERROR: Usuario admin NO existe
❌ Autenticación falló
```

**Solución:**
El script tiene 3 métodos de fallback:
1. Revisa logs completos de post-deploy
2. Busca cuál método intentó ejecutar
3. Si todos fallan, hay problema de PostgreSQL

### Problema: Login No Funciona

**Síntomas:**
```
"nombre de usuario y clave incorrectos"
```

**Solución:**
1. Verifica que estés usando HTTPS (no HTTP)
2. Limpia cookies del navegador
3. Prueba en modo incógnito
4. Revisa logs de post-deploy para confirmar creación de usuario

### Problema: 502 Bad Gateway

**Síntomas:**
```
502 Bad Gateway
```

**Solución:**
1. Espera 1-2 minutos (puede estar iniciando)
2. Verifica que el servicio esté "Live"
3. Check logs por errores de Python/Django

### Problema: Static Files No Cargan

**Síntomas:**
- Admin panel sin estilos
- CSS/JS no cargan

**Solución:**
1. Verifica `STATIC_ROOT` en settings
2. Confirma que `collectstatic` se ejecutó
3. Check whitenoise en middleware

## 📈 Optimizaciones

### Performance

El sistema está optimizado con:
- ✅ Gunicorn con 2 workers + 4 threads
- ✅ Whitenoise para static files
- ✅ PostgreSQL con connection pooling
- ✅ GZIP compression
- ✅ Static file caching

### Seguridad

Configuración endurecida:
- ✅ HTTPS obligatorio (SECURE_SSL_REDIRECT)
- ✅ HSTS habilitado
- ✅ Secure cookies
- ✅ CSRF protection
- ✅ XSS protection

### Monitoring

Render provee:
- ✅ Logs en tiempo real
- ✅ Métricas de CPU/RAM
- ✅ Uptime monitoring
- ✅ Health checks

## 📝 Comandos Útiles

### Ver Logs
```bash
# En Render Dashboard
Dashboard → soptraloc → Logs
```

### Forzar Re-Deploy
```bash
# En Render Dashboard
Dashboard → soptraloc → Manual Deploy → "Deploy latest commit"
```

### Rollback
```bash
# En Render Dashboard
Dashboard → soptraloc → Manual Deploy → "Deploy previous version"
```

## 🎯 URLs de Referencia

| Recurso | URL |
|---------|-----|
| **Render Dashboard** | https://dashboard.render.com |
| **Servicio Web** | Dashboard → soptraloc |
| **Base de Datos** | Dashboard → soptraloc-db |
| **Admin Panel** | https://soptraloc.onrender.com/admin/ |
| **Dashboard** | https://soptraloc.onrender.com/dashboard/ |
| **API Root** | https://soptraloc.onrender.com/api/v1/ |
| **Swagger** | https://soptraloc.onrender.com/swagger/ |
| **GitHub Repo** | https://github.com/Safary16/soptraloc |

## 🎉 Deploy Exitoso

Si todo funcionó correctamente, deberías:
- ✅ Ver el servicio en estado "Live" (verde)
- ✅ Poder acceder al admin con admin/1234
- ✅ Ver el dashboard sin errores
- ✅ API respondiendo correctamente

## 📞 Soporte

Si tienes problemas:
1. Revisa esta guía completa
2. Consulta los logs en Render
3. Verifica troubleshooting section
4. Documenta el error exacto que ves

---

**Versión:** 3.0  
**Fecha:** Octubre 2025  
**Configuración:** render.yaml optimizado  
**URL:** https://soptraloc.onrender.com
