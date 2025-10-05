# � CORRECCIÓN AUTOMÁTICA DE DATOS - Guía Simplificada

## ⚡ Solución RÁPIDA (Sin acceso a shell)

Ya tienes todo lo que necesitas en el código. El comando de corrección está disponible como Django management command.

### 📋 Estado Actual
- ✅ Código corregido y commiteado (commit b2a8cf2)
- ✅ Comando de corrección disponible: `fix_client_vendor_data`
- ✅ Base de datos actualmente vacía (0 contenedores)
- ✅ Deploy automático activado en Render

### Síntomas
```
Dashboard muestra:
Cliente: ANIKET METALS PVT LTD        ❌ INCORRECTO
Cliente: BESTWAY (HONG KONG)          ❌ INCORRECTO
Cliente: TBC HK INTERNATIONAL         ❌ INCORRECTO
```

Debería mostrar:
```
Cliente: Cliente Demo                 ✅ CORRECTO
Cliente: Cliente Demo                 ✅ CORRECTO
Cliente: Cliente Demo                 ✅ CORRECTO
```

---

## ✅ Solución

### 1. Script Standalone (Python directo)

```bash
cd soptraloc_system
python fix_client_data.py
```

**Características:**
- ✅ Ejecuta inmediatamente
- ✅ Muestra antes/después
- ✅ Actualiza todos los contenedores
- ⚠️ No tiene modo dry-run

### 2. Django Management Command (Recomendado)

```bash
cd soptraloc_system

# Ver qué se haría (sin modificar)
python manage.py fix_client_vendor_data --dry-run

# Aplicar cambios reales
python manage.py fix_client_vendor_data
```

**Características:**
- ✅ Modo dry-run disponible
- ✅ Integrado con Django
- ✅ Mejor formato de salida
- ✅ Manejo de errores robusto

---

## 🚀 Ejecución en Producción (Render)

### Opción A: Usar Render Shell

1. Ir a https://dashboard.render.com
2. Seleccionar el servicio `soptraloc-web`
3. Click en **"Shell"** en el menú
4. Ejecutar:

```bash
# Ver qué se haría
python manage.py fix_client_vendor_data --dry-run

# Si todo se ve bien, aplicar
python manage.py fix_client_vendor_data
```

### Opción B: Usar render.yaml (Automático en deploy)

Agregar al `render.yaml`:

```yaml
services:
  - type: web
    # ... configuración existente ...
    
    # Agregar en buildCommand
    buildCommand: |
      ./build.sh
      python manage.py fix_client_vendor_data  # <-- AGREGAR ESTO
```

⚠️ **CUIDADO**: Esto ejecutará en cada deploy. Mejor usar Shell manual una vez.

---

## 📊 Output Esperado

### Modo Dry-Run

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
  CGMU 531457-9     | Cliente: TBC HK INTERNATIONAL TRAD     | Owner: TBC HK INTERNATIONAL TRAD

⚠️  Contenedores con problema: 45

🔍 CONTENEDORES QUE SE ACTUALIZARÍAN:
----------------------------------------------------------------------
   1. CAAU 685778-8     | ANIKET METALS PVT LTD          → Cliente Demo
   2. CAIU 558847-6     | BESTWAY (HONG KONG) INTER      → Cliente Demo
   3. CGMU 531457-9     | TBC HK INTERNATIONAL TRAD      → Cliente Demo
  ... y 42 más

💡 Ejecuta sin --dry-run para aplicar cambios
```

### Ejecución Real

```
======================================================================
CORRECCIÓN DE DATOS: Cliente vs Vendor
======================================================================

📊 Total de contenedores en BD: 45

⚠️  Contenedores con problema: 45

🔧 Usando usuario: admin@soptraloc.com

✅ Cliente Demo: Cliente Demo (ID: 123)

🔄 Actualizando 45 contenedores...
----------------------------------------------------------------------
  ✓ CAAU 685778-8     | ANIKET METALS PVT LTD          → Cliente Demo
  ✓ CAIU 558847-6     | BESTWAY (HONG KONG) INTER      → Cliente Demo
  ✓ CGMU 531457-9     | TBC HK INTERNATIONAL TRAD      → Cliente Demo
  ... y 42 más

======================================================================
VERIFICACIÓN FINAL
======================================================================

📋 ESTADO FINAL (primeros 5):
----------------------------------------------------------------------
  ✅ CAAU 685778-8     | Cliente: Cliente Demo                  | Owner: ANIKET METALS PVT LTD
  ✅ CAIU 558847-6     | Cliente: Cliente Demo                  | Owner: BESTWAY (HONG KONG) INTER
  ✅ CGMU 531457-9     | Cliente: Cliente Demo                  | Owner: TBC HK INTERNATIONAL TRAD

📊 RESUMEN:
  ✅ Cliente Demo: 45
  ❌ Otros clientes: 0
  📦 Total: 45

🎉 ¡ÉXITO! Todos los contenedores tienen 'Cliente Demo'

======================================================================
✅ Proceso completado: 45 contenedores actualizados
======================================================================
```

---

## 🔍 Verificación Post-Corrección

### 1. Verificar en Dashboard

```
Ir a: https://soptraloc.onrender.com/dashboard/

Revisar columna "Cliente":
- ✅ Todos deben mostrar "Cliente Demo"
- ❌ Si aparece ANIKET METALS, BESTWAY, etc. → ejecutar script de nuevo
```

### 2. Verificar en Base de Datos

```bash
python manage.py shell

>>> from apps.containers.models import Container
>>> Container.objects.values_list('client__name', flat=True).distinct()
['Cliente Demo']  # ✅ Solo debe aparecer esto
```

### 3. Verificar Fechas Programadas

```
Dashboard debe mostrar:

Para LIBERADO:
  Fecha: 05/10/2025
  Hora: 08:30
  Badge: [Liberado]

Para PROGRAMADO:
  Fecha: 06/10/2025
  Hora: 14:30
  Badge: [HOY/MAÑANA si aplica]
```

---

## 📁 Archivos Creados

1. **`fix_client_data.py`** (raíz de soptraloc_system)
   - Script standalone Python
   - No requiere argumentos
   - Ejecución simple

2. **`apps/containers/management/commands/fix_client_vendor_data.py`**
   - Django management command
   - Soporta --dry-run
   - Mejor integración

---

## 🎯 Cuándo Ejecutar

### ✅ Ejecutar SI:
- Dashboard muestra vendors en lugar de "Cliente Demo"
- Importaste contenedores antes del 5 de octubre 2025
- Ves nombres como ANIKET METALS, BESTWAY, TBC HK, etc.

### ❌ NO ejecutar SI:
- Dashboard ya muestra "Cliente Demo" correctamente
- No hay contenedores en la BD
- Ya ejecutaste el script anteriormente

---

## 🐛 Troubleshooting

### Error: "No module named 'apps.containers'"

```bash
# Asegúrate de estar en soptraloc_system/
cd soptraloc_system
python manage.py fix_client_vendor_data
```

### Error: "No hay usuarios en el sistema"

```bash
# Crear superuser primero
python manage.py createsuperuser
# Luego ejecutar el script
python manage.py fix_client_vendor_data
```

### Error: "Company matching query does not exist"

- El script crea "Cliente Demo" automáticamente
- Si falla, verificar que `_get_or_create_company` funcione

---

## 📝 Notas Técnicas

### ¿Qué hace el script?

1. **Identifica contenedores problemáticos**
   ```python
   if not container.client or container.client.name != "Cliente Demo":
       problematic.append(container)
   ```

2. **Crea/obtiene "Cliente Demo"**
   ```python
   client_demo = _get_or_create_company("Cliente Demo", user)
   ```

3. **Actualiza cada contenedor**
   ```python
   container.client = client_demo
   container.save()
   ```

4. **NO modifica owner_company**
   - `owner_company` mantiene el vendor real (ANIKET METALS, etc.)
   - Solo `client` se actualiza a "Cliente Demo"

### ¿Por qué se necesita?

El código **actual** ya está correcto:
- ✅ `excel_importers.py` asigna "Cliente Demo" correctamente
- ✅ `models.py` no copia owner_company a client
- ✅ `dashboard.html` muestra client correctamente

**PERO** los datos **viejos** (importados antes del fix) siguen incorrectos en BD.

---

## ✅ Checklist Post-Ejecución

- [ ] Script ejecutado sin errores
- [ ] Output mostró "✅ Proceso completado"
- [ ] Dashboard muestra "Cliente Demo" en todos los contenedores
- [ ] Columna "Cliente" no muestra vendors (ANIKET, BESTWAY, etc.)
- [ ] Fechas de programación se visualizan correctamente
- [ ] Fechas de liberación se visualizan correctamente

---

**Creado**: 5 de Octubre 2025
**Autor**: Sistema SoptraLoc
**Prioridad**: 🔴 ALTA - Corrige datos incorrectos en producción
