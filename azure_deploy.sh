#!/bin/bash

# Azure App Service - Deploy automatizado para SafaryLoc
# Para usar con Azure Cloud Shell o Azure CLI local

echo "☁️ Preparando deploy de SafaryLoc en Azure..."

# Variables de configuración
RESOURCE_GROUP="SafaryLoc-RG"
APP_SERVICE_PLAN="SafaryLoc-Plan"
WEB_APP_NAME="safary-soptraloc-$(date +%s | tail -c 6)"
LOCATION="eastus"
RUNTIME="PYTHON|3.11"

echo "🔧 Configurando variables:"
echo "  Resource Group: $RESOURCE_GROUP"
echo "  App Name: $WEB_APP_NAME"
echo "  Location: $LOCATION"

# 1. Crear Resource Group
echo "📁 Creando Resource Group..."
az group create --name $RESOURCE_GROUP --location $LOCATION

# 2. Crear App Service Plan (Free tier)
echo "📋 Creando App Service Plan (FREE)..."
az appservice plan create \
  --name $APP_SERVICE_PLAN \
  --resource-group $RESOURCE_GROUP \
  --sku F1 \
  --is-linux

# 3. Crear PostgreSQL Flexible Server (Free tier)
echo "🗄️ Creando base de datos PostgreSQL..."
DB_SERVER_NAME="safary-db-$(date +%s | tail -c 6)"
DB_PASSWORD="SafaryLoc$(date +%s | tail -c 8)!"

az postgres flexible-server create \
  --resource-group $RESOURCE_GROUP \
  --name $DB_SERVER_NAME \
  --location $LOCATION \
  --admin-user safary \
  --admin-password $DB_PASSWORD \
  --sku-name Standard_B1ms \
  --tier Burstable \
  --storage-size 32 \
  --version 14

# 4. Configurar firewall de la base de datos
echo "🔒 Configurando acceso a base de datos..."
az postgres flexible-server firewall-rule create \
  --resource-group $RESOURCE_GROUP \
  --name $DB_SERVER_NAME \
  --rule-name "AllowAzureServices" \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0

# 5. Crear la base de datos
echo "📊 Creando base de datos safarylocdb..."
az postgres flexible-server db create \
  --resource-group $RESOURCE_GROUP \
  --server-name $DB_SERVER_NAME \
  --database-name safarylocdb

# 6. Crear Web App
echo "🌐 Creando Web App..."
az webapp create \
  --resource-group $RESOURCE_GROUP \
  --plan $APP_SERVICE_PLAN \
  --name $WEB_APP_NAME \
  --runtime $RUNTIME \
  --deployment-source-url https://github.com/Safary16/soptraloc \
  --deployment-source-branch main

# 7. Configurar variables de entorno
echo "⚙️ Configurando variables de entorno..."
DATABASE_URL="postgresql://safary:$DB_PASSWORD@$DB_SERVER_NAME.postgres.database.azure.com:5432/safarylocdb"

az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $WEB_APP_NAME \
  --settings \
    DEBUG="False" \
    SECRET_KEY="azure-safary-secret-$(openssl rand -hex 16)" \
    DATABASE_URL="$DATABASE_URL" \
    DJANGO_SETTINGS_MODULE="config.settings_production" \
    PYTHONPATH="/home/site/wwwroot/soptraloc_system" \
    SCM_DO_BUILD_DURING_DEPLOYMENT="true" \
    ENABLE_ORYX_BUILD="true" \
    DISABLE_COLLECTSTATIC="1"

# 8. Configurar startup command
echo "🚀 Configurando comando de inicio..."
az webapp config set \
  --resource-group $RESOURCE_GROUP \
  --name $WEB_APP_NAME \
  --startup-file "cd soptraloc_system && python manage.py migrate && python manage.py collectstatic --noinput && gunicorn --bind=0.0.0.0 --timeout 600 config.wsgi:application"

# 9. Habilitar logs
echo "📋 Habilitando logs..."
az webapp log config \
  --resource-group $RESOURCE_GROUP \
  --name $WEB_APP_NAME \
  --application-logging filesystem \
  --level information

# 10. Obtener URL de la aplicación
WEB_APP_URL=$(az webapp show --resource-group $RESOURCE_GROUP --name $WEB_APP_NAME --query "defaultHostName" --output tsv)

echo ""
echo "🎉 ¡Deploy completado!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🌐 TU APLICACIÓN:"
echo "   URL: https://$WEB_APP_URL"
echo "   Dashboard: https://$WEB_APP_URL/dashboard/"
echo "   Admin: https://$WEB_APP_URL/admin/"
echo ""
echo "🔐 DATOS DE LA BASE DE DATOS:"
echo "   Servidor: $DB_SERVER_NAME.postgres.database.azure.com"
echo "   Usuario: safary"
echo "   Contraseña: $DB_PASSWORD"
echo "   Base de datos: safarylocdb"
echo ""
echo "📱 ACCESO MÓVIL:"
echo "   Desde cualquier dispositivo: https://$WEB_APP_URL"
echo ""
echo "💰 COSTO:"
echo "   App Service: GRATUITO (F1 tier)"
echo "   PostgreSQL: GRATUITO por 12 meses"
echo "   Tráfico: GRATUITO hasta límites estudiantiles"
echo ""
echo "🔧 COMANDOS ÚTILES:"
echo "   Ver logs: az webapp log tail --resource-group $RESOURCE_GROUP --name $WEB_APP_NAME"
echo "   Reiniciar: az webapp restart --resource-group $RESOURCE_GROUP --name $WEB_APP_NAME"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ ¡Tu sistema logístico está en la nube de Microsoft!"

# Guardar información importante
echo "# Azure Deploy Information" > azure-info.txt
echo "Resource Group: $RESOURCE_GROUP" >> azure-info.txt
echo "Web App: $WEB_APP_NAME" >> azure-info.txt
echo "URL: https://$WEB_APP_URL" >> azure-info.txt
echo "Database Server: $DB_SERVER_NAME" >> azure-info.txt
echo "Database Password: $DB_PASSWORD" >> azure-info.txt
echo "" >> azure-info.txt
echo "Credenciales de admin:" >> azure-info.txt
echo "Usuario: admin" >> azure-info.txt
echo "Contraseña: admin123" >> azure-info.txt

echo "📄 Información guardada en: azure-info.txt"