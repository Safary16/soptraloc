#!/usr/bin/env python
"""
Script para importar conductores desde los datos proporcionados
"""
import os
import sys
import django
from datetime import datetime

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.drivers.models import Driver

def import_drivers():
    """Importar conductores desde los datos proporcionados"""
    
    # Conductores Flota Locales y Leasing
    conductores_locales = [
        {"nombre": "Mauricio Perez", "ppu": "BVWG80", "rut": "14156307-6", "telefono": "985170357", "tracto": "12", "coordinador": "BARBARA/NADYA", "faena": "Leasing", "estado": "OPERATIVO", "tipo": "LEASING"},
        {"nombre": "Guillermo Alegria", "ppu": "HDTY11", "rut": "9296154-0", "telefono": "950141437", "tracto": "55", "coordinador": "EVELYN/KEVIN", "faena": "Leasing", "estado": "OPERATIVO", "tipo": "LEASING"},
        {"nombre": "Omar Vielma", "ppu": "BVVY97", "rut": "13838494-2", "telefono": "988043061", "tracto": "5", "coordinador": "BARBARA/NADYA", "faena": "Leasing", "estado": "PANNE", "tipo": "LEASING"},
        {"nombre": "Jose Macaya", "ppu": "BVWG80", "rut": "7747655-5", "telefono": "950888526", "tracto": "12", "coordinador": "EVELYN/KEVIN", "faena": "Leasing", "estado": "OPERATIVO", "tipo": "LEASING"},
        {"nombre": "Marco Cabrera", "ppu": "HKFT72", "rut": "13677683-5", "telefono": "993957452", "tracto": "71", "coordinador": "BARBARA/NADYA", "faena": "Localero", "estado": "OPERATIVO", "tipo": "LOCALERO"},
        {"nombre": "Jorge Sepulveda", "ppu": "HKFT80", "rut": "17925067-5", "telefono": "987766567", "tracto": "79", "coordinador": "BARBARA/NADYA", "faena": "Localero", "estado": "OPERATIVO", "tipo": "LOCALERO"},
        {"nombre": "Rodrigo Diaz", "ppu": "HKFT73", "rut": "11847596-8", "telefono": "981588923", "tracto": "72", "coordinador": "BARBARA/JUAN", "faena": "Localero", "estado": "OPERATIVO", "tipo": "LOCALERO"},
        {"nombre": "Gabriel Pitron", "ppu": "HKFT81", "rut": "10862267-9", "telefono": "988915122", "tracto": "80", "coordinador": "EVELYN/KEVIN", "faena": "Localero", "estado": "OPERATIVO", "tipo": "LOCALERO"},
        {"nombre": "Sebastian Lorca", "ppu": "HKFT92", "rut": "16787949-7", "telefono": "977749235", "tracto": "86", "coordinador": "EVELYN/KEVIN", "faena": "Localero", "estado": "NO_DISPONIBLE", "tipo": "LOCALERO"},
        {"nombre": "Juan Navarrete", "ppu": "HKFT84", "rut": "9490668-7", "telefono": "941839432", "tracto": "83", "coordinador": "BARBARA/NADYA", "faena": "Localero", "estado": "OPERATIVO", "tipo": "LOCALERO"},
        {"nombre": "Wilderson Blanco", "ppu": "HKFT86", "rut": "25970394-8", "telefono": "979545851", "tracto": "85", "coordinador": "BARBARA/NADYA", "faena": "Localero", "estado": "OPERATIVO", "tipo": "LOCALERO"},
        {"nombre": "Wilmer Fonseca", "ppu": "HKSR99", "rut": "25922096-3", "telefono": "988187018", "tracto": "90", "coordinador": "EVELYN/KEVIN", "faena": "Localero", "estado": "OPERATIVO", "tipo": "LOCALERO"},
        {"nombre": "Jose Barcelo", "ppu": "JLJW21", "rut": "28529534-3", "telefono": "975122570", "tracto": "133", "coordinador": "EVELYN/KEVIN", "faena": "Localero", "estado": "PERMISO", "tipo": "LOCALERO"},
        {"nombre": "Nicolas Budin", "ppu": "JTGV82", "rut": "19375025-7", "telefono": "972574800", "tracto": "135", "coordinador": "EVELYN/KEVIN", "faena": "Localero", "estado": "OPERATIVO", "tipo": "LOCALERO"},
        {"nombre": "Alex Torres", "ppu": "HYKJ81", "rut": "11487767-0", "telefono": "951787491", "tracto": "150", "coordinador": "BARBARA/NADYA", "faena": "Localero", "estado": "OPERATIVO", "tipo": "LOCALERO"},
        {"nombre": "Bastian Diaz", "ppu": "JTGV87", "rut": "18481650-4", "telefono": "973078245", "tracto": "140", "coordinador": "BARBARA/NADYA", "faena": "Localero", "estado": "OPERATIVO", "tipo": "LOCALERO"},
        {"nombre": "Joan Campos", "ppu": "JXSH79", "rut": "13239173-4", "telefono": "976163321", "tracto": "148", "coordinador": "EVELYN/KEVIN", "faena": "Localero", "estado": "OPERATIVO", "tipo": "LOCALERO"},
        {"nombre": "Mario Diaz", "ppu": "HFVT50", "rut": "8335882-3", "telefono": "979858142", "tracto": "60", "coordinador": "EVELYN/KEVIN", "faena": "Localero", "estado": "OPERATIVO", "tipo": "LOCALERO"},
        {"nombre": "Victor Bautista", "ppu": "JXSH80", "rut": "24402138-7", "telefono": "964357135", "tracto": "149", "coordinador": "EVELYN/KEVIN", "faena": "Localero", "estado": "NO_DISPONIBLE", "tipo": "LOCALERO"},
        {"nombre": "Jonathan Briones", "ppu": "HKFT76", "rut": "20344648-9", "telefono": "978960902", "tracto": "75", "coordinador": "BARBARA/NADYA", "faena": "Localero", "estado": "OPERATIVO", "tipo": "LOCALERO"},
        {"nombre": "Carlos Leiva", "ppu": "HCKX80", "rut": "15584376-4", "telefono": "997152416", "tracto": "51", "coordinador": "EVELYN/KEVIN", "faena": "Localero", "estado": "OPERATIVO", "tipo": "LOCALERO"},
        {"nombre": "Andre Muñoz", "ppu": "HFVT49", "rut": "19221370-3", "telefono": "950032859", "tracto": "59", "coordinador": "EVELYN/KEVIN", "faena": "Localero", "estado": "OPERATIVO", "tipo": "LOCALERO"},
        {"nombre": "Jose Rios", "ppu": "LPKH13", "rut": "25030084-0", "telefono": "953156726", "tracto": "177", "coordinador": "", "faena": "Localero", "estado": "OPERATIVO", "tipo": "LOCALERO"},
        {"nombre": "Esteban Poblete", "ppu": "JLJW20", "rut": "19259623-8", "telefono": "936577259", "tracto": "132", "coordinador": "BARBARA/NADYA", "faena": "Localero", "estado": "OPERATIVO", "tipo": "LOCALERO"},
        {"nombre": "Angel Saldaña", "ppu": "HKFT78", "rut": "141863045", "telefono": "962624364", "tracto": "77", "coordinador": "", "faena": "Localero", "estado": "OPERATIVO", "tipo": "LOCALERO"},
    ]
    
    # Conductores Turno PM
    conductores_pm = [
        {"nombre": "Guillermo Chavez", "ppu": "HKFT76", "rut": "13564932-5", "telefono": "988043038", "tracto": "75", "coordinador": "Localero/TURNOPM", "faena": "TURNOPM", "estado": "OPERATIVO", "tipo": "TRONCO_PM"},
        {"nombre": "Gonzalo Vergara", "ppu": "HFVT49", "rut": "12906561-3", "telefono": "941668122", "tracto": "59", "coordinador": "Localero/TURNOPM", "faena": "TURNOPM", "estado": "OPERATIVO", "tipo": "TRONCO_PM"},
        {"nombre": "Marco Caceres", "ppu": "HCKX80", "rut": "14276814-3", "telefono": "935991072", "tracto": "51", "coordinador": "Localero/TURNOPM", "faena": "TURNOPM", "estado": "OPERATIVO", "tipo": "TRONCO_PM"},
    ]
    
    # Conductores Tronco
    conductores_tronco = [
        {"nombre": "Nicolas Salinas", "ppu": "LPKH12", "rut": "19912254-1", "telefono": "+56950961914", "tracto": "176", "coordinador": "", "faena": "", "estado": "OPERATIVO", "tipo": "TRONCO"},
        {"nombre": "Luis Navarrete", "ppu": "RHDW63", "rut": "18056912-K", "telefono": "+56950140506", "tracto": "222", "coordinador": "", "faena": "", "estado": "OPERATIVO", "tipo": "TRONCO"},
        {"nombre": "Jorge Lopez", "ppu": "RGBS49", "rut": "14190062-5", "telefono": "+56936339145", "tracto": "209", "coordinador": "", "faena": "", "estado": "OPERATIVO", "tipo": "TRONCO"},
        {"nombre": "Rodrigo Alvarez", "ppu": "LPKH18", "rut": "13474420-0", "telefono": "+56977749582", "tracto": "182", "coordinador": "", "faena": "", "estado": "OPERATIVO", "tipo": "TRONCO"},
        {"nombre": "Carlos Ahumada", "ppu": "LPKH21", "rut": "9897812-7", "telefono": " +56988043047", "tracto": "185", "coordinador": "", "faena": "", "estado": "OPERATIVO", "tipo": "TRONCO"},
        {"nombre": "Julian Pedreros", "ppu": "PRFS58", "rut": "10629381-3", "telefono": "+56950141894", "tracto": "206", "coordinador": "", "faena": "", "estado": "OPERATIVO", "tipo": "TRONCO"},
        {"nombre": "Enzo Barragan", "ppu": "PRFS56", "rut": "19118646-K", "telefono": "+56964957592", "tracto": "204", "coordinador": "", "faena": "", "estado": "OPERATIVO", "tipo": "TRONCO"},
        {"nombre": "Edison Sanchez", "ppu": "LPKH16", "rut": "25871360-5", "telefono": "56944806981", "tracto": "180", "coordinador": "", "faena": "", "estado": "OPERATIVO", "tipo": "TRONCO"},
        {"nombre": "Hugo Alegria", "ppu": "LPKH17", "rut": "20432604-5", "telefono": "56978568128", "tracto": "181", "coordinador": "", "faena": "", "estado": "OPERATIVO", "tipo": "TRONCO"},
        {"nombre": "Anibal Delgado", "ppu": "LPKH20", "rut": "23701723-4", "telefono": "+56942396802", "tracto": "184", "coordinador": "", "faena": "", "estado": "OPERATIVO", "tipo": "TRONCO"},
        {"nombre": "Jose Naipan", "ppu": "PRFS57", "rut": "16929613-8", "telefono": "+56977952955", "tracto": "205", "coordinador": "", "faena": "", "estado": "OPERATIVO", "tipo": "TRONCO"},
        {"nombre": "Leandro Orellana", "ppu": "RFZY34", "rut": "17151234-4", "telefono": "+56994040024", "tracto": "217", "coordinador": "", "faena": "", "estado": "OPERATIVO", "tipo": "TRONCO"},
        {"nombre": "Eugenio Madrid", "ppu": "RHDW62", "rut": "13677945-1", "telefono": "+56950140841", "tracto": "221", "coordinador": "", "faena": "", "estado": "OPERATIVO", "tipo": "TRONCO"},
        {"nombre": "Bladimir Tapia", "ppu": "RHDW61", "rut": "17180652-6", "telefono": "+56964952460", "tracto": "220", "coordinador": "", "faena": "", "estado": "OPERATIVO", "tipo": "TRONCO"},
        {"nombre": "Leonardo Mosqueda", "ppu": "SCRW80", "rut": "27718701-9", "telefono": "+56977763660", "tracto": "224", "coordinador": "", "faena": "", "estado": "OPERATIVO", "tipo": "TRONCO"},
        {"nombre": "Jesus Mistage", "ppu": "SCRW83", "rut": "26453105-5", "telefono": "+56945237078", "tracto": "227", "coordinador": "", "faena": "", "estado": "OPERATIVO", "tipo": "TRONCO"},
        {"nombre": "Genord Cochillus", "ppu": "HDTX99", "rut": "24732195-0", "telefono": "+56934830798", "tracto": "53", "coordinador": "", "faena": "", "estado": "OPERATIVO", "tipo": "TRONCO"},
        {"nombre": "Fernando Luzardo", "ppu": "JZLC27", "rut": "27237837-1", "telefono": "+56948500835", "tracto": "152", "coordinador": "", "faena": "", "estado": "OPERATIVO", "tipo": "TRONCO"},
        {"nombre": "Jose Orellana", "ppu": "PRFS60", "rut": "11602440-3", "telefono": "56941873362", "tracto": "208", "coordinador": "", "faena": "", "estado": "OPERATIVO", "tipo": "TRONCO"},
        {"nombre": "Darwin Vargas", "ppu": "RGBS59", "rut": "15420607-8", "telefono": "56941540381", "tracto": "211", "coordinador": "", "faena": "", "estado": "OPERATIVO", "tipo": "TRONCO"},
        {"nombre": "Sebastian Rojas", "ppu": "LPKH13", "rut": "15662363-6", "telefono": "+56972605225", "tracto": "177", "coordinador": "", "faena": "", "estado": "OPERATIVO", "tipo": "TRONCO"},
        {"nombre": "Gabriel Valdivia", "ppu": "LPKH14", "rut": "18157135-7", "telefono": " +56985482653", "tracto": "178", "coordinador": "", "faena": "", "estado": "OPERATIVO", "tipo": "TRONCO"},
        {"nombre": "Johnny Garnica", "ppu": "JXSH78", "rut": "8865172-3", "telefono": "+56993972736", "tracto": "147", "coordinador": "", "faena": "", "estado": "OPERATIVO", "tipo": "TRONCO"},
        {"nombre": "Cristian Valdes", "ppu": "JXSH74", "rut": "19239435-K", "telefono": "+56966969816", "tracto": "143", "coordinador": "", "faena": "", "estado": "OPERATIVO", "tipo": "TRONCO"},
    ]
    
    # Combinar todos los conductores
    todos_conductores = conductores_locales + conductores_pm + conductores_tronco
    
    # Mapeo de estados
    estado_mapping = {
        'OPERATIVO': 'OPERATIVO',
        'PANNE': 'PANNE',
        'PERMISO': 'PERMISO',
        'NO_DISPONIBLE': 'NO_DISPONIBLE',
        'AUSENTE': 'AUSENTE'
    }
    
    # Mapeo de tipos
    tipo_mapping = {
        'LEASING': 'LEASING',
        'LOCALERO': 'LOCALERO',
        'TRONCO_PM': 'TRONCO_PM',
        'TRONCO': 'TRONCO'
    }
    
    created_count = 0
    updated_count = 0
    
    print("🚛 IMPORTANDO CONDUCTORES")
    print("=" * 50)
    
    for data in todos_conductores:
        # Limpiar datos
        rut = data['rut'].strip()
        telefono = data['telefono'].replace('+56', '').replace(' ', '') if data['telefono'] else ''
        
        try:
            # Intentar encontrar conductor existente
            driver, created = Driver.objects.get_or_create(
                rut=rut,
                defaults={
                    'nombre': data['nombre'],
                    'telefono': telefono,
                    'ppu': data['ppu'],
                    'tracto': data['tracto'],
                    'tipo_conductor': tipo_mapping[data['tipo']],
                    'estado': estado_mapping[data['estado']],
                    'coordinador': data['coordinador'],
                    'faena': data['faena'],
                    'ubicacion_actual': 'CCTI',  # Por defecto en la base
                    'ingresa_agy': True,
                    'is_active': True
                }
            )
            
            if created:
                print(f"✅ Creado: {driver.nombre} ({driver.ppu}) - {driver.get_tipo_conductor_display()}")
                created_count += 1
            else:
                # Actualizar datos si ya existe
                driver.nombre = data['nombre']
                driver.telefono = telefono
                driver.ppu = data['ppu']
                driver.tracto = data['tracto']
                driver.tipo_conductor = tipo_mapping[data['tipo']]
                driver.estado = estado_mapping[data['estado']]
                driver.coordinador = data['coordinador']
                driver.faena = data['faena']
                driver.save()
                
                print(f"🔄 Actualizado: {driver.nombre} ({driver.ppu})")
                updated_count += 1
                
        except Exception as e:
            print(f"❌ Error con {data['nombre']}: {str(e)}")
            continue
    
    print(f"\n📊 RESUMEN DE IMPORTACIÓN:")
    print(f"✅ Conductores creados: {created_count}")
    print(f"🔄 Conductores actualizados: {updated_count}")
    print(f"👥 Total conductores: {Driver.objects.count()}")
    
    # Estadísticas por tipo
    for tipo, nombre in Driver.TIPO_CONDUCTOR_CHOICES:
        count = Driver.objects.filter(tipo_conductor=tipo).count()
        print(f"   - {nombre}: {count}")

if __name__ == "__main__":
    import_drivers()