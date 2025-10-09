# 🎯 ACCIÓN REQUERIDA: Corregir Datos en Producción

> ⚠️ **Documento archivado (Oct 8, 2025):** Esta guía corresponde al incidente previo a la migración de Mapbox y se conserva solo como referencia histórica. Para el estado actual del sistema y procedimientos vigentes, consulta `RESUMEN_FINAL_MIGRACION.md` y `CONFIGURAR_MAPBOX_PASO_A_PASO.md`.

## 📋 Situación Actual

### ✅ Lo que YA está correcto:
1. **Código del dashboard** - Muestra fechas programadas correctamente
2. **Importador de Excel** - Asigna "Cliente Demo" correctamente
3. **Scripts de corrección** - Creados y probados
4. **Documentación** - Completa y lista

### ⚠️ Lo que necesita corrección:
**Datos viejos en la base de datos de producción** (Render)

Los contenedores importados **antes del 5 de octubre** tienen vendors (ANIKET METALS, BESTWAY, etc.) en el campo `client` en lugar de "Cliente Demo".

---

## 🚀 PASOS A SEGUIR (5 minutos)

### Paso 1: Acceder a Render Shell

1. Ir a: https://dashboard.render.com
2. Click en el servicio **`soptraloc-web`**
3. Click en el botón **"Shell"** (arriba a la derecha)
4. Esperar a que se abra la terminal

### Paso 2: Ver qué se va a cambiar (DRY-RUN)

```bash
cd /opt/render/project/src/soptraloc_system
python manage.py fix_client_vendor_data --dry-run
```

**Verás algo como:**

```
======================================================================
CORRECCIÓN DE DATOS: Cliente vs Vendor
======================================================================
⚠️  MODO DRY-RUN: No se modificará la base de datos

📊 Total de contenedores en BD: 45

📋 ESTADO ACTUAL (primeros 5):
----------------------------------------------------------------------
  CAAU 685778-8     | Cliente: ANIKET METALS PVT LTD         | Owner: ANIKET METALS PVT LTD
  CAIU 558847-6     | Cliente: BESTWAY (HONG KONG) INTER     | Owner: BESTWAY (HONG KONG) INTER

⚠️  Contenedores con problema: 45

🔍 CONTENEDORES QUE SE ACTUALIZARÍAN:
----------------------------------------------------------------------
   1. CAAU 685778-8     | ANIKET METALS PVT LTD          → Cliente Demo
   2. CAIU 558847-6     | BESTWAY (HONG KONG) INTER      → Cliente Demo
  ... y 43 más

💡 Ejecuta sin --dry-run para aplicar cambios
```

### Paso 3: Aplicar los cambios

Si todo se ve bien en el paso anterior:

```bash
python manage.py fix_client_vendor_data
```

**Verás:**

```
🔄 Actualizando 45 contenedores...
----------------------------------------------------------------------
  ✓ CAAU 685778-8     | ANIKET METALS PVT LTD          → Cliente Demo
  ✓ CAIU 558847-6     | BESTWAY (HONG KONG) INTER      → Cliente Demo
  ... y 43 más

======================================================================
VERIFICACIÓN FINAL
======================================================================

📊 RESUMEN:
  ✅ Cliente Demo: 45
  ❌ Otros clientes: 0
  📦 Total: 45

🎉 ¡ÉXITO! Todos los contenedores tienen 'Cliente Demo'
```

### Paso 4: Verificar en el Dashboard

1. Ir a: https://soptraloc.onrender.com/dashboard/
2. Verificar que la columna **"Cliente"** muestre **"Cliente Demo"** en todos los contenedores
3. Verificar que las **fechas programadas** se muestren con hora

---

## ❓ ¿Y si no hay contenedores en BD?

Si ves:

```
📊 Total de contenedores en BD: 0
✅ No hay contenedores para procesar.
```

**No hay problema.** Significa que la BD está vacía. Cuando importes nuevos contenedores, ya usarán el código correcto y tendrán "Cliente Demo" automáticamente.

---

## 🐛 Troubleshooting

### Error: "No module named 'apps'"

```bash
# Asegúrate de estar en el directorio correcto
cd /opt/render/project/src/soptraloc_system
python manage.py fix_client_vendor_data
```

### Error: "No hay usuarios en el sistema"

Esto no debería pasar en producción, pero si sucede:

```bash
python manage.py createsuperuser
# Luego ejecutar de nuevo el script
python manage.py fix_client_vendor_data
```

### El script termina pero siguen apareciendo vendors

1. Verificar que el script haya terminado con "✅ Proceso completado"
2. Refrescar el navegador (Ctrl+Shift+R o Cmd+Shift+R)
3. Verificar en shell:

```bash
python manage.py shell

>>> from apps.containers.models import Container
>>> Container.objects.values_list('client__name', flat=True).distinct()
['Cliente Demo']  # ✅ Debe aparecer solo esto
```

---

## 📊 Antes y Después

### ❌ ANTES (Incorrecto)

```
Dashboard:
┌──────────────┬─────────────────────────────┬──────┐
│ Contenedor   │ Cliente                     │ Tipo │
├──────────────┼─────────────────────────────┼──────┤
│ CAAU 685778-8│ ANIKET METALS PVT LTD      │ 40ft │ ❌
│ CAIU 558847-6│ BESTWAY (HONG KONG)        │ 40ft │ ❌
│ CGMU 531457-9│ TBC HK INTERNATIONAL       │ 40ft │ ❌
└──────────────┴─────────────────────────────┴──────┘
```

### ✅ DESPUÉS (Correcto)

```
Dashboard:
┌──────────────┬──────────────┬──────┬───────────────┐
│ Contenedor   │ Cliente      │ Tipo │ Fecha Lib/Prog│
├──────────────┼──────────────┼──────┼───────────────┤
│ CAAU 685778-8│ Cliente Demo │ 40ft │ 06/10/2025    │ ✅
│              │              │      │ 14:30         │
│ CAIU 558847-6│ Cliente Demo │ 40ft │ 05/10/2025    │ ✅
│              │              │      │ 08:30         │
│              │              │      │ [Liberado]    │
│ CGMU 531457-9│ Cliente Demo │ 40ft │ 07/10/2025    │ ✅
│              │              │      │ 10:00         │
└──────────────┴──────────────┴──────┴───────────────┘
```

---

## ✅ Checklist Final

Después de ejecutar el script, verifica:

- [ ] Columna "Cliente" muestra "Cliente Demo" (no ANIKET, BESTWAY, etc.)
- [ ] Contenedores LIBERADO muestran fecha/hora + badge verde "Liberado"
- [ ] Contenedores PROGRAMADO muestran fecha/hora
- [ ] Badges "HOY" o "MAÑANA" aparecen si corresponde
- [ ] No aparecen vendors en la columna "Cliente"

---

## 📝 Notas Importantes

1. **El script es SEGURO** - Solo actualiza el campo `client`, no modifica `owner_company`
2. **No afecta datos históricos** - Solo corrige la visualización en dashboard
3. **Se puede ejecutar varias veces** - Es idempotente (mismo resultado)
4. **Modo dry-run disponible** - Siempre puedes previsualizar antes de aplicar

---

## 🎯 Resumen Ultra-Corto

```bash
# En Render Shell:
cd /opt/render/project/src/soptraloc_system

# Ver qué se haría
python manage.py fix_client_vendor_data --dry-run

# Aplicar cambios
python manage.py fix_client_vendor_data
```

**Eso es todo.** 5 minutos y el dashboard mostrará "Cliente Demo" correctamente.

---

## 📚 Referencias

- **Guía completa:** `INSTRUCCIONES_FIX_CLIENT_DATA.md`
- **Análisis técnico:** `CORRECCION_CLIENTE_VENDOR.md`
- **Resumen general:** `RESUMEN_FINAL_DASHBOARD_OCT05.md`

---

**Fecha:** 5 de Octubre 2025  
**Prioridad:** 🔴 ALTA  
**Tiempo estimado:** ⏱️ 5 minutos  
**Dificultad:** 🟢 Fácil (solo copiar/pegar comandos)
