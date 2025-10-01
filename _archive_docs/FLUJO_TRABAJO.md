# Flujo de Trabajo Completo - Soptraloc

## Descripción General
Sistema de gestión logística para contenedores de importación con seguimiento completo desde arribo hasta devolución.

---

## 1. 📦 IMPORTACIÓN DE NAVE (Estado: POR_ARRIBAR)

### Archivo: APL CHARLESTON ETA 26-09 SERRANO CCTI.xlsx
**Objetivo:** Registrar contenedores que vienen en tránsito marítimo

### Proceso:
1. Subir archivo Excel con manifiesto de nave
2. Sistema reconoce formato de contenedor:
   - **Entrada:** `AAAU1234561` (sin espacios ni guiones)
   - **Salida:** `AAAU 123456-1` (formato estándar)
3. Contenedores se crean en estado **POR_ARRIBAR**
4. Se registran:
   - Cliente
   - Tipo de contenedor (20', 40', 40HC, etc.)
   - Puerto de origen (SAN ANTONIO o VALPARAÍSO)
   - ETA (estimada de arribo)
   - Nave y línea naviera
   - Pesos (tara, carga, total)
   - Sello y descripción de mercadería

### Endpoint:
```
POST /api/v1/containers/import-manifest/
```

---

## 2. 🚢 LIBERACIÓN DE CONTENEDORES (Estado: LIBERADO)

### Archivo: WALMART TTS.xls
**Objetivo:** Actualizar horarios de liberación cuando la nave descarga

### Proceso:
1. Subir archivo Excel con horarios de liberación
2. Sistema busca contenedores por número
3. Actualiza:
   - Fecha de liberación
   - Hora de liberación
   - Cambia estado a **LIBERADO**
4. Contenedores quedan disponibles para programación

### Endpoint:
```
POST /api/v1/containers/import-release/
```

---

## 3. 📤 EXPORTAR CONTENEDORES LIBERADOS

### Objetivo: Generar Excel para enviar al cliente (Walmart) para programación

### Proceso:
1. Sistema filtra contenedores en estado LIBERADO
2. Genera archivo Excel con:
   - Número de contenedor
   - Tipo
   - Fecha de liberación
   - Terminal
   - Observaciones
3. Se envía al cliente por correo

### Endpoint:
```
GET /api/v1/containers/export-liberated/
```

### Botón en Dashboard:
```
📥 Exportar Liberados
```

---

## 4. 📋 PROGRAMACIÓN OPERATIVA (Estado: PROGRAMADO)

### Archivo: PROGRAMACION.xlsx
**Objetivo:** Aplicar programación del cliente

### Proceso:
1. Cliente devuelve Excel con programación
2. Subir archivo con datos:
   - Fecha y hora de entrega
   - CD de destino (Quilicura, Campos, Madero, Peñón)
   - Fecha de demurrage (alerta devolución)
   - Tipo de contenedor
3. Sistema actualiza:
   - scheduled_date, scheduled_time
   - cd_location
   - demurrage_date
   - Estado → **PROGRAMADO**
4. **Determina posición automática según puerto:**
   - SAN ANTONIO → **CLEP** (extraportuario SAI)
   - VALPARAÍSO → **ZEAL** (extraportuario VAP)
   - VALPARAÍSO directo CCTI → Manual

### Endpoint:
```
POST /api/v1/containers/import-programming/
```

---

## 5. 👨‍✈️ ASIGNACIÓN DE CONDUCTOR

### Reglas:
- **Contenedor en CLEP o ZEAL** → Asignar conductor **TRONCAL**
- **Contenedor en CCTI** → Asignar conductor **LOCAL**

### Proceso:
1. Filtrar contenedores programados
2. Ver posición actual
3. Asignar conductor según tipo:
   - Troncal: Largo recorrido desde puerto
   - Local: Distribución local desde CCTI

### Estado:
```
PROGRAMADO → ASIGNADO
```

---

## 6. 🚛 INICIO DE RUTA (Estado: EN_RUTA)

### Proceso:
1. Conductor confirma inicio de ruta
2. Sistema registra:
   - `tiempo_inicio_ruta = now()`
   - Estado → **EN_RUTA**
   - current_position → EN_RUTA

### Acción:
```
Botón: 🚀 Iniciar Ruta
```

---

## 7. 📍 LLEGADA AL CD (Estado: ARRIBADO)

### Proceso:
1. Conductor confirma llegada
2. Sistema registra:
   - `tiempo_llegada = now()`
   - Estado → **ARRIBADO**
   - `cd_arrival_date` y `cd_arrival_time`
   - current_position → CD específico

### Acción:
```
Botón: 📍 Marcar Llegada
```

---

## 8. 📦 DESCARGA (Estado: DESCARGANDO)

### Proceso:
1. Iniciar descarga
2. Sistema registra:
   - `tiempo_descarga = now()`
   - Estado → **DESCARGANDO**

### Tiempos calculados:
- **Duración ruta:** `tiempo_llegada - tiempo_inicio_ruta`
- **Duración descarga:** `tiempo_finalizacion - tiempo_descarga`
- **Duración total:** Desde asignación hasta finalización

---

## 9. ✅ FINALIZACIÓN Y DEVOLUCIÓN (Estado: FINALIZADO)

### Opciones:
1. **Contenedor vacío:**
   - Opción A: Traer a CCTI → luego a depósito
   - Opción B: Directo a depósito de devolución

2. **Reglas según depósito:**
   - **Apellido VAP o SAI** → Quinta Región → Conductor **TRONCAL**
   - **Sin apellido VAP/SAI** → Santiago → Conductor **LOCAL**

### Alertas Demurrage:
- Sistema alerta cuando está cerca demurrage_date
- Prioriza devolución de vacíos próximos a demurrage
- Evita sobrecostos por estadía

### Estado final:
```
ARRIBADO → FINALIZADO
```

---

## 10. 🤖 OPTIMIZACIÓN CON MACHINE LEARNING

### Datos recopilados:
- Tiempo de desplazamiento por ruta
- Tiempo de espera en CD
- Tiempos de descarga
- Patrones de tráfico

### Mejoras automáticas:
- Predice tiempos de devolución
- Optimiza asignación de conductores
- Ajusta programación según historial
- Detecta cuellos de botella

---

## Estados del Contenedor

```
POR_ARRIBAR → (llega nave) → 
EN_SECUENCIA → (descarga terminal) → 
DESCARGADO → (liberación) → 
LIBERADO → (programación cliente) → 
PROGRAMADO → (asigna conductor) → 
ASIGNADO → (inicio ruta) → 
EN_RUTA → (llegada CD) → 
ARRIBADO → (descarga) → 
FINALIZADO
```

---

## Posiciones del Contenedor

```
EN_PISO → En terminal, en piso
EN_CHASIS → En terminal, sobre chasis
CCTI → Base Maipú (puede venir directo desde VAP)
ZEAL → Extraportuario Valparaíso
CLEP → Extraportuario San Antonio
EN_RUTA → Viajando
CD_QUILICURA → Centro distribución Quilicura
CD_CAMPOS → Centro distribución Campos
CD_MADERO → Centro distribución Puerto Madero
CD_PENON → Centro distribución El Peñón
DEPOSITO_DEVOLUCION → Depósito para devolución vacío
```

---

## Tipos de Conductor

### TRONCAL
- Rutas largas desde/hacia puerto
- CLEP ↔ Santiago
- ZEAL ↔ Santiago
- CD → Depósito VAP/SAI

### LOCAL
- Distribución local Santiago
- CCTI → CD Santiago
- CD → Depósito Santiago

---

## Comandos útiles

### Resetear datos de testing:
```bash
python manage.py reset_test_data --keep-containers 30
```

### Eliminar todos los contenedores:
```bash
python manage.py reset_test_data --delete-all
```

### Exportar contenedores liberados:
```
GET /api/v1/containers/export-liberated/
```

---

## Archivos de ejemplo

1. **APL CHARLESTON ETA 26-09 SERRANO CCTI.xlsx** - Manifiesto de nave
2. **WALMART TTS.xls** - Liberaciones
3. **PROGRAMACION.xlsx** - Programación del cliente

---

## Dashboard Principal

### Estadísticas:
- Total contenedores
- Por arribar
- Liberados
- Programados
- En ruta
- Arribados
- Finalizados

### Acciones rápidas:
- 📤 Subir manifiesto
- 📋 Aplicar liberaciones
- 📥 Exportar liberados
- 📅 Actualizar programación
- 👥 Asignar conductores
- 🤖 Auto-asignar (optimizado)

---

## Consideraciones importantes

1. **Formato de contenedor:** Sistema reconoce automáticamente el formato sin espacios ni guiones
2. **Puerto automático:** Determina CLEP o ZEAL según puerto de origen
3. **Alertas demurrage:** 2 días antes del vencimiento
4. **Tiempos registrados:** Todos los movimientos tienen timestamp para facturación
5. **Machine Learning:** Se entrena con cada operación completada

---

## Próximas mejoras

- [ ] Integración con GPS en tiempo real
- [ ] Notificaciones push a conductores
- [ ] Dashboard móvil para conductores
- [ ] Predicción de tiempos con IA
- [ ] Integración con sistemas de clientes (API)
- [ ] Reportes automáticos por email
- [ ] Optimización de rutas en tiempo real

---

**Versión:** 2.0  
**Última actualización:** Octubre 2025
