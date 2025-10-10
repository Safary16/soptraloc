# 🚀 DEPLOYMENT GUIDE - SOPTRALOC TMS

## 📋 Tabla de Contenidos
1. [Variables de Entorno](#variables-de-entorno)
2. [Despliegue en Render.com](#despliegue-en-rendercom)
3. [CI/CD con GitHub Actions](#cicd-con-github-actions)
4. [Backups y Restauración](#backups-y-restauración)
5. [Monitoreo y Alertas](#monitoreo-y-alertas)
6. [Disaster Recovery](#disaster-recovery)
7. [Escalabilidad](#escalabilidad)
8. [Troubleshooting](#troubleshooting)

---

## 🔐 Variables de Entorno

### Variables Requeridas

```bash
# Django Core
SECRET_KEY=your-secret-key-here-min-50-chars
DEBUG=False
ALLOWED_HOSTS=soptraloc.onrender.com,.onrender.com
RENDER_EXTERNAL_HOSTNAME=soptraloc.onrender.com

# Database (Render auto-configura)
DATABASE_URL=postgresql://user:pass@host:port/dbname

# Redis (Render auto-configura)
REDIS_URL=redis://red-xxxxx:6379

# Mapbox API
MAPBOX_API_KEY=pk.eyJ1Ijoic2FmYXJ5MTYiLCJhIjoiY21naHlvYTQ5MDNlbDJrbjJjcXRtZGg1YSJ9.WCiyTSY_CCfB02N_Nfx7kg

# Sentry (opcional pero recomendado)
SENTRY_DSN=https://xxx@xxx.ingest.sentry.io/xxx

# AWS S3 (opcional)
USE_S3=False
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_STORAGE_BUCKET_NAME=soptraloc-media
AWS_S3_REGION_NAME=us-east-1
```

### Configuración en Render.com

1. **Web Service** → Environment
2. Agregar variables una por una o usar archivo `.env`
3. Variables sensibles: usar "Generate Value" de Render

---

## 🌐 Despliegue en Render.com

### Opción 1: Auto-deploy con render.yaml (Recomendado)

```bash
# 1. Conectar repositorio GitHub a Render
#    Dashboard → New → Blueprint

# 2. Render detecta render.yaml automáticamente

# 3. Configurar variables de entorno en el dashboard

# 4. Deploy automático en cada push a main
```

### Opción 2: Manual

```bash
# 1. Crear Web Service
#    - Environment: Python 3.12
#    - Build Command: cd soptraloc_system && pip install -r ../requirements.txt && python manage.py collectstatic --noinput
#    - Start Command: cd soptraloc_system && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 4

# 2. Crear PostgreSQL Database
#    - Plan: Starter (Free)
#    - Link to web service

# 3. Crear Redis Instance
#    - Plan: Starter (Free)
#    - Link to web service

# 4. Crear Celery Workers (2 services)
#    Worker: celery -A config worker -l info
#    Beat: celery -A config beat -l info
```

### Post-Deploy Automático

El comando `post_deploy` se ejecuta automáticamente y realiza:
- ✅ Migraciones de base de datos
- ✅ Carga de ubicaciones GPS iniciales
- ✅ Limpieza de datos excesivos
- ✅ Collectstatic
- ✅ Verificación de producción

```bash
# Manual (si es necesario)
cd soptraloc_system
python manage.py post_deploy
```

---

## 🔄 CI/CD con GitHub Actions

### Secrets Requeridos en GitHub

```bash
# Settings → Secrets and variables → Actions

MAPBOX_API_KEY=pk.eyJ1Ijoic2FmYXJ5MTYiLCJhIjoiY21naHlvYTQ5MDNlbDJrbjJjcXRtZGg1YSJ9.WCiyTSY_CCfB02N_Nfx7kg
RENDER_DEPLOY_HOOK=https://api.render.com/deploy/srv-xxx?key=xxx
RENDER_APP_URL=https://soptraloc.onrender.com
SENTRY_DSN=https://xxx@xxx.ingest.sentry.io/xxx (opcional)
```

### Workflow

```yaml
# .github/workflows/ci.yml se ejecuta en:
- Push a main/develop
- Pull requests a main

# Fases:
1. Lint (Black, isort, Flake8)
2. Tests + Coverage (70%+ requerido)
3. Security Scan (Safety)
4. Deploy a Render (solo en main)
5. Health Check post-deploy
```

### Obtener Deploy Hook de Render

```bash
# 1. Dashboard → Web Service → Settings
# 2. Scroll to "Deploy Hook"
# 3. Click "Create Deploy Hook"
# 4. Copy URL y agregar a GitHub Secrets
```

---

## 💾 Backups y Restauración

### Backup Automático (Recomendado)

```bash
# Configurar cron job en Render
# Dashboard → Web Service → Cron Jobs → Add Cron Job

# Diario a las 2 AM UTC
0 2 * * * cd soptraloc_system && python manage.py backup_db

# Con upload a S3
0 2 * * * cd soptraloc_system && python manage.py backup_db
```

### Backup Manual

```bash
# Local
cd soptraloc_system
python manage.py backup_db

# Solo local (sin S3)
python manage.py backup_db --local-only

# Retener 30 días
python manage.py backup_db --keep-days=30
```

### Restaurar Backup

```bash
# Desde archivo local
python manage.py restore_db backups/soptraloc_backup_20251010_140000.sql.gz --yes

# Desde S3
python manage.py restore_db soptraloc_backup_20251010_140000.sql.gz --from-s3 --yes

# Con confirmación interactiva (omitir --yes)
python manage.py restore_db backups/backup.sql.gz
```

### Backup Manual con pg_dump

```bash
# Export
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql
gzip backup_*.sql

# Import
gunzip backup_20251010.sql.gz
psql $DATABASE_URL < backup_20251010.sql
```

---

## 📊 Monitoreo y Alertas

### Health Checks

```bash
# Simple (Render usa este)
curl https://soptraloc.onrender.com/health/

# Detallado
curl https://soptraloc.onrender.com/api/health/

# Response:
{
  "status": "healthy",
  "checks": {
    "database": {"status": "ok"},
    "redis": {"status": "ok"},
    "celery": {"status": "ok", "workers": 2},
    "disk": {"status": "ok", "free_percent": 75.5}
  }
}
```

### Sentry Integration

```bash
# 1. Crear cuenta en sentry.io
# 2. Crear proyecto Django
# 3. Copiar DSN
# 4. Agregar SENTRY_DSN a variables de entorno en Render
# 5. Deploy → Sentry captura errores automáticamente
```

### Logs en Render

```bash
# Dashboard → Web Service → Logs
# Ver logs en tiempo real
# Filtrar por timestamp, nivel, servicio
```

### Monitoreo de Celery

```bash
# Flower (UI para Celery) - EN DESARROLLO
# Agregar a render.yaml:
# - type: web
#   name: soptraloc-flower
#   startCommand: celery -A config flower --port=$PORT
```

---

## 🔥 Disaster Recovery

### Escenarios y Procedimientos

#### 1. Base de Datos Corrupta

```bash
# Paso 1: Identificar último backup válido
ls -lh backups/

# Paso 2: Detener workers
# Render Dashboard → Workers → Suspend

# Paso 3: Restaurar backup
python manage.py restore_db backups/soptraloc_backup_YYYYMMDD.sql.gz --yes

# Paso 4: Verificar datos
python manage.py shell
>>> from apps.containers.models import Container
>>> Container.objects.count()

# Paso 5: Reactivar workers
# Render Dashboard → Workers → Resume
```

#### 2. Deploy Fallido

```bash
# Opción A: Rollback en Render
# Dashboard → Web Service → Deploys → Previous Deploy → Redeploy

# Opción B: Rollback en Git
git revert HEAD
git push origin main
# Render auto-deploya
```

#### 3. Pérdida Completa de Servicio

```bash
# 1. Crear nuevo proyecto en Render desde Blueprint
# 2. Conectar mismo repositorio GitHub
# 3. Configurar variables de entorno
# 4. Restaurar backup de DB
# 5. Deploy
# 6. Actualizar DNS (si aplicable)
```

### RTO (Recovery Time Objective)

- **Base de datos**: 15-30 minutos
- **Aplicación completa**: 30-60 minutos
- **Rollback de código**: 5-10 minutos

### RPO (Recovery Point Objective)

- **Con backups diarios**: Máximo 24 horas de pérdida
- **Recomendado**: Backups cada 6 horas para RPO de 6 horas

---

## 📈 Escalabilidad

### Escalar Verticalmente (Render Plans)

```bash
# Starter (Free): 512MB RAM, 0.1 CPU
# Standard: 2GB RAM, 1 CPU
# Pro: 4GB RAM, 2 CPU

# Dashboard → Service → Settings → Instance Type
```

### Escalar Horizontalmente

```bash
# Render auto-escala con plan Enterprise
# O configurar múltiples regiones manualmente
```

### Optimizaciones de Performance

```python
# 1. Redis Cache (YA CONFIGURADO)
# views.py
from django.views.decorators.cache import cache_page

@cache_page(60 * 5)  # 5 minutos
def dashboard(request):
    ...

# 2. Database Connection Pooling (YA CONFIGURADO)
# settings_production.py
DATABASES = {
    'default': {
        'conn_max_age': 600,  # 10 minutos
        'conn_health_checks': True
    }
}

# 3. Celery para tareas pesadas (YA CONFIGURADO)
# tasks.py
@shared_task
def procesar_manifiestos_async(file_path):
    ...
```

### CDN para Static/Media Files

```bash
# Opción A: AWS CloudFront + S3 (configurar USE_S3=True)
# Opción B: Cloudflare CDN (gratis)
#   1. Crear cuenta en Cloudflare
#   2. Agregar dominio
#   3. Actualizar nameservers
#   4. Activar cache para /static/ y /media/
```

---

## 🔧 Troubleshooting

### Error: ModuleNotFoundError

```bash
# Causa: Dependencia faltante
# Solución:
cd soptraloc_system
pip install -r ../requirements.txt
# O en Render: Trigger manual redeploy
```

### Error: relation "apps_container" does not exist

```bash
# Causa: Migraciones no aplicadas
# Solución:
python manage.py migrate
# O en post_deploy hook
```

### Error: Redis connection refused

```bash
# Causa: Redis service no iniciado o URL incorrecta
# Solución:
# 1. Verificar REDIS_URL en variables de entorno
# 2. Reiniciar Redis service en Render Dashboard
# 3. Health check: redis-cli -u $REDIS_URL ping
```

### Error: Celery workers not running

```bash
# Causa: Worker service suspended o crasheado
# Solución:
# 1. Render Dashboard → Workers → Logs
# 2. Ver error específico
# 3. Restart service
# 4. Verificar REDIS_URL y DATABASE_URL en worker
```

### Error: 502 Bad Gateway

```bash
# Causa: App crasheada o timeout
# Solución:
# 1. Ver logs en Render Dashboard
# 2. Verificar health check endpoint
# 3. Aumentar timeout en gunicorn (--timeout=120)
# 4. Revisar memory limits
```

### Performance lento

```bash
# Diagnóstico:
python manage.py shell_plus --print-sql

# Soluciones:
# 1. Agregar indices a modelos
# 2. Usar select_related() y prefetch_related()
# 3. Activar cache Redis
# 4. Mover tareas pesadas a Celery
```

---

## 📞 Soporte

### Contactos

- **Render Support**: https://render.com/docs
- **GitHub Issues**: https://github.com/Safary16/soptraloc/issues
- **Sentry Errors**: https://sentry.io/projects/

### Recursos

- [Django Deployment Checklist](https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/)
- [Render Python Docs](https://render.com/docs/deploy-django)
- [Celery Best Practices](https://docs.celeryq.dev/en/stable/userguide/tasks.html)

---

**Última actualización**: 2025-10-10  
**Versión**: 2.0  
**Mantenedor**: Safary16
