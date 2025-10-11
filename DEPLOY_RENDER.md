# 🚀 GUÍA DE DEPLOY EN RENDER.COM

**Fecha**: Octubre 11, 2025  
**Repositorio**: https://github.com/Safary16/soptraloc  
**Branch**: main  
**Último Commit**: `ca0a6603`

---

## 📋 PRE-REQUISITOS

✅ Repositorio GitHub limpio y pusheado  
✅ Python 3.12 especificado en `.python-version`  
✅ `render.yaml` configurado  
✅ `build.sh` funcional con permisos de ejecución  
✅ `requirements.txt` actualizado (pandas 2.2.3 compatible con Python 3.12)

---

## 🎯 PASOS PARA DEPLOY

### 1. **Acceder a Render Dashboard**
1. Ir a: https://dashboard.render.com
2. Login con tu cuenta GitHub
3. Si no tienes cuenta, crear una y conectar GitHub

### 2. **Crear Nuevo Blueprint (Automático)**
1. Click en **"New +"** (botón azul arriba derecha)
2. Seleccionar **"Blueprint"**
3. Conectar repositorio:
   - **Repository**: `Safary16/soptraloc`
   - **Branch**: `main`
4. Render detectará automáticamente el `render.yaml`
5. Click en **"Apply"**

### 3. **Servicios que se Crearán Automáticamente**

#### 🌐 Web Service: `soptraloc`
- **Runtime**: Python 3.12
- **Build Command**: `./build.sh`
- **Start Command**: `gunicorn config.wsgi:application`
- **Plan**: Free
- **URL**: `https://soptraloc.onrender.com`

#### 🗄️ PostgreSQL Database: `soptraloc-db`
- **Database Name**: `soptraloc`
- **User**: `soptraloc`
- **Plan**: Free
- **Auto-conectado**: El `DATABASE_URL` se inyecta automáticamente

### 4. **Configurar Variables de Entorno** ⚠️ CRÍTICO

Render crea algunas automáticamente, pero necesitas configurar **MAPBOX_ACCESS_TOKEN**:

1. Ir al servicio `soptraloc`
2. Click en **"Environment"** (menú izquierdo)
3. Agregar/Verificar variables:

| Variable | Valor | Auto-generado |
|----------|-------|---------------|
| `PYTHON_VERSION` | `3.12.0` | ✅ Auto |
| `DATABASE_URL` | PostgreSQL connection string | ✅ Auto |
| `SECRET_KEY` | Random string | ✅ Auto |
| `DEBUG` | `false` | ✅ Auto |
| `ALLOWED_HOSTS` | `.onrender.com` | ✅ Auto |
| `MAPBOX_ACCESS_TOKEN` | **TU TOKEN** | ⚠️ MANUAL |

#### ⚠️ **Configurar MAPBOX_ACCESS_TOKEN**:
```
1. Ir a: https://account.mapbox.com/access-tokens/
2. Copiar tu token (empieza con pk.ey...)
3. En Render > Environment > Add Environment Variable:
   - Key: MAPBOX_ACCESS_TOKEN
   - Value: [Tu token de Mapbox]
4. Click "Save Changes"
```

### 5. **Monitorear el Deploy**

Una vez que hagas "Apply" en Blueprint:

1. **Ver logs en tiempo real**:
   - Click en `soptraloc`
   - Tab **"Logs"**
   - Verás el proceso de build:
     ```
     🚀 SOPTRALOC TMS - BUILD
     📦 Actualizando pip...
     📦 Instalando dependencias...
     📂 Colectando archivos estáticos...
     🔄 Ejecutando migraciones...
     ✅ Build completado exitosamente
     ```

2. **Deploy exitoso** cuando veas:
   ```
   ==> Build successful 🎉
   ==> Starting service with 'gunicorn config.wsgi:application'...
   ==> Your service is live 🎉
   ```

3. **Tiempo estimado**: 5-8 minutos (primera vez)

### 6. **Verificar el Deploy**

#### A. **Verificar API**
```bash
curl https://soptraloc.onrender.com/api/
```

Deberías ver:
```json
{
  "message": "SoptraLoc TMS API v1.0",
  "version": "1.0.0",
  "status": "operational"
}
```

#### B. **Verificar Admin Django**
```
https://soptraloc.onrender.com/admin/
```
Deberías ver el login de Django admin

#### C. **Verificar Endpoints**
- Health: `https://soptraloc.onrender.com/health/`
- API Root: `https://soptraloc.onrender.com/api/`
- Containers: `https://soptraloc.onrender.com/api/containers/`
- Drivers: `https://soptraloc.onrender.com/api/drivers/`
- CDs: `https://soptraloc.onrender.com/api/cds/`

---

## 🔧 CONFIGURACIÓN ADICIONAL

### Crear Superusuario

Una vez deployed, necesitas crear un superusuario:

1. En Render Dashboard > `soptraloc`
2. Click en **"Shell"** (menú izquierdo)
3. Ejecutar:
```bash
python manage.py createsuperuser
```
4. Ingresar:
   - Username: `admin`
   - Email: `tu@email.com`
   - Password: [tu password seguro]

### Cargar Datos Iniciales

Si tienes archivos Excel de datos:

1. Subir archivos a través del admin o API
2. O usar shell de Render:
```bash
# En Render Shell
python manage.py shell

# Importar manualmente
from apps.core.services.excel_importer import ExcelImporterService
importer = ExcelImporterService()
# ... código de importación
```

---

## 🐛 TROUBLESHOOTING

### ❌ Error: "Build failed"

**Causa común**: pandas no puede compilar

**Solución**: Verificar que `.python-version` contenga `3.12`

```bash
# En tu repo local
cat .python-version
# Debe mostrar: 3.12

# Si no, crear/actualizar:
echo "3.12" > .python-version
git add .python-version
git commit -m "fix: Especificar Python 3.12"
git push
```

### ❌ Error: "Module not found"

**Causa**: Falta dependencia en `requirements.txt`

**Solución**: Agregar al `requirements.txt` y push

### ❌ Error: "Application timeout"

**Causa**: Gunicorn no encuentra la app

**Solución**: Verificar `startCommand` en `render.yaml`:
```yaml
startCommand: "gunicorn config.wsgi:application"
```

### ❌ Error: "Database connection failed"

**Causa**: PostgreSQL no está iniciado o `DATABASE_URL` no está configurado

**Solución**: 
1. Verificar que `soptraloc-db` esté "Available"
2. Verificar variable `DATABASE_URL` en Environment

### ❌ Mapbox no funciona

**Causa**: `MAPBOX_ACCESS_TOKEN` no configurado

**Solución**: Agregar token en Environment variables (ver paso 4)

---

## 📊 MÉTRICAS DE DEPLOY

### Plan Free de Render incluye:
- ✅ 512 MB RAM
- ✅ PostgreSQL 256 MB
- ✅ Sleep después de 15 min de inactividad
- ✅ 750 horas/mes (suficiente para testing)
- ✅ SSL automático (HTTPS)
- ✅ Backups automáticos DB

### Limitaciones Plan Free:
- ⏰ Sleep después de 15 min sin requests
- ⏰ Cold start: 30-60 segundos al despertar
- 📊 Requests lentos en cold start
- 💾 Storage temporal (se borra en redeploy)

### Upgrade a Plan Paid ($7/mes):
- ✅ Sin sleep
- ✅ 512 MB RAM garantizada
- ✅ PostgreSQL 1 GB
- ✅ Mejor performance
- ✅ Soporte prioritario

---

## 🎉 SIGUIENTE PASO DESPUÉS DEL DEPLOY

### 1. **Testing Inicial**
```bash
# Health check
curl https://soptraloc.onrender.com/health/

# Test API
curl https://soptraloc.onrender.com/api/containers/
```

### 2. **Importar Datos de Excel**
- Seguir `TESTING_GUIDE.md`
- Importar 4 archivos en orden:
  1. Embarque
  2. Liberación
  3. Programaciones
  4. Conductores

### 3. **Verificar ML**
- Crear operaciones de prueba
- Ver que se crean registros `TiempoOperacion`
- Verificar predicciones ML después de 5+ operaciones

### 4. **Configurar Frontend (Opcional)**
- Apuntar frontend a: `https://soptraloc.onrender.com/api/`
- Usar CORS configurado en settings

---

## 📞 SOPORTE

### Render Documentation
- **Docs**: https://render.com/docs
- **Status**: https://status.render.com/
- **Community**: https://community.render.com/

### Logs en Tiempo Real
```bash
# En Render Dashboard
1. Click en soptraloc
2. Tab "Logs"
3. Ver logs en vivo
```

### Comandos Útiles en Render Shell
```bash
# Ver migraciones
python manage.py showmigrations

# Crear superuser
python manage.py createsuperuser

# Shell interactivo
python manage.py shell

# Ver configuración
python manage.py check --deploy
```

---

## ✅ CHECKLIST FINAL

Antes de considerar el deploy exitoso:

- [ ] Web service está "Live" en Render
- [ ] Database está "Available"
- [ ] Admin Django accesible
- [ ] API `/api/` responde
- [ ] Superusuario creado
- [ ] `MAPBOX_ACCESS_TOKEN` configurado
- [ ] Health check pasa
- [ ] Endpoints responden (containers, drivers, cds)
- [ ] Logs no muestran errores críticos
- [ ] SSL/HTTPS funciona automáticamente

---

## 🚀 COMANDOS RÁPIDOS

### Deploy desde cero
```bash
# 1. Ir a Render Dashboard
# 2. New + > Blueprint
# 3. Conectar Safary16/soptraloc
# 4. Apply
# 5. Configurar MAPBOX_ACCESS_TOKEN
# 6. Esperar 5-8 minutos
# 7. ✅ Live!
```

### Re-deploy después de cambios
```bash
# En tu local
git add .
git commit -m "feat: Nueva funcionalidad"
git push origin main

# Render auto-detecta el push y redeploys automáticamente
# Tiempo: 3-5 minutos
```

---

**Generado por**: GitHub Copilot  
**Fecha**: Octubre 11, 2025  
**Repositorio**: https://github.com/Safary16/soptraloc  
**Estado**: ✅ Listo para Deploy
