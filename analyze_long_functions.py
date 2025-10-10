#!/usr/bin/env python
"""
Script para identificar funciones largas (200+ líneas) en el proyecto.
FASE 3: Refactoring de funciones largas y complejas.
"""
import os
import re


def count_function_lines(filepath):
    """Analiza un archivo Python y cuenta líneas por función."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Patrón para encontrar definiciones de funciones
    func_pattern = r'^\s*(def\s+\w+\([^)]*\):)'
    
    lines = content.split('\n')
    functions = []
    current_func = None
    current_indent = None
    func_start = 0
    
    for i, line in enumerate(lines, 1):
        # Detectar inicio de función
        match = re.match(func_pattern, line)
        if match:
            # Guardar función anterior
            if current_func:
                func_length = i - func_start - 1
                if func_length >= 50:  # Solo funciones de 50+ líneas
                    functions.append((current_func, func_start, func_length))
            
            # Nueva función
            current_func = match.group(1).strip()
            current_indent = len(line) - len(line.lstrip())
            func_start = i
    
    # Última función
    if current_func:
        func_length = len(lines) - func_start
        if func_length >= 50:
            functions.append((current_func, func_start, func_length))
    
    return functions


def analyze_codebase():
    """Analiza todo el codebase buscando funciones largas."""
    base_path = '/workspaces/soptraloc/soptraloc_system/apps'
    all_long_functions = []
    
    for app_name in os.listdir(base_path):
        app_path = os.path.join(base_path, app_name)
        
        if not os.path.isdir(app_path):
            continue
        
        # Buscar archivos Python
        for root, dirs, files in os.walk(app_path):
            for filename in files:
                if filename.endswith('.py') and not filename.startswith('__'):
                    filepath = os.path.join(root, filename)
                    relative_path = filepath.replace('/workspaces/soptraloc/soptraloc_system/', '')
                    
                    functions = count_function_lines(filepath)
                    
                    for func_name, line_num, length in functions:
                        all_long_functions.append({
                            'file': relative_path,
                            'function': func_name,
                            'line': line_num,
                            'length': length
                        })
    
    # Ordenar por longitud
    all_long_functions.sort(key=lambda x: x['length'], reverse=True)
    
    return all_long_functions


def main():
    print("🔍 Analizando funciones largas en el proyecto...\n")
    
    long_functions = analyze_codebase()
    
    if not long_functions:
        print("✅ No se encontraron funciones de 50+ líneas")
        return
    
    print(f"📊 Funciones largas encontradas: {len(long_functions)}\n")
    print("="*80)
    
    # Mostrar las 20 más largas
    for i, func in enumerate(long_functions[:20], 1):
        print(f"\n{i}. {func['function']}")
        print(f"   📁 {func['file']}:{func['line']}")
        print(f"   📏 {func['length']} líneas")
        
        if func['length'] >= 200:
            print(f"   🔴 CRÍTICO - Requiere refactoring urgente")
        elif func['length'] >= 100:
            print(f"   ⚠️  ALTO - Refactoring recomendado")
        else:
            print(f"   ℹ️  MEDIO - Considerar refactoring")
    
    print("\n" + "="*80)
    
    # Resumen
    critical = len([f for f in long_functions if f['length'] >= 200])
    high = len([f for f in long_functions if 100 <= f['length'] < 200])
    medium = len([f for f in long_functions if 50 <= f['length'] < 100])
    
    print(f"\n📈 Resumen:")
    print(f"   🔴 Crítico (200+ líneas): {critical}")
    print(f"   ⚠️  Alto (100-199 líneas): {high}")
    print(f"   ℹ️  Medio (50-99 líneas): {medium}")
    print(f"   Total: {len(long_functions)}")


if __name__ == '__main__':
    main()
