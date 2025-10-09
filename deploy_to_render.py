#!/usr/bin/env python3
"""
Script de Deploy Automatizado a Render
=======================================
Este script configura automáticamente todos los servicios necesarios en Render.

Requisitos:
1. Tener una cuenta en Render.com
2. Generar un API Key desde: https://dashboard.render.com/u/settings#api-keys
3. Configurar la variable de entorno RENDER_API_KEY

Uso:
    export RENDER_API_KEY="rnd_xxx..."
    python deploy_to_render.py
"""

import os
import sys
import json
import time
import secrets
import requests
from typing import Dict, List, Optional

# Colores para output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text: str):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(80)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}\n")

def print_success(text: str):
    print(f"{Colors.OKGREEN}✅ {text}{Colors.ENDC}")

def print_error(text: str):
    print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")

def print_warning(text: str):
    print(f"{Colors.WARNING}⚠️  {text}{Colors.ENDC}")

def print_info(text: str):
    print(f"{Colors.OKCYAN}ℹ️  {text}{Colors.ENDC}")

class RenderDeployer:
    """Clase para automatizar el deploy en Render"""
    
    BASE_URL = "https://api.render.com/v1"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        self.owner_id = None
        self.services = {}
        
    def test_connection(self) -> bool:
        """Verificar que el API key es válido"""
        print_info("Verificando conexión con Render API...")
        try:
            response = requests.get(
                f"{self.BASE_URL}/owners",
                headers=self.headers,
                timeout=10
            )
            if response.status_code == 200:
                owners = response.json()
                if owners:
                    self.owner_id = owners[0]['owner']['id']
                    print_success(f"Conectado exitosamente. Owner ID: {self.owner_id}")
                    return True
            print_error(f"Error al conectar: {response.status_code} - {response.text}")
            return False
        except Exception as e:
            print_error(f"Error de conexión: {str(e)}")
            return False
    
    def get_services(self) -> List[Dict]:
        """Obtener lista de servicios existentes"""
        try:
            response = requests.get(
                f"{self.BASE_URL}/services",
                headers=self.headers,
                params={"limit": 100},
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            print_error(f"Error al obtener servicios: {str(e)}")
            return []
    
    def create_postgres(self, name: str = "soptraloc-db") -> Optional[str]:
        """Crear base de datos PostgreSQL"""
        print_info(f"Creando PostgreSQL: {name}...")
        
        payload = {
            "name": name,
            "plan": "starter",  # Plan gratuito
            "databaseName": "soptraloc",
            "databaseUser": "soptraloc_user",
            "region": "oregon",
            "ipAllowList": []  # Permitir todas las IPs
        }
        
        try:
            response = requests.post(
                f"{self.BASE_URL}/postgres",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                db = response.json()
                db_id = db.get('postgres', {}).get('id')
                print_success(f"PostgreSQL creado: {name} (ID: {db_id})")
                print_info("Esperando que la BD esté disponible (puede tardar 2-3 min)...")
                time.sleep(10)  # Esperar un poco para que se inicialice
                return db_id
            else:
                print_warning(f"PostgreSQL ya existe o error: {response.status_code}")
                # Intentar buscar la BD existente
                existing = self._find_service_by_name(name)
                if existing:
                    print_info(f"Usando PostgreSQL existente: {existing['id']}")
                    return existing['id']
                return None
        except Exception as e:
            print_error(f"Error al crear PostgreSQL: {str(e)}")
            return None
    
    def create_redis(self, name: str = "soptraloc-redis") -> Optional[str]:
        """Crear servicio Redis"""
        print_info(f"Creando Redis: {name}...")
        
        payload = {
            "name": name,
            "plan": "starter",  # Plan gratuito (25MB)
            "maxmemoryPolicy": "allkeys-lru",
            "region": "oregon"
        }
        
        try:
            response = requests.post(
                f"{self.BASE_URL}/redis",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                redis = response.json()
                redis_id = redis.get('redis', {}).get('id')
                print_success(f"Redis creado: {name} (ID: {redis_id})")
                time.sleep(5)
                return redis_id
            else:
                print_warning(f"Redis ya existe o error: {response.status_code}")
                existing = self._find_service_by_name(name)
                if existing:
                    print_info(f"Usando Redis existente: {existing['id']}")
                    return existing['id']
                return None
        except Exception as e:
            print_error(f"Error al crear Redis: {str(e)}")
            return None
    
    def _find_service_by_name(self, name: str) -> Optional[Dict]:
        """Buscar un servicio por nombre"""
        services = self.get_services()
        for service in services:
            if service.get('service', {}).get('name') == name:
                return service['service']
        return None
    
    def create_web_service(
        self, 
        name: str = "soptraloc-web",
        repo_url: str = "https://github.com/Safary16/soptraloc",
        branch: str = "main",
        env_vars: Dict[str, str] = None
    ) -> Optional[str]:
        """Crear Web Service (Django)"""
        print_info(f"Creando Web Service: {name}...")
        
        if env_vars is None:
            env_vars = {}
        
        # Convertir env_vars a formato de Render
        env_vars_list = [
            {"key": key, "value": value}
            for key, value in env_vars.items()
        ]
        
        payload = {
            "type": "web_service",
            "name": name,
            "repo": repo_url,
            "branch": branch,
            "buildCommand": "pip install -r requirements.txt && python soptraloc_system/manage.py collectstatic --noinput && python soptraloc_system/manage.py migrate",
            "startCommand": "cd soptraloc_system && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 3 --timeout 120",
            "runtime": "python3",
            "plan": "starter",  # Plan gratuito
            "region": "oregon",
            "envVars": env_vars_list,
            "autoDeploy": "yes"
        }
        
        try:
            response = requests.post(
                f"{self.BASE_URL}/services",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                service = response.json()
                service_id = service.get('service', {}).get('id')
                service_url = service.get('service', {}).get('serviceDetails', {}).get('url')
                print_success(f"Web Service creado: {name} (ID: {service_id})")
                if service_url:
                    print_success(f"URL: https://{service_url}")
                self.services['web'] = service_id
                return service_id
            else:
                print_error(f"Error al crear Web Service: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print_error(f"Error al crear Web Service: {str(e)}")
            return None
    
    def create_background_worker(
        self,
        name: str,
        command: str,
        repo_url: str = "https://github.com/Safary16/soptraloc",
        branch: str = "main",
        env_vars: Dict[str, str] = None
    ) -> Optional[str]:
        """Crear Background Worker (Celery)"""
        print_info(f"Creando Background Worker: {name}...")
        
        if env_vars is None:
            env_vars = {}
        
        env_vars_list = [
            {"key": key, "value": value}
            for key, value in env_vars.items()
        ]
        
        payload = {
            "type": "background_worker",
            "name": name,
            "repo": repo_url,
            "branch": branch,
            "buildCommand": "pip install -r requirements.txt",
            "startCommand": command,
            "runtime": "python3",
            "plan": "starter",
            "region": "oregon",
            "envVars": env_vars_list,
            "autoDeploy": "yes"
        }
        
        try:
            response = requests.post(
                f"{self.BASE_URL}/services",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                service = response.json()
                service_id = service.get('service', {}).get('id')
                print_success(f"Background Worker creado: {name} (ID: {service_id})")
                return service_id
            else:
                print_error(f"Error al crear Background Worker: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print_error(f"Error al crear Background Worker: {str(e)}")
            return None
    
    def get_postgres_connection_string(self, postgres_id: str) -> Optional[str]:
        """Obtener string de conexión de PostgreSQL"""
        try:
            response = requests.get(
                f"{self.BASE_URL}/postgres/{postgres_id}",
                headers=self.headers,
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                # Construir connection string
                return data.get('postgres', {}).get('connectionString')
            return None
        except Exception as e:
            print_error(f"Error al obtener connection string: {str(e)}")
            return None
    
    def get_redis_connection_string(self, redis_id: str) -> Optional[str]:
        """Obtener string de conexión de Redis"""
        try:
            response = requests.get(
                f"{self.BASE_URL}/redis/{redis_id}",
                headers=self.headers,
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                return data.get('redis', {}).get('connectionString')
            return None
        except Exception as e:
            print_error(f"Error al obtener Redis connection string: {str(e)}")
            return None


def generate_secret_key() -> str:
    """Generar Django SECRET_KEY segura"""
    return secrets.token_urlsafe(50)


def main():
    """Función principal de deploy"""
    
    print_header("🚀 SOPTRALOC TMS - Deploy Automatizado a Render")
    
    # 1. Verificar API Key
    api_key = os.getenv('RENDER_API_KEY')
    if not api_key:
        print_error("RENDER_API_KEY no configurada")
        print_info("\nPasos para obtener tu API Key:")
        print_info("1. Ve a: https://dashboard.render.com/u/settings#api-keys")
        print_info("2. Haz clic en 'Create API Key'")
        print_info("3. Copia la key generada")
        print_info("4. Ejecuta: export RENDER_API_KEY='rnd_tu_key_aqui'")
        print_info("5. Vuelve a ejecutar este script\n")
        sys.exit(1)
    
    # 2. Configuración
    REPO_URL = "https://github.com/Safary16/soptraloc"
    BRANCH = "main"
    MAPBOX_API_KEY = "pk.eyJ1Ijoic2FmYXJ5MTYiLCJhIjoiY200cTN6MGY5MGlqMDJpb2o5a3RvYTh2dSJ9.B0A7Nw0nDCXzjUBBN0i4aQ"
    SECRET_KEY = generate_secret_key()
    
    print_info(f"Repositorio: {REPO_URL}")
    print_info(f"Branch: {BRANCH}")
    print_info(f"SECRET_KEY generada: {SECRET_KEY[:20]}...")
    
    # 3. Inicializar deployer
    deployer = RenderDeployer(api_key)
    
    if not deployer.test_connection():
        print_error("No se pudo conectar a Render API")
        sys.exit(1)
    
    # 4. Crear PostgreSQL
    print_header("📦 Creando Servicios de Base de Datos")
    postgres_id = deployer.create_postgres("soptraloc-db")
    if not postgres_id:
        print_error("No se pudo crear PostgreSQL")
        sys.exit(1)
    
    # 5. Crear Redis
    redis_id = deployer.create_redis("soptraloc-redis")
    if not redis_id:
        print_error("No se pudo crear Redis")
        sys.exit(1)
    
    # 6. Obtener connection strings
    print_header("🔗 Obteniendo Strings de Conexión")
    print_info("Esperando que los servicios estén disponibles...")
    time.sleep(15)  # Esperar a que los servicios se inicialicen
    
    database_url = deployer.get_postgres_connection_string(postgres_id)
    redis_url = deployer.get_redis_connection_string(redis_id)
    
    if not database_url:
        print_warning("No se pudo obtener DATABASE_URL automáticamente")
        database_url = f"postgresql://user:pass@host:5432/soptraloc"
    
    if not redis_url:
        print_warning("No se pudo obtener REDIS_URL automáticamente")
        redis_url = f"redis://host:6379"
    
    print_success(f"DATABASE_URL: {database_url[:50]}...")
    print_success(f"REDIS_URL: {redis_url[:50]}...")
    
    # 7. Variables de entorno comunes
    env_vars = {
        "SECRET_KEY": SECRET_KEY,
        "DEBUG": "False",
        "MAPBOX_API_KEY": MAPBOX_API_KEY,
        "DATABASE_URL": database_url,
        "REDIS_URL": redis_url,
        "CELERY_BROKER_URL": redis_url,
        "CELERY_RESULT_BACKEND": redis_url,
        "TIME_ZONE": "America/Santiago",
        "PYTHONUNBUFFERED": "1",
        "DJANGO_SETTINGS_MODULE": "config.settings"
    }
    
    # 8. Crear Web Service
    print_header("🌐 Creando Web Service (Django)")
    web_id = deployer.create_web_service(
        name="soptraloc-web",
        repo_url=REPO_URL,
        branch=BRANCH,
        env_vars=env_vars
    )
    
    if not web_id:
        print_error("No se pudo crear Web Service")
        sys.exit(1)
    
    # Esperar a que el web service se cree para obtener su URL
    time.sleep(5)
    
    # 9. Crear Celery Worker
    print_header("⚙️  Creando Celery Worker")
    worker_id = deployer.create_background_worker(
        name="soptraloc-celery-worker",
        command="cd soptraloc_system && celery -A config worker -l info --concurrency=2",
        repo_url=REPO_URL,
        branch=BRANCH,
        env_vars=env_vars
    )
    
    if worker_id:
        deployer.services['worker'] = worker_id
    
    # 10. Crear Celery Beat
    print_header("⏰ Creando Celery Beat")
    beat_id = deployer.create_background_worker(
        name="soptraloc-celery-beat",
        command="cd soptraloc_system && celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler",
        repo_url=REPO_URL,
        branch=BRANCH,
        env_vars=env_vars
    )
    
    if beat_id:
        deployer.services['beat'] = beat_id
    
    # 11. Resumen final
    print_header("✅ DEPLOY COMPLETADO")
    
    print_success("Servicios creados exitosamente:")
    print(f"  🗄️  PostgreSQL: soptraloc-db")
    print(f"  💾 Redis: soptraloc-redis")
    print(f"  🌐 Web Service: soptraloc-web")
    if worker_id:
        print(f"  ⚙️  Celery Worker: soptraloc-celery-worker")
    if beat_id:
        print(f"  ⏰ Celery Beat: soptraloc-celery-beat")
    
    print("\n" + "="*80)
    print_info("🔍 PRÓXIMOS PASOS:")
    print("="*80)
    print("\n1. Ve a tu Dashboard de Render:")
    print("   https://dashboard.render.com/")
    
    print("\n2. Espera a que los servicios terminen de construirse (~5-10 min)")
    print("   - Verifica que todos los servicios estén en estado 'Live'")
    
    print("\n3. Una vez que el Web Service esté 'Live', abre el Shell:")
    print("   - Ve a soptraloc-web → Shell")
    print("   - Ejecuta: cd soptraloc_system && python manage.py createsuperuser")
    
    print("\n4. (Opcional) Carga datos de prueba:")
    print("   cd soptraloc_system && python manage.py quick_test_data")
    
    print("\n5. Verifica el sistema:")
    print("   cd soptraloc_system && python test_system.py")
    
    print("\n6. Accede a tu aplicación:")
    print("   Busca la URL en el Dashboard (soptraloc-web → URL)")
    print("   Ejemplo: https://soptraloc-web.onrender.com")
    
    print("\n7. Ingresa al admin:")
    print("   https://tu-url.onrender.com/admin/")
    
    print("\n" + "="*80)
    print_success("🎉 ¡Deploy automatizado completado!")
    print_info("📚 Para más información, consulta RENDER_DEPLOYMENT_CHECKLIST.md")
    print("="*80 + "\n")
    
    # Guardar configuración
    config = {
        "deployment_date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "services": {
            "postgres_id": postgres_id,
            "redis_id": redis_id,
            "web_id": web_id,
            "worker_id": worker_id,
            "beat_id": beat_id
        },
        "env_vars": {
            "SECRET_KEY": SECRET_KEY,
            "MAPBOX_API_KEY": MAPBOX_API_KEY,
            "DATABASE_URL": database_url[:50] + "...",
            "REDIS_URL": redis_url[:50] + "..."
        }
    }
    
    with open('render_deployment_config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    print_success("Configuración guardada en: render_deployment_config.json")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_error("\n\nDeploy cancelado por el usuario")
        sys.exit(1)
    except Exception as e:
        print_error(f"\n\nError inesperado: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
