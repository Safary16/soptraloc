"""
Comando simple para crear datos de prueba rápidos - VERSION MINIMALISTA
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
import random

from apps.core.models import Company
from apps.containers.models import Container, Agency, ShippingLine, Vessel
from apps.drivers.models import Location


class Command(BaseCommand):
    help = 'Crea datos de prueba mínimos para testing rápido'

    def handle(self, *args, **options):
        self.stdout.write('🚀 Creando datos mínimos de prueba...\n')
        
        # 1. Obtener company existente
        company = Company.objects.first()
        if not company:
            self.stdout.write(self.style.ERROR('  ❌ No hay companies. Ejecuta: python manage.py generate_test_data'))
            return
        self.stdout.write(f'  ✅ Company: {company.name}')
        
        # 2. Obtener ubicaciones
        locations = list(Location.objects.all()[:2])
        if len(locations) < 2:
            self.stdout.write(self.style.ERROR('  ❌ Necesitas al menos 2 ubicaciones. Ejecuta: python manage.py load_locations'))
            return
        
        terminal = locations[0]
        self.stdout.write(f'  ✅ Terminal: {terminal.name}')
        
        # 3. Crear contenedores SIMPLES (sin vessel, sin agency, sin shipping_line)
        self.stdout.write('\n📦 Creando 5 contenedores básicos...')
        
        for i in range(1, 6):
            try:
                container_number = f'DEMO{i:04d}-TEST'
                container = Container.objects.create(
                    container_number=container_number,
                    container_type='40ft',
                    status='LIBERADO',
                    owner_company=company,
                    terminal=terminal,
                    cd_location=terminal.name,
                    cargo_weight=Decimal('18000'),
                    total_weight=Decimal('20000'),
                    free_days=7,
                    port='Valparaíso',
                    eta=timezone.now().date(),
                    cargo_description=f'Carga de prueba {i}',
                )
                self.stdout.write(f'  ✅ {container_number}')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ❌ Error: {e}'))
        
        # 4. Resumen
        total_containers = Container.objects.count()
        self.stdout.write(f'\n✅ COMPLETADO: {total_containers} contenedores en total')
