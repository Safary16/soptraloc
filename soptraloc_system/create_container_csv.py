#!/usr/bin/env python3
"""
Script para crear un archivo CSV de ejemplo con el formato de importación de contenedores.
Basado en el formato del Excel de Walmart proporcionado.
"""

import csv
import os
from datetime import datetime, timedelta

def create_sample_csv():
    """Crea un archivo CSV de ejemplo con datos de contenedores."""
    
    # Encabezados basados en tu Excel
    headers = [
        'ID', 'Cliente', 'Puerto', 'ETA', 'Nave', 'Contenedor', 'Status', 
        'Sello', 'Medida', 'Descripción', 'Peso Carga', 'Peso Total', 
        'Terminal', 'Fecha Liberación', 'Hora Liberación', 'Fecha Programación', 
        'Hora Programación', 'Fecha Arribo CD', 'Hora Arribo CD', 'CD', 
        'Fecha Descarga (GPS)', 'Hora Descarga', 'Fecha Devolución', 'EIR', 
        'Agencia', 'Cía Naviera/Línea', 'Dep/Dev', 'Días Libres', 'Demurrage', 
        'Sobreestadía Región (x ciclo 2 horas)', 'Sobreestadía (x ciclo de 4 horas)', 
        'Almc', 'Días Extras de Almacenaje', 'E.CHASIS', 'Tipo de Servicio', 
        'Servicio Adicional', 'OBS 1', 'OBS 2', 'Servicio Directo', 
        'Fecha Actualización', 'Hora Actualización', 'Días Calculados'
    ]
    
    # Datos de ejemplo basados en tu formato
    sample_data = [
        [
            1, 'WALMART CHILE S.A.', 'VAL', '15/01/2024', 'MSC REGULUS', 
            'MSCU1234567', 'Liberado', 'WMT001', '40HC', 'MERCADERIA GENERAL', 
            '22000', '24500', 'TPS', '16/01/2024', '08:30', '17/01/2024', 
            '14:00', '17/01/2024', '16:45', 'CD MELIPILLA', '17/01/2024', 
            '18:30', '20/01/2024', 'X', 'ULTRAMAR', 'MSC', 'DEPOSITO', 
            '7', '23/01/2024', '0', '1', 'A1', '0', '0', 'Indirecto Depósito', 
            'MONTACARGAS', 'CLIENTE VIP', 'ENTREGAR EN HORARIO AM', '', 
            '20/01/2024', '09:15', '3'
        ],
        [
            2, 'WALMART CHILE S.A.', 'VAL', '18/01/2024', 'EVER GIVEN', 
            'EGHU9876543', 'Programado', 'WMT002', '40', 'PRODUCTOS ELECTRÓNICOS', 
            '18500', '21000', 'STI', '19/01/2024', '10:15', '20/01/2024', 
            '09:30', '', '', 'CD LAS CONDES', '', '', '', '', 'SAAM', 
            'EVERGREEN', 'DIRECTO', '5', '24/01/2024', '0', '0', 'B2', 
            '0', '1', 'Directo', '', 'PRIORIDAD ALTA', 'COORDINAR CON BODEGA', 
            'DIRECTO A TIENDA', '19/01/2024', '11:30', '0'
        ],
        [
            3, 'WALMART CHILE S.A.', 'VAL', '20/01/2024', 'MAERSK ESSEX', 
            'MRKU5555444', 'En Secuencia', 'WMT003', '20', 'TEXTILES Y ROPA', 
            '15000', '17200', 'TCVAL', '', '', '', '', '', '', 'CD QUILICURA', 
            '', '', '', '', 'MAERSK CHILE', 'MAERSK LINE', 'DEPOSITO', 
            '10', '30/01/2024', '0', '0', 'C3', '2', '0', 'Indirecto Depósito', 
            'INSPECCIÓN', 'REVISION ADUANERA', 'MERCADERÍA SENSIBLE', '', 
            '20/01/2024', '15:45', '0'
        ]
    ]
    
    # Crear el archivo CSV
    filename = 'containers_sample.csv'
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)
        writer.writerows(sample_data)
    
    print(f"Archivo {filename} creado exitosamente!")
    print(f"El archivo contiene {len(sample_data)} contenedores de ejemplo.")
    print("\nPara importar los datos, ejecuta:")
    print(f"python manage.py import_containers {filename}")
    print("\nPara hacer una prueba sin guardar cambios:")
    print(f"python manage.py import_containers {filename} --dry-run")

def create_template_csv():
    """Crea un template CSV vacío para llenar con datos reales."""
    
    headers = [
        'ID', 'Cliente', 'Puerto', 'ETA', 'Nave', 'Contenedor', 'Status', 
        'Sello', 'Medida', 'Descripción', 'Peso Carga', 'Peso Total', 
        'Terminal', 'Fecha Liberación', 'Hora Liberación', 'Fecha Programación', 
        'Hora Programación', 'Fecha Arribo CD', 'Hora Arribo CD', 'CD', 
        'Fecha Descarga (GPS)', 'Hora Descarga', 'Fecha Devolución', 'EIR', 
        'Agencia', 'Cía Naviera/Línea', 'Dep/Dev', 'Días Libres', 'Demurrage', 
        'Sobreestadía Región (x ciclo 2 horas)', 'Sobreestadía (x ciclo de 4 horas)', 
        'Almc', 'Días Extras de Almacenaje', 'E.CHASIS', 'Tipo de Servicio', 
        'Servicio Adicional', 'OBS 1', 'OBS 2', 'Servicio Directo', 
        'Fecha Actualización', 'Hora Actualización', 'Días Calculados'
    ]
    
    filename = 'containers_template.csv'
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)
        # Agregar una fila vacía como ejemplo
        writer.writerow([''] * len(headers))
    
    print(f"Template {filename} creado exitosamente!")
    print("Llena el archivo con tus datos y luego importa con:")
    print(f"python manage.py import_containers {filename}")

if __name__ == '__main__':
    print("Generador de archivos CSV para importación de contenedores")
    print("1. Crear archivo con datos de ejemplo")
    print("2. Crear template vacío")
    
    choice = input("Selecciona una opción (1 o 2): ").strip()
    
    if choice == '1':
        create_sample_csv()
    elif choice == '2':
        create_template_csv()
    else:
        print("Opción inválida. Creando archivo de ejemplo...")
        create_sample_csv()