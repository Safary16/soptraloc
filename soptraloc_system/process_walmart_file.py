#!/usr/bin/env python3
"""
Procesador específico para el archivo de Walmart con separador ;
"""

import pandas as pd
import os
import sys
from pathlib import Path

def process_walmart_file():
    """Procesa el archivo real de Walmart"""
    file_path = Path('/workspaces/soptraloc/soptraloc_system/PLANILLA MATRIZ IMPORTACIONES 3(WALMART).csv')
    
    if not file_path.exists():
        print("❌ Archivo no encontrado")
        return None
    
    print(f"📊 PROCESANDO ARCHIVO REAL DE WALMART")
    print(f"Archivo: {file_path.name}")
    print(f"Tamaño: {file_path.stat().st_size / 1024:.1f} KB")
    print("=" * 60)
    
    try:
        # Leer con separador de punto y coma
        df = pd.read_csv(file_path, sep=';', encoding='utf-8')
        
        # Si no funciona, probar con encoding latin-1
        if len(df.columns) == 1:
            df = pd.read_csv(file_path, sep=';', encoding='latin-1')
        
        print(f"✅ ARCHIVO PROCESADO CORRECTAMENTE")
        print(f"📋 Filas: {len(df)}")
        print(f"📋 Columnas: {len(df.columns)}")
        print("\n🔍 COLUMNAS ENCONTRADAS:")
        
        for i, col in enumerate(df.columns, 1):
            print(f"  {i:2d}. {col}")
        
        # Mostrar datos de muestra
        print(f"\n📊 PRIMERAS 3 FILAS:")
        print(df.head(3).to_string(max_cols=10))
        
        # Analizar contenedores programados
        analyze_programmed_containers(df)
        
        return df
        
    except Exception as e:
        print(f"❌ Error procesando archivo: {e}")
        return None

def analyze_programmed_containers(df):
    """Analiza los contenedores programados"""
    print(f"\n🎯 ANÁLISIS DE CONTENEDORES PROGRAMADOS:")
    print("=" * 50)
    
    # Buscar columnas clave
    container_col = None
    status_col = None
    date_col = None
    client_col = None
    
    for col in df.columns:
        col_lower = col.lower()
        if 'contenedor' in col_lower:
            container_col = col
        elif 'status' in col_lower or 'estado' in col_lower:
            status_col = col
        elif 'programa' in col_lower and 'fecha' in col_lower:
            date_col = col
        elif 'cliente' in col_lower:
            client_col = col
    
    print(f"📦 Columna Contenedor: {container_col}")
    print(f"🏷️  Columna Status: {status_col}")
    print(f"📅 Columna Fecha Programación: {date_col}")
    print(f"🏢 Columna Cliente: {client_col}")
    
    if container_col and status_col:
        # Contar por status
        print(f"\n📊 CONTENEDORES POR STATUS:")
        status_counts = df[status_col].value_counts()
        for status, count in status_counts.items():
            print(f"  {status}: {count} contenedores")
        
        # Filtrar programados
        programmed_keywords = ['programado', 'programa', 'pendiente', 'asignado']
        programmed_mask = df[status_col].str.lower().str.contains('|'.join(programmed_keywords), na=False)
        
        programmed_containers = df[programmed_mask]
        print(f"\n🎯 CONTENEDORES PROGRAMADOS: {len(programmed_containers)}")
        
        if len(programmed_containers) > 0:
            print("📋 MUESTRA DE CONTENEDORES PROGRAMADOS:")
            cols_to_show = [container_col, status_col]
            if client_col:
                cols_to_show.append(client_col)
            if date_col:
                cols_to_show.append(date_col)
            
            print(programmed_containers[cols_to_show].head().to_string(index=False))
    
    print(f"\n✅ ARCHIVO LISTO PARA IMPORTAR A LA BASE DE DATOS")

def main():
    df = process_walmart_file()
    
    if df is not None:
        print(f"\n🚀 PRÓXIMOS PASOS:")
        print("1. ✅ Archivo procesado correctamente")
        print("2. 🔄 Crear migraciones de base de datos")  
        print("3. 📥 Importar contenedores a Django")
        print("4. 📊 Configurar dashboard con contenedores programados")

if __name__ == "__main__":
    main()