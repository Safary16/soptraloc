# 🚀 Deploy Automático en Render

Este proyecto está 100% configurado para **deploy automático sin necesidad de acceder a la consola** de Render.

---

## 📋 Pre-requisitos

1. ✅ Cuenta en [Render.com](https://render.com) (Plan Free disponible)
2. ✅ Repositorio ya está en GitHub: `Safary16/soptraloc`
3. ✅ Nada más - Todo es automático

---

## 🎯 Pasos para Deploy (3 minutos)

### 1️⃣ Conectar Repositorio en Render

1. Ve a [dashboard.render.com](https://dashboard.render.com)
2. Click en **"New +"** → **"Blueprint"**
3. Conecta tu cuenta de GitHub (si aún no lo has hecho)
4. Busca y selecciona el repositorio: **Safary16/soptraloc**
5. Click en **"Connect"**

### 2️⃣ Render Detecta `render.yaml` Automáticamente

Render leerá el archivo `render.yaml` y creará automáticamente:

#### ✅ PostgreSQL Database
- **Nombre**: `soptraloc-db`
- **Plan**: Free (90 días gratis, luego $7/mes)
- **Usuario**: `soptraloc`
- **Región**: Oregon

#### ✅ Web Service
- **Nombre**: `soptraloc`
- **Runtime**: Python 3.12.6
- **Plan**: Free (750 hrs/mes gratis)
- **Build**: Ejecuta `build.sh` automáticamente
- **Start**: Ejecuta Gunicorn con 2 workers

### 3️⃣ Variables de Entorno (Ya Configuradas)

El `render.yaml` ya incluye todas las variables necesarias:

```yaml
envVars:
  - SECRET_KEY: ✅ Generado automáticamente
  - DATABASE_URL: ✅ Conectado a PostgreSQL automáticamente
  - MAPBOX_API_KEY: ✅ Ya incluido (pk.eyJ1Ijoic2FmYXJ5MTYi...)
  - PYTHON_VERSION: ✅ 3.12.6
  - DJANGO_SETTINGS_MODULE: ✅ config.settings
```

**No necesitas configurar nada manualmente.**

### 4️⃣ Build Automático (`build.sh`)

Durante el deploy, el script `build.sh` ejecutará automáticamente:

```bash
✅ 1. Actualizar pip, setuptools, wheel
✅ 2. Instalar todas las dependencias (requirements.txt)
✅ 3. Verificar instalación (Django, psycopg2, DRF, gunicorn)
✅ 4. Recolectar archivos estáticos (collectstatic)
✅ 5. Aplicar migraciones de base de datos (migrate)
✅ 6. Crear superusuario admin/admin automáticamente
✅ 7. Cargar datos de prueba si la BD está vacía
```

**Todo esto sucede sin intervención manual.**

### 5️⃣ Deploy Completo

Después de 5-8 minutos, verás:

```
✅ BUILD COMPLETADO EXITOSAMENTE
========================================
🌐 Admin: https://soptraloc.onrender.com/admin/
📡 API: https://soptraloc.onrender.com/api/
👤 Usuario: admin
🔑 Contraseña: admin
========================================
```

---

## 🌐 Acceso al Sistema

### Admin Panel
- **URL**: `https://soptraloc.onrender.com/admin/`
- **Usuario**: `admin`
- **Contraseña**: `admin`

⚠️ **IMPORTANTE**: Cambia la contraseña después del primer login.

### API REST
- **URL**: `https://soptraloc.onrender.com/api/`
- **Endpoints**:
  - `/api/containers/`
  - `/api/drivers/`
  - `/api/programaciones/`
  - `/api/cds/`

---

## 📊 Datos de Prueba Incluidos

Si la base de datos está vacía en el primer deploy, se cargan automáticamente:

- ✅ **2 CCTIs**: ZEAL (Valparaíso), CLEP (San Antonio)
- ✅ **3 Clientes**: Viña del Mar, Santiago Centro, Quilicura
- ✅ **4 Conductores**: 3 disponibles con métricas
- ✅ **8 Contenedores**: En diferentes estados
- ✅ **3 Programaciones**: Incluyendo alertas urgentes

---

## 🔄 Re-Deploy Automático

Cada vez que hagas `git push` a la rama `main`:

1. Render detecta el cambio automáticamente
2. Ejecuta `build.sh` nuevamente
3. Actualiza el servicio sin downtime
4. Mantiene la base de datos intacta

---

## 🔍 Verificar Estado del Deploy

### En Render Dashboard

1. Ve a tu servicio `soptraloc`
2. Click en **"Logs"** para ver el progreso en tiempo real
3. Busca el mensaje:

```
✅ BUILD COMPLETADO EXITOSAMENTE
```

### Logs Importantes

```bash
# Instalación de dependencias
📦 Instalando dependencias...
✅ Django 5.1.4
✅ psycopg2 instalado
✅ djangorestframework instalado
✅ gunicorn instalado

# Migraciones
🗄️ Aplicando migraciones...
Operations to perform: Apply all migrations
Running migrations: OK

# Superusuario
👤 Creando superusuario admin/admin...
✅ Superusuario creado: admin/admin

# Datos de prueba
📦 Base de datos vacía, cargando datos de prueba...
✅ Creados 5 CDs
✅ Creados 4 conductores
✅ Creados 8 contenedores
✅ Creadas 3 programaciones
```

---

## 🧪 Probar el Sistema

### 1. Acceso al Admin

```bash
# Navega a:
https://soptraloc.onrender.com/admin/

# Login:
Usuario: admin
Contraseña: admin
```

### 2. Ver Contenedores

```bash
# En el admin, click en "Containers"
# Verás 8 contenedores de prueba en diferentes estados
```

### 3. Probar API con curl

```bash
# Listar contenedores
curl https://soptraloc.onrender.com/api/containers/

# Ver alertas (programaciones urgentes)
curl https://soptraloc.onrender.com/api/programaciones/alertas/

# Conductores disponibles
curl https://soptraloc.onrender.com/api/drivers/disponibles/
```

### 4. Importar Excel Real

```bash
# Importar embarque
curl -X POST https://soptraloc.onrender.com/api/containers/import_embarque/ \
  -F "file=@embarque.xlsx"

# Importar liberación
curl -X POST https://soptraloc.onrender.com/api/containers/import_liberacion/ \
  -F "file=@liberacion.xlsx"

# Importar programación
curl -X POST https://soptraloc.onrender.com/api/containers/import_programacion/ \
  -F "file=@programacion.xlsx"
```

---

## ⚠️ Troubleshooting

### ❌ Error: "Build failed"

**Verificar**:
1. Logs de Render para ver el error específico
2. Que `requirements.txt` tenga todas las dependencias
3. Que `build.sh` tenga permisos de ejecución (`chmod +x build.sh`)

**Solución**:
```bash
# Local:
git add build.sh
git update-index --chmod=+x build.sh
git commit -m "fix: permisos build.sh"
git push
```

### ❌ Error: "Database connection failed"

**Causa**: La variable `DATABASE_URL` no está configurada.

**Solución**:
1. En Render Dashboard → tu servicio
2. Environment → Variables
3. Verificar que `DATABASE_URL` esté conectada a `soptraloc-db`

### ❌ Error: "Static files not found"

**Causa**: `collectstatic` falló durante el build.

**Solución**:
```bash
# Verificar en build.sh que existe:
python manage.py collectstatic --no-input

# Y en settings.py:
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATIC_URL = '/static/'
```

### ❌ Servicio muy lento (Plan Free)

**Causa**: El plan Free de Render duerme después de 15 minutos de inactividad.

**Soluciones**:
1. **Primera petición**: Esperar 30-60 segundos al "despertar"
2. **Upgrade**: Plan Starter ($7/mes) sin sleep
3. **Keep-alive**: Servicio externo que haga ping cada 10 minutos

---

## 🔐 Seguridad Post-Deploy

### 1. Cambiar Contraseña Admin

```bash
# En admin panel:
1. Login con admin/admin
2. Click en tu usuario (esquina superior derecha)
3. "Change password"
4. Ingresa nueva contraseña segura
```

### 2. Cambiar SECRET_KEY (Opcional)

```bash
# En Render Dashboard:
1. Tu servicio → Environment
2. Click en SECRET_KEY → Edit
3. Generate new value
4. Save changes
5. Render re-deploya automáticamente
```

### 3. Configurar ALLOWED_HOSTS

```python
# En config/settings.py ya está configurado:
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1,.onrender.com').split(',')
```

---

## 📈 Monitoreo

### Logs en Tiempo Real

```bash
# En Render Dashboard:
1. Tu servicio → Logs
2. Ver logs en tiempo real
3. Filtrar por tipo: info, warning, error
```

### Métricas

```bash
# En Render Dashboard:
1. Tu servicio → Metrics
2. Ver CPU, memoria, requests
3. Tiempo de respuesta
```

---

## 🆙 Actualizar el Sistema

```bash
# 1. Hacer cambios locales
git add .
git commit -m "feat: nueva funcionalidad"

# 2. Push a GitHub
git push origin main

# 3. Render auto-deploya (5-8 minutos)
# No necesitas hacer nada más
```

---

## 💰 Costos

### Plan Free (Actual)
- **Web Service**: Gratis (750 hrs/mes)
- **PostgreSQL**: Gratis (90 días), luego $7/mes
- **Limitación**: Sleep después de 15 min inactividad

### Plan Starter ($7/mes por servicio)
- Sin sleep
- Mejor performance
- Más memoria y CPU
- 100 GB transfer/mes

---

## ✅ Checklist Deploy

- [x] Cuenta Render creada
- [x] Repositorio conectado
- [x] Blueprint detectado
- [x] PostgreSQL creado
- [x] Web service creado
- [x] Build completado
- [x] Migraciones aplicadas
- [x] Superusuario creado
- [x] Datos de prueba cargados
- [x] Admin accessible
- [x] API funcionando
- [ ] Contraseña admin cambiada
- [ ] Excel reales importados
- [ ] Sistema en producción

---

## 🆘 Soporte

Si tienes problemas durante el deploy:

1. **Logs de Render**: Revisar primero
2. **GitHub Issues**: [Abrir issue](https://github.com/Safary16/soptraloc/issues)
3. **Email**: admin@soptraloc.cl

---

**Sistema listo para deploy en 3 minutos** 🚀
