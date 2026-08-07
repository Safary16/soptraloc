import pandas as pd
import os

archivos = [
    'apps/APL CHARLESTON ETA 26-09 SERRANO CCTI.xlsx',
    'apps/liberacion.xlsx',
    'apps/programacion.xlsx'
]

for archivo in archivos:
    if os.path.exists(archivo):
        print(f"\n{'='*80}")
        print(f"ARCHIVO: {archivo}")
        print('='*80)
        
        try:
            # Leer todas las hojas
            excel_file = pd.ExcelFile(archivo)
            print(f"\nHojas disponibles: {excel_file.sheet_names}")
            
            # Leer la primera hoja
            df = pd.read_excel(archivo, sheet_name=0)
            
            print(f"\nColumnas encontradas ({len(df.columns)}):")
            for i, col in enumerate(df.columns, 1):
                print(f"  {i:2}. {col}")
            
            print(f"\nPrimeras 3 filas:")
            print(df.head(3).to_string())
            
            print(f"\nInfo del DataFrame:")
            print(f"  - Total filas: {len(df)}")
            print(f"  - Total columnas: {len(df.columns)}")
            
        except Exception as e:
            print(f"Error leyendo {archivo}: {str(e)}")
    else:
        print(f"\n❌ Archivo no encontrado: {archivo}")

