# ✅ Checklist de Testing - Nuevas Funcionalidades

## Pre-requisitos

- [ ] Migraciones aplicadas: `python manage.py migrate`
- [ ] Servidor corriendo: `python manage.py runserver`
- [ ] Usuario admin creado
- [ ] Al menos 1 conductor con usuario asignado
- [ ] Al menos 1 CD activo en el sistema

---

## 🧪 Test 1: Importador de Liberación con Fechas Futuras

### Preparación
- [ ] Crear Excel de prueba con 3 contenedores:
  - Container 1: Fecha = hoy
  - Container 2: Fecha = hace 2 días
  - Container 3: Fecha = en 5 días (futuro)

### Pasos
1. [ ] Ir a `/importar/` o usar API
2. [ ] Subir archivo Excel de liberación
3. [ ] Verificar respuesta JSON incluye:
   ```json
   {
     "liberados": 2,
     "por_liberar": 1,
     "detalles": [...]
   }
   ```
4. [ ] Verificar en base de datos:
   - [ ] Container 1 y 2: estado = `liberado`
   - [ ] Container 3: estado = `por_arribar`
   - [ ] Container 3: `fecha_liberacion` = fecha futura
5. [ ] Verificar en `/estados/`:
   - [ ] Container 1 y 2 aparecen en "Liberados"
   - [ ] Container 3 aparece en "Por Arribar"

### Criterios de éxito
- ✅ Solo contenedores con fecha actual/pasada se marcan como liberados
- ✅ Contenedores con fecha futura quedan en por_arribar
- ✅ API retorna contador `por_liberar`

---

## 🧪 Test 2: Exportación a Excel

### Pasos
1. [ ] Ir a `/containers/`
2. [ ] Clic en botón **"Exportar Excel"** (verde)
3. [ ] Verificar descarga inicia automáticamente
4. [ ] Abrir archivo descargado
5. [ ] Verificar:
   - [ ] Formato es `.xlsx` (no JSON)
   - [ ] Tiene 22 columnas
   - [ ] Header con color Ubuntu (#E95420)
   - [ ] Datos poblados correctamente
   - [ ] Columna "URGENCIA" con colores según demurrage

### Criterios de éxito
- ✅ Archivo Excel descarga correctamente
- ✅ No descarga JSON
- ✅ Formato profesional con colores

---

## 🧪 Test 3: Portal del Conductor - Iniciar Ruta

### Preparación
- [ ] Crear programación con estado `asignado`
- [ ] Asignar conductor con usuario
- [ ] (Opcional) Asignar patente al conductor: "ABC123"

### Pasos

#### 3.1 Login
1. [ ] Ir a `/driver/login/`
2. [ ] Ingresar credenciales del conductor
3. [ ] Verificar redirección a dashboard

#### 3.2 Ver Asignación
4. [ ] Verificar aparece contenedor asignado
5. [ ] Verificar badge muestra estado "asignado"
6. [ ] Verificar botón **"Iniciar Ruta"** visible

#### 3.3 Iniciar Ruta
7. [ ] Clic en **"Iniciar Ruta"**
8. [ ] Verificar aparece prompt: "Confirme la PATENTE"
9. [ ] Ingresar patente: "ABC123"
10. [ ] Permitir GPS cuando navegador solicite
11. [ ] Verificar mensaje: "✅ Ruta iniciada exitosamente"
12. [ ] Verificar badge cambia a "en_ruta"
13. [ ] Verificar botón cambia a **"Notificar Arribo"**

#### 3.4 Validación de Patente Incorrecta
14. [ ] Crear otra programación
15. [ ] Intentar iniciar con patente "XYZ999" (incorrecta)
16. [ ] Verificar mensaje: "❌ La patente no coincide"

### Criterios de éxito
- ✅ Prompt de patente aparece
- ✅ GPS se obtiene automáticamente
- ✅ Estado cambia a en_ruta
- ✅ Validación de patente funciona
- ✅ GPS se registra en base de datos

---

## 🧪 Test 4: Notificar Arribo

### Preparación
- [ ] Contenedor en estado `en_ruta`

### Pasos
1. [ ] Verificar botón **"Notificar Arribo"** visible
2. [ ] Clic en botón
3. [ ] Confirmar en diálogo: "¿Ha llegado al CD?"
4. [ ] Verificar mensaje: "✅ Arribo registrado"
5. [ ] Verificar badge cambia a "entregado"
6. [ ] Verificar botón cambia a **"Notificar Vacío"**

### Verificaciones en Base de Datos
7. [ ] Container.estado = `entregado`
8. [ ] Container.fecha_entrega = timestamp actual
9. [ ] Event creado con tipo `arribo_cd`
10. [ ] Event incluye GPS (si disponible)

### Criterios de éxito
- ✅ Estado cambia correctamente
- ✅ Timestamp registrado
- ✅ Evento de auditoría creado

---

## 🧪 Test 5: Notificar Vacío

### Preparación
- [ ] Contenedor en estado `entregado`

### Pasos
1. [ ] Verificar botón **"Notificar Vacío"** visible
2. [ ] Clic en botón
3. [ ] Confirmar en diálogo: "¿Contenedor vacío?"
4. [ ] Verificar mensaje: "✅ Contenedor marcado como vacío"
5. [ ] Verificar badge cambia a "vacio"

### Verificaciones en Base de Datos
6. [ ] Container.estado = `vacio`
7. [ ] Container.fecha_vacio = timestamp actual
8. [ ] Event creado con tipo `contenedor_vacio`

### Criterios de éxito
- ✅ Estado cambia correctamente
- ✅ Timestamp registrado
- ✅ Evento de auditoría creado

---

## 🧪 Test 6: GPS Tracking

### Pasos
1. [ ] Con ruta iniciada, esperar 30 segundos
2. [ ] Verificar indicador GPS muestra "Activo"
3. [ ] Mover dispositivo (cambiar ubicación)
4. [ ] Verificar posición se actualiza en servidor

### Verificar en API
```bash
curl http://localhost:8000/api/drivers/{id}/historial/?dias=1
```

5. [ ] Verificar respuesta incluye múltiples ubicaciones
6. [ ] Verificar cada ubicación tiene timestamp

### Criterios de éxito
- ✅ GPS se actualiza cada 30 segundos
- ✅ Historial se guarda en DriverLocation
- ✅ Indicador visual funciona

---

## 🧪 Test 7: Flujo Completo End-to-End

### Escenario: Entrega completa de un contenedor

1. [ ] **Operador**: Importar Excel con 1 contenedor (fecha hoy)
   - Verificar: estado = `liberado`

2. [ ] **Operador**: Importar programación para ese contenedor
   - Verificar: estado = `programado`

3. [ ] **Operador**: Asignar conductor
   - Verificar: estado = `asignado`

4. [ ] **Conductor**: Login al portal
   - Verificar: ve contenedor asignado

5. [ ] **Conductor**: Iniciar ruta (patente + GPS)
   - Verificar: estado = `en_ruta`
   - Verificar: GPS registrado

6. [ ] **Conductor**: Notificar arribo
   - Verificar: estado = `entregado`

7. [ ] **Conductor**: Notificar vacío
   - Verificar: estado = `vacio`

8. [ ] **Verificar eventos**:
   ```bash
   # Ver eventos del contenedor
   curl http://localhost:8000/api/containers/{id}/
   ```
   - [ ] Evento: `import_liberacion`
   - [ ] Evento: `import_programacion`
   - [ ] Evento: `asignacion`
   - [ ] Evento: `inicio_ruta` (con GPS)
   - [ ] Evento: `arribo_cd` (con GPS)
   - [ ] Evento: `contenedor_vacio` (con GPS)

### Criterios de éxito
- ✅ Todo el flujo funciona sin errores
- ✅ Estados cambian correctamente
- ✅ Todos los eventos se registran
- ✅ GPS se captura en cada paso

---

## 🧪 Test 8: Casos Extremos

### 8.1 Sin GPS
1. [ ] Iniciar ruta con GPS desactivado
   - Esperado: ❌ Error "Se requieren coordenadas GPS"

### 8.2 Patente Vacía
1. [ ] Iniciar ruta sin ingresar patente (cancelar prompt)
   - Esperado: ❌ Error "Debe ingresar la patente"

### 8.3 Estado Incorrecto
1. [ ] Intentar notificar arribo en estado `asignado`
   - Esperado: ❌ Error "Contenedor debe estar en_ruta"

### 8.4 Conductor sin Patente Asignada
1. [ ] Iniciar ruta con cualquier patente
   - Esperado: ✅ Acepta cualquier patente

### Criterios de éxito
- ✅ Validaciones funcionan correctamente
- ✅ Mensajes de error son claros

---

## 📊 Resumen de Resultados

### Test Completados

| # | Test | Estado | Notas |
|---|------|--------|-------|
| 1 | Importador Fecha Futura | ⬜ | |
| 2 | Exportación Excel | ⬜ | |
| 3 | Iniciar Ruta + Patente | ⬜ | |
| 4 | Notificar Arribo | ⬜ | |
| 5 | Notificar Vacío | ⬜ | |
| 6 | GPS Tracking | ⬜ | |
| 7 | Flujo Completo E2E | ⬜ | |
| 8 | Casos Extremos | ⬜ | |

### Leyenda
- ✅ Pasó
- ❌ Falló
- ⚠️ Parcial
- ⬜ Pendiente

---

## 🐛 Bugs Encontrados

| # | Descripción | Severidad | Estado |
|---|-------------|-----------|--------|
| 1 |  |  |  |
| 2 |  |  |  |

---

**Probado por**: _______________  
**Fecha**: _______________  
**Versión**: 2.0  
**Branch**: `copilot/fix-importer-and-export-functionality`
