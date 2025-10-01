# 🚀 Deploy Rápido en Render

## ⚡ Pasos Mínimos (5 minutos)

### 1. Conectar a Render

1. Ir a: https://dashboard.render.com/
2. Click: **"New +"** → **"Blueprint"**
3. Conectar GitHub → Seleccionar repo: **`Safary16/soptraloc`**
4. Branch: **`main`**

### 2. Render Detecta Automáticamente

✅ **render.yaml** encontrado  
✅ Web Service configurado  
✅ PostgreSQL Database configurado  

### 3. Click "Apply"

Render hará automáticamente:
- ✅ Crear PostgreSQL database
- ✅ Crear web service
- ✅ Instalar dependencias
- ✅ Ejecutar migraciones
- ✅ Cargar 10 contenedores de prueba
- ✅ Iniciar gunicorn

### 4. Esperar 5-10 minutos

Monitor del build en tiempo real en el dashboard.

### 5. ¡Listo!

Tu app estará en:
```
https://soptraloc-production.onrender.com
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
