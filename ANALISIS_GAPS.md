# 📋 ANÁLISIS DE GAPS - SoptraLoc TMS vs Requisitos de Negocio

Fecha: 11 de Octubre, 2025
Sistema: SoptraLoc TMS v1.0

---

## ✅ LO QUE ESTÁ CORRECTO (Funciona según requisitos)

### 1. Flujo de Embarque (Excel → Contenedores)
✅ **Implementado correctamente**
- Extrae: nave, ETA, tipo, nombre contenedor, peso, puerto, comuna, vendor, sello
- Vendor y sello quedan en detalle del contenedor
- Crea contenedores con estado `por_arribar`
- Vista principal muestra: Contenedor | Tipo | Peso | Nave | Estado

### 2. Flujo de Liberación (Excel → Liberación)
✅ **Implementado correctamente**
- Actualiza fecha_liberacion
- Cambia estado de `por_arribar` a `liberado`
- Mapeo de posiciones:
  - TPS Valparaíso → ZEAL ✅
  - STI/PCE San Antonio → CLEP SAI ✅
- Puede actualizar peso si viene en el Excel

### 3. Exportación Stock
✅ **Implementado correctamente**
- Exporta contenedores liberados y por arribar
- Flag `secuenciado` marca contenedores procesados
- Lógica: Si fecha_liberacion > hoy → secuenciado = True

### 4. Flujo de Programación (Excel → Programación)
✅ **Implementado correctamente**
- Sube Excel con programaciones
- Reconoce contenedor por container_id
- Cambia estado a `programado`
- Incluye: fecha_demurrage, peso, tipo

### 5. Sistema de Alertas
✅ **Implementado correctamente**
- Alerta si fecha_programacion < 48h sin conductor
- Endpoint: `/api/programaciones/alertas/`

### 6. Asignación de Conductor
✅ **Implementado correctamente**
- Estado cambia a `asignado` cuando se asigna conductor
- Asignación manual y automática disponible

### 7. Estado "En Ruta"
✅ **Implementado correctamente**
- Conductor inicia ruta → estado `en_ruta`
- Puede actualizar posición GPS

### 8. Integración Mapbox
✅ **Implementado correctamente**
- Calcula rutas reales con tráfico
- ETAs precisos para informar a cliente
- Usado en asignación automática (score de proximidad 15%)

### 9. Historial de Operaciones
✅ **Implementado correctamente**
- Modelo `Event` registra todas las operaciones
- 11 tipos de eventos (creado, cambio_estado, asignación, etc.)
- Incluye usuario, timestamp, detalles JSON

### 10. Control de Asistencia Conductores
✅ **Implementado correctamente**
- Marcar presente/ausente por conductor
- Endpoints: `/api/drivers/{id}/marcar_presente/` y `marcar_ausente/`
- Solo asigna conductores presentes

### 11. Asignación Automática Inteligente
✅ **Implementado correctamente**
- Algoritmo con pesos:
  - Disponibilidad: 30%
  - Ocupación: 25%
  - Cumplimiento: 30%
  - Proximidad (Mapbox): 15%
- Considera solo conductores presentes
- Endpoint: `/api/programaciones/{id}/asignar_automatico/`

---

## ⚠️ LO QUE FALTA O NECESITA AJUSTES

### ❌ 1. FALTA: Fecha ETA en Embarque
**Problema**: El importador de embarque NO extrae la fecha ETA (Estimated Time of Arrival)

**Solución requerida**:
- Agregar campo `fecha_eta` o `eta` al modelo Container
- Actualizar importador de embarque para leer columna ETA del Excel
- Mostrar ETA en vista principal

**Impacto**: MEDIO - Necesario para planificación

---

### ❌ 2. FALTA: Depósito de Devolución
**Problema**: El modelo Container NO tiene campo para "depósito de devolución" (dónde devuelve contenedor vacío)

**Solución requerida**:
- Agregar campo `deposito_devolucion` al modelo Container
- Actualizar importador de liberación para leer este campo del Excel
- Usar en lógica de rutas (punto 9, 10)

**Impacto**: ALTO - Crítico para logística de retorno

---

### ❌ 3. FALTA: Fecha de Demurrage
**Problema**: El modelo Container NO tiene campo `fecha_demurrage`

**Solución requerida**:
- Agregar campo `fecha_demurrage` al modelo Container
- Actualizar importador de liberación para extraer esta fecha
- Crear sistema de alertas para demurrages cercanos
- Priorización en dashboard por demurrage cercano

**Impacto**: ALTO - Crítico para evitar costos de demurrage

---

### ❌ 4. INCOMPLETO: Estados de Descarga y Manejo de Vacíos
**Problema**: Lógica de estados 8, 9, 10 está incompleta

**Requisitos faltantes**:

#### Estado 8: "Entregado" (Arribó)
- ✅ Existe estado `entregado`
- ❌ FALTA: Cambio manual de estado (puede ser vía API)
- ❌ FALTA: Registro de hora de arribo

#### Estado 9: "Descargado" + Espera Carga
- ✅ Existe estado `descargado`
- ❌ FALTA: Registro de horario de descarga
- ❌ FALTA: Lógica diferencial por CD:
  - **Puerto Madero / Campos de Chile / Quilicura**: 
    - Conductor espera con contenedor vacío en camión
    - Debe volver con vacío a CCTI o almacén devolución
  - **El Peñón**:
    - Conductor suelta contenedor
    - Queda libre para traer vacío desde El Peñón

#### Estado 10: Manejo de Vacíos
- ✅ Existen estados `en_almacen_ccti`, `vacio_en_ruta`, `vacio_en_ccti`
- ❌ FALTA: Lógica para diferenciar comportamiento por CD
- ❌ FALTA: Campo `cd_entrega` en Container para saber dónde se entregó
- ❌ FALTA: Tracking de vacíos por CD

**Solución requerida**:
- Agregar campo `cd_entrega` (ForeignKey a CD)
- Agregar campo `hora_descarga`
- Agregar lógica en CD para identificar tipo de operación:
  - `requiere_espera_carga`: Boolean
  - `permite_soltar_contenedor`: Boolean
- Crear endpoint para registrar descarga con hora
- Actualizar lógica de ocupación de conductor según tipo de CD

**Impacto**: ALTO - Crítico para optimización de rutas

---

### ❌ 5. FALTA: Machine Learning / Aprendizaje de Tiempos
**Problema**: Sistema NO aprende de tiempos reales de operación

**Requisitos faltantes**:
- Guardar tiempos de viaje reales vs estimados
- Guardar tiempos de operación en cada CD
- Guardar tiempos en CCTI
- Mejorar predicciones basándose en histórico

**Solución requerida**:
- Crear modelo `TiempoOperacion`:
  - cd (ForeignKey)
  - tipo_operacion (carga/descarga/espera)
  - tiempo_estimado
  - tiempo_real
  - fecha
  - conductor
- Crear modelo `TiempoViaje`:
  - origen
  - destino
  - tiempo_estimado_mapbox
  - tiempo_real
  - fecha
  - conductor
- Algoritmo de aprendizaje:
  - Promedio móvil ponderado (60% últimos 10 viajes, 40% histórico)
  - Ajuste por hora del día y día de semana
- Integrar en cálculo de ocupación de conductor

**Impacto**: MEDIO - Mejora continua de eficiencia

---

### ❌ 6. FALTA: Priorización por Demurrage
**Problema**: Dashboard NO prioriza por demurrage cercano

**Solución requerida**:
- Una vez agregado campo `fecha_demurrage`
- Crear score de prioridad que combine:
  - Días hasta programación (peso 50%)
  - Días hasta demurrage (peso 50%)
- Ordenar dashboard por este score
- Alertas de demurrage cercano (<2 días)

**Impacto**: ALTO - Evita pérdidas económicas

---

### ❌ 7. FALTA: Control de Vacíos por CD
**Problema**: Sistema NO mantiene inventario de vacíos por CD

**Solución requerida**:
- El modelo CD ya tiene campos `capacidad_vacios` y `vacios_actual`
- ✅ Métodos `recibir_vacio()` y `retirar_vacio()` implementados
- ❌ FALTA: Integración con flujo de contenedores:
  - Cuando contenedor cambia a `descargado` en CD tipo "soltar"
  - Automáticamente incrementar `vacios_actual` del CD
  - Cuando se retira vacío de CD
  - Automáticamente decrementar `vacios_actual`
- ❌ FALTA: Dashboard de vacíos por CD

**Solución requerida**:
- Conectar cambios de estado con inventario de vacíos
- Crear señal (Django signal) en cambio de estado a `descargado`
- Verificar si CD `permite_soltar_contenedor`
- Si sí, llamar `cd.recibir_vacio(container)`

**Impacto**: MEDIO - Importante para planificación

---

### ❌ 8. FALTA: Tercera Opción de Movimiento
**Problema**: Sistema solo maneja liberación automática (TPS→ZEAL, STI/PCE→CLEP)

**Requisito faltante**:
> "Existe una tercera opción en la que vamos a buscarlo y lo traemos a CCTI o cliente"

**Solución requerida**:
- Agregar campo `tipo_movimiento` en Container:
  - `automatico`: Movimiento puerto (TPS→ZEAL, etc.)
  - `retiro_ccti`: CCTI va a buscar al puerto → CCTI
  - `retiro_directo`: CCTI va a buscar al puerto → Cliente
- Crear endpoint para generar "Programación de Retiro":
  - Similar a programación normal
  - Origen: Puerto (posición actual del contenedor)
  - Destino: CCTI o CD Cliente
  - Asigna conductor
- Actualizar importador de liberación para detectar este caso

**Impacto**: ALTO - Flexibilidad operacional

---

### ❌ 9. FALTA: Generación Manual de Rutas
**Problema**: Sistema solo tiene rutas automáticas vía programación

**Solución requerida**:
- Endpoint para crear ruta manual:
  ```
  POST /api/programaciones/crear_ruta_manual/
  {
    "container_id": "...",
    "origen": "...",
    "destino": "...",
    "fecha_programacion": "...",
    "tipo_operacion": "retiro/entrega"
  }
  ```
- Interfaz en frontend para crear rutas ad-hoc
- Útil para movimientos especiales (retiros de puerto, traslados CCTI, etc.)

**Impacto**: MEDIO - Mejora flexibilidad

---

### ❌ 10. FALTA: Estética Ubuntu + Logo
**Problema**: Sistema usa estilos default de Django Admin

**Solución requerida**:
- Crear tema custom para Django Admin:
  - Paleta de colores Ubuntu (naranja #E95420, gris oscuro #2C001E)
  - Tipografía Ubuntu Font
  - Esquinas redondeadas
- Crear logo SoptraLoc inspirado en logo Ubuntu:
  - Círculo con 3 personas conectadas (concepto colaboración)
  - Colores naranjas y grises
- Aplicar tema a todas las vistas
- Usar django-grappelli o django-suit para admin mejorado

**Impacto**: BAJO - Estético pero importante para UX

---

### ⚠️ 11. FALTA: Formato de Excel No Documentado
**Problema**: No se han subido archivos de ejemplo

**Solución requerida**:
- Crear carpeta `docs/excel_templates/`
- Agregar archivos de ejemplo:
  - `embarque_template.xlsx`
  - `liberacion_template.xlsx`
  - `programacion_template.xlsx`
- Documentar columnas exactas requeridas
- Agregar validación en importadores para dar feedback claro

**Impacto**: MEDIO - Facilita onboarding

---

## 📊 RESUMEN DE PRIORIDADES

### 🔴 CRÍTICAS (Bloquean operación)
1. ❌ Agregar campo `deposito_devolucion` (Punto 2)
2. ❌ Agregar campo `fecha_demurrage` + alertas (Punto 3)
3. ❌ Completar lógica de descarga por tipo de CD (Punto 4)
4. ❌ Implementar tercera opción de movimiento (Punto 8)

### 🟡 IMPORTANTES (Mejoran eficiencia)
5. ⚠️ Agregar campo `fecha_eta` (Punto 1)
6. ⚠️ Priorización por demurrage (Punto 6)
7. ⚠️ Control de vacíos integrado (Punto 7)
8. ⚠️ Generación manual de rutas (Punto 9)

### 🟢 DESEABLES (Mejora continua)
9. ⚠️ Machine Learning de tiempos (Punto 5)
10. ⚠️ Estética Ubuntu (Punto 10)
11. ⚠️ Templates Excel (Punto 11)

---

## 🎯 PLAN DE ACCIÓN RECOMENDADO

### Fase 1: Correcciones Críticas (2-3 días)
- Agregar campos faltantes al modelo Container
- Actualizar importadores
- Implementar lógica de descarga por tipo de CD
- Testing completo del flujo

### Fase 2: Mejoras Importantes (2-3 días)
- Sistema de alertas demurrage
- Priorización en dashboard
- Control de vacíos integrado
- Rutas manuales

### Fase 3: Refinamiento (1-2 días)
- Machine Learning básico (promedio móvil)
- Estética Ubuntu
- Templates Excel
- Documentación

---

## 🔍 VALIDACIÓN REQUERIDA

Por favor confirma:

1. ✅ **Formato exacto de los 3 Excel** (embarque, liberación, programación)
   - ¿Cuáles son los nombres EXACTOS de las columnas?
   - ¿Hay filas de encabezado múltiples?
   - ¿Formato de fechas? (dd/mm/yyyy, mm/dd/yyyy, etc.)

2. ✅ **Lista de CDs con tipo de operación**
   - Puerto Madero: ¿requiere_espera_carga=True?
   - Campos de Chile: ¿requiere_espera_carga=True?
   - Quilicura: ¿requiere_espera_carga=True?
   - El Peñón: ¿permite_soltar_contenedor=True?
   - Otros CDs?

3. ✅ **Lógica de demurrage**
   - ¿Fecha_demurrage es cuando VENCE o cuando COMIENZA a cobrar?
   - ¿Cuántos días antes de demurrage se debe alertar? (actualmente: 2)

4. ✅ **Definición de "ocupado" para conductor**
   - Tiempo en ruta (calculado por Mapbox) ✅
   - + Tiempo de espera carga (¿cuánto?)
   - + Tiempo de descarga (¿cuánto?)
   - ¿Varía por tipo de CD?

---

**¿Procedo con las correcciones críticas (Fase 1)?**
