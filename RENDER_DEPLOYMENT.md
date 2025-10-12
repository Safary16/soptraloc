# 🚀 Despliegue Automático en Render.com

## 📋 Resumen

Este repositorio está configurado para desplegarse automáticamente en Render.com usando el archivo `render.yaml` (Blueprint).

**URL del Sitio**: https://soptraloc.onrender.com
**URL Admin**: https://soptraloc.onrender.com/admin/
**Credenciales**: admin / 1234

---

## ✅ Pre-requisitos Verificados

- ✅ `render.yaml` configurado con Blueprint
- ✅ `build.sh` ejecutable y funcional
- ✅ `requirements.txt` completo
- ✅ `.python-version` (3.12) trackeado en git
- ✅ `config/wsgi.py` con WSGI application
- ✅ Variables de entorno configuradas en render.yaml

---

## 🎯 Pasos para Desplegar desde Cero

### 1. Conectar Repositorio en Render

1. Ve a: https://dashboard.render.com/
2. Click en **"New +"** → **"Blueprint"**
3. Conecta tu repositorio de GitHub: `Safary16/soptraloc`
4. Render detectará automáticamente el archivo `render.yaml`
5. Click en **"Apply"**

### 2. Servicios que se Crearán Automáticamente

Render creará automáticamente:

#### 🌐 Web Service: `soptraloc`
- **Runtime**: Python 3.12
- **Build Command**: `./build.sh`
- **Start Command**: `gunicorn config.wsgi:application` ⚠️ **CORRECTO**
- **Plan**: Free
- **URL**: `https://soptraloc.onrender.com`

#### 🗄️ PostgreSQL Database: `soptraloc-db`
- **Database Name**: `soptraloc`
- **User**: `soptraloc`
- **Plan**: Free
- **Auto-conectado**: La variable `DATABASE_URL` se inyecta automáticamente

### 3. Variables de Entorno (Auto-configuradas)

El `render.yaml` ya configura estas variables:

| Variable | Valor | Fuente |
|----------|-------|--------|
| `PYTHON_VERSION` | `3.12.0` | render.yaml |
| `DATABASE_URL` | Auto | Base de datos PostgreSQL |
| `SECRET_KEY` | Auto-generado | render.yaml |
| `DEBUG` | `false` | render.yaml |
| `ALLOWED_HOSTS` | `.onrender.com` | render.yaml |
| `MAPBOX_API_KEY` | Tu token | render.yaml (línea 24) |

⚠️ **IMPORTANTE**: El token de Mapbox ya está en el render.yaml. Si necesitas cambiarlo:
1. Ve a: https://account.mapbox.com/access-tokens/
2. Copia tu nuevo token
3. Actualiza la línea 24 en `render.yaml`
4. Haz commit y push

### 4. Proceso de Build

El script `build.sh` ejecutará automáticamente:

```bash
1. pip install --upgrade pip
2. pip install -r requirements.txt
3. python manage.py collectstatic --no-input
4. python manage.py migrate --no-input
```

### 5. Monitoreo del Deploy

1. Ve a tu Dashboard de Render
2. Click en el servicio `soptraloc`
3. Ve a la pestaña **"Logs"**
4. Verás el progreso del build y deploy en tiempo real

**Tiempo estimado**: 5-10 minutos para el primer deploy

### 6. Verificar Deploy Exitoso

Una vez completado, verifica:

```bash
✅ Build completado sin errores
✅ Deploy completado sin errores
✅ Servicio en estado "Live"
```

Prueba las URLs:
- **Home**: https://soptraloc.onrender.com/
- **Admin**: https://soptraloc.onrender.com/admin/
- **API**: https://soptraloc.onrender.com/api/containers/

---

## 🔐 Acceso al Sistema

### Credenciales de Superusuario

El superusuario se crea automáticamente en el primer deploy:

```
URL: https://soptraloc.onrender.com/admin/
Username: admin
Password: 1234
```

**⚠️ SEGURIDAD**: En producción, cambia esta contraseña:
1. Ingresa al admin
2. **Authentication and Authorization** → **Users**
3. Click en `admin`
4. **Change password form**
5. Ingresa contraseña segura
6. **SAVE**

---

## 🐛 Troubleshooting

### ❌ Error: "ModuleNotFoundError: No module named 'app'"

**Causa**: Render está usando comando incorrecto

**Solución**:
1. Verifica que el `render.yaml` tenga:
   ```yaml
   startCommand: "gunicorn config.wsgi:application"
   ```
2. **NO** debe ser: `gunicorn app:app`
3. Si el error persiste, elimina el servicio y recréalo desde Blueprint

### ❌ Error: "Build failed"

**Causa**: Error en dependencias o build script

**Solución**:
1. Verifica los logs en Render
2. Asegúrate que `build.sh` sea ejecutable:
   ```bash
   git update-index --chmod=+x build.sh
   git commit -m "Make build.sh executable"
   git push
   ```

### ❌ Error: "Database connection failed"

**Causa**: PostgreSQL no está conectado

**Solución**:
1. Verifica que `soptraloc-db` esté "Available"
2. Verifica que `DATABASE_URL` esté en Environment variables
3. El `render.yaml` debe tener:
   ```yaml
   DATABASE_URL:
     fromDatabase:
       name: soptraloc-db
       property: connectionString
   ```

### ❌ Mapbox no funciona

**Causa**: Token no válido o no configurado

**Solución**:
1. Verifica el token en `render.yaml` línea 24
2. Prueba el token en: https://account.mapbox.com/access-tokens/
3. Actualiza si es necesario y haz push

---

## 🔄 Actualizaciones y Re-deploys

### Deploy Automático

Cada vez que hagas push a la rama principal:
1. Render detecta el cambio automáticamente
2. Ejecuta `build.sh`
3. Inicia el servicio con `gunicorn config.wsgi:application`
4. El sitio se actualiza automáticamente

### Deploy Manual

Si necesitas forzar un deploy:
1. Ve al Dashboard de Render
2. Click en el servicio `soptraloc`
3. Click en **"Manual Deploy"** → **"Deploy latest commit"**

### Rollback

Si algo sale mal:
1. Ve al Dashboard de Render
2. Click en el servicio `soptraloc`
3. Ve a **"Deploys"**
4. Click en un deploy anterior
5. Click en **"Redeploy"**

---

## 📊 Estructura del Proyecto

```
soptraloc/
├── .python-version         # Python 3.12
├── render.yaml             # ⚠️ Blueprint de Render
├── build.sh                # ⚠️ Script de build
├── requirements.txt        # Dependencias
├── manage.py               # Django management
├── config/
│   ├── settings.py         # Configuración Django
│   ├── wsgi.py            # ⚠️ WSGI application
│   └── urls.py            # URLs principales
├── apps/                   # Aplicaciones Django
│   ├── containers/        # Gestión de contenedores
│   ├── drivers/           # Gestión de conductores
│   ├── programaciones/    # Programación de entregas
│   ├── cds/              # Centros de distribución
│   ├── events/           # Eventos y auditoría
│   └── notifications/    # Notificaciones
├── static/               # Archivos estáticos
└── templates/            # Templates Django
```

---

## ✅ Checklist de Verificación

Antes de desplegar, verifica:

- [x] `render.yaml` existe en la raíz del repositorio
- [x] `build.sh` es ejecutable (chmod +x)
- [x] `requirements.txt` completo
- [x] `.python-version` trackeado en git
- [x] `config/wsgi.py` existe y exporta `application`
- [x] Variables de entorno configuradas en `render.yaml`
- [x] Token de Mapbox válido (si se usa)
- [x] Todos los archivos importantes están en git

---

## 📞 Soporte

Si tienes problemas:

1. **Logs de Render**: Dashboard → Servicio → Logs
2. **Documentación Render**: https://render.com/docs
3. **Django Debug**: Verifica `python manage.py check --deploy`

---

## 🎉 ¡Listo!

Con esto, tu aplicación debería estar desplegada y funcionando en:
- **https://soptraloc.onrender.com**
- **Admin**: https://soptraloc.onrender.com/admin/ (admin/1234)

**Tiempo total**: 5-10 minutos desde que aplicas el Blueprint.
