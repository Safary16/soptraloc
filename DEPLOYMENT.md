# 🎓 SOPTRALOC - GitHub Student Pack Setup Guide

Este documento explica cómo aprovechar al máximo el GitHub Student Pack para desplegar y mantener SOPTRALOC en la nube de forma **gratuita**.

## 🌟 Herramientas del GitHub Student Pack Utilizadas

### 1. 🚀 **Railway** (Hosting Principal)
- **Beneficio**: $5/mes en créditos
- **Ideal para**: Backend Django + PostgreSQL + Redis
- **Setup**:
  ```bash
  # Instalar Railway CLI
  npm install -g @railway/cli
  
  # Login y deploy
  railway login
  railway init
  railway up
  ```

### 2. 🎨 **Render** (Hosting Alternativo)
- **Beneficio**: Servicios gratuitos ilimitados
- **Ideal para**: Backup hosting y servicios estáticos
- **Setup**: Conectar repo GitHub directamente

### 3. ☁️ **Heroku** (Opción Enterprise)
- **Beneficio**: Créditos gratuitos para estudiantes
- **Setup**:
  ```bash
  heroku create soptraloc-app
  git push heroku main
  ```

### 4. 🗄️ **Base de Datos**
- **PostgreSQL en Railway/Render**: Incluido en el plan gratuito
- **MongoDB Atlas**: $200 en créditos
- **Redis**: Incluido en Railway/Render

### 5. 📊 **Monitoreo y Analytics**
- **Sentry**: Monitoreo de errores (gratis para estudiantes)
- **DataDog**: $200 en créditos para monitoring
- **LogDNA**: Gestión de logs

### 6. 🔧 **CI/CD**
- **GitHub Actions**: 2000 minutos/mes gratis
- **GitKraken**: Cliente Git profesional gratis

### 7. 💾 **Almacenamiento**
- **AWS**: $200 en créditos (S3, EC2, RDS)
- **DigitalOcean**: $200 en créditos
- **Azure**: $100 en créditos

## 🚀 Configuración Paso a Paso

### Paso 1: Preparar el Repositorio
```bash
git add .
git commit -m "Initial SOPTRALOC setup"
git push origin main
```

### Paso 2: Railway Deployment
1. Ir a [Railway](https://railway.app)
2. Conectar con GitHub
3. Seleccionar repositorio `soptraloc`
4. Railway detectará automáticamente Django
5. Configurar variables de entorno:
   ```env
   DJANGO_SETTINGS_MODULE=config.settings
   SECRET_KEY=your-secret-key
   DEBUG=False
   ALLOWED_HOSTS=*.railway.app
   DATABASE_URL=postgresql://... (automático)
   REDIS_URL=redis://... (automático)
   ```

### Paso 3: Configurar Base de Datos
```bash
# Railway CLI commands
railway run python manage.py migrate
railway run python manage.py createsuperuser
railway run python manage.py load_sample_data
```

### Paso 4: Configurar Dominio Personalizado (Opcional)
- Railway permite dominios personalizados
- Configurar DNS para apuntar a Railway
- SSL automático incluido

## 🔒 Variables de Entorno Requeridas

### Producción (Railway/Render/Heroku)
```env
# Django Core
SECRET_KEY=your-super-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-domain.com,*.railway.app,*.render.com

# Database (Automático en Railway/Render)
DATABASE_URL=postgresql://user:pass@host:port/dbname

# Redis (Automático en Railway/Render)
REDIS_URL=redis://host:port

# Email (Gmail/SendGrid)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Sentry (Monitoreo de errores)
SENTRY_DSN=https://your-sentry-dsn-here

# AWS S3 (Archivos estáticos)
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_STORAGE_BUCKET_NAME=your-bucket-name
AWS_S3_REGION_NAME=us-east-1
```

## 📈 Monitoreo y Analytics

### Sentry Setup
```bash
pip install sentry-sdk
```

Agregar a `settings.py`:
```python
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn=os.environ.get('SENTRY_DSN'),
    integrations=[DjangoIntegration()],
    traces_sample_rate=1.0,
    send_default_pii=True
)
```

### DataDog Setup (Opcional)
```bash
pip install ddtrace
```

## 🔄 CI/CD con GitHub Actions

El archivo `.github/workflows/django.yml` ya está configurado para:
- ✅ Tests automáticos en cada push
- ✅ Deploy automático a Railway en main branch
- ✅ Linting de código
- ✅ Verificación de migraciones

## 💡 Tips y Mejores Prácticas

### 1. Gestión de Secretos
- Usar GitHub Secrets para variables sensibles
- Never commit `.env` files
- Rotar secrets regularmente

### 2. Base de Datos
- Backups automáticos en Railway/Render
- Usar migraciones de Django correctamente
- Monitorear queries lentas

### 3. Performance
- Usar WhiteNoise para archivos estáticos
- Configurar caching con Redis
- Implementar CDN para media files

### 4. Seguridad
- SSL automático en Railway/Render
- Configurar CORS correctamente
- Rate limiting en API endpoints

## 🆘 Troubleshooting

### Problemas Comunes

1. **Build Failures**
   ```bash
   # Verificar requirements.txt
   pip freeze > requirements.txt
   
   # Verificar runtime.txt (opcional)
   echo "python-3.12" > runtime.txt
   ```

2. **Database Connection Issues**
   ```bash
   # Verificar DATABASE_URL
   railway variables
   
   # Test connection
   railway run python manage.py dbshell
   ```

3. **Static Files**
   ```bash
   # Collectstatic en producción
   railway run python manage.py collectstatic --noinput
   ```

## 📊 Costs and Limits

### Railway (Recomendado)
- ✅ $5/mes en créditos (suficiente para desarrollo)
- ✅ PostgreSQL incluido
- ✅ Redis incluido
- ✅ SSL automático
- ✅ Deploy automático

### Render (Backup)
- ✅ Web Service gratuito (con limitaciones)
- ✅ PostgreSQL gratuito (90 días)
- ⚠️ Slower cold starts en plan gratuito

### Heroku
- ⚠️ Ya no tiene plan gratuito
- 💰 Mínimo $7/mes por app
- ✅ Ecosystem maduro

## 🎯 Próximos Pasos

1. **Deploy a Railway**: Subir la aplicación
2. **Configurar Sentry**: Monitoreo de errores
3. **Setup CI/CD**: Automático con GitHub Actions
4. **Custom Domain**: Configurar dominio propio
5. **Scaling**: Configurar auto-scaling
6. **Monitoring**: Dashboard de métricas
7. **Backup Strategy**: Backups automáticos

## 📞 Soporte

- **Railway Docs**: https://docs.railway.app
- **Render Docs**: https://render.com/docs
- **GitHub Student Pack**: https://education.github.com/pack
- **Django Deployment**: https://docs.djangoproject.com/en/stable/howto/deployment/

---

🎓 **¡Aprovecha al máximo tu GitHub Student Pack para hacer realidad SOPTRALOC!**