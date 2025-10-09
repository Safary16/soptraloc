# 🚀 GUÍA POST-DEPLOY RENDER - SOPTRALOC TMS

## ⚠️ PROBLEMA ACTUAL
- **1000+ conductores** en producción (deberían ser ~50)
- **Dashboard con Error 500** al intentar cargar todos los conductores
- **Verificación necesaria** de que las direcciones GPS están correctas

---

## ✅ SOLUCIÓN IMPLEMENTADA

### 1. **Código actualizado** (ya en GitHub)
- ✅ Dashboard optimizado: solo carga conductores con asignaciones recientes
- ✅ Límite de 50 conductores en vistas
- ✅ Management commands para limpieza segura
- ✅ Script de verificación de producción

### 2. **Archivos creados**
```
apps/core/management/commands/verify_production.py
apps/drivers/management/commands/aggressive_cleanup.py
apps/drivers/management/commands/cleanup_drivers.py
post_deploy_setup.sh
```

---

## 📋 PASOS PARA EJECUTAR EN RENDER

### **Opción A: Automática (Recomendada)**

1. **Ir a Render Dashboard** → Tu servicio web
2. **Clic en "Shell"** (consola interactiva)
3. **Ejecutar el script completo:**
```bash
cd /opt/render/project/src/soptraloc_system
chmod +x post_deploy_setup.sh
./post_deploy_setup.sh
```

Este script ejecuta en orden:
- ✅ Verificación del sistema
- ✅ Migraciones
- ✅ Carga de ubicaciones GPS
- ✅ Vista previa de conductores a eliminar
- ⏸️ Solicita confirmación ("ELIMINAR")
- ✅ Limpia dejando solo 50 conductores con mejor info
- ✅ Verificación final

---

### **Opción B: Manual (paso a paso)**

#### 1. **Verificar estado actual**
```bash
python manage.py verify_production
```
Esto te muestra:
- ✅ Mapbox API configurado
- ✅ Direcciones GPS de CD El Peñón, CD Quilicura, etc.
- ⚠️ Cantidad de conductores (si >100 es crítico)
- ✅ Variables de entorno

#### 2. **Aplicar migraciones** (si hay pendientes)
```bash
python manage.py migrate
```

#### 3. **Cargar ubicaciones GPS reales** (si no existen)
```bash
python manage.py load_initial_times
```
Carga las **direcciones reales** de:
- **CD El Peñón**: Av. Pdte. Jorge Alessandri 18899, San Bernardo (-33.6370, -70.7050)
- **CD Quilicura**: Eduardo Frei Montalva 8301, Quilicura (-33.3609, -70.7266)
- **CCTI**: Camino a Noviciado 1420, Maipú (-33.5167, -70.8667)
- Y más...

#### 4. **Ver qué conductores se eliminarían** (DRY RUN)
```bash
python manage.py aggressive_cleanup --dry-run
```
Muestra:
- Los 50 conductores que SE MANTIENEN (mejor info)
- Los que SE ELIMINARÁN (sin asignaciones, info incompleta)

#### 5. **ELIMINAR conductores** (acción irreversible)
```bash
python manage.py aggressive_cleanup --force --keep=50
```
O si quieres mantener más/menos:
```bash
python manage.py aggressive_cleanup --force --keep=40
```

#### 6. **Verificar resultado final**
```bash
python manage.py verify_production
```

---

## 🔍 VERIFICAR QUE TODO FUNCIONA

### 1. **Dashboard accesible**
- Ir a: `https://tu-app.onrender.com/dashboard/`
- ✅ Debería cargar sin Error 500
- ✅ Ver contenedores programados
- ✅ Ver alertas de proximidad

### 2. **Mapbox funcionando**
- En el dashboard, asignar un conductor a un contenedor
- ✅ Debería mostrar tiempo estimado con tráfico en tiempo real
- ✅ Ver distancia calculada por Mapbox

### 3. **Conductores limpios**
- Ir a: `https://tu-app.onrender.com/drivers/`
- ✅ Debería mostrar ~50 conductores
- ✅ Todos con información completa

---

## 🎯 DIRECCIONES REALES CONFIGURADAS

Las siguientes direcciones **YA ESTÁN** en el código con coordenadas GPS:

| Código | Nombre | Dirección | GPS |
|--------|--------|-----------|-----|
| **CD_PENON** | CD El Peñón | Av. Pdte. Jorge Alessandri 18899, San Bernardo | -33.6370, -70.7050 |
| **CD_QUILICURA** | CD Quilicura | Eduardo Frei Montalva 8301, Quilicura | -33.3609, -70.7266 |
| **CCTI** | CCTI Base Maipú | Camino a Noviciado 1420, Maipú | -33.5167, -70.8667 |
| **CD_CAMPOS** | CD Campos de Chile | Av. José Joaquín Prieto 9600, Pudahuel | -33.3892, -70.8025 |
| **CD_PUERTO_MADERO** | CD Puerto Madero | Puerto Madero 9710, Pudahuel | -33.3925, -70.7890 |
| **PUERTO_VALPARAISO** | Puerto Valparaíso | Av. Errázuriz, Valparaíso | -33.0266, -71.6194 |
| **PUERTO_SAN_ANTONIO** | Puerto San Antonio | Av. Pdte. Alessandri, San Antonio | -33.5900, -71.6144 |

**Mapbox usará estas coordenadas** para calcular tiempos en tiempo real.

---

## 📊 CRITERIOS DE LIMPIEZA DE CONDUCTORES

El comando `aggressive_cleanup` evalúa cada conductor con un **puntaje de completitud**:

### Puntaje (máximo ~20 puntos):
- **Nombre completo** (>3 chars): +1
- **RUT válido** (>5 chars): +1
- **Teléfono**: +1
- **Email válido**: +1
- **Dirección**: +1
- **Licencia número**: +2
- **Licencia tipo**: +2
- **Licencia vencimiento**: +2
- **Estado activo**: +1
- **Tiene asignaciones**: +5
- **Más de 5 asignaciones**: +3 bonus
- **Vehículo asignado**: +3
- **Comuna**: +1
- **Fecha nacimiento**: +1
- **Contacto emergencia**: +1

**Se mantienen los 50 con mayor puntaje**, el resto se elimina.

---

## 🆘 TROUBLESHOOTING

### Error: "relation core_location already exists"
```bash
python manage.py migrate drivers 0013 --fake
python manage.py migrate
```

### Dashboard sigue con Error 500
```bash
# Ver logs de Render
# Buscar el error específico en:
Settings → Logs
```

### Conductores no se eliminan
```bash
# Verificar que el comando se ejecuta en producción
python manage.py shell
>>> from apps.drivers.models import Driver
>>> Driver.objects.count()
```

### Mapbox no funciona
```bash
# Verificar API key en variables de entorno
python manage.py shell
>>> from django.conf import settings
>>> settings.MAPBOX_ACCESS_TOKEN
# Debe empezar con 'pk.eyJ...'
```

---

## ✅ CHECKLIST POST-DEPLOY

- [ ] Build exitoso en Render
- [ ] Migraciones aplicadas (`python manage.py migrate`)
- [ ] Ubicaciones GPS cargadas (`load_initial_times`)
- [ ] Conductores limpiados (~50 restantes)
- [ ] Dashboard accesible sin Error 500
- [ ] Mapbox muestra tiempos estimados
- [ ] Asignaciones funcionan correctamente

---

## 🔐 ACCESO A RENDER SHELL

1. Ir a: https://dashboard.render.com
2. Seleccionar tu servicio web
3. Clic en **"Shell"** en el menú lateral
4. Se abre una terminal interactiva
5. Ya estás en `/opt/render/project/src/`
6. Ejecutar comandos de Django

---

## 📞 COMANDOS ÚTILES EN RENDER

```bash
# Ver estado de migraciones
python manage.py showmigrations

# Ver conductores actuales
python manage.py shell -c "from apps.drivers.models import Driver; print(f'Conductores: {Driver.objects.count()}')"

# Ver ubicaciones en DB
python manage.py shell -c "from apps.core.models import Location; print(Location.objects.values_list('code', 'name', 'latitude', 'longitude'))"

# Test rápido de Mapbox
python manage.py shell -c "from apps.routing.mapbox_service import MapboxService; m = MapboxService(); print(m.get_travel_time_with_traffic('CCTI', 'CD_PENON'))"

# Ver logs en tiempo real
tail -f /var/log/render/*
```

---

**Fecha de creación**: 9 de Octubre, 2025  
**Última actualización**: Commit 1b0b777 (CRITICAL FIX: Dashboard Error 500 + Driver cleanup)
