# GUÍA DE TESTING DE INTEGRACIÓN

## Sistema de Gestión de Transporte de Contenedores

**Fecha**: Octubre 2024  
**Versión**: 1.0.0  
**Propósito**: Validar flujo completo desde importación Excel hasta entrega final

---

## 1. PREPARACIÓN DEL ENTORNO

### 1.1 Requisitos Previos
```bash
# Activar entorno virtual
cd /workspaces/soptraloc
source venv/bin/activate

# Verificar configuración
python manage.py check

# Ejecutar servidor de desarrollo
python manage.py runserver 0.0.0.0:8000
```

### 1.2 Cargar Datos Base
```bash
# Cargar CDs, CCTIs y datos iniciales
python manage.py cargar_datos_prueba
```

**Resultado Esperado:**
- 4 CDs creados: Puerto Madero, Campos de Chile, Quilicura, El Peñón
- 2 CCTIs creados: ZEAL, CLEP
- Configuraciones correctas de espera/drop-and-hook

---

## 2. FLUJO 1: IMPORTACIÓN DESDE EXCEL

### 2.1 Importar Embarques
**Endpoint**: `POST /api/containers/import_embarques/`

**Archivo**: `EMBARQUE.xlsx` (25 contenedores)

**Comando Curl**:
```bash
curl -X POST http://localhost:8000/api/containers/import_embarques/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@apps/EMBARQUE.xlsx"
```

**Resultado Esperado**:
```json
{
  "success": true,
  "creados": 25,
  "actualizados": 0,
  "errores": 0,
  "detalles": [
    {
      "container_id": "TCNU1234567",
      "accion": "creado",
      "estado": "por_arribar",
      "fecha_eta": "2024-10-28T10:00:00Z"
    },
    ...
  ]
}
```

**Validaciones**:
- ✅ `Container.container_id` debe ser único
- ✅ `Container.estado` debe ser `'por_arribar'`
- ✅ `Container.fecha_eta` debe estar poblado desde columna "ETA Confirmada"
- ✅ `Container.booking` debe coincidir con columna Excel
- ✅ `Container.ccti_actual` debe estar asignado (ZEAL o CLEP)

**Verificar en Admin**:
```
http://localhost:8000/admin/containers/container/
- Ver lista de 25 contenedores nuevos
- Estado: por_arribar
- Fecha ETA poblada
```

---

### 2.2 Importar Liberaciones
**Endpoint**: `POST /api/containers/import_liberaciones/`

**Archivo**: `LIBERACION.xlsx`

**Comando Curl**:
```bash
curl -X POST http://localhost:8000/api/containers/import_liberaciones/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@apps/LIBERACION.xlsx"
```

**Resultado Esperado**:
```json
{
  "success": true,
  "creados": 0,
  "actualizados": 15,
  "errores": 0,
  "detalles": [
    {
      "container_id": "TCNU1234567",
      "accion": "actualizado",
      "estado": "liberado",
      "deposito_devolucion": "ZEAL",
      "fecha_demurrage": "2024-10-30T23:59:59Z"
    },
    ...
  ]
}
```

**Validaciones**:
- ✅ `Container.estado` cambia a `'liberado'`
- ✅ `Container.deposito_devolucion` poblado desde "DEVOLUCION VACIO"
- ✅ `Container.fecha_demurrage` calculado desde "FECHA DEMURRAGE" o "WK DEMURRAGE"
- ✅ `Container.peso` actualizado si cambió en Excel
- ✅ Evento `'liberacion'` creado

**Verificar en Admin**:
```
- Abrir cualquier contenedor liberado
- Ver deposito_devolucion = "ZEAL" o "CLEP"
- Ver fecha_demurrage con fecha futura
- Ver en eventos: tipo='liberacion'
```

---

### 2.3 Importar Programaciones
**Endpoint**: `POST /api/programaciones/import_programaciones/`

**Archivo**: `PROGRAMACION.xlsx`

**Comando Curl**:
```bash
curl -X POST http://localhost:8000/api/programaciones/import_programaciones/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@apps/PROGRAMACION.xlsx"
```

**Resultado Esperado**:
```json
{
  "success": true,
  "creados": 20,
  "errores": 0,
  "detalles": [
    {
      "container_id": "TCNU1234567",
      "accion": "programado",
      "cd": "El Peñón",
      "fecha_programada": "2024-10-28T08:00:00Z",
      "cliente": "WALMART"
    },
    ...
  ]
}
```

**Validaciones**:
- ✅ `Container.estado` cambia a `'programado'`
- ✅ `Programacion` creada con CD correcto
- ✅ CD extraído desde columna "BODEGA" formato "6020 - PEÑÓN"
- ✅ `fecha_programada` poblada desde columna Excel
- ✅ `Container.fecha_demurrage` actualizado si está en Excel
- ✅ Evento `'programacion'` creado

**Verificar en Admin**:
```
http://localhost:8000/admin/programaciones/programacion/
- Ver 20 programaciones nuevas
- CD asignado correctamente
- Container.estado = 'programado'
```

---

### 2.4 Importar Conductores
**Endpoint**: `POST /api/drivers/import_conductores/`

**Archivo**: `conductores.xlsx` (157 conductores)

**Comando Curl**:
```bash
curl -X POST http://localhost:8000/api/drivers/import_conductores/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@apps/conductores.xlsx"
```

**Resultado Esperado**:
```json
{
  "success": true,
  "creados": 157,
  "actualizados": 0,
  "errores": 0,
  "detalles": [
    {
      "nombre": "JUAN PEREZ",
      "rut": "12345678-9",
      "patente": "AB1234",
      "telefono": "+56912345678",
      "presente": true,
      "accion": "creado"
    },
    ...
  ]
}
```

**Validaciones**:
- ✅ `Driver.rut` formateado correctamente (sin puntos, con guión)
- ✅ `Driver.telefono` con prefijo +56
- ✅ `Driver.presente` = True si ASISTENCIA = "OPERATIVO" o "SI"
- ✅ `Driver.disponible` = True inicialmente
- ✅ `Driver.max_entregas_dia` = 8 por default

**Verificar en Admin**:
```
http://localhost:8000/admin/drivers/driver/
- Ver 157 conductores
- RUT formateado: 12345678-9
- Teléfono: +56912345678
- presente: True/False según Excel
```

---

## 3. FLUJO 2: OPERACIONES AUTOMÁTICAS

### 3.1 Alertas de Demurrage
**Endpoint**: `GET /api/programaciones/alertas_demurrage/`

**Comando Curl**:
```bash
curl http://localhost:8000/api/programaciones/alertas_demurrage/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Resultado Esperado**:
```json
{
  "alertas": [
    {
      "container_id": "TCNU1234567",
      "fecha_demurrage": "2024-10-29T23:59:59Z",
      "dias_restantes": 1.5,
      "urgencia": "CRÍTICA",
      "cd": "El Peñón",
      "cliente": "WALMART"
    },
    ...
  ]
}
```

**Validaciones**:
- ✅ Solo contenedores con `fecha_demurrage < now + 2 days`
- ✅ `dias_restantes` calculado correctamente
- ✅ `urgencia` categorizada: CRÍTICA (<1d), ALTA (1-2d)
- ✅ Sin driver asignado aún

**Casos de Prueba**:
1. Contenedor con demurrage en 6 horas → Debe aparecer como CRÍTICA
2. Contenedor con demurrage en 3 días → NO debe aparecer
3. Contenedor ya asignado → NO debe aparecer

---

### 3.2 Dashboard de Priorización
**Endpoint**: `GET /api/programaciones/dashboard/`

**Comando Curl**:
```bash
curl http://localhost:8000/api/programaciones/dashboard/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Resultado Esperado**:
```json
{
  "programaciones": [
    {
      "id": 1,
      "container_id": "TCNU1234567",
      "fecha_programada": "2024-10-28T08:00:00Z",
      "fecha_demurrage": "2024-10-29T23:59:59Z",
      "dias_hasta_programacion": 0.5,
      "dias_hasta_demurrage": 1.5,
      "score_prioridad": 1.0,
      "urgencia": "CRÍTICA",
      "driver": "Juan Pérez",
      "cd": "El Peñón"
    },
    ...
  ],
  "leyenda": {
    "CRÍTICA": "<1 día",
    "ALTA": "1-2 días",
    "MEDIA": "2-3 días",
    "BAJA": ">3 días"
  }
}
```

**Validaciones**:
- ✅ `score_prioridad` = (dias_programacion * 0.5) + (dias_demurrage * 0.5)
- ✅ Ordenado por score ascendente (más urgente primero)
- ✅ Solo programaciones con driver asignado
- ✅ Categorización correcta de urgencia

**Casos de Prueba**:
1. Programación hoy + demurrage mañana → score ~0.5 (CRÍTICA)
2. Programación en 2 días + demurrage en 3 días → score ~2.5 (MEDIA)
3. Programación pasada → score negativo (aparece primero)

---

## 4. FLUJO 3: ASIGNACIÓN Y SEGUIMIENTO

### 4.1 Asignar Conductor a Programación
**Endpoint**: `POST /api/programaciones/{id}/asignar_driver/`

**Comando Curl**:
```bash
curl -X POST http://localhost:8000/api/programaciones/1/asignar_driver/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "driver_id": 5
  }'
```

**Resultado Esperado**:
```json
{
  "success": true,
  "mensaje": "Driver asignado correctamente",
  "programacion": {
    "id": 1,
    "driver": {
      "id": 5,
      "nombre": "Juan Pérez",
      "disponible": false,
      "num_entregas_dia": 1
    },
    "container": {
      "estado": "asignado"
    }
  }
}
```

**Validaciones**:
- ✅ `Container.estado` cambia a `'asignado'`
- ✅ `Driver.disponible` = False
- ✅ `Driver.num_entregas_dia` incrementado en 1
- ✅ Evento `'asignacion_driver'` creado

**Casos de Prueba**:
1. Asignar a driver disponible → OK
2. Asignar a driver no disponible → Error 400
3. Asignar a driver con 8 entregas → Error 400
4. Re-asignar mismo driver → OK (no incrementa entregas)

---

### 4.2 Iniciar Ruta
**Endpoint**: `POST /api/containers/{id}/iniciar_ruta/`

**Comando Curl**:
```bash
curl -X POST http://localhost:8000/api/containers/1/iniciar_ruta/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Resultado Esperado**:
```json
{
  "success": true,
  "mensaje": "Ruta iniciada",
  "container": {
    "id": 1,
    "container_id": "TCNU1234567",
    "estado": "en_ruta",
    "driver": "Juan Pérez"
  }
}
```

**Validaciones**:
- ✅ `Container.estado` cambia a `'en_ruta'`
- ✅ Evento `'inicio_ruta'` creado con timestamp
- ✅ Solo puede iniciar si estado = 'asignado'

---

### 4.3 Registrar Arribo a CD
**Endpoint**: `POST /api/containers/{id}/registrar_arribo/`

**Comando Curl**:
```bash
curl -X POST http://localhost:8000/api/containers/1/registrar_arribo/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Resultado Esperado**:
```json
{
  "success": true,
  "mensaje": "Arribo registrado",
  "container": {
    "id": 1,
    "estado": "entregado",
    "fecha_entrega": "2024-10-28T14:30:00Z"
  }
}
```

**Validaciones**:
- ✅ `Container.estado` cambia a `'entregado'`
- ✅ `Container.fecha_entrega` = now()
- ✅ Evento `'arribo'` creado

---

### 4.4 Registrar Descarga en CD
**Endpoint**: `POST /api/containers/{id}/registrar_descarga/`

**Comando Curl**:
```bash
curl -X POST http://localhost:8000/api/containers/1/registrar_descarga/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "cd_entrega_id": 3
  }'
```

**Resultado Esperado**:
```json
{
  "success": true,
  "mensaje": "Descarga registrada",
  "container": {
    "id": 1,
    "estado": "descargado",
    "hora_descarga": "2024-10-28T16:00:00Z",
    "cd_entrega": "El Peñón"
  },
  "driver": {
    "disponible": true
  }
}
```

**Validaciones**:
- ✅ `Container.estado` cambia a `'descargado'`
- ✅ `Container.hora_descarga` = now()
- ✅ `Container.cd_entrega` = CD proporcionado
- ✅ `Driver.disponible` = True (liberado para nueva entrega)
- ✅ Evento `'descarga'` creado

**SIGNALS AUTOMÁTICOS**:
Si CD.permite_soltar_contenedor = True (El Peñón):
- ✅ Signal `manejar_vacios_automaticamente` se dispara
- ✅ `CD.vacios_actual` incrementado en 1
- ✅ Evento `'recepcion_vacio'` creado automáticamente

---

### 4.5 Drop and Hook (Solo El Peñón)
**Endpoint**: `POST /api/containers/{id}/soltar_contenedor/`

**Comando Curl**:
```bash
curl -X POST http://localhost:8000/api/containers/1/soltar_contenedor/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "cd_entrega_id": 3
  }'
```

**Resultado Esperado**:
```json
{
  "success": true,
  "mensaje": "Contenedor soltado en El Peñón (drop and hook)",
  "container": {
    "estado": "descargado",
    "cd_entrega": "El Peñón"
  },
  "driver": {
    "disponible": true
  }
}
```

**Validaciones**:
- ✅ Solo funciona si `CD.permite_soltar_contenedor = True`
- ✅ Driver queda disponible inmediatamente
- ✅ CD descargará contenedor después
- ✅ `CD.vacios_actual` NO se incrementa aún (se hará al descargar)

---

## 5. FLUJO 4: RUTAS MANUALES

### 5.1 Retiro desde CCTI
**Endpoint**: `POST /api/programaciones/crear_ruta_manual/`

**Comando Curl**:
```bash
curl -X POST http://localhost:8000/api/programaciones/crear_ruta_manual/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "container_id": 10,
    "tipo_movimiento": "retiro_ccti",
    "fecha_programacion": "2024-10-29T08:00:00Z",
    "cliente": "FALABELLA",
    "observaciones": "Retiro urgente desde ZEAL"
  }'
```

**Resultado Esperado**:
```json
{
  "success": true,
  "mensaje": "Ruta manual creada: Retiro desde CCTI",
  "programacion": {
    "id": 25,
    "container_id": "TCNU9999999",
    "tipo_movimiento": "retiro_ccti",
    "cd": null,
    "fecha_programada": "2024-10-29T08:00:00Z"
  }
}
```

**Validaciones**:
- ✅ `Container.tipo_movimiento` = 'retiro_ccti'
- ✅ `Container.estado` cambia a 'programado'
- ✅ `Programacion` creada sin CD (se lleva a otro CCTI o puerto)
- ✅ Container debe estar en estado 'liberado' o 'por_arribar'

---

### 5.2 Retiro Directo a Cliente
**Endpoint**: `POST /api/programaciones/crear_ruta_manual/`

**Comando Curl**:
```bash
curl -X POST http://localhost:8000/api/programaciones/crear_ruta_manual/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "container_id": 11,
    "tipo_movimiento": "retiro_directo",
    "cd_destino_id": 2,
    "fecha_programacion": "2024-10-29T10:00:00Z",
    "cliente": "RIPLEY",
    "observaciones": "Directo a bodega Quilicura"
  }'
```

**Resultado Esperado**:
```json
{
  "success": true,
  "mensaje": "Ruta manual creada: Retiro directo desde puerto a cliente",
  "programacion": {
    "id": 26,
    "container_id": "TCNU8888888",
    "tipo_movimiento": "retiro_directo",
    "cd": "Quilicura",
    "fecha_programada": "2024-10-29T10:00:00Z"
  }
}
```

**Validaciones**:
- ✅ `Container.tipo_movimiento` = 'retiro_directo'
- ✅ `Programacion` creada con CD destino
- ✅ Container se retira desde puerto y va directo a CD cliente
- ✅ Requiere `cd_destino_id` obligatorio

---

## 6. FLUJO 5: APRENDIZAJE ML

### 6.1 Registrar Tiempo de Operación
**Proceso**: Automático al descargar contenedor

**Creación Manual para Testing**:
```python
from apps.programaciones.models import TiempoOperacion
from apps.cds.models import CD
from apps.drivers.models import Driver
from apps.containers.models import Container
from datetime import datetime, timedelta

cd = CD.objects.get(nombre="El Peñón")
driver = Driver.objects.get(id=5)
container = Container.objects.get(id=1)

hora_inicio = datetime(2024, 10, 28, 14, 30)
hora_fin = datetime(2024, 10, 28, 15, 15)  # 45 minutos real

TiempoOperacion.objects.create(
    cd=cd,
    conductor=driver,
    container=container,
    tipo_operacion='descarga_cd',
    tiempo_estimado_min=30,  # CD.tiempo_promedio_descarga_min
    tiempo_real_min=45,  # Real = 45 min
    hora_inicio=hora_inicio,
    hora_fin=hora_fin,
    observaciones="Primera descarga"
)
```

**Validaciones**:
- ✅ Anomalía automática si `tiempo_real > 3x estimado`
- ✅ Cálculo de desviación: (45-30)/30 = +50%

**Obtener Tiempo Aprendido**:
```python
tiempo = TiempoOperacion.obtener_tiempo_aprendido(
    cd=cd,
    tipo_operacion='descarga_cd',
    conductor=driver
)
print(f"Tiempo aprendido: {tiempo} minutos")
# Con <5 registros → usa CD.tiempo_promedio_descarga_min
# Con ≥5 registros → 60% últimos 10 + 40% histórico
```

---

### 6.2 Registrar Tiempo de Viaje
**Proceso**: Automático al completar ruta

**Creación Manual para Testing**:
```python
from apps.programaciones.models import TiempoViaje
from datetime import datetime

origen = (-33.4569, -70.6483)  # Santiago Centro
destino = (-33.3981, -70.5771)  # El Peñón

hora_salida = datetime(2024, 10, 28, 8, 0)
hora_llegada = datetime(2024, 10, 28, 9, 15)  # 75 minutos real

TiempoViaje.objects.create(
    origen_lat=origen[0],
    origen_lon=origen[1],
    destino_lat=destino[0],
    destino_lon=destino[1],
    origen_nombre="CCTI ZEAL",
    destino_nombre="El Peñón",
    conductor=driver,
    tiempo_mapbox_min=45,  # Mapbox estimó 45 min
    tiempo_real_min=75,  # Real = 75 min (tráfico)
    hora_salida=hora_salida,
    hora_llegada=hora_llegada,
    distancia_km=25.5
)
```

**Validaciones**:
- ✅ `hora_del_dia` y `dia_semana` calculados automáticamente en save()
- ✅ Factor corrección = 75/45 = 1.67x (🔴 Muy lento)
- ✅ Anomalía si factor > 3x o velocidad < 10 km/h

**Obtener Tiempo Aprendido**:
```python
tiempo = TiempoViaje.obtener_tiempo_aprendido(
    origen_coords=origen,
    destino_coords=destino,
    tiempo_mapbox=45,
    hora_salida=datetime.now(),
    conductor=driver
)
print(f"Tiempo aprendido: {tiempo} minutos")
# Busca viajes similares (±1km) en ±2 horas
# Aplica factor: 60% reciente + 40% histórico
```

---

## 7. CASOS DE PRUEBA CRÍTICOS

### 7.1 Demurrage Vencido
**Escenario**: Contenedor con fecha_demurrage en el pasado

**Pasos**:
1. Crear contenedor con `fecha_demurrage = ayer`
2. Consultar alertas: `GET /api/programaciones/alertas_demurrage/`
3. Verificar aparece con `dias_restantes` negativo
4. Signal debe haber disparado `requiere_alerta = True`

**Resultado Esperado**:
- ✅ Aparece en alertas con urgencia CRÍTICA
- ✅ `Programacion.requiere_alerta = True`
- ✅ Evento `alerta_demurrage` creado

---

### 7.2 CD con Vacíos Completos
**Escenario**: CD.vacios_actual = CD.capacidad_vacios_max

**Pasos**:
1. Descargar contenedores hasta llenar capacidad
2. Intentar descargar uno más
3. Verificar comportamiento

**Resultado Esperado**:
- ✅ Signal NO incrementa vacios_actual si está en máximo
- ✅ O devuelve error indicando CD lleno

---

### 7.3 Conductor con 8 Entregas
**Escenario**: Driver.num_entregas_dia = 8

**Pasos**:
1. Asignar 8 programaciones a un driver
2. Intentar asignar la 9na

**Resultado Esperado**:
- ✅ Error 400: "Driver alcanzó máximo de entregas diarias"
- ✅ NO se crea la asignación

---

### 7.4 Retiro Directo sin CD
**Escenario**: Crear ruta retiro_directo sin cd_destino_id

**Pasos**:
1. POST a crear_ruta_manual con tipo_movimiento='retiro_directo'
2. Omitir campo cd_destino_id

**Resultado Esperado**:
- ✅ Error 400: "cd_destino_id es obligatorio para retiro_directo"

---

### 7.5 Drop and Hook en CD Incorrecto
**Escenario**: Intentar soltar contenedor en Puerto Madero

**Pasos**:
1. POST a /api/containers/{id}/soltar_contenedor/
2. cd_entrega_id = Puerto Madero (permite_soltar_contenedor=False)

**Resultado Esperado**:
- ✅ Error 400: "CD no permite drop and hook"

---

## 8. MÉTRICAS DE ÉXITO

### 8.1 Performance
- ✅ Importación de 157 conductores: < 10 segundos
- ✅ Dashboard con 50+ programaciones: < 2 segundos
- ✅ Alertas demurrage: < 1 segundo

### 8.2 Integridad de Datos
- ✅ 0 contenedores duplicados por container_id
- ✅ 0 programaciones sin CD (excepto retiro_ccti)
- ✅ 0 drivers con num_entregas_dia > max_entregas_dia
- ✅ Suma de vacios_actual ≤ capacidad_vacios_max por CD

### 8.3 Signals
- ✅ 100% de contenedores descargados en El Peñón incrementan vacios
- ✅ 100% de demurrages <2d disparan alerta
- ✅ 0 loops infinitos en signals

---

## 9. COMANDOS ÚTILES

### 9.1 Resetear Base de Datos
```bash
python manage.py flush --no-input
python manage.py migrate
python manage.py cargar_datos_prueba
```

### 9.2 Ver Logs de Signals
```python
# En apps/containers/signals.py
import logging
logger = logging.getLogger(__name__)

# En cada signal
logger.info(f"Signal disparado: {instance}")
```

### 9.3 Consultar Datos
```bash
python manage.py shell

# Ver contenedores por estado
from apps.containers.models import Container
Container.objects.values('estado').annotate(count=models.Count('id'))

# Ver drivers disponibles
from apps.drivers.models import Driver
Driver.objects.filter(disponible=True, presente=True).count()

# Ver vacíos por CD
from apps.cds.models import CD
for cd in CD.objects.all():
    print(f"{cd.nombre}: {cd.vacios_actual}/{cd.capacidad_vacios_max}")
```

---

## 10. CHECKLIST FINAL

Antes de dar por completa la implementación:

**Modelos**:
- [x] Container: 6 nuevos campos
- [x] CD: 3 nuevos campos
- [x] TiempoOperacion: Modelo completo
- [x] TiempoViaje: Modelo completo

**Importers**:
- [x] Embarque: Lee ETA Confirmada
- [x] Liberacion: Lee DEVOLUCION VACIO y FECHA DEMURRAGE
- [x] Programacion: Extrae CD de BODEGA
- [x] Conductores: Importa 157 drivers

**Endpoints**:
- [x] registrar_arribo
- [x] registrar_descarga
- [x] soltar_contenedor
- [x] alertas_demurrage
- [x] dashboard
- [x] crear_ruta_manual
- [x] import_conductores

**Signals**:
- [x] manejar_vacios_automaticamente
- [x] alertar_demurrage_cercano

**ML**:
- [x] TiempoOperacion.obtener_tiempo_aprendido()
- [x] TiempoViaje.obtener_tiempo_aprendido()

**Testing**:
- [ ] Flujo completo con 4 Excel files
- [ ] 7 casos de prueba críticos
- [ ] Métricas de éxito validadas

**Documentación**:
- [x] ANALISIS_GAPS.md
- [x] RESUMEN_GAPS.md
- [x] FLUJOS_COMPARACION.md
- [x] IMPLEMENTACION_COMPLETA.md
- [x] TESTING_GUIDE.md (este archivo)

---

## 11. CONTACTO Y SOPORTE

Para dudas o issues:
- Revisar logs: `/workspaces/soptraloc/logs/`
- Django admin: `http://localhost:8000/admin/`
- API docs: `http://localhost:8000/api/swagger/`

**Fecha última actualización**: Octubre 2024
