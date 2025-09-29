# 🎨 SafaryLoc - Sistema de Gestión Logística

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/Safary16/soptraloc)

## � **Deploy Instantáneo en Render**

Tu sistema logístico completo listo para la nube en **5 minutos**.

### **✅ Lo que incluye:**
- **692 contenedores** de Walmart ya cargados
- **Dashboard responsive** para móviles y tablets  
- **Sistema de conductores** con asignación inteligente
- **Control de asistencia** diario
- **Seguimiento temporal** de rutas completo
- **API REST** documentada
- **Panel de administración** profesional

## 🚀 Características Principales

### 📦 Gestión de Contenedores
- **Stock en almacenes**: Control de inventario en múltiples ubicaciones
- **Registro de movimientos**: Seguimiento completo de cada contenedor (piso ↔ chasis)
- **Códigos únicos**: Generación automática de códigos para cada movimiento
- **Histórico completo**: Trazabilidad total de cada contenedor

### 📋 Programación y Asignaciones
- **Programación flexible**: Asignación de contenedores a lugares y fechas específicas
- **Gestión de conductores**: Control de disponibilidad y asignaciones
- **Gestión de vehículos**: Seguimiento de chasis y camiones

### 🔔 Alertas Inteligentes
- **Contenedores sin asignación**: Avisos cuando un contenedor no tiene conductor
- **Programaciones pendientes**: Alertas de programaciones sin asignar
- **Notificaciones anticipadas**: Avisos con tiempo suficiente para tomar acción

### ⚡ Optimización Automática
- **Propuesta de asignaciones**: Sugerencias inteligentes basadas en disponibilidad
- **Optimización de rutas**: Mejora de eficiencia en transportes
- **Análisis de capacidad**: Evaluación de recursos disponibles

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

### 6. Crear Superusuario
```bash
python manage.py createsuperuser
```

### 7. Iniciar Servidor
```bash
python manage.py runserver
```

El sistema estará disponible en:
- **API**: http://localhost:8000/
- **Panel Admin**: http://localhost:8000/admin/
- **Documentación API**: http://localhost:8000/swagger/

## 🚀 Despliegue en la Nube (GitHub Student Pack)

El proyecto está configurado para desplegarse en múltiples plataformas gratuitas del GitHub Student Pack:

### Railway
```bash
railway login
railway init
railway up
```

### Render
- Conectar repositorio GitHub
- Configurar variables de entorno
- Deploy automático

### Heroku
```bash
git push heroku main
```

## 📁 Estructura del Proyecto

```
soptraloc/
├── soptraloc_system/           # Proyecto Django principal
│   ├── apps/                   # Aplicaciones modulares
│   │   ├── core/              # Funcionalidades básicas
│   │   ├── containers/        # Gestión de contenedores
│   │   ├── warehouses/        # Gestión de almacenes
│   │   ├── scheduling/        # Programación y asignaciones
│   │   ├── alerts/            # Sistema de alertas
│   │   └── optimization/      # Optimización y IA
│   ├── config/                # Configuración Django
│   └── manage.py              # Script de gestión Django
├── requirements.txt           # Dependencias Python
├── Dockerfile                # Configuración Docker
├── docker-compose.yml        # Orquestación de servicios
└── .github/workflows/        # CI/CD con GitHub Actions
```

## 🔧 API Endpoints Principales

### Core (Entidades Básicas)
- `GET/POST /api/v1/core/companies/` - Empresas/Clientes
- `GET/POST /api/v1/core/drivers/` - Conductores
- `GET/POST /api/v1/core/vehicles/` - Vehículos/Chasis
- `GET/POST /api/v1/core/locations/` - Ubicaciones
- `GET /api/v1/core/dashboard/` - Dashboard principal

### Containers (En desarrollo)
- `GET/POST /api/v1/containers/containers/` - Gestión de contenedores
- `GET /api/v1/containers/containers/{id}/history/` - Histórico de movimientos

### Documentación Completa
- **Swagger UI**: http://localhost:8000/swagger/
- **ReDoc**: http://localhost:8000/redoc/

## 🧪 Testing

```bash
python manage.py test
```

## 📊 Modelos de Datos Implementados

### Entidades Core
- **Company**: Empresas y clientes
- **Driver**: Conductores con disponibilidad
- **Vehicle**: Vehículos/chasis con estado
- **Location**: Ubicaciones geográficas
- **MovementCode**: Códigos únicos para movimientos

### Funcionalidades Avanzadas (En desarrollo)
- **Container**: Contenedores con seguimiento
- **Movement**: Movimientos de contenedores
- **Schedule**: Programaciones de transporte
- **Alert**: Sistema de alertas
- **Optimization**: Reportes y optimizaciones

## 🤝 Contribuir

1. Fork el proyecto
2. Crear rama feature (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add: AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Crear Pull Request

## 📝 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.

## 📞 Contacto

- **Proyecto**: [GitHub Repository](https://github.com/Safary16/soptraloc)
- **Issues**: [GitHub Issues](https://github.com/Safary16/soptraloc/issues)

## 🌟 GitHub Student Pack

Este proyecto aprovecha las herramientas gratuitas del GitHub Student Pack:
- **Railway** - Hosting y despliegue
- **Render** - Alternativa de hosting
- **Heroku** - Plataforma como servicio
- **GitHub Actions** - CI/CD
- **Sentry** - Monitoreo de errores
- **AWS Credits** - Almacenamiento y servicios cloud
