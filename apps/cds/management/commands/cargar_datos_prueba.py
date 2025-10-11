"""
Comando para cargar datos de prueba en el sistema
Útil para desarrollo y testing
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from apps.cds.models import CD
from apps.drivers.models import Driver
from apps.containers.models import Container
from apps.programaciones.models import Programacion


class Command(BaseCommand):
    help = 'Carga datos de prueba en el sistema'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Cargando datos de prueba...'))
        
        # Crear CCTIs
        self.stdout.write('Creando CCTIs...')
        ccti_zeal, _ = CD.objects.get_or_create(
            codigo='ZEAL',
            defaults={
                'nombre': 'CCTI ZEAL',
                'direccion': 'Zona Extra portuaria, Valparaíso',
                'comuna': 'Valparaíso',
                'tipo': 'ccti',
                'lat': Decimal('-33.0458'),
                'lng': Decimal('-71.6197'),
                'capacidad_vacios': 100,
                'vacios_actuales': 15
            }
        )
        
        ccti_clep, _ = CD.objects.get_or_create(
            codigo='CLEP',
            defaults={
                'nombre': 'CCTI CLEP',
                'direccion': 'Padre Hurtado, Santiago',
                'comuna': 'Padre Hurtado',
                'tipo': 'ccti',
                'lat': Decimal('-33.5733'),
                'lng': Decimal('-70.8075'),
                'capacidad_vacios': 150,
                'vacios_actuales': 25
            }
        )
        
        # Crear algunos clientes
        self.stdout.write('Creando clientes...')
        cd_quilicura, _ = CD.objects.get_or_create(
            codigo='CLI_QUILICURA',
            defaults={
                'nombre': 'Cliente Quilicura',
                'direccion': 'Parque Industrial Quilicura',
                'comuna': 'Quilicura',
                'tipo': 'cliente',
                'lat': Decimal('-33.3600'),
                'lng': Decimal('-70.7267'),
            }
        )
        
        cd_maipu, _ = CD.objects.get_or_create(
            codigo='CLI_MAIPU',
            defaults={
                'nombre': 'Cliente Maipú',
                'direccion': 'Zona Industrial Maipú',
                'comuna': 'Maipú',
                'tipo': 'cliente',
                'lat': Decimal('-33.5115'),
                'lng': Decimal('-70.7592'),
            }
        )
        
        cd_colina, _ = CD.objects.get_or_create(
            codigo='CLI_COLINA',
            defaults={
                'nombre': 'Cliente Colina',
                'direccion': 'Ruta 57, Colina',
                'comuna': 'Colina',
                'tipo': 'cliente',
                'lat': Decimal('-33.1878'),
                'lng': Decimal('-70.6751'),
            }
        )
        
        self.stdout.write(self.style.SUCCESS(f'✓ {CD.objects.count()} CDs creados'))
        
        # Crear conductores
        self.stdout.write('Creando conductores...')
        conductores_data = [
            {
                'nombre': 'Juan Pérez',
                'rut': '12345678-9',
                'telefono': '+56912345678',
                'presente': True,
                'activo': True,
                'cumplimiento_porcentaje': Decimal('95.5'),
                'max_entregas_dia': 3,
                'num_entregas_dia': 1,
                'ultima_posicion_lat': Decimal('-33.4489'),
                'ultima_posicion_lng': Decimal('-70.6693'),
                'total_entregas': 120,
                'entregas_a_tiempo': 115,
            },
            {
                'nombre': 'María González',
                'rut': '23456789-0',
                'telefono': '+56923456789',
                'presente': True,
                'activo': True,
                'cumplimiento_porcentaje': Decimal('98.2'),
                'max_entregas_dia': 3,
                'num_entregas_dia': 0,
                'ultima_posicion_lat': Decimal('-33.5000'),
                'ultima_posicion_lng': Decimal('-70.7000'),
                'total_entregas': 150,
                'entregas_a_tiempo': 148,
            },
            {
                'nombre': 'Pedro Sánchez',
                'rut': '34567890-1',
                'telefono': '+56934567890',
                'presente': True,
                'activo': True,
                'cumplimiento_porcentaje': Decimal('92.0'),
                'max_entregas_dia': 3,
                'num_entregas_dia': 2,
                'ultima_posicion_lat': Decimal('-33.3500'),
                'ultima_posicion_lng': Decimal('-70.7200'),
                'total_entregas': 100,
                'entregas_a_tiempo': 92,
            },
            {
                'nombre': 'Ana Martínez',
                'rut': '45678901-2',
                'telefono': '+56945678901',
                'presente': False,
                'activo': True,
                'cumplimiento_porcentaje': Decimal('96.8'),
                'max_entregas_dia': 3,
                'num_entregas_dia': 0,
                'ultima_posicion_lat': Decimal('-33.4000'),
                'ultima_posicion_lng': Decimal('-70.7500'),
                'total_entregas': 80,
                'entregas_a_tiempo': 78,
            },
        ]
        
        for data in conductores_data:
            Driver.objects.get_or_create(
                rut=data['rut'],
                defaults=data
            )
        
        self.stdout.write(self.style.SUCCESS(f'✓ {Driver.objects.count()} conductores creados'))
        
        # Crear contenedores de muestra
        self.stdout.write('Creando contenedores...')
        contenedores_data = [
            # Por arribar
            {'container_id': 'CONT001', 'tipo': '40', 'nave': 'MSC MARIA', 'estado': 'por_arribar'},
            {'container_id': 'CONT002', 'tipo': '20', 'nave': 'EVER FORWARD', 'estado': 'por_arribar'},
            # Liberados
            {'container_id': 'CONT003', 'tipo': '40HC', 'nave': 'MAERSK LINE', 'estado': 'liberado', 'posicion_fisica': 'ZEAL'},
            {'container_id': 'CONT004', 'tipo': '40', 'nave': 'CMA CGM', 'estado': 'liberado', 'posicion_fisica': 'CLEP'},
            {'container_id': 'CONT005', 'tipo': '20', 'nave': 'HAPAG LLOYD', 'estado': 'liberado', 'posicion_fisica': 'ZEAL', 'secuenciado': True},
            # Programados
            {'container_id': 'CONT006', 'tipo': '40', 'nave': 'MSC MARIA', 'estado': 'programado', 'posicion_fisica': 'CLEP', 'comuna': 'Quilicura'},
            {'container_id': 'CONT007', 'tipo': '40HC', 'nave': 'EVER FORWARD', 'estado': 'programado', 'posicion_fisica': 'ZEAL', 'comuna': 'Maipú'},
            # Asignado
            {'container_id': 'CONT008', 'tipo': '20', 'nave': 'MAERSK LINE', 'estado': 'asignado', 'posicion_fisica': 'CLEP', 'comuna': 'Colina'},
        ]
        
        for data in contenedores_data:
            Container.objects.get_or_create(
                container_id=data['container_id'],
                defaults=data
            )
        
        self.stdout.write(self.style.SUCCESS(f'✓ {Container.objects.count()} contenedores creados'))
        
        # Crear programaciones
        self.stdout.write('Creando programaciones...')
        now = timezone.now()
        
        # Programación urgente (< 48h sin conductor)
        cont006 = Container.objects.get(container_id='CONT006')
        prog1, created = Programacion.objects.get_or_create(
            container=cont006,
            defaults={
                'cd': cd_quilicura,
                'fecha_programada': now + timedelta(hours=40),
                'cliente': 'Empresa ABC',
                'requiere_alerta': True,
            }
        )
        if created:
            prog1.verificar_alerta()
        
        # Programación con conductor
        cont007 = Container.objects.get(container_id='CONT007')
        driver1 = Driver.objects.get(nombre='Juan Pérez')
        Programacion.objects.get_or_create(
            container=cont007,
            defaults={
                'cd': cd_maipu,
                'fecha_programada': now + timedelta(days=3),
                'cliente': 'Empresa XYZ',
                'driver': driver1,
            }
        )
        
        # Programación sin conductor (pero con tiempo)
        cont008 = Container.objects.get(container_id='CONT008')
        driver2 = Driver.objects.get(nombre='María González')
        Programacion.objects.get_or_create(
            container=cont008,
            defaults={
                'cd': cd_colina,
                'fecha_programada': now + timedelta(days=5),
                'cliente': 'Empresa DEF',
                'driver': driver2,
            }
        )
        
        self.stdout.write(self.style.SUCCESS(f'✓ {Programacion.objects.count()} programaciones creadas'))
        
        # Resumen
        self.stdout.write(self.style.SUCCESS('\n=== RESUMEN ==='))
        self.stdout.write(f'CDs: {CD.objects.count()} ({CD.objects.filter(tipo="ccti").count()} CCTIs, {CD.objects.filter(tipo="cliente").count()} Clientes)')
        self.stdout.write(f'Conductores: {Driver.objects.count()} ({Driver.objects.filter(presente=True, activo=True).count()} disponibles)')
        self.stdout.write(f'Contenedores: {Container.objects.count()}')
        self.stdout.write(f'  - Por arribar: {Container.objects.filter(estado="por_arribar").count()}')
        self.stdout.write(f'  - Liberados: {Container.objects.filter(estado="liberado").count()}')
        self.stdout.write(f'  - Programados: {Container.objects.filter(estado="programado").count()}')
        self.stdout.write(f'  - Asignados: {Container.objects.filter(estado="asignado").count()}')
        self.stdout.write(f'Programaciones: {Programacion.objects.count()}')
        self.stdout.write(f'  - Con alerta: {Programacion.objects.filter(requiere_alerta=True).count()}')
        self.stdout.write(f'  - Sin conductor: {Programacion.objects.filter(driver__isnull=True).count()}')
        
        self.stdout.write(self.style.SUCCESS('\n✓ Datos de prueba cargados exitosamente!'))
