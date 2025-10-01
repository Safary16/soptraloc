# SoptraLoc TMS v2.0

Sistema de Gestión de Transporte con Machine Learning desarrollado con Django 5.2.6.

## 🚀 Features

- ✅ Sistema de routing con ML (35 rutas + 70 operaciones de Chile)
- ✅ Reloj ATC en tiempo real (actualización cada 1s)
- ✅ Alertas de contenedores urgentes (check cada 30s)
- ✅ Dashboard administrativo completo
- ✅ API REST con autenticación JWT
- ✅ 5 apps funcionales: core, containers, routing, drivers, warehouses

## 📊 Stack Tecnológico

- **Backend:** Django 5.2.6, Python 3.12
- **Database:** PostgreSQL
- **Server:** Gunicorn
- **Static Files:** WhiteNoise
- **Deploy:** Render.com

## 🛠️ Desarrollo Local

```bash
# 1. Clonar repositorio
git clone https://github.com/Safary16/soptraloc.git
cd soptraloc

# 2. Crear entorno virtual
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus configuraciones

# 5. Aplicar migraciones
cd soptraloc_system
python manage.py migrate

# 6. Cargar datos iniciales (opcional)
python manage.py load_initial_times

# 7. Crear superusuario
python manage.py createsuperuser

# 8. Iniciar servidor
python manage.py runserver
```

Acceder a: http://localhost:8000

## 🌐 Deploy en Render.com

### Requisitos
- Cuenta en Render.com
- Repositorio conectado a GitHub

### Pasos

1. **Crear servicio en Render Dashboard:**
   - New → Web Service
   - Connect repository: `Safary16/soptraloc`
   - Branch: `main`
   - Root Directory: (dejar vacío)

2. **Configuración automática:**
   Render detectará el `render.yaml` y creará:
   - Web Service: `soptraloc`
   - PostgreSQL Database: `soptraloc-db`

3. **Deploy automático:**
   Cada push a `main` despliega automáticamente.

### Post-Deploy (Manual)

Una vez deployed, ejecutar en Render Shell:

```bash
# Cargar datos de Chile
cd soptraloc_system
python manage.py load_initial_times --settings=config.settings_production

# Crear superusuario
python manage.py createsuperuser --settings=config.settings_production
```

## 📝 Documentación

- `ANALISIS_TMS_RECOMENDACIONES.md` - Análisis del sistema TMS
- `ROUTING_ML_QUICKSTART.md` - Guía del sistema de routing ML
- `SISTEMA_RELOJ_Y_ALERTAS.md` - Documentación del reloj ATC y alertas
- `SISTEMA_TIEMPOS_ML.md` - Sistema de tiempos con ML
- `ROOT_CAUSE_ANALYSIS.md` - Análisis de troubleshooting
- `DEPLOYMENT_ANALYSIS.md` - Análisis de deployment
- `DEPLOY_FINAL_EXECUTIVO.md` - Resumen ejecutivo de deploy

## 🔧 Scripts Disponibles

- `build.sh` - Build para Render (pip install + migrate + collectstatic)
- `post_deploy.sh` - Post-deploy automático (datos + superuser)
- `validate_deploy.sh` - Validación pre-deploy

## 🏗️ Estructura del Proyecto

```
soptraloc/
├── soptraloc_system/          # Proyecto Django principal
│   ├── config/                # Configuración
│   │   ├── settings.py       # Settings desarrollo
│   │   ├── settings_production.py  # Settings producción
│   │   ├── urls.py           # URLs principales
│   │   └── wsgi.py           # WSGI application
│   ├── apps/                 # Aplicaciones Django
│   │   ├── core/             # Autenticación y modelos base
│   │   ├── containers/       # Gestión de contenedores
│   │   ├── routing/          # Sistema de routing y ML
│   │   ├── drivers/          # Conductores y alertas
│   │   └── warehouses/       # Almacenes y ubicaciones
│   ├── static/               # Archivos estáticos
│   ├── templates/            # Templates HTML
│   └── manage.py             # Django CLI
├── build.sh                  # Build script para Render
├── post_deploy.sh            # Post-deploy script
├── render.yaml               # Configuración de Render
├── requirements.txt          # Dependencias Python
└── README.md                 # Este archivo
```

## 🎯 Modelos Principales

### Core App
- `User` - Usuarios del sistema
- `UserProfile` - Perfiles de usuario
- `Notification` - Sistema de notificaciones

### Containers App
- `Container` - Contenedores
- `ContainerTracking` - Tracking de contenedores

### Routing App
- `Route` - Rutas de transporte
- `Operation` - Operaciones de transporte
- `RouteOperation` - Relación ruta-operación
- `OperationTime` - Tiempos históricos con ML

### Drivers App
- `Driver` - Conductores
- `Alert` - Alertas del sistema
- `DriverAssignment` - Asignaciones de conductores

### Warehouses App
- `Warehouse` - Almacenes y ubicaciones

## 🔐 Seguridad

- DEBUG = False en producción
- SECRET_KEY generada automáticamente
- HTTPS obligatorio en producción
- HSTS habilitado (31536000s)
- Secure cookies
- CSRF protection
- XSS protection

## 📦 Dependencias Principales

```
Django==5.2.6
djangorestframework==3.16.1
gunicorn==23.0.0
psycopg2-binary==2.9.9
whitenoise==6.11.0
dj-database-url==2.2.0
python-decouple==3.8
django-cors-headers==4.9.0
djangorestframework-simplejwt==5.5.1
```

## 🐛 Troubleshooting

### Error: ModuleNotFoundError
- Verificar que `soptraloc_system` existe
- Verificar que `config/wsgi.py` existe
- Revisar `DJANGO_SETTINGS_MODULE` en env vars

### Error: DATABASE_URL not found
- Verificar que la base de datos está creada en Render
- Verificar que el servicio web está conectado a la DB

### Error: Static files 404
- Ejecutar `python manage.py collectstatic`
- Verificar WhiteNoise en MIDDLEWARE

## 📞 Soporte

- GitHub Issues: https://github.com/Safary16/soptraloc/issues
- Email: admin@soptraloc.com

## 📄 Licencia

Propietario - SoptraLoc © 2025

---

**Última actualización:** 1 de Octubre 2025
**Versión:** 2.0
**Status:** ✅ Producción
