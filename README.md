# SoptraLoc TMS - Sistema de Gestión de Contenedores# SoptraLoc - Sistema de Gestión de Contenedores TMS# 🚀 SoptraLoc - Sistema TMS Inteligente con Machine Learning



Sistema profesional de gestión de contenedores para CCTi con integración de Mapbox, asignación inteligente de conductores y seguimiento en tiempo real.



[![Django 5.1.4](https://img.shields.io/badge/Django-5.1.4-green.svg)](https://www.djangoproject.com/)Sistema profesional de gestión de contenedores para CCTi con integración de Mapbox, asignación inteligente de conductores y seguimiento en tiempo real.[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/Safary16/soptraloc)

[![Python 3.12+](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/Safary16/soptraloc)[![Django 5.2.6](https://img.shields.io/badge/Django-5.2.6-green.svg)](https://www.djangoproject.com/)



---## 🚀 Características principales[![Python 3.12+](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)



## 🚀 Características Principales[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Ready-blue.svg)](https://www.postgresql.org/)



### 📦 Gestión Completa de Contenedores- **Importación de Excel**: Embarque, Liberación, Programación

- **11 Estados**: `por_arribar`, `liberado`, `secuenciado`, `programado`, `asignado`, `en_ruta`, `entregado`, `descargado`, `en_almacen_ccti`, `vacio_en_ruta`, `vacio_en_ccti`

- **Importación Excel**: Embarque, Liberación, Programación- **Gestión de estados**: 11 estados de contenedores con transiciones automáticas## ✨ **Sistema Completo de Gestión de Transporte (TMS)**

- **Exportación**: Stock con flag de secuenciado

- **Trazabilidad**: Historial completo de eventos- **Asignación inteligente**: Algoritmo automático de asignación de conductores



### 🚛 Sistema Inteligente de Conductores- **Mapbox Integration**: Rutas reales, tiempos estimados, tráfico en vivoSistema profesional de gestión logística con **Machine Learning**, **alertas en tiempo real** y **dashboard estilo torre de control aéreo**.

- **Asignación Automática**: Algoritmo con 4 factores ponderados

  - Disponibilidad (30%)- **Alertas**: Demurrage cercano, programación sin conductor

  - Ocupación (25%)

  - Cumplimiento (30%)- **Exportación**: Stock liberado/por arribar con flag de secuenciado### **🎯 Lo que incluye:**

  - Proximidad (15%)

- **Métricas**: Cumplimiento, ocupación, total entregas- **Historial completo**: Auditoría de todas las operaciones- ⏰ **Reloj en tiempo real** estilo torre de control aéreo

- **GPS**: Actualización de posición en tiempo real

- **API REST**: Endpoints completos para integración- 🚨 **Sistema de alertas urgentes** con verificación automática cada 30 segundos

### 🗺️ Integración Mapbox

- **Rutas Reales**: Cálculo con tráfico en tiempo real- 🗺️ **35 rutas Chile pre-configuradas** (puertos, CDs, bodegas)

- **ETAs Precisos**: Tiempo estimado de llegada

- **Matriz de Distancias**: Cálculos masivos## 📋 Flujo del sistema- 🤖 **Machine Learning** para predicción de tiempos (60% reciente / 40% histórico)

- **Scores de Proximidad**: Para asignación inteligente

- 📊 **Dashboard inteligente** con ordenamiento por urgencia

### 🚨 Sistema de Alertas

- **48 Horas**: Alerta automática si programación sin conductor```- 🚛 **Sistema de conductores** con asignación inteligente

- **Demurrage**: Seguimiento de tiempos límite

- **Verificación**: Checks automáticos cada hora1. EMBARQUE (Excel) → Contenedores creados con estado "por_arribar"- 📦 **Gestión completa de contenedores** con estados y movimientos



### 🏢 Gestión de Centros de Distribución   ├─ Campos: container_id, nave, ETA, tipo, peso, puerto, vendor, sello- 🔔 **Sistema de proximidad** con alertas automáticas

- **CCTIs**: Control de contenedores vacíos

- **Clientes**: Centros de entrega final   - 🔌 **API REST completa** con endpoints documentados

- **Capacidad**: Monitoreo de espacios disponibles

- **Geocodificación**: Coordenadas para cálculo de rutas2. LIBERACIÓN (Excel) → Contenedores pasan a "liberado"- 👨‍💼 **Panel de administración** profesional con badges ML



---   ├─ Reglas de posición física:



## 📋 Flujo del Sistema   │  ├─ TPS Valparaíso → ZEAL---



```   │  ├─ STI/PCE San Antonio → CLEP SAI

1. EMBARQUE (Excel)

   └─> Contenedores creados con estado "por_arribar"   │  └─ Retiro CCTi → en_transito_a_ccti## 🚀 Características Principales

       • Campos: container_id, nave, ETA, tipo, peso, puerto, vendor, sello

   

2. LIBERACIÓN (Excel)

   └─> Contenedores actualizados a "liberado"3. EXPORTACIÓN → Stock para cliente### ⏰ Reloj en Tiempo Real - Estilo Torre de Control

       • Mapeo automático de posiciones:

         - TPS Valparaíso → ZEAL   ├─ Liberados + Por arribar- **Diseño profesional**: Colores verde fosforescente sobre azul gradiente

         - STI/PCE San Antonio → CLEP

   └─ Flag "secuenciado" si liberación futura- **Actualización**: Cada 1 segundo con precisión milimétrica

3. EXPORTACIÓN

   └─> Stock para cliente (Liberados + Por arribar)   - **Formato**: HH:MM:SS + DÍA DD MES YYYY

       • Flag "secuenciado" si liberación futura

4. PROGRAMACIÓN (Excel) → Contenedores pasan a "programado"- **Badge urgente**: Contador animado de contenedores críticos

4. PROGRAMACIÓN (Excel)

   └─> Contenedores pasan a "programado"   ├─ Asigna fecha, demurrage, centro entrega- **Modal detallado**: Lista completa de contenedores urgentes con niveles

       • Asigna fecha, demurrage, centro entrega

       • Alerta si falta conductor 48h antes   



5. ASIGNACIÓN (Manual/Automática)5. ASIGNACIÓN → Conductor asignado (manual/automático)### 🗺️ Sistema de Routing con Machine Learning

   └─> Conductor asignado según algoritmo

       • Evalúa disponibilidad, ocupación, cumplimiento, proximidad   ├─ Alerta si falta conductor 48h antes- **35 rutas Chile**: Puertos (San Antonio, Valparaíso, San Vicente, Lirquén, Coronel)



6. EN RUTA   - **70 operaciones**: Tiempos estándar para cada tipo de operación

   └─> Operador inicia ruta

       • Calcula ETA con Mapbox6. RUTA → Operador inicia, calcula ETA con Mapbox- **Algoritmo ML**: Promedio ponderado (60% datos recientes + 40% históricos)

       • Tracking en tiempo real

   - **Predicción inteligente**: Tiempos estimados basados en datos reales

7. ENTREGA

   └─> Registro de llegada y descarga7. ENTREGA → Registro de llegada y descarga- **Sistema de confianza**: Badges visuales (Alta/Media/Baja)

       • Actualiza métricas del conductor

   - **Aprendizaje continuo**: Actualización diaria con datos reales

8. VACÍO

   └─> Control de retorno a CCTi8. VACÍO → Control de retorno y ubicación

       • Gestión de espacios disponibles

``````### � Gestión Avanzada de Contenedores



---- **Múltiples estados**: PROGRAMADO, EN_PROCESO, EN_TRANSITO, LIBERADO, DESCARGADO, EN_SECUENCIA



## 🏗️ Arquitectura## 🗂️ Estados del contenedor- **Trazabilidad completa**: Histórico de todos los movimientos



### Apps Django- **Alertas de proximidad**: Contenedores urgentes < 2 horas



```- `por_arribar` - Nave aún no atracada- **Asignación rápida**: Integración con sistema de conductores

apps/

├── containers/       # Modelo Container, importadores, exportación- `liberado` - Contenedor liberado por aduana- **Importación Excel**: Carga masiva de manifiestos y liberaciones

├── drivers/          # Modelo Driver, métricas, posiciones

├── programaciones/   # Modelo Programacion, alertas, asignación- `secuenciado` - Liberación futura programada

├── cds/              # Modelo CD (CCTIs y Clientes)

└── events/           # Modelo Event (auditoría)- `programado` - Entrega programada con fecha### � Sistema de Alertas Inteligentes



config/- `asignado` - Conductor asignado- **Verificación automática**: Cada 30 segundos verifica contenedores urgentes

├── settings.py       # Configuración Django

└── urls.py          # Routing API- `en_ruta` - Ruta iniciada- **3 niveles de urgencia**: CRÍTICO (< 1h), ALTO (< 2h), MEDIO (< 4h)



apps/core/- `entregado` - Entregado a cliente- **Notificaciones visuales**: Badge pulsante en navbar

└── services/

    ├── mapbox.py     # Integración Mapbox Directions API- `descargado` - Descargado en CD- **Modal detallado**: Click para ver lista completa con información

    └── assignment.py # Algoritmo de asignación

```- `en_almacen_ccti` - En bodega CCTi- **API endpoint**: `/api/v1/containers/urgent/` para integraciones



### Modelos de Datos- `vacio_en_ruta` - Retorno con vacío



**Container**- `vacio_en_ccti` - Vacío en CCTi### 📊 Dashboard Ejecutivo

- `container_id`, `nave`, `eta`, `tipo`, `peso`

- `estado`, `posicion_fisica`, `puerto`, `vendor`, `sello`- **Estadísticas en tiempo real**: Total activos, por estado, disponibilidad

- `fecha_liberacion`, `fecha_programada`, `fecha_asignacion`

- `metodo cambiar_estado(nuevo_estado)`## 🛠️ Stack tecnológico- **Vista prioritaria**: Contenedores urgentes destacados y ordenados



**Driver**- **Integración ML**: Predicciones de tiempos en ruta

- `nombre`, `rut`, `disponible`, `presente`

- `total_entregas_dia`, `entregas_cumplidas`, `entregas_totales`- **Backend**: Django 5.1.4 + Django REST Framework- **Alertas pendientes**: Asignaciones sin completar

- `posicion_lat`, `posicion_lng`

- `@property ocupacion_porcentaje`, `esta_disponible`- **Base de datos**: PostgreSQL 15- **Responsive design**: Adaptable a móviles y tablets

- `metodo actualizar_posicion()`, `registrar_entrega()`

- **Cache/Queue**: Redis (Celery opcional)

**Programacion**

- `container`, `conductor`, `cd`- **Mapas**: Mapbox API (GitHub Student Pack)## 🛠️ Tecnologías Utilizadas

- `fecha_programada`, `hora_programada`, `demurrage_hasta`

- `alerta_conductor`, `asignacion_automatica`- **Deploy**: Render.com

- `@property requiere_conductor_urgente`

- `metodo verificar_alerta()`, `asignar_conductor()`- **Python**: 3.12- **Backend**: Django 5.2.6 + Django REST Framework



**CD (Centro de Distribución)**- **Base de Datos**: SQLite (desarrollo) / PostgreSQL (producción)

- `nombre`, `tipo` (CCTI/CLIENTE), `direccion`

- `latitud`, `longitud`## 🏗️ Estructura del proyecto- **API Documentation**: DRF-YASG (Swagger/OpenAPI)

- `puede_recibir_vacios`, `capacidad_vacios`, `vacios_actuales`

- `metodo recibir_vacio()`, `retirar_vacio()`- **Autenticación**: JWT (Simple JWT)



**Event**```- **Frontend**: API REST (listo para integración con cualquier frontend)

- `container`, `tipo_evento`, `timestamp`, `detalles` (JSON)

- Tipos: embarque, liberacion, programacion, asignacion, en_ruta, etc.soptraloc/



---├── apps/## 📋 Instalación y Configuración



## 🔌 API REST Completa│   ├── containers/      # Gestión de contenedores



### Contenedores│   ├── drivers/         # Conductores y asignaciones### Prerrequisitos



```bash│   ├── programaciones/  # Programación de entregas- Python 3.12+

# Listar contenedores

GET /api/containers/│   ├── events/          # Historial y auditoría- Git



# Importar embarque│   └── cds/            # Centros de distribución- Entorno virtual (recomendado)

POST /api/containers/import_embarque/

Content-Type: multipart/form-data├── config/             # Configuración Django

file: embarque.xlsx

├── importers/          # Procesadores de Excel### 1. Clonar el Repositorio

# Importar liberación

POST /api/containers/import_liberacion/├── exporters/          # Generadores de reportes```bash

file: liberacion.xlsx

├── services/           # Lógica de negociogit clone https://github.com/Safary16/soptraloc.git

# Importar programación

POST /api/containers/import_programacion/└── utils/              # Utilidades compartidascd soptraloc

file: programacion.xlsx

``````

# Exportar stock

GET /api/containers/export_stock/



# Cambiar estado## 📦 Instalación local### 2. Crear Entorno Virtual

POST /api/containers/{id}/cambiar_estado/

{"nuevo_estado": "en_ruta", "usuario": "operador1"}```bash

```

```bashpython3 -m venv venv

### Conductores

# Clonar repositoriosource venv/bin/activate  # En Linux/Mac

```bash

# Listar conductoresgit clone https://github.com/Safary16/soptraloc.git# venv\\Scripts\\activate     # En Windows

GET /api/drivers/

cd soptraloc```

# Conductores disponibles con scores

GET /api/drivers/disponibles/



# Actualizar posición GPS# Crear entorno virtual### 3. Instalar Dependencias

POST /api/drivers/{id}/actualizar_posicion/

{"latitud": -33.4489, "longitud": -70.6693}python3.12 -m venv venv```bash



# Registrar entregasource venv/bin/activate  # En Windows: venv\Scripts\activatepip install -r requirements.txt

POST /api/drivers/{id}/registrar_entrega/

{"cumplida": true}```



# Marcar presente/ausente# Instalar dependencias> 💡 Este paso instala bibliotecas de machine learning como `scikit-learn` y `scipy`. El proceso puede tardar unos minutos en la primera ejecución.

POST /api/drivers/{id}/marcar_presente/

POST /api/drivers/{id}/marcar_ausente/pip install -r requirements.txt



# Resetear entregas del día### 4. Configurar Variables de Entorno

POST /api/drivers/resetear_entregas_dia/

```# Configurar variables de entorno```bash



### Programacionescp .env.example .envcp .env.example .env



```bash# Editar .env con tus credenciales# Editar .env con tus configuraciones

# Listar programaciones

GET /api/programaciones/```



# Ver alertas (programaciones urgentes <48h)# Aplicar migraciones

GET /api/programaciones/alertas/

python manage.py migrate### 5. Ejecutar Migraciones

# Asignar conductor manualmente

POST /api/programaciones/{id}/asignar_conductor/```bash

{"conductor_id": 1}

# Crear superusuariocd soptraloc_system

# Asignar conductor automáticamente

POST /api/programaciones/{id}/asignar_automatico/python manage.py createsuperuserpython manage.py migrate



# Ver conductores disponibles con scores```

GET /api/programaciones/{id}/conductores_disponibles/

# Cargar datos iniciales (conductores, CDs)

# Asignar múltiples programaciones

POST /api/programaciones/asignar_multiples/python manage.py loaddata initial_data### 6. Cargar Datos Iniciales (Chile)

{"programacion_ids": [1, 2, 3]}

``````bash



### Centros de Distribución# Ejecutar servidor# Cargar 35 rutas y 70 operaciones para Chile



```bashpython manage.py runserverpython manage.py load_initial_times

# Listar CDs

GET /api/cds/``````



# Listar CCTIs

GET /api/cds/cctis/

## 🌐 Deploy en Render### 7. Crear Superusuario

# Listar Clientes

GET /api/cds/clientes/```bash



# Recibir contenedor vacíoEl proyecto está configurado para deploy automático en Render.com:python manage.py createsuperuser

POST /api/cds/{id}/recibir_vacio/

{"container_id": "ABCD1234567"}```



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
