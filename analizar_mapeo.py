import pandas as pd
from datetime import datetime

print("\n" + "="*80)
print("ANÁLISIS DETALLADO DE ARCHIVOS EXCEL")
print("="*80)

# 1. ARCHIVO DE EMBARQUE (NAVE)
print("\n📦 1. EMBARQUE / NAVE")
print("-" * 80)

df_nave = pd.read_excel('apps/APL CHARLESTON ETA 26-09 SERRANO CCTI.xlsx')

print("\n✅ Columnas presentes:")
for col in df_nave.columns:
    print(f"   - {col}")

print("\n🔍 Muestra de datos importantes:")
print(f"\n   Container Numbers: {df_nave['Container Numbers'].iloc[0]}")
print(f"   Container Size: {df_nave['Container Size'].iloc[0]}")
print(f"   Weight Kgs: {df_nave['Weight Kgs'].iloc[0]}")
print(f"   Nave Confirmado: {df_nave['Nave Confirmado'].iloc[0]}")
print(f"   Viaje Confirmado: {df_nave['Viaje Confirmado'].iloc[0]}")
print(f"   ETA Confirmada: {df_nave['ETA Confirmada'].iloc[0]}")
print(f"   Vendor: {df_nave['Vendor'].iloc[0]}")
print(f"   Container Seal: {df_nave['Container Seal'].iloc[0]}")
print(f"   Destino: {df_nave['Destino'].iloc[0]}")

# 2. ARCHIVO DE LIBERACIÓN
print("\n\n📋 2. LIBERACIÓN")
print("-" * 80)

df_lib = pd.read_excel('apps/liberacion.xlsx')

print("\n✅ Columnas presentes:")
for col in df_lib.columns:
    print(f"   - {col}")

# Saltar primera fila si es encabezado
if pd.isna(df_lib['CONTENEDOR '].iloc[0]):
    df_lib = df_lib.iloc[1:].reset_index(drop=True)

print("\n🔍 Muestra de datos importantes:")
print(f"\n   CONTENEDOR: {df_lib['CONTENEDOR '].iloc[0]}")
print(f"   CLIENTE: {df_lib['CLIENTE'].iloc[0]}")
print(f"   M/N (Nave): {df_lib['M/N'].iloc[0]}")
print(f"   TIPO CONT: {df_lib['TIPO  CONT- TEMPERATURA'].iloc[0]}")
print(f"   PESO UNIDADES: {df_lib['PESO UNIDADES'].iloc[0]}")
print(f"   ALMACEN: {df_lib['ALMACEN'].iloc[0]}")
print(f"   DEVOLUCION VACIO: {df_lib['DEVOLUCION VACIO'].iloc[0]}")
print(f"   FECHA SALIDA: {df_lib['FECHA SALIDA'].iloc[0]}")
print(f"   HORA SALIDA: {df_lib['HORA SALIDA '].iloc[0]}")

# 3. ARCHIVO DE PROGRAMACIÓN
print("\n\n📅 3. PROGRAMACIÓN")
print("-" * 80)

df_prog = pd.read_excel('apps/programacion.xlsx')

print("\n✅ Columnas presentes:")
for col in df_prog.columns:
    print(f"   - {col}")

print("\n🔍 Muestra de datos importantes:")
print(f"\n   CONTENEDOR: {df_prog['CONTENEDOR'].iloc[0]}")
print(f"   TRANSPORTISTA: {df_prog['RANSPORTISTA'].iloc[0]}")  # Nota: falta T
print(f"   TERMINAL: {df_prog['TERMINAL'].iloc[0]}")
print(f"   NAVE: {df_prog['NAVE'].iloc[0]}")
print(f"   FECHA DE PROGRAMACION: {df_prog['FECHA DE PROGRAMACION'].iloc[0]}")
print(f"   FECHA DEMURRAGE: {df_prog['FECHA DEMURRAGE'].iloc[0]}")
print(f"   WK DEMURRAGE: {df_prog['WK DEMURRAGE'].iloc[0]}")
print(f"   BODEGA (CD): {df_prog['BODEGA'].iloc[0]}")
print(f"   HORA: {df_prog['HORA'].iloc[0]}")
print(f"   PRODUCTO: {df_prog['PRODUCTO'].iloc[0]}")
print(f"   REFERENCIA: {df_prog['REFERENCIA'].iloc[0]}")

# ANÁLISIS DE COINCIDENCIAS
print("\n\n🔄 4. ANÁLISIS DE COINCIDENCIAS")
print("-" * 80)

# Extraer contenedores
containers_nave = set(df_nave['Container Numbers'].dropna().str.strip().str.upper())
containers_lib = set(df_lib['CONTENEDOR '].dropna().astype(str).str.strip().str.upper())
containers_prog = set(df_prog['CONTENEDOR'].dropna().astype(str).str.strip().str.upper())

print(f"\n   Contenedores en NAVE: {len(containers_nave)}")
print(f"   Contenedores en LIBERACIÓN: {len(containers_lib)}")
print(f"   Contenedores en PROGRAMACIÓN: {len(containers_prog)}")

print(f"\n   En NAVE y LIBERACIÓN: {len(containers_nave & containers_lib)}")
print(f"   En LIBERACIÓN y PROGRAMACIÓN: {len(containers_lib & containers_prog)}")
print(f"   En las 3 planillas: {len(containers_nave & containers_lib & containers_prog)}")

# Mostrar ejemplos
print("\n   Ejemplo de contenedor en las 3:")
comunes = containers_nave & containers_lib & containers_prog
if comunes:
    ejemplo = list(comunes)[0]
    print(f"      {ejemplo}")

