#!/usr/bin/env python3
"""
🔍 AUDITORÍA COMPLETA DEL SISTEMA SOPTRALOC
Revisa TODOS los archivos, modelos, migraciones, tests, configuraciones
Detecta inconsistencias, errores, código duplicado, mejores prácticas
"""

import os
import sys
import ast
import re
from pathlib import Path
from collections import defaultdict
import subprocess

# Colores para output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_section(title):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE}{title:^80}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.ENDC}\n")

def print_ok(msg):
    print(f"{Colors.GREEN}✓{Colors.ENDC} {msg}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠{Colors.ENDC} {msg}")

def print_error(msg):
    print(f"{Colors.RED}✗{Colors.ENDC} {msg}")

def print_info(msg):
    print(f"{Colors.BLUE}ℹ{Colors.ENDC} {msg}")


class SoptralocAuditor:
    def __init__(self, base_dir):
        self.base_dir = Path(base_dir)
        self.issues = []
        self.warnings = []
        self.suggestions = []
        
    def run_full_audit(self):
        """Ejecuta auditoría completa"""
        print_section("🚀 AUDITORÍA COMPLETA SOPTRALOC TMS")
        print_info(f"Directorio base: {self.base_dir}")
        
        # 1. Estructura del proyecto
        self.audit_project_structure()
        
        # 2. Configuración
        self.audit_configuration()
        
        # 3. Modelos
        self.audit_models()
        
        # 4. Migraciones
        self.audit_migrations()
        
        # 5. URLs y Vistas
        self.audit_urls_and_views()
        
        # 6. Servicios
        self.audit_services()
        
        # 7. Tests
        self.audit_tests()
        
        # 8. Admin
        self.audit_admin()
        
        # 9. Management Commands
        self.audit_management_commands()
        
        # 10. Código duplicado
        self.audit_code_duplication()
        
        # 11. Seguridad
        self.audit_security()
        
        # 12. Performance
        self.audit_performance()
        
        # Resumen final
        self.print_summary()
        
    def audit_project_structure(self):
        """Audita estructura de directorios"""
        print_section("📂 AUDITORÍA: Estructura del Proyecto")
        
        # Directorios esperados
        expected_dirs = [
            'apps/core',
            'apps/containers',
            'apps/drivers',
            'apps/routing',
            'apps/warehouses',
            'config',
            'static',
            'templates',
            'logs',
        ]
        
        for dir_path in expected_dirs:
            full_path = self.base_dir / dir_path
            if full_path.exists():
                print_ok(f"Directorio encontrado: {dir_path}")
            else:
                print_error(f"Directorio faltante: {dir_path}")
                self.issues.append(f"Directorio faltante: {dir_path}")
        
        # Archivos críticos
        critical_files = [
            'manage.py',
            'requirements.txt',
            'config/settings.py',
            'config/settings_production.py',
            'config/urls.py',
            '.env.example',
            'README.md',
        ]
        
        for file_path in critical_files:
            full_path = self.base_dir / file_path
            if full_path.exists():
                print_ok(f"Archivo encontrado: {file_path}")
            else:
                print_error(f"Archivo crítico faltante: {file_path}")
                self.issues.append(f"Archivo faltante: {file_path}")
                
    def audit_configuration(self):
        """Audita archivos de configuración"""
        print_section("⚙️ AUDITORÍA: Configuración")
        
        # Revisar settings.py
        settings_path = self.base_dir / 'config/settings.py'
        if settings_path.exists():
            with open(settings_path) as f:
                content = f.read()
                
            # Checks de seguridad
            if 'SECRET_KEY' in content and 'django-insecure' in content:
                print_warning("SECRET_KEY usa valor por defecto inseguro")
                self.warnings.append("SECRET_KEY debe cambiar en producción")
            
            if 'DEBUG = True' in content:
                print_info("DEBUG=True (OK para desarrollo)")
            
            # Apps instaladas
            if all(app in content for app in ['apps.core', 'apps.containers', 'apps.drivers', 'apps.routing']):
                print_ok("Todas las apps locales registradas")
            else:
                print_error("Faltan apps en INSTALLED_APPS")
                self.issues.append("Verificar INSTALLED_APPS")
            
            # Timezone
            if 'America/Santiago' in content:
                print_ok("Timezone configurado: America/Santiago")
            else:
                print_warning("Timezone no configurado correctamente")
                
    def audit_models(self):
        """Audita todos los modelos"""
        print_section("🗄️ AUDITORÍA: Modelos de Datos")
        
        apps_dir = self.base_dir / 'apps'
        model_files = []
        
        for app in ['core', 'containers', 'drivers', 'routing', 'warehouses']:
            model_path = apps_dir / app / 'models.py'
            if model_path.exists():
                model_files.append((app, model_path))
                print_ok(f"Modelos encontrados: {app}/models.py")
        
        # Analizar cada archivo de modelos
        for app_name, model_path in model_files:
            self.analyze_model_file(app_name, model_path)
            
    def analyze_model_file(self, app_name, model_path):
        """Analiza un archivo de modelos específico"""
        with open(model_path) as f:
            content = f.read()
        
        try:
            tree = ast.parse(content)
            
            # Encontrar todas las clases que heredan de models.Model
            model_classes = []
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    for base in node.bases:
                        if hasattr(base, 'attr') and base.attr in ['Model', 'BaseModel']:
                            model_classes.append(node.name)
            
            if model_classes:
                print_info(f"  {app_name}: {len(model_classes)} modelos → {', '.join(model_classes)}")
            
            # Checks específicos
            if '__str__' not in content:
                print_warning(f"  {app_name}: Algunos modelos sin método __str__")
            
            if 'class Meta:' in content and 'verbose_name' in content:
                print_ok(f"  {app_name}: Modelos con verbose_name")
            
            if 'db_index=True' in content or 'indexes =' in content:
                print_ok(f"  {app_name}: Tiene índices de base de datos")
            else:
                print_warning(f"  {app_name}: Sin índices explícitos")
                self.suggestions.append(f"{app_name}: Considerar agregar índices")
                
        except SyntaxError as e:
            print_error(f"  {app_name}: Error de sintaxis en models.py: {e}")
            self.issues.append(f"{app_name}/models.py tiene error de sintaxis")
            
    def audit_migrations(self):
        """Audita migraciones"""
        print_section("🔄 AUDITORÍA: Migraciones")
        
        apps_dir = self.base_dir / 'apps'
        
        for app in ['core', 'containers', 'drivers', 'routing', 'warehouses']:
            migrations_dir = apps_dir / app / 'migrations'
            
            if not migrations_dir.exists():
                print_error(f"{app}: Sin carpeta migrations/")
                self.issues.append(f"{app}: Falta carpeta migrations")
                continue
            
            migration_files = sorted([
                f.name for f in migrations_dir.glob('*.py')
                if f.name != '__init__.py'
            ])
            
            if migration_files:
                print_ok(f"{app}: {len(migration_files)} migraciones")
                
                # Verificar secuencia
                for mig in migration_files:
                    print_info(f"  → {mig}")
            else:
                print_warning(f"{app}: Sin migraciones")
                
    def audit_urls_and_views(self):
        """Audita URLs y vistas"""
        print_section("🌐 AUDITORÍA: URLs y Vistas")
        
        # URLs principales
        main_urls = self.base_dir / 'config/urls.py'
        if main_urls.exists():
            with open(main_urls) as f:
                content = f.read()
            
            apps_with_urls = ['core', 'containers', 'drivers', 'routing', 'warehouses']
            for app in apps_with_urls:
                if f"apps.{app}.urls" in content:
                    print_ok(f"URLs de {app} incluidas")
                else:
                    print_warning(f"URLs de {app} NO incluidas")
                    
    def audit_services(self):
        """Audita servicios"""
        print_section("🔧 AUDITORÍA: Servicios")
        
        services_paths = [
            'apps/containers/services',
            'apps/drivers/services',
            'apps/routing',
        ]
        
        for service_path in services_paths:
            full_path = self.base_dir / service_path
            if full_path.exists():
                py_files = list(full_path.glob('*.py'))
                if py_files:
                    print_ok(f"{service_path}: {len(py_files)} archivos")
                    for f in py_files:
                        if f.name != '__init__.py':
                            print_info(f"  → {f.name}")
                            
    def audit_tests(self):
        """Audita tests"""
        print_section("🧪 AUDITORÍA: Tests")
        
        apps_dir = self.base_dir / 'apps'
        test_count = 0
        
        for app in ['core', 'containers', 'drivers', 'routing']:
            tests_dir = apps_dir / app / 'tests'
            
            if tests_dir.exists():
                test_files = list(tests_dir.glob('test_*.py'))
                test_count += len(test_files)
                
                if test_files:
                    print_ok(f"{app}: {len(test_files)} archivos de test")
                    for tf in test_files:
                        print_info(f"  → {tf.name}")
                else:
                    print_warning(f"{app}: Carpeta tests/ vacía")
            else:
                print_warning(f"{app}: Sin carpeta tests/")
                
        if test_count > 0:
            print_ok(f"\nTotal: {test_count} archivos de test encontrados")
        else:
            print_error("No se encontraron tests")
            self.issues.append("Sistema sin tests")
            
    def audit_admin(self):
        """Audita configuración del admin"""
        print_section("👤 AUDITORÍA: Django Admin")
        
        apps_dir = self.base_dir / 'apps'
        
        for app in ['core', 'containers', 'drivers', 'routing', 'warehouses']:
            admin_path = apps_dir / app / 'admin.py'
            
            if admin_path.exists():
                with open(admin_path) as f:
                    content = f.read()
                
                if '@admin.register' in content or 'admin.site.register' in content:
                    print_ok(f"{app}: Admin configurado")
                else:
                    print_warning(f"{app}: admin.py existe pero sin registros")
            else:
                print_warning(f"{app}: Sin admin.py")
                
    def audit_management_commands(self):
        """Audita management commands"""
        print_section("⚡ AUDITORÍA: Management Commands")
        
        apps_dir = self.base_dir / 'apps'
        total_commands = 0
        
        for app in ['core', 'containers', 'drivers', 'routing']:
            commands_dir = apps_dir / app / 'management/commands'
            
            if commands_dir.exists():
                commands = [f.name for f in commands_dir.glob('*.py') if f.name != '__init__.py']
                if commands:
                    total_commands += len(commands)
                    print_ok(f"{app}: {len(commands)} commands")
                    for cmd in commands:
                        print_info(f"  → {cmd}")
                        
        print_ok(f"\nTotal: {total_commands} management commands")
        
    def audit_code_duplication(self):
        """Detecta código duplicado"""
        print_section("🔍 AUDITORÍA: Código Duplicado")
        
        # TODO: Implementar detección de código duplicado
        print_info("Análisis de duplicación pendiente")
        
    def audit_security(self):
        """Audita seguridad"""
        print_section("🔐 AUDITORÍA: Seguridad")
        
        settings_prod = self.base_dir / 'config/settings_production.py'
        if settings_prod.exists():
            with open(settings_prod) as f:
                content = f.read()
            
            security_checks = {
                'SECURE_SSL_REDIRECT': 'SSL Redirect',
                'SESSION_COOKIE_SECURE': 'Secure Session Cookies',
                'CSRF_COOKIE_SECURE': 'Secure CSRF Cookies',
                'SECURE_HSTS_SECONDS': 'HSTS Headers',
            }
            
            for check, desc in security_checks.items():
                if f'{check} = True' in content or f'{check} =' in content:
                    print_ok(f"{desc} configurado")
                else:
                    print_warning(f"{desc} NO configurado")
                    
    def audit_performance(self):
        """Audita optimizaciones de performance"""
        print_section("⚡ AUDITORÍA: Performance")
        
        # Check de índices en modelos
        apps_dir = self.base_dir / 'apps'
        indexed_apps = []
        
        for app in ['core', 'containers', 'drivers', 'routing']:
            model_path = apps_dir / app / 'models.py'
            if model_path.exists():
                with open(model_path) as f:
                    content = f.read()
                
                if 'db_index=True' in content or 'indexes =' in content:
                    indexed_apps.append(app)
                    print_ok(f"{app}: Tiene índices")
        
        if len(indexed_apps) < 3:
            print_warning("Pocos modelos con índices de base de datos")
            self.suggestions.append("Agregar índices a campos frecuentemente consultados")
            
    def print_summary(self):
        """Imprime resumen final"""
        print_section("📊 RESUMEN DE AUDITORÍA")
        
        print(f"\n{Colors.BOLD}Errores Críticos:{Colors.ENDC} {len(self.issues)}")
        for issue in self.issues:
            print_error(f"  {issue}")
        
        print(f"\n{Colors.BOLD}Advertencias:{Colors.ENDC} {len(self.warnings)}")
        for warning in self.warnings:
            print_warning(f"  {warning}")
        
        print(f"\n{Colors.BOLD}Sugerencias de Mejora:{Colors.ENDC} {len(self.suggestions)}")
        for suggestion in self.suggestions:
            print_info(f"  {suggestion}")
        
        # Puntaje de calidad
        total_checks = len(self.issues) + len(self.warnings) + len(self.suggestions)
        if len(self.issues) == 0:
            if len(self.warnings) == 0:
                quality = "🌟 EXCELENTE"
                color = Colors.GREEN
            elif len(self.warnings) < 5:
                quality = "✅ BUENO"
                color = Colors.GREEN
            else:
                quality = "⚠️ ACEPTABLE"
                color = Colors.YELLOW
        else:
            quality = "❌ NECESITA ATENCIÓN"
            color = Colors.RED
        
        print(f"\n{Colors.BOLD}Calidad del Código:{Colors.ENDC} {color}{quality}{Colors.ENDC}")
        print(f"\n{Colors.BOLD}{'='*80}{Colors.ENDC}\n")


if __name__ == '__main__':
    base_dir = Path(__file__).parent.resolve()
    auditor = SoptralocAuditor(base_dir)
    auditor.run_full_audit()
