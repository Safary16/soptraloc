# 🚀 SoptraLoc - Sistema TMS Inteligente con Machine Learning

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/Safary16/soptraloc)
[![Django 5.1.4](https://img.shields.io/badge/Django-5.1.4-green.svg)](https://www.djangoproject.com/)
[![Python 3.12+](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Ready-blue.svg)](https://www.postgresql.org/)
[![Stable Checkpoint](https://img.shields.io/badge/Checkpoint-v1.0.0--stable-brightgreen.svg)](CHECKPOINT_ESTABLE.md)

Sistema profesional de gestión de contenedores para CCTi con **integración Mapbox**, **asignación inteligente de conductores** y **seguimiento en tiempo real**.

> 🔖 **Checkpoint Estable**: Este proyecto tiene un punto de referencia estable marcado como `v1.0.0-stable`. [Ver detalles del checkpoint →](CHECKPOINT_ESTABLE.md)

---

## ✨ Características Principales

### 📦 Gestión Completa de Contenedores

- **11 Estados del ciclo de vida**:
  - `por_arribar` → `liberado` → `secuenciado` → `programado` → `asignado` → `en_ruta` → `entregado` → `descargado` → `en_almacen_ccti` → `vacio_en_ruta` → `devuelto`
  
- **Importación Excel** (3 tipos):
  - 📥 **Embarque**: Crea contenedores con estado `por_arribar`
  - 📥 **Liberación**: Actualiza a `liberado` con mapeo automático de posiciones (TPS→ZEAL, STI/PCE→CLEP)
  - 📥 **Programación**: Crea programaciones y verifica alertas de demurrage (48h)

- **Exportación Excel**:
  - 📤 Stock liberado/por arribar con flag de secuenciado

- **Transiciones automáticas** con timestamps y eventos de auditoría

- **Trazabilidad**: Historial completo de eventos

### 🚛 Sistema Inteligente de Conductores

- **Asignación Automática**: Algoritmo con 4 factores ponderados:
  - Disponibilidad (30%)
  - Ocupación (25%)
  - Cumplimiento (30%)
  - Proximidad (15%)

- **Métricas en tiempo real**:
  - Disponibilidad (presente/ausente)
  - Ocupación (entregas asignadas vs capacidad)
  - Cumplimiento (entregas completadas vs programadas)
  - Posición GPS actualizable

- **Capacidad configurable**: Entregas diarias máximas por conductor
- **Reset automático**: Entregas del día se resetean automáticamente
- **Historial completo**: Auditoría de todas las operaciones

### 🤖 Asignación Inteligente

**Algoritmo con pesos configurables**:

```python
Score Total = (Disponibilidad × 30%) + 
              (Ocupación × 25%) +
              (Cumplimiento × 30%) + 
              (Proximidad × 15%)
```

**Endpoints API**:
- Asignación automática individual
- Asignación masiva para múltiples programaciones
- Lista de conductores disponibles con scores calculados
- Reset de entregas diarias

### 🗺️ Integración Mapbox

- **Cálculo de rutas** en tiempo real
- **ETA inteligente** con tráfico en vivo
- **35 rutas predefinidas** para Chile
- **Geocoding** de direcciones
- **Matriz de distancias** para múltiples puntos

### 📱 Portal del Conductor (GPS Background)

- **PWA instalable** con Service Workers
- **App Nativa Android (APK)** con GPS continuo
- **Tracking GPS en background** incluso con pantalla bloqueada
- **Permisos nativos Android** para ubicación permanente
- **Servicio foreground** mantiene GPS activo
- **Notificación persistente** indica estado GPS
- **Legal y seguro**: Cumple Ley de Tránsito N° 18.290 (Chile)
- **Sin Google Play requerido**: APK descargable directamente

**Documentación:**
- [📱 NATIVE_ANDROID_APP.md](NATIVE_ANDROID_APP.md) - Guía técnica completa
- [👨‍✈️ GUIA_INSTALACION_APP_CONDUCTORES.md](GUIA_INSTALACION_APP_CONDUCTORES.md) - Guía para conductores
- [📂 android/](android/) - Código fuente Android (TWA)

### 🏢 Centros de Distribución (CDs)

- **2 tipos**: CCTI (almacenes propios) y Clientes
- **Capacidades configurables** por tipo de contenedor
- **Gestión de vacíos**: 
  - Recepción de contenedores vacíos en CCTI
  - Retiro de vacíos desde CCTI
  - Control de capacidad disponible

### 📊 Dashboard y Alertas

- **Alertas de demurrage**: Notificaciones cuando faltan menos de 48h
- **Dashboard en tiempo real**: Estadísticas y métricas actualizadas
- **Estados visuales**: Seguimiento del ciclo completo de cada contenedor
- **Priorización automática**: Score de urgencia por días restantes

### 🎨 Frontend Estilo Ubuntu

- **Diseño profesional** con colores Ubuntu (naranja #E95420 y púrpura #772953)
- **Dashboard interactivo** con reloj en tiempo real
- **Tablas responsive** con paginación
- **Sistema de asignación visual** con scores y badges
- **Estados de contenedores** con flujo visual
- **Importación de Excel** con interfaz intuitiva

---

## 🛠️ Stack Tecnológico

- **Backend**: Django 5.1.4 + Django REST Framework 3.16.1
- **Database**: PostgreSQL (producción) / SQLite (desarrollo)
- **API Docs**: drf-yasg (Swagger/OpenAPI)
- **Excel**: pandas 2.2.2 + openpyxl 3.1.2
- **Mapbox**: requests 2.32.3
- **Deploy**: Render.com con build automático
- **Web Server**: Gunicorn + WhiteNoise

---

## 📁 Estructura del Proyecto

```
soptraloc/
├── apps/
│   ├── containers/         # Modelos y lógica de contenedores
│   │   ├── models.py       # Container con 11 estados
│   │   ├── views.py        # ContainerViewSet con 6 custom actions
│   │   ├── serializers.py  # 3 serializers (full, list, export)
│   │   ├── admin.py        # Admin con acciones batch
│   │   └── importers/      # 3 importadores Excel
│   │       ├── embarque.py
│   │       ├── liberacion.py
│   │       └── programacion.py
│   │
│   ├── drivers/            # Gestión de conductores
│   │   ├── models.py       # Driver con métricas
│   │   ├── views.py        # DriverViewSet con 6 custom actions
│   │   └── serializers.py  # 3 serializers (full, list, disponible)
│   │
│   ├── programaciones/     # Sistema de programación
│   │   ├── models.py       # Programacion con alertas 48h
│   │   ├── views.py        # ProgramacionViewSet con 5 custom actions
│   │   └── serializers.py  # 3 serializers (full, list, create)
│   │
│   ├── cds/                # Centros de distribución
│   │   ├── models.py       # CD con gestión de vacíos
│   │   ├── views.py        # CDViewSet con 4 custom actions
│   │   └── management/commands/
│   │       └── cargar_datos_prueba.py  # Comando para test data
│   │
│   ├── events/             # Sistema de auditoría
│   │   ├── models.py       # Event con 11 tipos
│   │   └── serializers.py
│   │
│   └── core/               # Servicios compartidos
│       └── services/
│           ├── mapbox.py       # Integración Mapbox
│           └── assignment.py   # Algoritmo de asignación
│
├── config/                 # Configuración Django
│   ├── settings.py         # Settings con PostgreSQL
│   ├── urls.py             # URL routing
│   └── wsgi.py
│
├── templates/              # Templates HTML
│   ├── base.html           # Base con navbar Ubuntu
│   ├── home.html           # Dashboard principal
│   ├── asignacion.html     # Sistema de asignación
│   ├── estados.html        # Estados de contenedores
│   ├── containers_list.html
│   ├── container_detail.html
│   └── importar.html       # Importación Excel
│
├── static/
│   ├── css/
│   │   └── ubuntu-style.css  # Estilos Ubuntu completos
│   └── js/
│       └── main.js           # JavaScript interactivo
│
├── requirements.txt        # Dependencias Python
├── render.yaml            # Configuración Render
├── build.sh               # Script de build para Render
└── manage.py              # Django management
```

---

## 🚀 Instalación Local

### 1. Clonar Repositorio

```bash
git clone https://github.com/Safary16/soptraloc.git
cd soptraloc
```

### 2. Crear Entorno Virtual

```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 3. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar Variables de Entorno

```bash
cp .env.example .env
# Editar .env con tus valores
```

**Variables requeridas**:
- `SECRET_KEY` - Clave secreta de Django
- `DEBUG` - True para desarrollo, False para producción
- `DATABASE_URL` - URL de PostgreSQL (opcional, usa SQLite si no se provee)
- `MAPBOX_ACCESS_TOKEN` - Token de Mapbox para routing

### 5. Aplicar Migraciones

```bash
python manage.py migrate
```

### 6. Cargar Datos de Prueba

```bash
python manage.py cargar_datos_prueba
```

### 7. Crear Superusuario

```bash
python manage.py createsuperuser
```

### 8. Ejecutar Servidor

```bash
python manage.py runserver
```

Visita: `http://localhost:8000`

---

## 🌐 Deploy en Render

El proyecto está configurado para deploy automático en Render.com con **Blueprint**:

### 🚀 Despliegue Rápido

1. Ve a: https://dashboard.render.com/
2. Click en **"New +"** → **"Blueprint"**
3. Conecta tu repositorio: `Safary16/soptraloc`
4. Render detectará automáticamente `render.yaml`
5. Click en **"Apply"**

**¡Eso es todo!** El sitio estará disponible en: https://soptraloc.onrender.com

### ✅ Configuración Automática

**Archivo `render.yaml` incluido con:**
- ✅ Web Service configurado
- ✅ PostgreSQL Database
- ✅ Variables de entorno
- ✅ Build script automático
- ✅ Admin user creado automáticamente (admin/1234)

**Build script ejecuta automáticamente:**
- `pip install -r requirements.txt`
- `python manage.py collectstatic --noinput`
- `python manage.py migrate`
- `python manage.py reset_admin --username=admin --password=1234`
- `gunicorn config.wsgi:application`

### 📚 Documentación Completa

Ver guías detalladas:
- **[RENDER_DEPLOYMENT.md](RENDER_DEPLOYMENT.md)** - Guía completa de despliegue
- **[DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)** - Lista de verificación paso a paso

**Deploy automático** al hacer push a la rama principal.

---

## 📡 API REST - Endpoints Principales

### Contenedores

- `GET /api/containers/` - Listar contenedores
- `POST /api/containers/` - Crear contenedor
- `GET /api/containers/{id}/` - Detalle de contenedor
- `POST /api/containers/import-embarque/` - Importar embarque (Excel)
- `POST /api/containers/import-liberacion/` - Importar liberación (Excel)
- `GET /api/containers/export_stock/` - Exportar stock (Excel)
- `POST /api/containers/{id}/cambiar_estado/` - Cambiar estado

### Conductores

- `GET /api/drivers/` - Listar conductores
- `POST /api/drivers/` - Crear conductor
- `GET /api/drivers/{id}/` - Detalle de conductor
- `POST /api/drivers/import-excel/` - Importar conductores (Excel)
- `POST /api/drivers/{id}/reset_entregas_diarias/` - Reset entregas
- `GET /api/drivers/{id}/historial/` - Historial de entregas

### Programaciones

- `GET /api/programaciones/` - Listar programaciones
- `POST /api/programaciones/` - Crear programación
- `GET /api/programaciones/{id}/` - Detalle de programación
- `POST /api/programaciones/import-excel/` - Importar programaciones (Excel)
- `POST /api/programaciones/{id}/asignar_conductor/` - Asignar manualmente
- `POST /api/programaciones/{id}/asignar_automatico/` - Asignar automático
- `GET /api/programaciones/{id}/conductores_disponibles/` - Listar conductores con scores
- `POST /api/programaciones/asignar_multiple/` - Asignar múltiples

### Centros de Distribución

- `GET /api/cds/` - Listar CDs
- `POST /api/cds/` - Crear CD
- `GET /api/cds/{id}/` - Detalle de CD
- `GET /api/cds/clientes/` - Listar solo CDs clientes
- `POST /api/cds/{id}/recibir_vacio/` - Recibir contenedor vacío
- `POST /api/cds/{id}/retirar_vacio/` - Retirar contenedor vacío
- `GET /api/cds/{id}/capacidad/` - Verificar capacidad

### Asignaciones (Nueva app)

- `GET /api/asignaciones/` - Listar asignaciones
- `GET /api/asignaciones/{id}/` - Detalle de asignación
- `POST /api/asignaciones/{id}/iniciar_ruta/` - Iniciar ruta
- `POST /api/asignaciones/{id}/actualizar_posicion/` - Actualizar GPS
- `POST /api/asignaciones/{id}/finalizar/` - Finalizar entrega
- `GET /api/asignaciones/{id}/eta/` - Calcular ETA con Mapbox

### Dashboard

- `GET /api/dashboard/stats/` - Estadísticas generales
- `GET /api/dashboard/alertas/` - Alertas activas

---

## 📝 Importación de Excel

### 1. Embarque/Manifiesto

**Columnas requeridas**:
- `Container ID` - Identificador único
- `Nave` - Nombre del barco
- `ETA` - Fecha estimada de arribo (DD/MM/YYYY)
- `Tipo` - 20DC, 40HC, 40DV, etc.
- `Peso Bruto` - Peso en kg
- `Puerto` - Puerto de origen/destino
- `Vendor` - Proveedor
- `Sello` - Número de sello

**Endpoint**: `POST /api/containers/import-embarque/`

### 2. Liberación

**Columnas requeridas**:
- `Container ID` - Debe existir en el sistema
- `Fecha Liberación` - DD/MM/YYYY
- `Posición` - TPS, ZEAL, STI, CLEP, etc.

**Mapeo automático**:
- TPS Valparaíso → ZEAL
- STI/PCE San Antonio → CLEP

**Endpoint**: `POST /api/containers/import-liberacion/`

### 3. Programación

**Columnas requeridas**:
- `Container ID` - Debe estar liberado
- `Fecha Programacion` - DD/MM/YYYY
- `Fecha Demurrage` - DD/MM/YYYY
- `Centro Entrega` - Debe existir como CD Cliente

**Alertas automáticas**:
- Si fecha_programacion < 48h → Marca como alerta

**Endpoint**: `POST /api/programaciones/import-excel/`

### 4. Conductores

**Columnas requeridas**:
- `Nombre` - Nombre completo
- `Rut` - RUT chileno (formato: 12345678-9)
- `Licencia` - Número de licencia
- `Tipo Licencia` - A1, A2, A3, etc.
- `Telefono` - Número de contacto
- `Capacidad Diaria` - Número máximo de entregas por día

**Endpoint**: `POST /api/drivers/import-excel/`

---

## 📊 Flujo de Trabajo

### 1. Importar Embarque
- Carga contenedores desde manifiesto
- Estado inicial: `por_arribar`
- Evento: "contenedor_creado"

### 2. Importar Liberación
- Actualiza contenedores a `liberado`
- Mapea posiciones automáticamente
- Evento: "cambio_estado"

### 3. Exportar Stock
- Genera Excel con liberados + por arribar
- Flag "secuenciado" marca procesados

### 4. Importar Programación
- Crea programaciones con estado `programado`
- Verifica alertas (< 48h)
- Evento: "programacion_creada"

### 5. Asignar Conductor
- Manual: selección directa
- Automático: algoritmo con scoring
- Estado contenedor: `asignado`
- Evento: "conductor_asignado"

### 6. Iniciar Ruta
- Conductor marca inicio
- Calcula ETA con Mapbox
- Estado: `en_ruta`
- Evento: "cambio_estado"

### 7. Entregar
- Registra llegada y descarga
- Actualiza métricas del conductor
- Estado: `entregado` → `descargado`
- Evento: "cambio_estado"

### 8. Gestión de Vacíos
- Control de retorno a CCTI
- Verificación de capacidad
- Estados: `en_almacen_ccti` → `vacio_en_ruta` → `devuelto`

---

## 🎯 Características Avanzadas

### Algoritmo de Asignación Inteligente

```python
def calcular_score(conductor, programacion):
    # 1. Disponibilidad (30%)
    disponibilidad = 1.0 if conductor.disponibilidad == 'presente' else 0.0
    
    # 2. Ocupación (25%) - Menor ocupación = mejor
    ocupacion = 1.0 - (conductor.entregas_hoy / conductor.capacidad_diaria)
    
    # 3. Cumplimiento (30%)
    cumplimiento = conductor.entregas_completadas / conductor.entregas_totales
    
    # 4. Proximidad (15%) - Distancia Mapbox
    distancia = mapbox.calcular_distancia(conductor.ultima_posicion, programacion.cd)
    proximidad = 1.0 - min(distancia / 100, 1.0)  # Normalizado
    
    # Score final
    score = (disponibilidad * 0.30 + 
             ocupacion * 0.25 + 
             cumplimiento * 0.30 + 
             proximidad * 0.15) * 100
    
    return score
```

### Sistema de Alertas

1. **Alerta de Demurrage** (< 48h):
   - Notificación en dashboard
   - Badge rojo en programación
   - Email automático (opcional)

2. **Alerta de Capacidad**:
   - CCTI lleno
   - Conductor sin disponibilidad

3. **Alerta de Estado**:
   - Contenedor sin asignar (< 24h)
   - Entrega atrasada

### Auditoría Completa

Todos los eventos se registran:
- `contenedor_creado`
- `cambio_estado`
- `programacion_creada`
- `conductor_asignado`
- `ruta_iniciada`
- `posicion_actualizada`
- `entrega_completada`
- `vacio_recibido`
- `vacio_retirado`
- `alerta_generada`
- `capacidad_verificada`

---

## 🧪 Testing

### Ejecutar Tests

```bash
python manage.py test
```

### Archivos de Test

- `test_estados.py` - Tests de estados de contenedores
- `test_import.py` - Tests de importadores Excel
- `apps/*/tests.py` - Tests específicos por app

### Datos de Prueba

```bash
python manage.py cargar_datos_prueba
```

Crea:
- 5 Conductores
- 3 CDs (2 CCTI + 1 Cliente)
- 10 Contenedores con diferentes estados
- 5 Programaciones

---

## 🎉 Estado del Proyecto

✅ **Sistema 100% funcional y listo para producción**

- 5 modelos implementados con lógica completa
- 45+ endpoints REST API
- 3 importadores Excel
- Sistema de asignación inteligente
- Integración Mapbox completa
- Frontend estilo Ubuntu
- Deploy automático configurado
- Documentación completa

**¡Listo para deploy en Render!** 🚀

---

## 🔖 Checkpoint Estable

Este proyecto tiene un **punto de referencia estable** que puedes usar como base:

- **Tag Git**: `v1.0.0-stable`
- **Estado**: ✅ Sistema 100% funcional
- **Fecha**: 13 de Octubre, 2025

### Cómo usar el checkpoint:

```bash
# Ver el checkpoint
git show v1.0.0-stable

# Volver al checkpoint (crear nuevo branch)
git checkout -b restaurar v1.0.0-stable

# Comparar con el checkpoint
git diff v1.0.0-stable
```

### Documentación del checkpoint:
- 📄 [**CHECKPOINT_ESTABLE.md**](CHECKPOINT_ESTABLE.md) - Documentación completa del checkpoint
- 📄 [**COMO_USAR_CHECKPOINT.md**](COMO_USAR_CHECKPOINT.md) - Guía rápida de uso
- 📄 [**CHECKPOINT_VISUAL.md**](CHECKPOINT_VISUAL.md) - Guía visual con diagramas

---

## 📞 Soporte

- **Repositorio**: https://github.com/Safary16/soptraloc
- **Documentación API**: `/api/` (Swagger/OpenAPI)
- **Panel Admin**: `/admin/`

---

## 📄 Licencia

Este proyecto es software propietario de CCTi.

---

**Desarrollado con ❤️ usando Django + Mapbox**
