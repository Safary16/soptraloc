# 🚀 SoptraLoc TMS - Sistema de Gestión de Transporte# SoptraLoc TMS - Sistema de Gestión de Contenedores# SoptraLoc - Sistema de Gestión de Contenedores TMS# 🚀 SoptraLoc - Sistema TMS Inteligente con Machine Learning



[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/Safary16/soptraloc)

[![Django 5.1.4](https://img.shields.io/badge/Django-5.1.4-green.svg)](https://www.djangoproject.com/)

[![Python 3.12+](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)Sistema profesional de gestión de contenedores para CCTi con integración de Mapbox, asignación inteligente de conductores y seguimiento en tiempo real.

[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Ready-blue.svg)](https://www.postgresql.org/)



Sistema profesional de gestión de contenedores para CCTi con **integración Mapbox**, **asignación inteligente de conductores** y **seguimiento en tiempo real**.

[![Django 5.1.4](https://img.shields.io/badge/Django-5.1.4-green.svg)](https://www.djangoproject.com/)Sistema profesional de gestión de contenedores para CCTi con integración de Mapbox, asignación inteligente de conductores y seguimiento en tiempo real.[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/Safary16/soptraloc)

---

[![Python 3.12+](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)

## ✨ Características Principales

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/Safary16/soptraloc)[![Django 5.2.6](https://img.shields.io/badge/Django-5.2.6-green.svg)](https://www.djangoproject.com/)

### 📦 Gestión Completa de Contenedores



- **11 Estados del ciclo de vida**:

  - `por_arribar` → `liberado` → `secuenciado` → `programado` → `asignado` → `en_ruta` → `entregado` → `descargado` → `en_almacen_ccti` → `vacio_en_ruta` → `vacio_en_ccti`---## 🚀 Características principales[![Python 3.12+](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)

  

- **Importación Excel** (3 tipos):

  - 📥 **Embarque**: Crea contenedores con estado `por_arribar`

  - 📥 **Liberación**: Actualiza a `liberado` con mapeo de posiciones (TPS→ZEAL, STI/PCE→CLEP)## 🚀 Características Principales[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Ready-blue.svg)](https://www.postgresql.org/)

  - 📥 **Programación**: Crea programaciones y verifica alertas 48h



- **Exportación Excel**:

  - 📤 Stock liberado/por arribar con flag de secuenciado### 📦 Gestión Completa de Contenedores- **Importación de Excel**: Embarque, Liberación, Programación



- **Transiciones automáticas** con timestamps y eventos de auditoría- **11 Estados**: `por_arribar`, `liberado`, `secuenciado`, `programado`, `asignado`, `en_ruta`, `entregado`, `descargado`, `en_almacen_ccti`, `vacio_en_ruta`, `vacio_en_ccti`



### 🚛 Gestión de Conductores- **Importación Excel**: Embarque, Liberación, Programación- **Gestión de estados**: 11 estados de contenedores con transiciones automáticas## ✨ **Sistema Completo de Gestión de Transporte (TMS)**



- **Métricas en tiempo real**:- **Exportación**: Stock con flag de secuenciado

  - Disponibilidad (presente/ausente)

  - Ocupación (entregas asignadas vs capacidad)- **Trazabilidad**: Historial completo de eventos- **Asignación inteligente**: Algoritmo automático de asignación de conductores

  - Cumplimiento (entregas completadas vs programadas)

  - Posición GPS actualizable



- **Capacidad configurable**: Entregas diarias máximas por conductor### 🚛 Sistema Inteligente de Conductores- **Mapbox Integration**: Rutas reales, tiempos estimados, tráfico en vivoSistema profesional de gestión logística con **Machine Learning**, **alertas en tiempo real** y **dashboard estilo torre de control aéreo**.



- **Reset automático**: Entregas del día se resetean automáticamente- **Asignación Automática**: Algoritmo con 4 factores ponderados



### 🤖 Asignación Inteligente  - Disponibilidad (30%)- **Alertas**: Demurrage cercano, programación sin conductor



**Algoritmo con pesos configurables**:  - Ocupación (25%)



```python  - Cumplimiento (30%)- **Exportación**: Stock liberado/por arribar con flag de secuenciado### **🎯 Lo que incluye:**

Score Total = (Disponibilidad × 30%) + 

              (Ocupación × 25%) +   - Proximidad (15%)

              (Cumplimiento × 30%) + 

              (Proximidad × 15%)- **Métricas**: Cumplimiento, ocupación, total entregas- **Historial completo**: Auditoría de todas las operaciones- ⏰ **Reloj en tiempo real** estilo torre de control aéreo

```

- **GPS**: Actualización de posición en tiempo real

- **Asignación individual**: Selecciona mejor conductor para una programación

- **Asignación múltiple**: Procesa varias programaciones en batch- **API REST**: Endpoints completos para integración- 🚨 **Sistema de alertas urgentes** con verificación automática cada 30 segundos

- **Integración Mapbox**: Calcula distancias y ETAs reales

### 🗺️ Integración Mapbox

### 🗺️ Integración Mapbox

- **Rutas Reales**: Cálculo con tráfico en tiempo real- 🗺️ **35 rutas Chile pre-configuradas** (puertos, CDs, bodegas)

- **Rutas reales** con tráfico en tiempo real

- **Cálculo de distancias** entre origen y destino- **ETAs Precisos**: Tiempo estimado de llegada

- **ETAs precisos** considerando tráfico

- **Score de proximidad** para asignación- **Matriz de Distancias**: Cálculos masivos## 📋 Flujo del sistema- 🤖 **Machine Learning** para predicción de tiempos (60% reciente / 40% histórico)



### 🚨 Sistema de Alertas- **Scores de Proximidad**: Para asignación inteligente



- **Alerta 48h**: Programaciones sin conductor asignado a menos de 48h de la fecha programada- 📊 **Dashboard inteligente** con ordenamiento por urgencia

- **Consulta de alertas**: Endpoint dedicado para visualizar programaciones urgentes

- **Verificación automática** al importar programaciones### 🚨 Sistema de Alertas



### 🏢 Gestión de CDs- **48 Horas**: Alerta automática si programación sin conductor```- 🚛 **Sistema de conductores** con asignación inteligente



- **CCTIs** (Centros de Consolidación):- **Demurrage**: Seguimiento de tiempos límite

  - Capacidad de contenedores vacíos

  - Gestión de recepción y retiro de vacíos- **Verificación**: Checks automáticos cada hora1. EMBARQUE (Excel) → Contenedores creados con estado "por_arribar"- 📦 **Gestión completa de contenedores** con estados y movimientos

  - Tracking de espacios disponibles



- **Clientes**:

  - Direcciones de entrega### 🏢 Gestión de Centros de Distribución   ├─ Campos: container_id, nave, ETA, tipo, peso, puerto, vendor, sello- 🔔 **Sistema de proximidad** con alertas automáticas

  - Coordenadas GPS

  - Relación con programaciones- **CCTIs**: Control de contenedores vacíos



### 📊 Auditoría Completa- **Clientes**: Centros de entrega final   - 🔌 **API REST completa** con endpoints documentados



- **Sistema de eventos**: Registra todas las acciones- **Capacidad**: Monitoreo de espacios disponibles

- **11 tipos de eventos**: Creación, cambio de estado, asignación, importación, etc.

- **Detalles JSON**: Información completa de cada evento- **Geocodificación**: Coordenadas para cálculo de rutas2. LIBERACIÓN (Excel) → Contenedores pasan a "liberado"- 👨‍💼 **Panel de administración** profesional con badges ML

- **Usuario tracking**: Quién realizó cada acción



---

---   ├─ Reglas de posición física:

## 🎯 Flujo del Sistema



```

1. EMBARQUE (Excel)## 📋 Flujo del Sistema   │  ├─ TPS Valparaíso → ZEAL---

   └─→ Contenedores creados con estado "por_arribar"

        ├─ container_id, nave, ETA, tipo, peso, puerto, vendor, sello

        └─ Evento: "container_creado"

```   │  ├─ STI/PCE San Antonio → CLEP SAI

2. LIBERACIÓN (Excel)

   └─→ Contenedores pasan a "liberado"1. EMBARQUE (Excel)

        ├─ Mapeo de posiciones:

        │   ├─ TPS Valparaíso → ZEAL   └─> Contenedores creados con estado "por_arribar"   │  └─ Retiro CCTi → en_transito_a_ccti## 🚀 Características Principales

        │   └─ STI/PCE San Antonio → CLEP SAI

        └─ Evento: "cambio_estado"       • Campos: container_id, nave, ETA, tipo, peso, puerto, vendor, sello



3. EXPORTACIÓN STOCK   

   └─→ Excel con contenedores liberados/por arribar

        └─ Flag "secuenciado" marca como procesados2. LIBERACIÓN (Excel)



4. PROGRAMACIÓN (Excel)   └─> Contenedores actualizados a "liberado"3. EXPORTACIÓN → Stock para cliente### ⏰ Reloj en Tiempo Real - Estilo Torre de Control

   └─→ Crea programaciones en estado "programado"

        ├─ Verifica alerta si fecha_programacion < 48h       • Mapeo automático de posiciones:

        └─ Evento: "programacion_creada"

         - TPS Valparaíso → ZEAL   ├─ Liberados + Por arribar- **Diseño profesional**: Colores verde fosforescente sobre azul gradiente

5. ASIGNACIÓN CONDUCTOR

   └─→ Asigna conductor óptimo         - STI/PCE San Antonio → CLEP

        ├─ Calcula scores (disponibilidad, ocupación, cumplimiento, proximidad)

        ├─ Contenedor pasa a "asignado"   └─ Flag "secuenciado" si liberación futura- **Actualización**: Cada 1 segundo con precisión milimétrica

        └─ Evento: "conductor_asignado"

3. EXPORTACIÓN

6. EN RUTA

   └─→ Conductor inicia viaje   └─> Stock para cliente (Liberados + Por arribar)   - **Formato**: HH:MM:SS + DÍA DD MES YYYY

        ├─ Actualiza posición GPS

        └─ Evento: "cambio_estado"       • Flag "secuenciado" si liberación futura



7. ENTREGADO4. PROGRAMACIÓN (Excel) → Contenedores pasan a "programado"- **Badge urgente**: Contador animado de contenedores críticos

   └─→ Contenedor entregado en CD Cliente

        ├─ Registra entrega en conductor4. PROGRAMACIÓN (Excel)

        └─ Evento: "cambio_estado"

   └─> Contenedores pasan a "programado"   ├─ Asigna fecha, demurrage, centro entrega- **Modal detallado**: Lista completa de contenedores urgentes con niveles

8. DESCARGADO

   └─→ Contenedor descargado por cliente       • Asigna fecha, demurrage, centro entrega

        └─ Evento: "cambio_estado"

       • Alerta si falta conductor 48h antes   

9. ALMACÉN CCTI

   └─→ Contenedor vacío en CCTI

        ├─ Verifica capacidad CCTI

        └─ Evento: "cambio_estado"5. ASIGNACIÓN (Manual/Automática)5. ASIGNACIÓN → Conductor asignado (manual/automático)### 🗺️ Sistema de Routing con Machine Learning



10. VACÍO EN RUTA   └─> Conductor asignado según algoritmo

    └─→ Retorno de vacío a puerto

         └─ Evento: "cambio_estado"       • Evalúa disponibilidad, ocupación, cumplimiento, proximidad   ├─ Alerta si falta conductor 48h antes- **35 rutas Chile**: Puertos (San Antonio, Valparaíso, San Vicente, Lirquén, Coronel)



11. VACÍO EN CCTI

    └─→ Vacío disponible para reutilización

         ├─ Puede recibirse en CCTI si hay espacio6. EN RUTA   - **70 operaciones**: Tiempos estándar para cada tipo de operación

         └─ Puede retirarse de CCTI

```   └─> Operador inicia ruta



---       • Calcula ETA con Mapbox6. RUTA → Operador inicia, calcula ETA con Mapbox- **Algoritmo ML**: Promedio ponderado (60% datos recientes + 40% históricos)



## 🛠️ Stack Tecnológico       • Tracking en tiempo real



- **Backend**: Django 5.1.4 + Django REST Framework 3.16.1   - **Predicción inteligente**: Tiempos estimados basados en datos reales

- **Database**: PostgreSQL (producción) / SQLite (desarrollo)

- **API Docs**: drf-yasg (Swagger/OpenAPI)7. ENTREGA

- **Excel**: pandas 2.2.2 + openpyxl 3.1.2

- **Mapbox**: requests 2.32.3   └─> Registro de llegada y descarga7. ENTREGA → Registro de llegada y descarga- **Sistema de confianza**: Badges visuales (Alta/Media/Baja)

- **Deploy**: Render.com con build automático

- **Web Server**: Gunicorn + WhiteNoise       • Actualiza métricas del conductor



---   - **Aprendizaje continuo**: Actualización diaria con datos reales



## 📁 Estructura del Proyecto8. VACÍO



```   └─> Control de retorno a CCTi8. VACÍO → Control de retorno y ubicación

soptraloc/

├── apps/       • Gestión de espacios disponibles

│   ├── containers/         # Modelos y lógica de contenedores

│   │   ├── models.py       # Container con 11 estados``````### � Gestión Avanzada de Contenedores

│   │   ├── views.py        # ContainerViewSet con 6 custom actions

│   │   ├── serializers.py  # 3 serializers (full, list, export)

│   │   ├── admin.py        # Admin con acciones batch

│   │   └── importers/      # 3 importadores Excel---- **Múltiples estados**: PROGRAMADO, EN_PROCESO, EN_TRANSITO, LIBERADO, DESCARGADO, EN_SECUENCIA

│   │       ├── embarque.py

│   │       ├── liberacion.py

│   │       └── programacion.py

│   │## 🏗️ Arquitectura## 🗂️ Estados del contenedor- **Trazabilidad completa**: Histórico de todos los movimientos

│   ├── drivers/            # Gestión de conductores

│   │   ├── models.py       # Driver con métricas

│   │   ├── views.py        # DriverViewSet con 6 custom actions

│   │   └── serializers.py  # 3 serializers (full, list, disponible)### Apps Django- **Alertas de proximidad**: Contenedores urgentes < 2 horas

│   │

│   ├── programaciones/     # Sistema de programación

│   │   ├── models.py       # Programacion con alertas 48h

│   │   ├── views.py        # ProgramacionViewSet con 5 custom actions```- `por_arribar` - Nave aún no atracada- **Asignación rápida**: Integración con sistema de conductores

│   │   └── serializers.py  # 3 serializers (full, list, create)

│   │apps/

│   ├── cds/                # Centros de distribución

│   │   ├── models.py       # CD con gestión de vacíos├── containers/       # Modelo Container, importadores, exportación- `liberado` - Contenedor liberado por aduana- **Importación Excel**: Carga masiva de manifiestos y liberaciones

│   │   ├── views.py        # CDViewSet con 4 custom actions

│   │   └── management/commands/├── drivers/          # Modelo Driver, métricas, posiciones

│   │       └── cargar_datos_prueba.py  # Comando para test data

│   │├── programaciones/   # Modelo Programacion, alertas, asignación- `secuenciado` - Liberación futura programada

│   ├── events/             # Sistema de auditoría

│   │   ├── models.py       # Event con 11 tipos├── cds/              # Modelo CD (CCTIs y Clientes)

│   │   └── serializers.py

│   │└── events/           # Modelo Event (auditoría)- `programado` - Entrega programada con fecha### � Sistema de Alertas Inteligentes

│   └── core/               # Servicios compartidos

│       └── services/

│           ├── mapbox.py       # Integración Mapbox

│           └── assignment.py   # Algoritmo de asignaciónconfig/- `asignado` - Conductor asignado- **Verificación automática**: Cada 30 segundos verifica contenedores urgentes

│

├── config/├── settings.py       # Configuración Django

│   ├── settings.py         # Configuración con decouple

│   ├── urls.py             # Routing con DefaultRouter└── urls.py          # Routing API- `en_ruta` - Ruta iniciada- **3 niveles de urgencia**: CRÍTICO (< 1h), ALTO (< 2h), MEDIO (< 4h)

│   └── wsgi.py

│

├── build.sh                # Build automático para Render

├── render.yaml             # Configuración de deployapps/core/- `entregado` - Entregado a cliente- **Notificaciones visuales**: Badge pulsante en navbar

├── requirements.txt        # Dependencias Python

├── manage.py└── services/

├── .env.example            # Plantilla de variables de entorno

├── DEPLOY.md               # Guía completa de deploy    ├── mapbox.py     # Integración Mapbox Directions API- `descargado` - Descargado en CD- **Modal detallado**: Click para ver lista completa con información

└── API_DOCS.md             # Documentación de API

```    └── assignment.py # Algoritmo de asignación



---```- `en_almacen_ccti` - En bodega CCTi- **API endpoint**: `/api/v1/containers/urgent/` para integraciones



## 🚀 Instalación y Deploy



### Opción 1: Deploy Automático en Render (Recomendado)### Modelos de Datos- `vacio_en_ruta` - Retorno con vacío



1. **Clic en el botón Deploy to Render** (arriba)

2. **Render detecta `render.yaml`** automáticamente

3. **Espera 5-7 minutos** mientras:**Container**- `vacio_en_ccti` - Vacío en CCTi### 📊 Dashboard Ejecutivo

   - Instala dependencias

   - Crea base de datos PostgreSQL- `container_id`, `nave`, `eta`, `tipo`, `peso`

   - Aplica migraciones

   - Crea superusuario (admin/admin)- `estado`, `posicion_fisica`, `puerto`, `vendor`, `sello`- **Estadísticas en tiempo real**: Total activos, por estado, disponibilidad

   - Carga datos de prueba

4. **¡Listo!** Accede a tu app- `fecha_liberacion`, `fecha_programada`, `fecha_asignacion`



Ver guía detallada en [`DEPLOY.md`](DEPLOY.md)- `metodo cambiar_estado(nuevo_estado)`## 🛠️ Stack tecnológico- **Vista prioritaria**: Contenedores urgentes destacados y ordenados



### Opción 2: Desarrollo Local



```bash**Driver**- **Integración ML**: Predicciones de tiempos en ruta

# 1. Clonar repositorio

git clone https://github.com/Safary16/soptraloc.git- `nombre`, `rut`, `disponible`, `presente`

cd soptraloc

- `total_entregas_dia`, `entregas_cumplidas`, `entregas_totales`- **Backend**: Django 5.1.4 + Django REST Framework- **Alertas pendientes**: Asignaciones sin completar

# 2. Crear entorno virtual

python -m venv venv- `posicion_lat`, `posicion_lng`

source venv/bin/activate  # Windows: venv\Scripts\activate

- `@property ocupacion_porcentaje`, `esta_disponible`- **Base de datos**: PostgreSQL 15- **Responsive design**: Adaptable a móviles y tablets

# 3. Instalar dependencias

pip install -r requirements.txt- `metodo actualizar_posicion()`, `registrar_entrega()`



# 4. Configurar variables de entorno- **Cache/Queue**: Redis (Celery opcional)

cp .env.example .env

# Editar .env con tus valores**Programacion**



# 5. Migrar base de datos- `container`, `conductor`, `cd`- **Mapas**: Mapbox API (GitHub Student Pack)## 🛠️ Tecnologías Utilizadas

python manage.py migrate

- `fecha_programada`, `hora_programada`, `demurrage_hasta`

# 6. Crear superusuario

python manage.py createsuperuser- `alerta_conductor`, `asignacion_automatica`- **Deploy**: Render.com



# 7. Cargar datos de prueba (opcional)- `@property requiere_conductor_urgente`

python manage.py cargar_datos_prueba

- `metodo verificar_alerta()`, `asignar_conductor()`- **Python**: 3.12- **Backend**: Django 5.2.6 + Django REST Framework

# 8. Ejecutar servidor

python manage.py runserver

```

**CD (Centro de Distribución)**- **Base de Datos**: SQLite (desarrollo) / PostgreSQL (producción)

Accede a:

- 🌐 Admin: http://127.0.0.1:8000/admin/- `nombre`, `tipo` (CCTI/CLIENTE), `direccion`

- 📡 API: http://127.0.0.1:8000/api/

- `latitud`, `longitud`## 🏗️ Estructura del proyecto- **API Documentation**: DRF-YASG (Swagger/OpenAPI)

---

- `puede_recibir_vacios`, `capacidad_vacios`, `vacios_actuales`

## 📡 API REST

- `metodo recibir_vacio()`, `retirar_vacio()`- **Autenticación**: JWT (Simple JWT)

### Endpoints Principales



#### **Contenedores** (`/api/containers/`)

**Event**```- **Frontend**: API REST (listo para integración con cualquier frontend)

```bash

# Listar contenedores- `container`, `tipo_evento`, `timestamp`, `detalles` (JSON)

GET /api/containers/

- Tipos: embarque, liberacion, programacion, asignacion, en_ruta, etc.soptraloc/

# Crear contenedor

POST /api/containers/



# Importar embarque---├── apps/## 📋 Instalación y Configuración

POST /api/containers/import_embarque/

  -F "file=@embarque.xlsx"



# Importar liberación## 🔌 API REST Completa│   ├── containers/      # Gestión de contenedores

POST /api/containers/import_liberacion/

  -F "file=@liberacion.xlsx"



# Importar programación### Contenedores│   ├── drivers/         # Conductores y asignaciones### Prerrequisitos

POST /api/containers/import_programacion/

  -F "file=@programacion.xlsx"



# Exportar stock```bash│   ├── programaciones/  # Programación de entregas- Python 3.12+

GET /api/containers/export_stock/

# Listar contenedores

# Cambiar estado

POST /api/containers/{id}/cambiar_estado/GET /api/containers/│   ├── events/          # Historial y auditoría- Git

  {"nuevo_estado": "en_ruta"}

```



#### **Conductores** (`/api/drivers/`)# Importar embarque│   └── cds/            # Centros de distribución- Entorno virtual (recomendado)



```bashPOST /api/containers/import_embarque/

# Listar conductores disponibles

GET /api/drivers/disponibles/Content-Type: multipart/form-data├── config/             # Configuración Django



# Actualizar posiciónfile: embarque.xlsx

POST /api/drivers/{id}/actualizar_posicion/

  {"latitud": -33.4372, "longitud": -70.6506}├── importers/          # Procesadores de Excel### 1. Clonar el Repositorio



# Registrar entrega# Importar liberación

POST /api/drivers/{id}/registrar_entrega/

  {"exitosa": true}POST /api/containers/import_liberacion/├── exporters/          # Generadores de reportes```bash



# Marcar presentefile: liberacion.xlsx

POST /api/drivers/{id}/marcar_presente/

├── services/           # Lógica de negociogit clone https://github.com/Safary16/soptraloc.git

# Reset entregas del día

POST /api/drivers/{id}/resetear_entregas_dia/# Importar programación

```

POST /api/containers/import_programacion/└── utils/              # Utilidades compartidascd soptraloc

#### **Programaciones** (`/api/programaciones/`)

file: programacion.xlsx

```bash

# Ver alertas (<48h sin conductor)``````

GET /api/programaciones/alertas/

# Exportar stock

# Asignar conductor manualmente

POST /api/programaciones/{id}/asignar_conductor/GET /api/containers/export_stock/

  {"conductor_id": 1}



# Asignación automática (inteligente)

POST /api/programaciones/{id}/asignar_automatico/# Cambiar estado## 📦 Instalación local### 2. Crear Entorno Virtual



# Conductores disponibles con scoresPOST /api/containers/{id}/cambiar_estado/

GET /api/programaciones/{id}/conductores_disponibles/

{"nuevo_estado": "en_ruta", "usuario": "operador1"}```bash

# Asignar múltiples

POST /api/programaciones/asignar_multiples/```

  {"programacion_ids": [1, 2, 3]}

``````bashpython3 -m venv venv



#### **CDs** (`/api/cds/`)### Conductores



```bash# Clonar repositoriosource venv/bin/activate  # En Linux/Mac

# Listar CCTIs

GET /api/cds/cctis/```bash



# Listar Clientes# Listar conductoresgit clone https://github.com/Safary16/soptraloc.git# venv\\Scripts\\activate     # En Windows

GET /api/cds/clientes/

GET /api/drivers/

# Recibir contenedor vacío

POST /api/cds/{id}/recibir_vacio/cd soptraloc```

  {"container_id": 1}

# Conductores disponibles con scores

# Retirar contenedor vacío

POST /api/cds/{id}/retirar_vacio/GET /api/drivers/disponibles/

  {"container_id": 1}

```



Ver documentación completa en [`API_DOCS.md`](API_DOCS.md)# Actualizar posición GPS# Crear entorno virtual### 3. Instalar Dependencias



---POST /api/drivers/{id}/actualizar_posicion/



## 🧪 Datos de Prueba{"latitud": -33.4489, "longitud": -70.6693}python3.12 -m venv venv```bash



El comando `cargar_datos_prueba` crea:



- **2 CCTIs**: ZEAL (Valparaíso), CLEP (San Antonio)# Registrar entregasource venv/bin/activate  # En Windows: venv\Scripts\activatepip install -r requirements.txt

- **3 Clientes**: Walmart, Falabella, Ripley

- **4 Conductores**: 3 disponibles, 1 ocupadoPOST /api/drivers/{id}/registrar_entrega/

- **8 Contenedores**: En diferentes estados

- **3 Programaciones**: 1 con alerta, 1 sin conductor{"cumplida": true}```



```bash

python manage.py cargar_datos_prueba

```# Marcar presente/ausente# Instalar dependencias> 💡 Este paso instala bibliotecas de machine learning como `scikit-learn` y `scipy`. El proceso puede tardar unos minutos en la primera ejecución.



---POST /api/drivers/{id}/marcar_presente/



## ⚙️ ConfiguraciónPOST /api/drivers/{id}/marcar_ausente/pip install -r requirements.txt



### Variables de Entorno



```env# Resetear entregas del día### 4. Configurar Variables de Entorno

# Django

SECRET_KEY=tu-secret-key-seguraPOST /api/drivers/resetear_entregas_dia/

DEBUG=False

ALLOWED_HOSTS=tudominio.com,*.onrender.com```# Configurar variables de entorno```bash



# Database

DATABASE_URL=postgresql://user:pass@host:5432/dbname

### Programacionescp .env.example .envcp .env.example .env

# Mapbox

MAPBOX_API_KEY=pk.tu-api-key-de-mapbox



# Alertas (días)```bash# Editar .env con tus credenciales# Editar .env con tus configuraciones

ALERTA_PROGRAMACION_DIAS=2

ALERTA_DEMURRAGE_DIAS=2# Listar programaciones



# Pesos asignación (deben sumar 1.0)GET /api/programaciones/```

PESO_DISPONIBILIDAD=0.30

PESO_OCUPACION=0.25

PESO_CUMPLIMIENTO=0.30

PESO_PROXIMIDAD=0.15# Ver alertas (programaciones urgentes <48h)# Aplicar migraciones

```

GET /api/programaciones/alertas/

---

python manage.py migrate### 5. Ejecutar Migraciones

## 🔒 Seguridad

# Asignar conductor manualmente

**Configuración automática en producción** (cuando `DEBUG=False`):

POST /api/programaciones/{id}/asignar_conductor/```bash

- ✅ `SECURE_SSL_REDIRECT = True`

- ✅ `SESSION_COOKIE_SECURE = True`{"conductor_id": 1}

- ✅ `CSRF_COOKIE_SECURE = True`

- ✅ `SECURE_HSTS_SECONDS = 31536000`# Crear superusuariocd soptraloc_system

- ✅ HTTPS forzado por Render

- ✅ Database connection pooling# Asignar conductor automáticamente



**⚠️ Cambiar password del superusuario después del primer login**POST /api/programaciones/{id}/asignar_automatico/python manage.py createsuperuserpython manage.py migrate



---



## 📚 Documentación# Ver conductores disponibles con scores```



- **[DEPLOY.md](DEPLOY.md)**: Guía completa de deploy en RenderGET /api/programaciones/{id}/conductores_disponibles/

- **[API_DOCS.md](API_DOCS.md)**: Documentación detallada de API

- **[ESTADO_ACTUAL.md](ESTADO_ACTUAL.md)**: Estado actual del proyecto# Cargar datos iniciales (conductores, CDs)



---# Asignar múltiples programaciones



## 🤝 ContribuirPOST /api/programaciones/asignar_multiples/python manage.py loaddata initial_data### 6. Cargar Datos Iniciales (Chile)



1. Fork el repositorio{"programacion_ids": [1, 2, 3]}

2. Crea una rama: `git checkout -b feature/nueva-funcionalidad`

3. Commit: `git commit -m 'Agrega nueva funcionalidad'```````bash

4. Push: `git push origin feature/nueva-funcionalidad`

5. Abre un Pull Request



---### Centros de Distribución# Ejecutar servidor# Cargar 35 rutas y 70 operaciones para Chile



## 📄 Licencia



Este proyecto es privado y propiedad de SoptraLoc.```bashpython manage.py runserverpython manage.py load_initial_times



---# Listar CDs



## 📞 SoporteGET /api/cds/``````



- **Documentación**: Ver archivos `.md` en el repositorio

- **Issues**: [GitHub Issues](https://github.com/Safary16/soptraloc/issues)

- **Email**: admin@soptraloc.cl# Listar CCTIs



---GET /api/cds/cctis/



## 🎉 Estado del Proyecto## 🌐 Deploy en Render### 7. Crear Superusuario



✅ **Sistema 100% funcional y listo para producción**# Listar Clientes



- 5 modelos implementados con lógica completaGET /api/cds/clientes/```bash

- 45+ endpoints REST API

- 3 importadores Excel

- Sistema de asignación inteligente

- Integración Mapbox completa# Recibir contenedor vacíoEl proyecto está configurado para deploy automático en Render.com:python manage.py createsuperuser

- Deploy automático configurado

- Documentación completaPOST /api/cds/{id}/recibir_vacio/



**¡Listo para deploy en Render!** 🚀{"container_id": "ABCD1234567"}```




# Retirar contenedor vacío1. Conectar repositorio en Render

POST /api/cds/{id}/retirar_vacio/

{"container_id": "ABCD1234567"}2. Configurar variables de entorno (ver `.env.example`)### 8. Iniciar Servidor

```

3. Deploy automático al hacer push a `main````bash

---

python manage.py runserver

## 🚀 Deploy Automático en Render

Variables requeridas:```

### Paso 1: Configurar en Render

- `SECRET_KEY`

1. Ve a [render.com/dashboard](https://dashboard.render.com)

2. Click **"New +"** → **"Blueprint"**- `DATABASE_URL` (PostgreSQL)El sistema estará disponible en:

3. Conecta GitHub y selecciona: **Safary16/soptraloc**

4. Click **"Connect"**- `MAPBOX_API_KEY`- **Home**: http://localhost:8000/



### Paso 2: Deploy Automático- **Dashboard**: http://localhost:8000/dashboard/



Render detectará `render.yaml` y automáticamente:## 📊 API Endpoints- **Panel Admin**: http://localhost:8000/admin/



- ✅ Creará base de datos PostgreSQL (Free)- **API Containers**: http://localhost:8000/api/v1/containers/

- ✅ Creará web service Python/Django (Free)

- ✅ Instalará dependencias### Containers- **API Routing**: http://localhost:8000/api/v1/routing/

- ✅ Aplicará migraciones

- ✅ Creará superusuario `admin/admin`- `POST /api/containers/import-embarque/` - Importar Excel embarque

- ✅ Cargará datos de prueba (si BD vacía)

- `POST /api/containers/import-liberacion/` - Importar Excel liberación---

### Paso 3: Acceder al Sistema

- `POST /api/containers/import-programacion/` - Importar Excel programación

```

🌐 Admin: https://soptraloc.onrender.com/admin/- `GET /api/containers/export-stock/` - Exportar stock (XLSX)## 🚀 Despliegue en Producción

📡 API: https://soptraloc.onrender.com/api/

👤 Usuario: admin- `GET /api/containers/` - Lista de contenedores

🔑 Contraseña: admin

```- `GET /api/containers/{id}/` - Detalle de contenedor### Deploy en Render.com (Recomendado)



**⚠️ IMPORTANTE**: Cambia la contraseña del admin después del primer login.- `GET /api/containers/{id}/historial/` - Historial de eventos



---**Auto-deploy configurado desde GitHub main branch**



## 💻 Desarrollo Local### Drivers



### Requisitos- `GET /api/drivers/` - Lista de conductores1. Crear cuenta en [Render.com](https://render.com)

- Python 3.12+

- PostgreSQL o SQLite- `POST /api/drivers/{id}/marcar-presente/` - Pasar lista2. Conectar repositorio GitHub



### Instalación- `GET /api/drivers/{id}/metricas/` - Métricas de rendimiento3. Configurar variables de entorno:



```bash   ```

# 1. Clonar repositorio

git clone https://github.com/Safary16/soptraloc.git### Asignaciones   SECRET_KEY=tu-secret-key-segura

cd soptraloc

- `POST /api/asignaciones/manual/` - Asignar conductor manualmente   DEBUG=False

# 2. Crear entorno virtual

python -m venv venv- `POST /api/asignaciones/automatica/` - Asignación automática   ALLOWED_HOSTS=tu-app.onrender.com

source venv/bin/activate  # Linux/Mac

# venv\Scripts\activate  # Windows- `POST /api/asignaciones/{id}/iniciar-ruta/` - Iniciar ruta   DATABASE_URL=postgres://... (auto-generado)



# 3. Instalar dependencias- `POST /api/asignaciones/{id}/finalizar/` - Finalizar entrega   ```

pip install -r requirements.txt

- `GET /api/asignaciones/{id}/eta/` - Calcular ETA con Mapbox4. Deploy automático al hacer push a main

# 4. Configurar variables de entorno

cp .env.example .env5. Render ejecuta automáticamente:

# Editar .env con tus valores

### Dashboard   - `pip install -r requirements.txt`

# 5. Aplicar migraciones

python manage.py migrate- `GET /api/dashboard/stats/` - Estadísticas generales   - `python manage.py collectstatic --noinput`



# 6. Cargar datos de prueba- `GET /api/dashboard/alertas/` - Alertas activas   - `python manage.py migrate`

python manage.py cargar_datos_prueba

   - `gunicorn config.wsgi:application`

# 7. Crear superusuario

python manage.py createsuperuser## 📝 Importación de Excel



# 8. Ejecutar servidor**Archivo `render.yaml` incluido con configuración completa**

python manage.py runserver

```### Formato embarque



### Acceso Local| container_id | nave | eta_estimada | tipo_contenedor | peso_kg | puerto_destino | comuna | vendor | sello |### 🚀 Despliegue guiado desde local (`deploy_render.sh`)



- 🌐 Admin: http://localhost:8000/admin/|--------------|------|--------------|-----------------|---------|----------------|--------|--------|-------|

- 📡 API: http://localhost:8000/api/

| TLLU337965-6 | MSC AURORA | 2025-10-15 14:00 | 40HC | 28500 | TPS | Quilicura | ACME Inc | ABC123 |Para automatizar el ciclo "verificar → probar → desplegar" ejecuta:

---



## 📊 Datos de Prueba

### Formato liberación```bash

El comando `cargar_datos_prueba` crea:

| container_id | fecha_liberacion | deposito_devolucion | demurrage_inicio | peso_actualizado_kg |chmod +x deploy_render.sh

- **2 CCTIs**: ZEAL (Valparaíso), CLEP (San Antonio)

- **3 Clientes**: Viña del Mar, Santiago Centro, Quilicura|--------------|------------------|---------------------|------------------|---------------------|./deploy_render.sh

- **4 Conductores**: 3 disponibles con métricas

- **8 Contenedores**: En diferentes estados| TLLU337965-6 | 2025-10-16 09:00 | ZEAL | 2025-10-23 | 28800 |```

- **3 Programaciones**: Incluyendo alertas urgentes



---

### Formato programaciónEl script realiza, en orden:

## 🔧 Configuración

| container_id | fecha_programada | centro_entrega | cliente_final | tipo_servicio |

### Variables de Entorno

|--------------|------------------|----------------|---------------|---------------|1. Instalación/actualización de dependencias.

```env

# Django| TLLU337965-6 | 2025-10-18 10:00 | CD Quilicura | Walmart Chile | directo |2. Verificación de migraciones pendientes (`makemigrations --check`).

SECRET_KEY=tu-secret-key-super-segura

DEBUG=True3. Ejecución de pruebas críticas (`drivers` ML + importadores Excel).

ALLOWED_HOSTS=localhost,127.0.0.1,.onrender.com

## 🔔 Alertas automáticas4. `manage.py check --deploy` con settings de producción.

# Database (SQLite local, PostgreSQL producción)

DATABASE_URL=postgresql://user:pass@host:5432/dbname5. Migraciones y `collectstatic` en tu entorno local.



# Mapbox- **Programación cercana**: Contenedores programados en ≤48h sin conductor6. Validación de árbol Git limpio y, si encuentra un remoto válido, hace push automático a `origin` y a `render`.

MAPBOX_API_KEY=pk.eyJ1Ijoic2FmYXJ5MTYiLCJhIjoiY21naHlvYTQ5MDNlbDJrbjJjcXRtZGg1YSJ9.WCiyTSY_CCfB02N_Nfx7kg

```- **Demurrage próximo**: Demurrage vence en ≤2 días



### Archivos Importantes- **Conductor ocupado**: Asignación solapada detectada> 💡 El script configura por defecto el remoto `render` apuntando a `https://git.render.com/soptraloc/soptraloc.git`.



- `render.yaml` - Configuración deploy Render- **Retraso en ruta**: ETA superado por >30min> - Si tu servicio usa otra URL, sobreescríbela con `export RENDER_REMOTE_URL="https://git.render.com/tu-servicio.git"` antes de ejecutar el script.

- `build.sh` - Script de build automático

- `requirements.txt` - Dependencias Python> - (Opcional) cambia el nombre del remoto con `RENDER_REMOTE_NAME=my-render`.

- `.env.example` - Template variables de entorno

## 🎯 Asignación automática de conductores> - Siempre que detecte el remoto (o lo cree automáticamente) hará push a `origin` y a Render.

---



## 🧪 Testing

Algoritmo de scoring considera:### Comandos Post-Deploy

### Pruebas con Datos Reales

- **Disponibilidad** (30%): Conductor presente```bash

1. **Importar Embarque**:

   - Prepara Excel con columnas: `container_id`, `nave`, `eta`, `tipo`, `peso`, `puerto`, `vendor`, `sello`- **Ocupación** (25%): Tiempo libre vs comprometido# Cargar datos iniciales de Chile en producción

   - POST a `/api/containers/import_embarque/`

- **Cumplimiento** (30%): Histórico de entregas a tiempopython manage.py load_initial_times

2. **Importar Liberación**:

   - Columnas: `container_id`, `fecha_liberacion`, `posicion_fisica`- **Proximidad** (15%): Distancia al punto de inicio

   - POST a `/api/containers/import_liberacion/`

# Actualizar predicciones ML diariamente (configurar en cron)

3. **Importar Programación**:

   - Columnas: `container_id`, `fecha_programada`, `hora`, `demurrage_hasta`, `cd_nombre`## 📈 Aprendizaje del sistemapython manage.py update_time_predictions --verbose

   - POST a `/api/containers/import_programacion/`

```

4. **Asignación Automática**:

   - GET `/api/programaciones/alertas/` para ver urgentesEl sistema registra y aprende:

   - POST `/api/programaciones/{id}/asignar_automatico/`

- Tiempos reales de viaje (vs estimados Mapbox)---

---

- Tiempos de carga/descarga por CD

## 📚 Documentación Adicional

- Patrones de tráfico por hora/día## 📁 Estructura del Proyecto

- **API Completa**: Ver `API_DOCS.md` (generado automáticamente)

- **Guía Deploy**: Ver `DEPLOY.md`- Rendimiento por conductor

- **Estado del Proyecto**: Ver `TODO.md`

```

---

## 🔒 Seguridadsoptraloc/

## 🤝 Contribución

├── soptraloc_system/           # Proyecto Django principal

Este proyecto está en desarrollo activo. Para contribuir:

- Autenticación JWT│   ├── apps/                   # Aplicaciones modulares

1. Fork el repositorio

2. Crea una rama: `git checkout -b feature/nueva-funcionalidad`- Roles: Admin, Planificador, Operador│   │   ├── core/              # Auth, dashboard, funciones base

3. Commit: `git commit -m 'feat: nueva funcionalidad'`

4. Push: `git push origin feature/nueva-funcionalidad`- Auditoría completa de operaciones│   │   ├── containers/        # Gestión completa de contenedores

5. Abre un Pull Request

- Validación de Excel con reportes de errores│   │   ├── drivers/           # Conductores y asignaciones

---

│   │   ├── vehicles/          # Vehículos y chasis

## 📝 Licencia

## 📞 Soporte│   │   ├── routing/           # 🆕 Sistema ML de tiempos

Proyecto privado - Todos los derechos reservados © 2025 SoptraLoc

│   │   └── warehouses/        # Almacenes y ubicaciones

---

Para consultas: [Tu contacto aquí]│   ├── config/                # Configuración Django

## 🆘 Soporte

│   │   ├── settings.py        # Settings principal

Para problemas o preguntas:

- 📧 Email: admin@soptraloc.cl## 📄 Licencia│   │   └── urls.py            # URL routing

- 🐛 Issues: [GitHub Issues](https://github.com/Safary16/soptraloc/issues)

│   ├── templates/             # Templates HTML

---

[Definir licencia]│   │   └── base.html          # 🆕 Con reloj ATC

**Desarrollado con ❤️ usando Django + Mapbox**

│   ├── static/                # Archivos estáticos
│   │   └── js/
│   │       └── realtime-clock.js  # 🆕 Reloj torre de control
│   └── manage.py              # Script de gestión Django
├── requirements.txt           # Dependencias Python
├── render.yaml               # 🆕 Config auto-deploy Render
├── SISTEMA_TIEMPOS_ML.md     # 🆕 Guía completa ML (600+ líneas)
├── ROUTING_ML_QUICKSTART.md  # 🆕 Quick start routing
├── DASHBOARD_FUNCIONAL_COMPLETO.md  # 🆕 Pruebas y verificación
├── RESUMEN_EJECUTIVO_FINAL.md       # 🆕 Overview del sistema
├── GUIA_ACCESO_DASHBOARD.md         # 🆕 Instrucciones de acceso
└── README.md                 # Este archivo
```

---

## � API Endpoints Principales

### Containers API
- `GET /api/v1/containers/` - Listar contenedores
- `POST /api/v1/containers/` - Crear contenedor
- `GET /api/v1/containers/{id}/` - Detalle de contenedor
- `PUT /api/v1/containers/{id}/` - Actualizar contenedor
- `GET /api/v1/containers/urgent/` - 🆕 Contenedores urgentes
- `POST /api/v1/containers/import-manifest/` - Importar Excel
- `POST /api/v1/containers/import-release/` - Importar liberaciones

### Routing API (Machine Learning)
- `GET /api/v1/routing/location-pairs/` - Pares de ubicaciones
- `GET /api/v1/routing/operation-times/` - Tiempos de operaciones
- `GET /api/v1/routing/routes/` - Rutas configuradas
- `GET /api/v1/routing/predict-time/` - 🤖 Predicción ML
- `POST /api/v1/routing/record-actual-time/` - Registrar tiempo real

### Drivers API
- `GET /api/v1/drivers/` - Listar conductores
- `GET /api/v1/drivers/available/` - Conductores disponibles
- `POST /api/v1/drivers/attendance/` - Registrar asistencia
- `GET /api/v1/drivers/alerts/` - Alertas pendientes

### Vehicles API
- `GET /api/v1/vehicles/` - Listar vehículos
- `GET /api/v1/vehicles/available/` - Vehículos disponibles
- `PUT /api/v1/vehicles/{id}/status/` - Actualizar estado

### Documentación Completa
Ver documentación técnica completa en:
- `SISTEMA_TIEMPOS_ML.md` - Sistema de routing y ML
- `ROUTING_ML_QUICKSTART.md` - Quick start guide
- `DASHBOARD_FUNCIONAL_COMPLETO.md` - Pruebas y features

---

## 🧪 Testing y Verificación

### Tests automatizados
```bash
python manage.py test
```

### System Check
```bash
python manage.py check
# Debe mostrar: System check identified no issues (0 silenced).
```

### Verificar migraciones
```bash
python manage.py showmigrations
# Todas deben estar marcadas con [X]
```

### Verificar servidor local
```bash
# Iniciar servidor
python manage.py runserver

# En otra terminal, verificar endpoints:
curl http://localhost:8000/
curl http://localhost:8000/api/v1/containers/
curl http://localhost:8000/dashboard/
```

---

## 📊 Modelos de Datos Implementados

### Core Models
- **Company**: Empresas y clientes
- **Driver**: Conductores con disponibilidad y asistencia
- **Vehicle**: Vehículos/chasis con estado y ubicación
- **Location**: Ubicaciones geográficas (puertos, CDs, bodegas)
- **MovementCode**: Códigos únicos para movimientos

### Container Models
- **Container**: Contenedores con estado, programación y trazabilidad
- **ContainerMovement**: Histórico de movimientos (piso ↔ chasis)
- **ContainerDocument**: Documentos adjuntos (manifiestos, liberaciones)
- **ContainerInspection**: Inspecciones y check-in/check-out

### Routing Models (🆕 Machine Learning)
- **LocationPair**: Pares origen-destino con tiempos estimados
- **OperationTime**: Tiempos de operaciones estándar
- **ActualTripRecord**: Registros reales para entrenamiento ML
- **ActualOperationRecord**: Tiempos reales de operaciones
- **Route**: Rutas completas con múltiples paradas
- **RouteStop**: Paradas individuales de cada ruta

### Driver Models
- **Alert**: Sistema de alertas con prioridades
- **Attendance**: Registro de asistencia diaria
- **Assignment**: Asignaciones de contenedores a conductores

---

## 📚 Documentación Completa

El proyecto incluye documentación exhaustiva:

1. **SISTEMA_TIEMPOS_ML.md** (600+ líneas)
   - Arquitectura completa del sistema de routing
   - Algoritmo de Machine Learning explicado
   - Modelos de datos detallados
   - Ejemplos de uso con código
   - Guía de administración

2. **ROUTING_ML_QUICKSTART.md**
   - Guía rápida de inicio
   - Comandos principales
   - Casos de uso comunes
   - Troubleshooting

3. **DASHBOARD_FUNCIONAL_COMPLETO.md**
   - Pruebas completas realizadas
   - Checklist de verificación
   - Características implementadas
   - Guía de deployment

4. **RESUMEN_EJECUTIVO_FINAL.md**
   - Overview del sistema completo
   - Arquitectura con diagramas
   - Métricas y performance
   - Roadmap futuro

5. **GUIA_ACCESO_DASHBOARD.md**
   - Instrucciones paso a paso
   - URLs y credenciales
   - Tips de debugging
   - Testing móvil

---

## 🎯 Características Técnicas Destacadas

### Machine Learning
- **Algoritmo**: Weighted Average (60% reciente + 40% histórico)
- **Actualización**: Diaria vía comando `update_time_predictions`
- **Confianza**: Sistema de badges visuales en admin
- **Precisión**: Mejora automáticamente con más datos
- **Escalable**: Diseño preparado para algoritmos avanzados

### Real-Time Dashboard
- **Reloj**: Actualización cada 1 segundo
- **Alertas**: Verificación cada 30 segundos
- **WebSockets ready**: Preparado para implementar
- **Responsive**: Bootstrap 5.3.0
- **API-first**: Separación frontend/backend

### Performance
- **Queries optimizadas**: select_related y prefetch_related
- **Indexación**: Campos críticos indexados
- **Caché ready**: Configurado para Redis
- **Static files**: Whitenoise para servir estáticos
- **Database**: PostgreSQL en producción

### Security
- **CSRF protection**: Activado por defecto
- **Authentication**: Django auth system
- **API authentication**: JWT ready
- **HTTPS**: Forzado en producción (Render)
- **Secrets**: Variables de entorno

---

## 🤝 Contribuir

1. Fork el proyecto
2. Crear rama feature (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add: AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Crear Pull Request

### Guía de estilo
- Seguir PEP 8 para código Python
- Usar type hints donde sea posible
- Documentar funciones con docstrings
- Escribir tests para nuevas features
- Actualizar documentación correspondiente

---

## �️ Roadmap

### Fase 1: Core TMS ✅ COMPLETADO
- [x] Gestión de contenedores
- [x] Sistema de conductores y vehículos
- [x] Alertas inteligentes
- [x] Dashboard en tiempo real
- [x] API REST completa

### Fase 2: Machine Learning ✅ COMPLETADO
- [x] Sistema de routing con ML
- [x] 35 rutas Chile pre-cargadas
- [x] 70 operaciones estándar
- [x] Predicción de tiempos
- [x] Aprendizaje continuo

### Fase 3: Optimización Avanzada 🔄 EN PROGRESO
- [ ] Tracking GPS en tiempo real
- [ ] Optimización de rutas con GPS
- [ ] Algoritmos ML avanzados (LSTM, Random Forest)
- [ ] Sistema de recomendaciones IA

### Fase 4: Módulos Adicionales 📋 PLANIFICADO
- [ ] Sistema de costos (Cost Management)
- [ ] Módulo de facturación
- [ ] Integración con ERPs (SAP, Odoo)
- [ ] App móvil para conductores
- [ ] Business Intelligence dashboard

### Fase 5: Enterprise Features 🎯 FUTURO
- [ ] Multi-tenant architecture
- [ ] API pública para clientes
- [ ] Sistema de notificaciones push
- [ ] Integración con IoT sensors
- [ ] Blockchain para trazabilidad

---

## �📝 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.

---

## 📞 Contacto y Soporte

- **Proyecto**: [GitHub Repository](https://github.com/Safary16/soptraloc)
- **Issues**: [GitHub Issues](https://github.com/Safary16/soptraloc/issues)
- **Documentación**: Ver archivos `.md` en el repositorio
- **Deploy Status**: [Render Dashboard](https://dashboard.render.com)

### Para soporte técnico:
1. Revisar documentación técnica en archivos `.md`
2. Buscar en Issues existentes
3. Crear nuevo Issue con detalles completos
4. Revisar logs en Render (producción)

---

## 🏆 Reconocimientos

- **Django Framework** - Por el excelente framework web
- **PostgreSQL** - Por la robusta base de datos
- **Render.com** - Por el hosting gratuito
- **Bootstrap** - Por el framework CSS
- **GitHub Student Pack** - Por las herramientas gratuitas

---

## 📊 Estado del Proyecto

```
┌────────────────────────────────────────────────────┐
│  🚀 SISTEMA SOPTRALOC - ESTADO ACTUAL             │
│                                                    │
│  Versión: 1.0.0                                   │
│  Status: ✅ PRODUCCIÓN READY                      │
│  Commit: 8e848dc                                  │
│  Branch: main                                     │
│                                                    │
│  Features Implementadas:                          │
│  ✅ Dashboard en tiempo real                      │
│  ✅ Reloj estilo torre de control                 │
│  ✅ Sistema de alertas automático                 │
│  ✅ Machine Learning routing (35 rutas)          │
│  ✅ 70 operaciones Chile pre-cargadas            │
│  ✅ API REST completa                             │
│  ✅ Admin panel profesional                       │
│  ✅ Documentación exhaustiva                      │
│                                                    │
│  Performance:                                     │
│  ⚡ Reloj update: 1s                              │
│  ⚡ Alertas check: 30s                            │
│  ⚡ ML predictions: < 100ms                       │
│  ⚡ Dashboard load: < 2s                          │
│                                                    │
│  Deployment:                                      │
│  🔧 Auto-deploy: GitHub → Render                  │
│  🗄️  Database: PostgreSQL                         │
│  🔐 HTTPS: Enabled                                │
│  📊 Monitoring: Ready                             │
│                                                    │
│  Next Steps:                                      │
│  📱 GPS tracking (pendiente permisos)             │
│  💰 Módulo de costos                              │
│  📲 App móvil conductores                         │
│  🤖 ML avanzado (LSTM)                            │
└────────────────────────────────────────────────────┘
```

---

## 🎉 Agradecimientos Especiales

A todos los que han contribuido al desarrollo de este sistema TMS profesional con Machine Learning integrado.

**¡El sistema está 100% funcional y listo para producción!** 🚀✅

---

*Última actualización: 30 de Septiembre de 2025*  
*Desarrollado con ❤️ usando Django y Python*
