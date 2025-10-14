# 🚀 Guía Rápida - Nuevas Funcionalidades

## Para Operadores de Importación

### ✅ Importar Excel de Liberación

**¿Qué cambió?**
- Ahora respeta las **fechas futuras** del Excel
- Contenedores con fecha futura **NO** se liberan automáticamente

**Ejemplo:**

| Container | Fecha en Excel | Fecha Hoy | Resultado |
|-----------|----------------|-----------|-----------|
| ABCD123 | 10/10/2025 | 14/10/2025 | ✅ `liberado` (pasado) |
| EFGH456 | 20/10/2025 | 14/10/2025 | ⏳ `por_arribar` (futuro) |

**Respuesta del sistema:**
```
✅ Importación completada:
   • 15 liberados
   • 8 por liberar (fechas futuras)
   • 0 errores
```

---

## Para Conductores

### 📱 Portal del Conductor - Nuevo Flujo

#### 1️⃣ Ver Asignación
- Aparece contenedor con estado "Asignado"
- Botón: **"Iniciar Ruta"**

#### 2️⃣ Confirmar Patente
```
🚚 Confirme la PATENTE del vehículo que está usando:

Ejemplo: ABC123, ABCD12, etc.
```
- ✅ Ingresar patente del camión
- ✅ Permitir GPS
- ✅ Clic OK

**El sistema valida:**
- Si tienes patente asignada → debe coincidir
- GPS activo → registra tu ubicación

#### 3️⃣ En Ruta
- Estado cambia a "En Ruta"
- GPS se actualiza cada 30 segundos
- Botón: **"Notificar Arribo"**

#### 4️⃣ Llegar al CD
- Clic en **"Notificar Arribo"**
- Confirmar: "¿Ha llegado al CD?"
- Estado cambia a "Entregado"
- Botón: **"Notificar Vacío"**

#### 5️⃣ Contenedor Vacío
- Después de descargar
- Clic en **"Notificar Vacío"**
- Confirmar: "¿Contenedor vacío?"
- Estado cambia a "Vacío"
- ✅ Entrega completa

---

## Para Administradores

### 🔧 Aplicar Migraciones

```bash
# Activar entorno virtual
source venv/bin/activate

# Aplicar migraciones
python manage.py migrate drivers
python manage.py migrate programaciones

# Verificar
python manage.py showmigrations
```

### 📊 Exportar a Excel

**URL correcta:**
```
http://tu-dominio.com/api/containers/export-liberacion-excel/
```

**Botones en el sistema:**
- Desde `/containers/` → Botón "Exportar Excel"
- Desde `/estados/` → Botón verde "Exportar Excel"

**Formato del archivo:**
- ✅ Excel (.xlsx)
- ✅ 22 columnas
- ✅ Colores según urgencia demurrage

### 👥 Asignar Patente a Conductores

**Opción 1: Admin Django**
```
/admin/drivers/driver/
→ Editar conductor
→ Campo: "Patente"
→ Ejemplo: "ABC123"
```

**Opción 2: Importar desde Excel**
- Si el Excel de conductores incluye columna "patente"
- Se importa automáticamente

---

## ❓ Preguntas Frecuentes

### ¿Qué pasa si no ingreso la patente?
- ❌ No puedes iniciar la ruta
- El sistema solicita la patente obligatoriamente

### ¿Qué pasa si ingreso patente incorrecta?
- ✅ Si NO tienes patente asignada → acepta cualquier patente
- ❌ Si tienes patente asignada → debe coincidir exactamente

### ¿El GPS es obligatorio?
- ✅ Sí, para iniciar ruta
- ⚠️ Para arribo/vacío es opcional (pero recomendado)

### ¿Puedo ver el historial GPS?
- Sí, desde el admin o API:
  ```
  /api/drivers/{id}/historial/?dias=7
  ```

### ¿Cómo saber si un contenedor tiene fecha futura?
- En el Excel de liberación, busca columna "ESTADO"
- `por_arribar` = fecha futura
- `liberado` = fecha actual o pasada

---

## 🎯 Estados del Contenedor

```
por_arribar → liberado → programado → asignado 
    ↓            ↓           ↓           ↓
(futuro)     (hoy/pasado)  (con CD)   (con conductor)

asignado → en_ruta → entregado → descargado → vacio
    ↓         ↓          ↓           ↓          ↓
 (espera)  (confirma  (llegó)   (descargó)  (retiro)
          patente+GPS)
```

---

## 📞 Soporte

**Errores comunes:**

1. **"Contenedor debe estar en_ruta"**
   - Solución: Primero debes iniciar la ruta

2. **"La patente no coincide"**
   - Solución: Ingresar la patente correcta o contactar admin

3. **"GPS desactivado"**
   - Solución: Activar GPS en el navegador
   - Chrome: Configuración → Privacidad → Permisos de sitio

4. **"Exportación descarga JSON"**
   - Solución: Usar el botón verde "Exportar Excel" (no el de stock)

---

**Última actualización**: 2025-10-14  
**Versión**: 2.0
