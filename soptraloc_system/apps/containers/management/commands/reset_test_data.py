"""
Management command para resetear datos de testing.
Mantiene solo una cantidad limitada de contenedore        # Crear cliente demo si no existe
        cliente_demo, created = Company.objects.get_or_create(
            code='CLIENTEDEMO',
            defaults={
                'name': 'Cliente Demo',
                'rut': '12345678-9',
                'email': 'cliente@example.com',pruebas.
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.containers.models import Container, Vessel, ShippingLine, Agency
from apps.core.models import Company
from datetime import datetime, timedelta
from django.utils import timezone


class Command(BaseCommand):
    help = 'Resetea datos de testing manteniendo solo contenedores de prueba'

    def add_arguments(self, parser):
        parser.add_argument(
            '--keep-containers',
            type=int,
            default=20,
            help='Número de contenedores a mantener (default: 20)'
        )
        parser.add_argument(
            '--delete-all',
            action='store_true',
            help='Eliminar todos los contenedores'
        )

    @transaction.atomic
    def handle(self, *args, **options):
        keep_containers = options['keep_containers']
        delete_all = options['delete_all']
        
        self.stdout.write(self.style.WARNING('Iniciando reset de datos de testing...'))
        
        # Contar contenedores actuales
        total_containers = Container.objects.count()
        self.stdout.write(f'Contenedores actuales: {total_containers}')
        
        if delete_all:
            # Eliminar todos los contenedores
            deleted_count, _ = Container.objects.all().delete()
            self.stdout.write(self.style.SUCCESS(f'✓ Eliminados {deleted_count} contenedores'))
            
        else:
            # Mantener solo los más recientes
            containers_to_keep = Container.objects.order_by('-created_at')[:keep_containers]
            keep_ids = list(containers_to_keep.values_list('id', flat=True))
            
            containers_to_delete = Container.objects.exclude(id__in=keep_ids)
            deleted_count = containers_to_delete.count()
            
            if deleted_count > 0:
                containers_to_delete.delete()
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Eliminados {deleted_count} contenedores')
                )
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Mantenidos {keep_containers} contenedores más recientes')
                )
            else:
                self.stdout.write(self.style.WARNING('No hay contenedores para eliminar'))
        
        # Crear datos básicos si no existen
        self._create_basic_data()
        
        self.stdout.write(self.style.SUCCESS('\n✓ Reset de datos completado exitosamente'))
        self.stdout.write(f'Contenedores totales: {Container.objects.count()}')

    def _create_basic_data(self):
        """Crear datos básicos necesarios para el sistema"""
        
        # Crear línea naviera de prueba
        shipping_line, created = ShippingLine.objects.get_or_create(
            code='APL',
            defaults={
                'name': 'American President Lines',
                'contact_info': 'info@apl.com'
            }
        )
        if created:
            self.stdout.write('✓ Creada línea naviera APL')
        
        # Crear nave de prueba
        vessel, created = Vessel.objects.get_or_create(
            name='APL CHARLESTON',
            defaults={
                'shipping_line': shipping_line,
                'imo_number': 'IMO1234567'
            }
        )
        if created:
            self.stdout.write('✓ Creada nave APL CHARLESTON')
        
        # Crear agencia de prueba
        agency, created = Agency.objects.get_or_create(
            code='SERRANO',
            defaults={
                'name': 'Agencia Serrano',
                'contact_info': 'contacto@serrano.cl'
            }
        )
        if created:
            self.stdout.write('✓ Creada agencia SERRANO')
        
        # Crear cliente Walmart si no existe
        walmart, created = Company.objects.get_or_create(
            code='WALMART',
            defaults={
                'name': 'Walmart Chile',
                'rut': '76000000-0',
                'email': 'walmart@example.com',
                'phone': '+56912345678',
                'address': 'Santiago, Chile'
            }
        )
        if created:
            self.stdout.write('✓ Creado cliente demo')
        else:
            self.stdout.write('✓ Cliente demo ya existe')
