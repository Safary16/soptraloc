# 🐛 Corrección Crítica: Cliente vs Vendor - 5 de Octubre 2025

## 🎯 Problema Identificado

El dashboard mostraba información **incorrecta** en la columna "Cliente":

### ❌ ANTES (Incorrecto)
```
Cliente: ANIKET METALS PVT LTD
Cliente: BESTWAY (HONG KONG) INTERNATIONAL LI
Cliente: TBC HK INTERNATIONAL TRADER & CONSUL
Cliente: SEMTEL HONG KONG LTD
Cliente: GUANLONG CORPORATION LIMITED
```

**Problema**: Estos son los **VENDORS** (proveedores de mercancía), NO el cliente que solicita el servicio de transporte.

### ✅ DESPUÉS (Correcto)
```
Cliente: Cliente Demo
Cliente: Cliente Demo
Cliente: Cliente Demo
```

**Correcto**: "Cliente Demo" es quien solicita el servicio de transporte (la compañía de logística).

---

## 🔍 Análisis del Problema

### Conceptos Clave
1. **Vendor/Owner Company** = Dueño de la mercancía (ej: ANIKET METALS)
   - Aparece en el Excel de manifiesto en columna "Vendor"
   - Es el fabricante/proveedor de los productos en el contenedor

2. **Client** = Cliente del servicio de transporte (ej: Cliente Demo)
   - Quien contrata a SoptraLoc para transportar los contenedores
   - Debería ser siempre la misma compañía (Cliente Demo)

### Root Cause
El modelo `Container` tenía lógica incorrecta en el método `save()`:

```python
# ❌ CÓDIGO INCORRECTO (REMOVIDO)
def save(self, *args, **kwargs):
    # Usar owner_company como client si no hay client específico
    if not self.client and self.owner_company:
        self.client = self.owner_company  # 🔴 ESTO ESTABA MAL
```

Esto causaba que el vendor (ANIKET METALS) se asignara automáticamente como cliente.

---

## ✅ Solución Implementada

### 1. Corrección en `excel_importers.py`

**Antes**:
```python
company_name = row.get(column_lookup.get("vendor"))
company = _get_or_create_company(company_name, user)
container.owner_company = company
# client no se asignaba, entonces save() lo copiaba de owner_company
```

**Después**:
```python
# Vendor es el dueño de la mercancía (ej: ANIKET METALS)
vendor_name = row.get(column_lookup.get("vendor")) or row.get(column_lookup.get("division"))
vendor_company = _get_or_create_company(vendor_name, user)

# Cliente es quien solicita el servicio de transporte (Cliente Demo)
client_company = _get_or_create_company("CLIENTE DEMO", user)

container.owner_company = vendor_company  # Dueño de mercancía
container.client = client_company         # Cliente del servicio de transporte
```

### 2. Corrección en `models.py`

**Antes**:
```python
def save(self, *args, **kwargs):
    # Usar owner_company como client si no hay client específico
    if not self.client and self.owner_company:
        self.client = self.owner_company  # ❌ INCORRECTO
        
    # Calcular días si hay fechas disponibles
    ...
```

**Después**:
```python
def save(self, *args, **kwargs):
    # Calcular días si hay fechas disponibles
    ...
    # ✅ Lógica incorrecta ELIMINADA
```

---

## 📅 Problema Adicional: Fechas No Visibles

### ❌ ANTES
```
Fecha Programada: Sin programar
```
Incluso cuando los contenedores estaban LIBERADOS o PROGRAMADOS con fecha/hora.

### ✅ DESPUÉS

**Para contenedores LIBERADO**:
```
Fecha Liberación/Programación: 05/10/2025
                               08:30
                               [Badge verde: Liberado]
```

**Para contenedores PROGRAMADO**:
```
Fecha Liberación/Programación: 06/10/2025
                               14:30
                               [Badge: HOY/MAÑANA si aplica]
```

### Código del Template

**Antes**:
```html
<th>Fecha Programada</th>
...
<td>
    {% if container.scheduled_date %}
        {{ container.scheduled_date|date:"d/m/Y" }}
    {% endif %}
</td>
```

**Después**:
```html
<th>Fecha Liberación/Programación</th>
...
<td>
    {% if container.status == 'LIBERADO' and container.release_date %}
        {{ container.release_date|date:"d/m/Y" }}
        {% if container.release_time %}
            <br><small class="text-muted">{{ container.release_time|time:"H:i" }}</small>
        {% endif %}
        <br><span class="badge bg-success">Liberado</span>
    {% elif container.scheduled_date %}
        {{ container.scheduled_date|date:"d/m/Y" }}
        {% if container.scheduled_time %}
            <br><small class="text-muted">{{ container.scheduled_time|time:"H:i" }}</small>
        {% endif %}
        ...
    {% endif %}
</td>
```

---

## 📊 Resultado Final

### Dashboard Correcto
```
┌───────────────┬──────────────┬──────┬────────────────────────┬────────────┬──────────────┬────────────┐
│ Contenedor    │ Cliente      │ Tipo │ Fecha Lib/Prog         │ CD Destino │ Conductor    │ Estado     │
├───────────────┼──────────────┼──────┼────────────────────────┼────────────┼──────────────┼────────────┤
│ CAAU 685778-8 │ Cliente Demo │ 40ft │ -                      │ -          │ -            │ Por Arribar│
│ CAIU 558847-6 │ Cliente Demo │ 40ft │ 05/10/2025             │ -          │ -            │ Liberado   │
│               │              │      │ 08:30                  │            │              │ [Verde]    │
│ CGMU 531457-9 │ Cliente Demo │ 40ft │ 06/10/2025             │ CD PEÑÓN   │ SIN ASIGNAR  │ Programado │
│               │              │      │ 14:30                  │            │              │            │
└───────────────┴──────────────┴──────┴────────────────────────┴────────────┴──────────────┴────────────┘
```

### Ventajas
✅ **Cliente siempre es "Cliente Demo"** (correcto para presentación)
✅ **Vendor/Owner se mantiene en BD** para trazabilidad pero no se muestra en dashboard
✅ **Fechas de liberación visibles** con hora y badge verde
✅ **Fechas de programación visibles** con hora
✅ **Columna renombrada** para mayor claridad

---

## 🧪 Validación

### Tests Ejecutados
```bash
Ran 12 tests in 4.485s

OK ✅
```

### Verificación Manual
1. ✅ Importar manifest → `client` = "Cliente Demo"
2. ✅ Dashboard muestra "Cliente Demo" en todos los contenedores
3. ✅ Contenedores LIBERADO muestran fecha/hora de liberación
4. ✅ Contenedores PROGRAMADO muestran fecha/hora de programación
5. ✅ Badge verde "Liberado" se muestra correctamente

---

## 📝 Archivos Modificados

1. **`apps/containers/services/excel_importers.py`**
   - Separación de vendor_company y client_company
   - Asignación explícita de ambos campos

2. **`apps/containers/models.py`**
   - Eliminación de lógica incorrecta en save()

3. **`templates/core/dashboard.html`**
   - Lógica condicional para mostrar release_date vs scheduled_date
   - Badge verde para contenedores liberados
   - Columna renombrada a "Fecha Liberación/Programación"

---

## 🚀 Impacto en Producción

### Antes del Deploy
```
Cliente: ANIKET METALS PVT LTD          ❌ Incorrecto
Fecha Programada: Sin programar         ❌ Incorrecto (tenía fecha)
```

### Después del Deploy
```
Cliente: Cliente Demo                   ✅ Correcto
Fecha Liberación/Programación:          ✅ Correcto
  05/10/2025 08:30
  [Badge: Liberado]
```

---

## 📋 Checklist de Verificación Post-Deploy

- [ ] Importar manifest nuevo
- [ ] Verificar que columna "Cliente" muestre "Cliente Demo"
- [ ] Importar liberacion.xlsx
- [ ] Verificar que muestre fecha/hora de liberación
- [ ] Verificar badge verde "Liberado"
- [ ] Importar programacion.xlsx
- [ ] Verificar que muestre fecha/hora de programación
- [ ] Verificar CD de destino normalizado (sin código)

---

## 🎯 Resumen Ejecutivo

### Problema
El sistema confundía el **vendor** (proveedor de mercancía) con el **cliente** (quien solicita transporte).

### Solución
- Separación clara de conceptos: `owner_company` (vendor) vs `client` (cliente)
- Asignación automática de "Cliente Demo" como cliente del servicio
- Mejora en visualización de fechas según estado del contenedor

### Resultado
Dashboard ahora muestra información precisa y profesional, lista para presentación sin datos privados.

---

**Commit**: `8917ccd`
**Fecha**: 5 de Octubre 2025
**Tests**: ✅ 12/12 OK
**Deploy**: ✅ Listo para producción
**Prioridad**: 🔴 CRÍTICO - Corrige información mostrada al usuario
