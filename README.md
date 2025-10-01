# 🚀 SoptraLoc - Sistema TMS Inteligente con Machine Learning

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/Safary16/soptraloc)
[![Django 5.2.6](https://img.shields.io/badge/Django-5.2.6-green.svg)](https://www.djangoproject.com/)
[![Python 3.12+](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Ready-blue.svg)](https://www.postgresql.org/)

## ✨ **Sistema Completo de Gestión de Transporte (TMS)**

Sistema profesional de gestión logística con **Machine Learning**, **alertas en tiempo real** y **dashboard estilo torre de control aéreo**.

### **🎯 Lo que incluye:**
- ⏰ **Reloj en tiempo real** estilo torre de control aéreo
- 🚨 **Sistema de alertas urgentes** con verificación automática cada 30 segundos
- 🗺️ **35 rutas Chile pre-configuradas** (puertos, CDs, bodegas)
- 🤖 **Machine Learning** para predicción de tiempos (60% reciente / 40% histórico)
- 📊 **Dashboard inteligente** con ordenamiento por urgencia
- 🚛 **Sistema de conductores** con asignación inteligente
- 📦 **Gestión completa de contenedores** con estados y movimientos
- 🔔 **Sistema de proximidad** con alertas automáticas
- 🔌 **API REST completa** con endpoints documentados
- 👨‍💼 **Panel de administración** profesional con badges ML

---

## 🚀 Características Principales

### ⏰ Reloj en Tiempo Real - Estilo Torre de Control
- **Diseño profesional**: Colores verde fosforescente sobre azul gradiente
- **Actualización**: Cada 1 segundo con precisión milimétrica
- **Formato**: HH:MM:SS + DÍA DD MES YYYY
- **Badge urgente**: Contador animado de contenedores críticos
- **Modal detallado**: Lista completa de contenedores urgentes con niveles

### 🗺️ Sistema de Routing con Machine Learning
- **35 rutas Chile**: Puertos (San Antonio, Valparaíso, San Vicente, Lirquén, Coronel)
- **70 operaciones**: Tiempos estándar para cada tipo de operación
- **Algoritmo ML**: Promedio ponderado (60% datos recientes + 40% históricos)
- **Predicción inteligente**: Tiempos estimados basados en datos reales
- **Sistema de confianza**: Badges visuales (Alta/Media/Baja)
- **Aprendizaje continuo**: Actualización diaria con datos reales

### � Gestión Avanzada de Contenedores
- **Múltiples estados**: PROGRAMADO, EN_PROCESO, EN_TRANSITO, LIBERADO, DESCARGADO, EN_SECUENCIA
- **Trazabilidad completa**: Histórico de todos los movimientos
- **Alertas de proximidad**: Contenedores urgentes < 2 horas
- **Asignación rápida**: Integración con sistema de conductores
- **Importación Excel**: Carga masiva de manifiestos y liberaciones

### � Sistema de Alertas Inteligentes
- **Verificación automática**: Cada 30 segundos verifica contenedores urgentes
- **3 niveles de urgencia**: CRÍTICO (< 1h), ALTO (< 2h), MEDIO (< 4h)
- **Notificaciones visuales**: Badge pulsante en navbar
- **Modal detallado**: Click para ver lista completa con información
- **API endpoint**: `/api/v1/containers/urgent/` para integraciones

### 📊 Dashboard Ejecutivo
- **Estadísticas en tiempo real**: Total activos, por estado, disponibilidad
- **Vista prioritaria**: Contenedores urgentes destacados y ordenados
- **Integración ML**: Predicciones de tiempos en ruta
- **Alertas pendientes**: Asignaciones sin completar
- **Responsive design**: Adaptable a móviles y tablets

## 🛠️ Tecnologías Utilizadas

- **Backend**: Django 5.2.6 + Django REST Framework
- **Base de Datos**: SQLite (desarrollo) / PostgreSQL (producción)
- **API Documentation**: DRF-YASG (Swagger/OpenAPI)
- **Autenticación**: JWT (Simple JWT)
- **Frontend**: API REST (listo para integración con cualquier frontend)

## 📋 Instalación y Configuración

### Prerrequisitos
- Python 3.12+
- Git
- Entorno virtual (recomendado)

### 1. Clonar el Repositorio
```bash
git clone https://github.com/Safary16/soptraloc.git
cd soptraloc
```

### 2. Crear Entorno Virtual
```bash
python3 -m venv venv
source venv/bin/activate  # En Linux/Mac
# venv\\Scripts\\activate     # En Windows
```

### 3. Instalar Dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar Variables de Entorno
```bash
cp .env.example .env
# Editar .env con tus configuraciones
```

### 5. Ejecutar Migraciones
```bash
cd soptraloc_system
python manage.py migrate
```

### 6. Cargar Datos Iniciales (Chile)
```bash
# Cargar 35 rutas y 70 operaciones para Chile
python manage.py load_initial_times
```

### 7. Crear Superusuario
```bash
python manage.py createsuperuser
```

### 8. Iniciar Servidor
```bash
python manage.py runserver
```

El sistema estará disponible en:
- **Home**: http://localhost:8000/
- **Dashboard**: http://localhost:8000/dashboard/
- **Panel Admin**: http://localhost:8000/admin/
- **API Containers**: http://localhost:8000/api/v1/containers/
- **API Routing**: http://localhost:8000/api/v1/routing/

---

## 🚀 Despliegue en Producción

### Deploy en Render.com (Recomendado)

**Auto-deploy configurado desde GitHub main branch**

1. Crear cuenta en [Render.com](https://render.com)
2. Conectar repositorio GitHub
3. Configurar variables de entorno:
   ```
   SECRET_KEY=tu-secret-key-segura
   DEBUG=False
   ALLOWED_HOSTS=tu-app.onrender.com
   DATABASE_URL=postgres://... (auto-generado)
   ```
4. Deploy automático al hacer push a main
5. Render ejecuta automáticamente:
   - `pip install -r requirements.txt`
   - `python manage.py collectstatic --noinput`
   - `python manage.py migrate`
   - `gunicorn config.wsgi:application`

**Archivo `render.yaml` incluido con configuración completa**

### Comandos Post-Deploy
```bash
# Cargar datos iniciales de Chile en producción
python manage.py load_initial_times

# Actualizar predicciones ML diariamente (configurar en cron)
python manage.py update_time_predictions --verbose
```

---

## 📁 Estructura del Proyecto

```
soptraloc/
├── soptraloc_system/           # Proyecto Django principal
│   ├── apps/                   # Aplicaciones modulares
│   │   ├── core/              # Auth, dashboard, funciones base
│   │   ├── containers/        # Gestión completa de contenedores
│   │   ├── drivers/           # Conductores y asignaciones
│   │   ├── vehicles/          # Vehículos y chasis
│   │   ├── routing/           # 🆕 Sistema ML de tiempos
│   │   └── warehouses/        # Almacenes y ubicaciones
│   ├── config/                # Configuración Django
│   │   ├── settings.py        # Settings principal
│   │   └── urls.py            # URL routing
│   ├── templates/             # Templates HTML
│   │   └── base.html          # 🆕 Con reloj ATC
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
