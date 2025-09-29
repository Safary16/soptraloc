#!/usr/bin/env python3
"""
Importador automático para el Excel de WALMART
Detecta automáticamente el formato y mapea columnas
"""

import pandas as pd
import os
import sys
from pathlib import Path

def detect_excel_file():
    """Detecta archivos Excel en el workspace"""
    workspace = Path('/workspaces/soptraloc')
    excel_files = []
    
    # Buscar archivos Excel/CSV
    patterns = ['*.xlsx', '*.xls', '*.csv']
    for pattern in patterns:
        excel_files.extend(list(workspace.glob(pattern)))
        excel_files.extend(list(workspace.glob(f'*/{pattern}')))
    
    return excel_files

def analyze_excel_structure(file_path):
    """Analiza la estructura del Excel"""
    print(f"📊 ANALIZANDO: {file_path.name}")
    print("=" * 50)
    
    try:
        # Intentar leer como Excel
        if file_path.suffix.lower() in ['.xlsx', '.xls']:
            df = pd.read_excel(file_path, nrows=5)  # Solo primeras 5 filas
        else:
            df = pd.read_csv(file_path, nrows=5)
        
        print(f"📋 Columnas encontradas ({len(df.columns)}):")
        for i, col in enumerate(df.columns, 1):
            print(f"  {i:2d}. {col}")
        
        print(f"\n📊 Forma de datos: {df.shape[0]} filas x {df.shape[1]} columnas")
        
        print("\n🔍 PRIMERAS FILAS:")
        print(df.head().to_string())
        
        # Mapeo automático de columnas comunes
        column_mapping = detect_column_mapping(df.columns)
        if column_mapping:
            print("\n🎯 MAPEO AUTOMÁTICO DETECTADO:")
            for field, column in column_mapping.items():
                print(f"  {field} → {column}")
        
        return df, column_mapping
        
    except Exception as e:
        print(f"❌ Error al leer archivo: {e}")
        return None, None

def detect_column_mapping(columns):
    """Detecta automáticamente el mapeo de columnas"""
    mapping = {}
    
    # Diccionario de patrones de columnas comunes
    patterns = {
        'container_number': ['contenedor', 'container', 'numero', 'number', 'booking'],
        'container_type': ['tipo', 'type', 'size', 'tamaño', 'ft'],
        'status': ['estado', 'status', 'situacion'],
        'seal_number': ['sello', 'seal', 'precinto'],
        'customs_document': ['bl', 'bill', 'documento', 'aduana'],
        'owner_company': ['empresa', 'company', 'cliente', 'importador'],
        'programmed_date': ['fecha', 'date', 'programado', 'programada', 'eta'],
        'warehouse': ['almacen', 'warehouse', 'bodega', 'deposito'],
        'vehicle': ['vehiculo', 'vehicle', 'camion', 'truck'],
    }
    
    # Buscar coincidencias
    for field, keywords in patterns.items():
        for col in columns:
            for keyword in keywords:
                if keyword.lower() in col.lower():
                    mapping[field] = col
                    break
            if field in mapping:
                break
    
    return mapping

def main():
    print("🔍 BUSCANDO ARCHIVOS EXCEL/CSV...")
    files = detect_excel_file()
    
    if not files:
        print("❌ No se encontraron archivos Excel/CSV")
        print("\n💡 INSTRUCCIONES:")
        print("1. Sube tu archivo Excel al workspace")
        print("2. Ejecuta este script nuevamente")
        return
    
    print(f"✅ Encontrados {len(files)} archivo(s):")
    for i, file in enumerate(files, 1):
        print(f"  {i}. {file.name} ({file.stat().st_size / 1024:.1f} KB)")
    
    # Analizar cada archivo
    for file in files:
        analyze_excel_structure(file)
        print("\n" + "="*50 + "\n")

if __name__ == "__main__":
    main()