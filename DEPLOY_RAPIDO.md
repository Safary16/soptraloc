# � Actualización Rápida del Servicio Existente

## ⚡ Para el servicio existente: https://soptraloc.onrender.com/

### Opción A: Auto-Deploy (AUTOMÁTICO) ✨

Ya hiciste `git push origin main` → **¡Listo!**

Render detecta el cambio y deploya automáticamente.

**Monitorear en**:
```
https://dashboard.render.com/ → soptraloc → Logs
```

---

### Opción B: Manual Deploy (SI AUTO-DEPLOY ESTÁ OFF)

1. Ir a: https://dashboard.render.com/
2. Click en servicio: **`soptraloc`**
3. Click: **"Manual Deploy"** → **"Deploy latest commit"**
4. Esperar 5 minutos

---

### ✅ Verificación (después de 5 min)

```bash
# 1. URL principal
open https://soptraloc.onrender.com/dashboard/

# 2. Verificar reloj en navbar
# Debe mostrar: HH:MM:SS y fecha actual

# 3. API de urgentes
curl https://soptraloc.onrender.com/api/v1/containers/urgent/

# 4. Health check
curl https://soptraloc.onrender.com/health/
```

---

## 🔍 Verificación Rápida

```bash
# Health check
curl https://soptraloc-production.onrender.com/health/

# Dashboard
open https://soptraloc-production.onrender.com/dashboard/

# Admin (user: admin, pass: admin123)
open https://soptraloc-production.onrender.com/admin/
```

---

## 📊 Características Incluidas

✅ Reloj en tiempo real en navbar  
✅ Sistema de alertas de proximidad (< 2h)  
✅ 10 contenedores de prueba cargados  
✅ Dashboard optimizado con priorización  
✅ API REST completa con Swagger  
✅ Gestión de conductores y asignaciones  
✅ Import/Export de Excel  

---

## 🆘 Si Algo Falla

Ver logs en tiempo real:
```
Dashboard → soptraloc-production → Logs
```

Problemas comunes resueltos en:
```
DEPLOYMENT_RENDER.md (sección Troubleshooting)
```

---

## 🎯 Todo Listo

El sistema está **100% funcional** y listo para producción.

**Versión**: v2.0-optimized  
**Última actualización**: Octubre 2025
