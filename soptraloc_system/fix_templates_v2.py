#!/usr/bin/env python3
"""
Script mejorado para corregir errores de JavaScript inline en templates Django
"""

import os
import re
from pathlib import Path

def fix_template_js_errors_v2(template_dir):
    """Corregir errores de JavaScript inline usando un enfoque diferente"""
    
    print("🔧 CORRIGIENDO ERRORES DE JAVASCRIPT EN TEMPLATES (V2)")
    print("=" * 60)
    
    files_fixed = 0
    total_fixes = 0
    
    # Buscar todos los archivos .html en templates
    for template_file in Path(template_dir).rglob("*.html"):
        try:
            with open(template_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            fixes_in_file = 0
            
            # Corregir patrones específicos usando data-attributes en lugar de onclick inline
            # Esto es más limpio y no causa errores de parsing
            
            # Buscar todas las líneas con onclick problemático
            lines = content.split('\n')
            new_lines = []
            
            for line in lines:
                new_line = line
                
                # Si la línea contiene onclick con Django templates, cambiarla
                if 'onclick=' in line and '{{' in line and '}}' in line:
                    # Reemplazar las barras invertidas escapadas que agregamos mal antes
                    if r'\'' in line:
                        new_line = new_line.replace(r"\'", "'")
                        fixes_in_file += 1
                    
                    # También podemos usar un enfoque alternativo con data-attributes
                    # Por ejemplo: onclick="viewContainer({{ id }})" -> data-action="view" data-id="{{ id }}"
                    
                new_lines.append(new_line)
            
            content = '\n'.join(new_lines)
            
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
    
    files_fixed, total_fixes = fix_template_js_errors_v2(template_dir)
    
    if total_fixes > 0:
        print(f"\n🎉 Templates corregidos exitosamente!")
        print("   Ahora el servidor Django debería iniciarse sin errores.")
    else:
        print("   No se encontraron errores para corregir.")

if __name__ == "__main__":
    main()