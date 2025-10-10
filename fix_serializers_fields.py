#!/usr/bin/env python
"""
Script para reemplazar fields='__all__' con listas explícitas de campos.
FASE 5: Seguridad en serializers - Evitar exposición de campos sensibles.
"""
import os
import sys
import re
import django

# Configurar Django
sys.path.insert(0, '/workspaces/soptraloc/soptraloc_system')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.apps import apps


def get_model_fields(model):
    """Obtiene todos los campos de un modelo excepto los sensibles."""
    fields = []
    sensitive_fields = ['password', 'token', 'secret', 'key', 'api_key']
    
    for field in model._meta.get_fields():
        if hasattr(field, 'name'):
            # Excluir campos sensibles
            if any(sensitive in field.name.lower() for sensitive in sensitive_fields):
                continue
            # Excluir reverse relations que no son fields reales
            if hasattr(field, 'auto_created') and field.auto_created:
                continue
            fields.append(field.name)
    
    return sorted(fields)


def fix_serializer_file(filepath):
    """Arregla un archivo de serializers reemplazando fields='__all__'."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    changes_made = 0
    
    # Buscar todas las clases de serializers
    serializer_pattern = r'class\s+(\w+)\(.*?ModelSerializer.*?\):.*?class\s+Meta:.*?model\s*=\s*(\w+).*?fields\s*=\s*["\']__all__["\'](.*?)(?=\n\s{0,8}[a-z_]|\n\n|\Z)'
    
    for match in re.finditer(serializer_pattern, content, re.DOTALL | re.MULTILINE):
        serializer_name = match.group(1)
        model_name = match.group(2)
        rest_of_meta = match.group(3)
        
        # Intentar encontrar el modelo
        try:
            # Buscar el modelo en todas las apps
            model = None
            for app_config in apps.get_app_configs():
                try:
                    model = app_config.get_model(model_name)
                    break
                except LookupError:
                    continue
            
            if not model:
                print(f"⚠️ No se encontró modelo {model_name} para {serializer_name}")
                continue
            
            # Obtener campos del modelo
            model_fields = get_model_fields(model)
            
            if not model_fields:
                print(f"⚠️ No se obtuvieron campos para {model_name}")
                continue
            
            # Crear lista de campos formateada
            if len(model_fields) <= 5:
                # Una línea
                fields_str = f"fields = {model_fields}"
            else:
                # Múltiples líneas
                fields_list = ',\n            '.join(f"'{field}'" for field in model_fields)
                fields_str = f"fields = [\n            {fields_list}\n        ]"
            
            # Reemplazar fields='__all__' con la lista explícita
            old_text = match.group(0)
            new_text = old_text.replace("fields = '__all__'", fields_str)
            new_text = new_text.replace('fields = "__all__"', fields_str)
            
            content = content.replace(old_text, new_text)
            changes_made += 1
            print(f"✅ {serializer_name}: {len(model_fields)} campos explícitos")
            
        except Exception as e:
            print(f"❌ Error procesando {serializer_name}: {e}")
            continue
    
    # Guardar si hubo cambios
    if changes_made > 0 and content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return changes_made
    
    return 0


def main():
    """Procesa todos los archivos serializers.py."""
    base_path = '/workspaces/soptraloc/soptraloc_system/apps'
    total_changes = 0
    
    for app_name in os.listdir(base_path):
        serializers_file = os.path.join(base_path, app_name, 'serializers.py')
        
        if os.path.exists(serializers_file):
            print(f"\n📄 Procesando: {app_name}/serializers.py")
            changes = fix_serializer_file(serializers_file)
            total_changes += changes
    
    print(f"\n{'='*60}")
    print(f"✅ Total de serializers corregidos: {total_changes}")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
