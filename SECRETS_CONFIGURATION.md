# GitHub Secrets Configuration for CI/CD

Add the following secrets to your GitHub repository:
**Settings → Secrets and variables → Actions → New repository secret**

## Required Secrets

### 1. MAPBOX_API_KEY
```
pk.eyJ1Ijoic2FmYXJ5MTYiLCJhIjoiY21naHlvYTQ5MDNlbDJrbjJjcXRtZGg1YSJ9.WCiyTSY_CCfB02N_Nfx7kg
```

### 2. RENDER_DEPLOY_HOOK
Obtener de Render.com:
1. Dashboard → Web Service "soptraloc-web" → Settings
2. Scroll down to "Deploy Hook"
3. Click "Create Deploy Hook"
4. Copy the URL (ejemplo: `https://api.render.com/deploy/srv-xxxxx?key=xxxxx`)

### 3. RENDER_APP_URL
```
https://soptraloc.onrender.com
```

### 4. SENTRY_DSN (Opcional pero recomendado)
Obtener de Sentry.io:
1. Crear cuenta en https://sentry.io
2. Create Project → Django
3. Copy DSN (ejemplo: `https://xxx@xxx.ingest.sentry.io/xxx`)

## Render.com Environment Variables

Configure in Render Dashboard → Web Service → Environment:

```bash
# Core
SECRET_KEY=[Auto-generate in Render]
DEBUG=False
DJANGO_SETTINGS_MODULE=config.settings_production
PYTHON_VERSION=3.12.0

# Domains
ALLOWED_HOSTS=soptraloc.onrender.com,.onrender.com
RENDER_EXTERNAL_HOSTNAME=soptraloc.onrender.com

# Database (Auto-configured by Render)
DATABASE_URL=[Auto-linked from database]

# Redis (Auto-configured by Render)
REDIS_URL=[Auto-linked from Redis service]

# Mapbox
MAPBOX_API_KEY=pk.eyJ1Ijoic2FmYXJ5MTYiLCJhIjoiY21naHlvYTQ5MDNlbDJrbjJjcXRtZGg1YSJ9.WCiyTSY_CCfB02N_Nfx7kg

# Sentry (Optional)
SENTRY_DSN=[Your Sentry DSN]

# AWS S3 (Optional)
USE_S3=False
# AWS_ACCESS_KEY_ID=[Your key]
# AWS_SECRET_ACCESS_KEY=[Your secret]
# AWS_STORAGE_BUCKET_NAME=soptraloc-media
# AWS_S3_REGION_NAME=us-east-1
```

## Post-Configuration

After adding secrets and environment variables:

1. **Trigger first deploy**: Push to main branch
2. **Verify CI/CD**: Check Actions tab in GitHub
3. **Monitor deployment**: Check Render dashboard logs
4. **Test health check**: Visit https://soptraloc.onrender.com/health/
5. **Verify Sentry**: Trigger a test error to confirm Sentry captures it

## Troubleshooting

- **CI/CD fails**: Check GitHub Actions logs
- **Deploy fails**: Check Render logs in Dashboard
- **Sentry not working**: Verify DSN is correct and Sentry project exists
- **Mapbox errors**: Verify API key has Directions API enabled
