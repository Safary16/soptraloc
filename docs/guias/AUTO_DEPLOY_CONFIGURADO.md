# 🚀 AUTO-DEPLOY CONFIGURADO - OCTUBRE 9, 2025

## ✅ PROBLEMA RESUELTO

### El Problema:
- **post_deploy.sh** cargaba **82 conductores cada vez** con `--force`
- En cada deploy se sumaban más conductores
- Resultado: **1000+ conductores** en producción (deberían ser ~50)
- Dashboard con **Error 500** al intentar cargar todos

### La Solución:
Se modificó el proceso de deploy para que sea **inteligente y automático**.

---

## 📋 LO QUE SE HIZO

### 1. **Modificado `post_deploy.sh`** (líneas 175-245)

#### PASO 5 - ANTES:
```bash
# Cargaba 82 conductores SIEMPRE con --force
python manage.py load_drivers --count=82 --force
```

#### PASO 5 - AHORA:
```bash
# Solo carga si la DB está VACÍA (primer deploy)
EXISTING_DRIVERS=$(python manage.py shell -c "from apps.drivers.models import Driver; print(Driver.objects.count())")

if [ "$EXISTING_DRIVERS" -eq 0 ]; then
    python manage.py load_drivers --count=50  # Sin --force
else
    echo "✅ Conductores ya existen, omitiendo carga"
fi
```

#### PASO 7 - NUEVO:
```bash
# Limpieza automática si hay más de 100 conductores
DRIVER_COUNT=$(contar conductores)

if [ "$DRIVER_COUNT" -gt 100 ]; then
    python manage.py aggressive_cleanup --force --keep=50
fi
```

#### PASO 8 - NUEVO:
```bash
# Verifica que existan ubicaciones GPS (CD Peñón, Quilicura, CCTI)
LOC_COUNT=$(contar ubicaciones)

if [ "$LOC_COUNT" -lt 5 ]; then
    python manage.py load_initial_times
fi
```

---

### 2. **Creado `post_deploy.py`** (management command)

Comando Django que se ejecuta automáticamente:

```python
python manage.py post_deploy
```

**Hace:**
1. ✅ Aplica migraciones pendientes
2. ✅ Verifica ubicaciones GPS (carga si faltan)
3. ✅ **Limpia conductores si >100** (mantiene los 50 mejores)
4. ✅ Recolecta archivos estáticos
5. ✅ Ejecuta `verify_production`

**Criterio de limpieza:**
- Puntaje de completitud (0-25 puntos)
- Campos: nombre, RUT, teléfono, PPU, tracto, tipo, estado
- Asignaciones: hasta +10 puntos
- Actividad reciente: +2 puntos
- Se **mantienen los 50 con mayor puntaje**

---

## 🎯 QUÉ PASARÁ EN EL PRÓXIMO DEPLOY

### Al hacer `git push`:

1. **Render detecta el push** → inicia build automático
2. **Ejecuta `build.sh`**:
   - Instala dependencias
   - Ejecuta migraciones
   - Recolecta estáticos
   - Llama a `post_deploy.sh`

3. **`post_deploy.sh` ejecuta**:
   - ✅ Crea superusuario (admin/1234)
   - ✅ Verifica conductores existentes
   - ✅ **NO carga nuevos** (porque ya existen)
   - ✅ **LIMPIA los 1000+ conductores** → deja 50
   - ✅ Verifica ubicaciones GPS
   - ✅ Carga ubicaciones si faltan

4. **Dashboard funciona**:
   - ✅ Solo carga 50 conductores
   - ✅ Sin Error 500
   - ✅ Mapbox con coordenadas reales

---

## 🔍 VERIFICAR QUE FUNCIONÓ

### 1. Ver logs de Render:
```
https://dashboard.render.com → tu servicio → Logs
```

Buscar en los logs:
```
🧹 PASO 7: Verificando y limpiando conductores
📊 Conductores actuales: 1000+
⚠️  ALERTA: Más de 100 conductores detectados
🧹 Ejecutando limpieza automática...
✅ Limpieza completada. Conductores actuales: 50
```

### 2. Acceder al dashboard:
```
https://tu-app.onrender.com/dashboard/
```
- ✅ Debe cargar sin Error 500
- ✅ Ver contenedores programados
- ✅ Ver alertas de proximidad

### 3. Ver conductores:
```
https://tu-app.onrender.com/drivers/
```
- ✅ Debe mostrar ~50 conductores
- ✅ Todos con información completa

---

## 📊 DIRECCIONES GPS CONFIGURADAS

Las siguientes coordenadas **YA ESTÁN** en el código y se cargan automáticamente:

| Ubicación | Dirección | Coordenadas |
|-----------|-----------|-------------|
| **CD El Peñón** | Av. Pdte. Jorge Alessandri 18899, San Bernardo | -33.6370, -70.7050 |
| **CD Quilicura** | Eduardo Frei Montalva 8301, Quilicura | -33.3609, -70.7266 |
| **CCTI Base Maipú** | Camino a Noviciado 1420, Maipú | -33.5167, -70.8667 |
| **CD Campos** | Av. José Joaquín Prieto 9600, Pudahuel | -33.3892, -70.8025 |
| **CD Puerto Madero** | Puerto Madero 9710, Pudahuel | -33.3925, -70.7890 |

**Mapbox** usará estas coordenadas para calcular tiempos con tráfico en tiempo real.

---

## 🛠️ COMANDOS ÚTILES (OPCIONAL)

Si necesitas ejecutar manualmente algo en Render:

### Ver estado de conductores:
```bash
cd soptraloc_system
python manage.py shell -c "from apps.drivers.models import Driver; print(f'Conductores: {Driver.objects.count()}')"
```

### Ejecutar limpieza manualmente:
```bash
cd soptraloc_system
python manage.py aggressive_cleanup --dry-run  # Ver qué se eliminaría
python manage.py aggressive_cleanup --force --keep=50  # Ejecutar
```

### Verificar producción:
```bash
cd soptraloc_system
python manage.py verify_production
```

### Cargar ubicaciones GPS:
```bash
cd soptraloc_system
python manage.py load_initial_times
```

---

## ✅ CHECKLIST POST-DEPLOY

Después del próximo deploy, verificar:

- [ ] Build exitoso en Render (sin errores rojos)
- [ ] Logs muestran limpieza de conductores
- [ ] Dashboard accesible sin Error 500
- [ ] ~50 conductores en `/drivers/`
- [ ] Mapbox muestra tiempos estimados
- [ ] Asignaciones funcionan
- [ ] Alertas de proximidad se generan

---

## 🚨 IMPORTANTE

### Este deploy es **SEGURO** porque:
1. ✅ NO borra conductores con asignaciones activas
2. ✅ Solo elimina conductores sin información completa
3. ✅ Mantiene los 50 con mejor puntaje
4. ✅ Se ejecuta en transacción (si falla, rollback automático)
5. ✅ Builds futuros NO volverán a cargar conductores

### Próximos deploys:
- **Automáticos** al hacer `git push`
- **NO cargarán** conductores nuevos
- **Mantendrán** los 50 conductores limpios
- **Actualizarán** código, migraciones, estáticos

---

## 📝 COMMITS RELACIONADOS

- `1201d9c` - AUTO-DEPLOY: Post-deploy automático con limpieza
- `de1445f` - FIX: Correcciones en management commands
- `3e79087` - DEPLOY TOOLS: Scripts completos para Render
- `1b0b777` - CRITICAL FIX: Dashboard Error 500 + Driver cleanup

---

**Fecha**: 9 de Octubre, 2025  
**Estado**: ✅ Configuración completa - Listo para deploy  
**Próxima acción**: Esperar que Render termine el build automático (~5 minutos)
