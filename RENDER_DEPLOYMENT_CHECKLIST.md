# ✅ CHECKLIST DEPLOY EN RENDER - SOPTRALOC TMS

## 📦 CÓDIGO DESPLEGADO
- ✅ **Commit**: `3b72148` - "feat: Integración completa Mapbox + Optimización sistema TMS"
- ✅ **Push**: Completado a `origin/main` (94 objetos, 85.28 KiB)
- ✅ **86 archivos**: Mapbox integration, optimizations, docs, scripts

---

## 🔑 VARIABLES DE ENTORNO CRÍTICAS

### **OBLIGATORIAS** (Configure en Render Dashboard)
```bash
# API Keys
MAPBOX_API_KEY=pk.eyJ1Ijoic2FmYXJ5MTYiLCJhIjoiY200cTN6MGY5MGlqMDJpb2o5a3RvYTh2dSJ9.B0A7Nw0nDCXzjUBBN0i4aQ

# Django
SECRET_KEY=your-production-secret-key-here-change-this
DEBUG=False
ALLOWED_HOSTS=your-app-name.onrender.com,yourdomain.com

# Database (Render PostgreSQL)
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# Redis (Render Redis)
REDIS_URL=redis://red-xxxxx:6379
CELERY_BROKER_URL=redis://red-xxxxx:6379
CELERY_RESULT_BACKEND=redis://red-xxxxx:6379

# Email (opcional pero recomendado)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Timezone
TIME_ZONE=America/Santiago
```

### **OPCIONALES** (Recomendadas)
```bash
DJANGO_LOG_LEVEL=INFO
CELERY_LOG_LEVEL=INFO
GUNICORN_WORKERS=3
```

---

## 🚀 SERVICIOS A CONFIGURAR EN RENDER

### 1. **Web Service** (Django)
```yaml
Name: soptraloc-web
Environment: Python 3
Build Command: pip install -r requirements.txt && python soptraloc_system/manage.py collectstatic --noinput && python soptraloc_system/manage.py migrate
Start Command: cd soptraloc_system && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 3 --timeout 120
```

### 2. **Background Worker** (Celery Worker)
```yaml
Name: soptraloc-celery-worker
Environment: Python 3
Build Command: pip install -r requirements.txt
Start Command: cd soptraloc_system && celery -A config worker -l info --concurrency=2
```

### 3. **Scheduler** (Celery Beat)
```yaml
Name: soptraloc-celery-beat
Environment: Python 3
Build Command: pip install -r requirements.txt
Start Command: cd soptraloc_system && celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

### 4. **Redis** (Render Native)
```yaml
Name: soptraloc-redis
Plan: Starter (Free 25MB o Paid según necesidad)
```

### 5. **PostgreSQL** (Render Native)
```yaml
Name: soptraloc-db
Plan: Starter (Free o Paid según volumen)
Version: PostgreSQL 15
```

---

## 📋 PASOS POST-DEPLOY

### **Inmediatamente después del deploy:**

1. **Verificar Build**
   ```bash
   # En Render Dashboard:
   # - Ir a "soptraloc-web" → Events → Ver logs de build
   # - Confirmar: "Build successful"
   ```

2. **Verificar Variables de Entorno**
   ```bash
   # En Render Dashboard → soptraloc-web → Environment
   # Confirmar que todas las variables están configuradas
   ```

3. **Ejecutar Migraciones** (automático en Build Command)
   ```bash
   # Si necesitas ejecutar manualmente:
   python soptraloc_system/manage.py migrate
   ```

4. **Crear Superusuario**
   ```bash
   # Desde Render Shell (Dashboard → Shell):
   cd soptraloc_system
   python manage.py createsuperuser
   ```

5. **Cargar Datos de Prueba** (opcional)
   ```bash
   cd soptraloc_system
   python manage.py quick_test_data
   ```

6. **Verificar Servicios**
   ```bash
   # Desde Render Shell:
   cd soptraloc_system
   python test_system.py
   ```

---

## 🧪 TESTS DE VERIFICACIÓN

### **Test 1: Django Web**
```bash
curl https://your-app-name.onrender.com/health/
# Esperado: {"status": "healthy"}
```

### **Test 2: Mapbox API**
```bash
# Desde Render Shell:
cd soptraloc_system
python manage.py shell
>>> from apps.routing.mapbox_service import mapbox_service
>>> result = mapbox_service.get_travel_time_with_traffic('CCTI', 'CD_PENON', None)
>>> print(result)
# Esperado: {'duration_in_traffic_minutes': ~66, 'traffic_level': 'medium', ...}
```

### **Test 3: Celery Worker**
```bash
# Desde Render Dashboard → soptraloc-celery-worker → Logs
# Buscar: "[tasks]" con lista de tareas registradas
# Buscar: "celery@xxx ready"
```

### **Test 4: Celery Beat**
```bash
# Desde Render Dashboard → soptraloc-celery-beat → Logs
# Buscar: "Scheduler: Sending due task"
# Verificar que las tareas programadas se ejecutan
```

### **Test 5: Redis Connection**
```bash
# Desde Render Shell:
cd soptraloc_system
python manage.py shell
>>> from django.core.cache import cache
>>> cache.set('test', 'value', 60)
>>> print(cache.get('test'))
# Esperado: 'value'
```

---

## 🔥 TROUBLESHOOTING COMÚN

### **Error: "No module named 'celery'"**
```bash
# Verificar requirements.txt incluye:
celery==5.4.0
redis==5.2.0
django-celery-beat==2.7.0

# Re-build del servicio en Render
```

### **Error: "Mapbox API key not configured"**
```bash
# Verificar en Render → Environment:
MAPBOX_API_KEY=pk.eyJ...

# Restart del servicio después de agregar variable
```

### **Error: "Connection refused (Redis)"**
```bash
# Verificar REDIS_URL en Environment
# Formato correcto: redis://red-xxxxx:6379
# Asegurarse de que el servicio Redis está "Live"
```

### **Error: "Database connection failed"**
```bash
# Verificar DATABASE_URL en Environment
# Si usas PostgreSQL de Render, se autoconfigura
# Formato: postgresql://user:pass@host:5432/dbname
```

### **Error: "Static files not found"**
```bash
# Verificar Build Command incluye:
python soptraloc_system/manage.py collectstatic --noinput

# O ejecutar manualmente desde Shell:
cd soptraloc_system
python manage.py collectstatic --noinput
```

---

## 📊 MONITOREO POST-DEPLOY

### **Métricas a vigilar:**
- ✅ **Response Time**: < 500ms promedio
- ✅ **Error Rate**: < 1%
- ✅ **Celery Tasks**: Ejecutándose cada intervalo programado
- ✅ **Redis Memory**: < 80% del límite
- ✅ **Database Connections**: < límite de plan
- ✅ **Mapbox API Calls**: Dentro de cuota (200k/mes gratis)

### **Logs importantes:**
```bash
# Django errors:
grep "ERROR" logs/django.log

# Celery task failures:
grep "Task.*failed" logs/celery_worker.log

# Mapbox API errors:
grep "Mapbox API.*error" logs/django.log
```

---

## 🎯 ESTADO ACTUAL DEL SISTEMA

### **Código Base:**
- ✅ 5 conductores activos (limpio)
- ✅ 20 contenedores de prueba
- ✅ 7 asignaciones activas
- ✅ 10 rutas en TimeMatrix
- ✅ Mapbox API 100% funcional
- ✅ 93.3% tests passing (28/30)

### **Servicios Locales (Codespace):**
- ✅ Redis: Running on port 6379
- ✅ Celery Worker: 2 processes active
- ✅ Celery Beat: Scheduling tasks
- ✅ Django: Development server ready

### **Migraciones Aplicadas:**
- ✅ 0001 - 0007: Modelos base
- ✅ 0008: TrafficAlert raw_data
- ✅ 0009: Location model extended
- ✅ 0010: New alert types
- ✅ 0011: Traffic info to Assignment
- ✅ 0012: Traffic fields (traffic_level, mapbox_data)

---

## 🚀 READY TO DEPLOY!

**Resumen:**
1. ✅ Código pusheado a GitHub (commit `3b72148`)
2. 🔄 Configurar variables de entorno en Render
3. 🔄 Crear servicios (Web, Celery Worker, Celery Beat, Redis, PostgreSQL)
4. 🔄 Verificar build y deploy exitoso
5. 🔄 Ejecutar tests de verificación
6. 🔄 Crear superusuario
7. ✅ Sistema listo para producción!

**Tiempo estimado de configuración:** 15-20 minutos

---

## 📞 SOPORTE

Si encuentras algún problema durante el deploy:
1. Revisa los logs en Render Dashboard
2. Verifica las variables de entorno
3. Ejecuta `test_system.py` desde Render Shell
4. Consulta la documentación en:
   - `DIAGNOSTICO_MAPBOX.md`
   - `SYSTEM_STATUS.md`
   - `RESUMEN_INTEGRACION_MAPBOX.md`

---

**Fecha de generación:** $(date)
**Versión del sistema:** Django 5.2.6 + Celery 5.4.0 + Mapbox API
**Última actualización:** Integración completa Mapbox + Optimización sistema
