#!/usr/bin/env python3
"""
Script para corregir errores de JavaScript inline en templates Django
"""

import os
import re
from pathlib import Path

def fix_template_js_errors(template_dir):
    """Corregir errores de JavaScript inline en todos los templates"""
    
    print("🔧 CORRIGIENDO ERRORES DE JAVASCRIPT EN TEMPLATES")
    print("=" * 60)
    
    # Patrones a corregir
    patterns = [
        # onclick="function({{ var.id }})" -> onclick="function('{{ var.id }}')"
        (r'onclick="([^"]*)\(\{\{\s*([^}]+)\.id\s*\}\}([^)]*)\)"', r'onclick="\1(\'\{\{\s*\2.id\s*\}\}\'\3)"'),
        # onclick="function({{ var.id }}, 'value')" -> onclick="function('{{ var.id }}', 'value')"
        (r'onclick="([^"]*)\(\{\{\s*([^}]+)\.id\s*\}\}([^)]*)\)"', r'onclick="\1(\'\{\{\s*\2.id\s*\}\}\'\3)"'),
    ]
    
    files_fixed = 0
    total_fixes = 0
    
    # Buscar todos los archivos .html en templates
    for template_file in Path(template_dir).rglob("*.html"):
        try:
            with open(template_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Aplicar correcciones específicas
            fixes_in_file = 0
            
            # Corregir patrones específicos encontrados
            specific_fixes = [
                (r'onclick="viewContainer\(\{\{ container\.id \}\}\)"', r'onclick="viewContainer(\'{{ container.id }}\')"'),
                (r'onclick="assignDriver\(\{\{ container\.id \}\}\)"', r'onclick="assignDriver(\'{{ container.id }}\')"'),
                (r'onclick="editContainer\(\{\{ container\.id \}\}\)"', r'onclick="editContainer(\'{{ container.id }}\')"'),
                (r'onclick="viewDetails\(\{\{ container\.id \}\}\)"', r'onclick="viewDetails(\'{{ container.id }}\')"'),
                (r'onclick="unassignDriver\(\{\{ driver\.id \}\}\)"', r'onclick="unassignDriver(\'{{ driver.id }}\')"'),
                (r'onclick="unassignDriver\(\{\{ container\.id \}\}\)"', r'onclick="unassignDriver(\'{{ container.id }}\')"'),
                (r'onclick="updatePosition\(\{\{ container\.id \}\}, \'([^\']+)\'\)"', r'onclick="updatePosition(\'{{ container.id }}\', \'\1\')"'),
                (r'onclick="resolveAlert\(\{\{ alert\.id \}\}\)"', r'onclick="resolveAlert(\'{{ alert.id }}\')"'),
                (r'onclick="viewContainer\(\{\{ alert\.container\.id \}\}\)"', r'onclick="viewContainer(\'{{ alert.container.id }}\')"'),
                (r'onclick="assignDriverFromAlert\(\{\{ alert\.container\.id \}\}', r'onclick="assignDriverFromAlert(\'{{ alert.container.id }}\''),
            ]
            
            for pattern, replacement in specific_fixes:
                new_content = re.sub(pattern, replacement, content)
                if new_content != content:
                    fixes_in_file += 1
                    content = new_content
            
            # Guardar archivo si hubo cambios
            if content != original_content:
                with open(template_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                files_fixed += 1
                total_fixes += fixes_in_file
                print(f"✅ {template_file.relative_to(template_dir)}: {fixes_in_file} correcciones")
        
        except Exception as e:
            print(f"❌ Error procesando {template_file}: {e}")
    
    print(f"\n📊 RESUMEN:")
    print(f"   Archivos corregidos: {files_fixed}")
    print(f"   Total de correcciones: {total_fixes}")
    
    return files_fixed, total_fixes

def main():
    template_dir = Path("/workspaces/soptraloc/soptraloc_system/templates")
    
    if not template_dir.exists():
        print(f"❌ No se encuentra el directorio de templates: {template_dir}")
        return
    
    files_fixed, total_fixes = fix_template_js_errors(template_dir)
    
    if total_fixes > 0:
        print(f"\n🎉 Templates corregidos exitosamente!")
        print("   Ahora el servidor Django debería iniciarse sin errores.")
    else:
        print("   No se encontraron errores para corregir.")

if __name__ == "__main__":
    main()