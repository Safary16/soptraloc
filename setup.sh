#!/bin/bash
# Script de configuración para desarrollo local de SOPTRALOC

echo "🚀 Configurando SOPTRALOC para desarrollo local..."

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Función para imprimir con colores
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Verificar Python
if command -v python3 &> /dev/null; then
    print_status "Python 3 encontrado: $(python3 --version)"
else
    print_error "Python 3 no está instalado"
    exit 1
fi

# Crear entorno virtual si no existe
if [ ! -d "venv" ]; then
    print_status "Creando entorno virtual..."
    python3 -m venv venv
else
    print_warning "El entorno virtual ya existe"
fi

# Activar entorno virtual
print_status "Activando entorno virtual..."
source venv/bin/activate

# Actualizar pip
print_status "Actualizando pip..."
pip install --upgrade pip

# Instalar dependencias
print_status "Instalando dependencias..."
pip install -r requirements.txt

# Copiar archivo .env si no existe
if [ ! -f ".env" ]; then
    print_status "Creando archivo .env..."
    cp .env.example .env
else
    print_warning "El archivo .env ya existe"
fi

# Cambiar al directorio del proyecto Django
cd soptraloc_system

# Ejecutar migraciones
print_status "Ejecutando migraciones..."
python manage.py migrate

# Crear superusuario si no existe
print_status "Verificando superusuario..."
echo "from django.contrib.auth.models import User; User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@soptraloc.local', 'admin123')" | python manage.py shell

# Cargar datos de ejemplo
print_status "Cargando datos de ejemplo..."
python manage.py load_sample_data

# Crear directorio static si no existe
if [ ! -d "static" ]; then
    mkdir -p static
    print_status "Directorio static creado"
fi

print_status "¡Configuración completada!"
echo ""
echo "🌟 SOPTRALOC está listo para desarrollo"
echo "📋 Para iniciar el servidor:"
echo "   cd soptraloc_system"
echo "   source ../venv/bin/activate"
echo "   python manage.py runserver"
echo ""
echo "🌐 URLs importantes:"
echo "   • API: http://localhost:8000/"
echo "   • Admin: http://localhost:8000/admin/"
echo "   • Swagger: http://localhost:8000/swagger/"
echo "   • Dashboard: http://localhost:8000/api/v1/core/dashboard/"
echo ""
echo "👤 Credenciales por defecto:"
echo "   • Admin: admin / admin123"
echo "   • Conductores: [usuario] / conductor123"
echo ""
print_status "¡Happy coding! 🚀"