"""
Comando para generar datos de prueba completos para demostrar el TMS.
Crea un flujo realista con contenedores, asignaciones y alertas.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import timedelta
from decimal import Decimal
import random

from apps.containers.models import Container, Agency, ShippingLine, Vessel
from apps.drivers.models import Driver, Location, Assignment, TimeMatrix
from apps.core.models import Company, Vehicle

User = get_user_model()


class Command(BaseCommand):
    help = 'Genera datos de prueba completos para demostrar el TMS'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Elimina datos de prueba existentes antes de crear nuevos'
        )
        parser.add_argument(
            '--containers',
            type=int,
            default=20,
            help='Número de contenedores a crear (default: 20)'
        )
    
    def handle(self, *args, **options):
        reset = options.get('reset', False)
        num_containers = options.get('containers', 20)
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*70))
        self.stdout.write(self.style.SUCCESS('  🚀 GENERANDO DATOS DE PRUEBA - SOPTRALOC TMS'))
        self.stdout.write(self.style.SUCCESS('='*70 + '\n'))
        
        if reset:
            self.stdout.write('🗑️  Eliminando datos de prueba existentes...')
            Container.objects.filter(container_number__startswith='TEST').delete()
            self.stdout.write(self.style.SUCCESS('✅ Datos anteriores eliminados\n'))
        
        # 1. Verificar/Crear Empresas
        self.stdout.write('📦 Creando empresas...')
        company, _ = Company.objects.get_or_create(
            code='WALMART',
            defaults={
                'name': 'Walmart Chile',
                'rut': '76123456-7',
                'email': 'contacto@walmart.cl',
                'phone': '+56 2 2345 6789',
                'address': 'Santiago, Chile'
            }
        )
        self.stdout.write(f'  ✅ Empresa: {company.name}')
        
        # 2. Verificar/Crear Agency y ShippingLine
        self.stdout.write('\n🚢 Creando agencias y líneas navieras...')
        agency, _ = Agency.objects.get_or_create(
            code='AGUNSA',
            defaults={
                'name': 'Agencias Universales S.A.',
                'contact_info': 'info@agunsa.com'
            }
        )
        
        shipping_line, _ = ShippingLine.objects.get_or_create(
            code='MAERSK',
            defaults={
                'name': 'Maersk Line',
                'contact_info': 'info@maersk.com'
            }
        )
        
        try:
            vessel, _ = Vessel.objects.get_or_create(
                name='MAERSK ESSEX',
                defaults={
                    'imo_number': 'IMO9876543',
                    'shipping_line': shipping_line
                }
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating vessel: {e}'))
            # Create without shipping_line constraint
            vessel = Vessel.objects.create(
                name='MAERSK ESSEX',
                imo_number='IMO9876543',
                shipping_line=shipping_line
            )
        self.stdout.write(f'  ✅ Agencia: {agency.name}')
        self.stdout.write(f'  ✅ Línea: {shipping_line.name}')
        self.stdout.write(f'  ✅ Nave: {vessel.name}')
        
        # 3. Obtener ubicaciones
        self.stdout.write('\n📍 Verificando ubicaciones...')
        locations = list(Location.objects.all())
        if len(locations) < 2:
            self.stdout.write(self.style.WARNING('  ⚠️  Pocas ubicaciones. Ejecuta: python manage.py load_locations'))
            return
        
        terminals = [loc for loc in locations if 'CCTI' in loc.name or 'CLEP' in loc.name]
        cds = [loc for loc in locations if 'CD' in loc.name or 'Centro de Distribución' in loc.name]
        
        if not terminals:
            terminals = [locations[0]]
        if not cds:
            cds = [locations[-1]]
        
        self.stdout.write(f'  ✅ Terminales: {len(terminals)}')
        self.stdout.write(f'  ✅ Centros de Distribución: {len(cds)}')
        
        # 4. Crear Matriz de Tiempos
        self.stdout.write('\n⏱️  Creando matriz de tiempos...')
        time_matrix_count = 0
        for terminal in terminals:
            for cd in cds:
                if terminal != cd:
                    TimeMatrix.objects.get_or_create(
                        from_location=terminal,
                        to_location=cd,
                        defaults={
                            'travel_time': random.randint(45, 90),
                            'loading_time': random.randint(15, 30),
                            'unloading_time': random.randint(20, 40)
                        }
                    )
                    time_matrix_count += 1
        self.stdout.write(f'  ✅ Rutas configuradas: {time_matrix_count}')
        
        # 5. Obtener/Verificar Conductores
        self.stdout.write('\n🚗 Verificando conductores...')
        drivers = list(Driver.objects.filter(is_active=True))
        if len(drivers) < 3:
            self.stdout.write(self.style.WARNING('  ⚠️  Pocos conductores. Ejecuta: python manage.py load_drivers'))
        else:
            self.stdout.write(f'  ✅ Conductores disponibles: {len(drivers)}')
        
        # 6. Crear Contenedores con estados realistas
        self.stdout.write(f'\n📦 Creando {num_containers} contenedores de prueba...')
        
        container_types = ['40ft', '40hc', '20ft']
        now = timezone.now()
        
        # Distribuir estados de forma realista
        estados_distribucion = [
            ('LIBERADO', 5),
            ('PROGRAMADO', 8),
            ('ASIGNADO', 4),
            ('EN_RUTA', 2),
            ('ARRIBADO', 1),
        ]
        
        containers_created = []
        container_num = 1
        
        for estado, cantidad in estados_distribucion:
            if container_num > num_containers:
                break
                
            for i in range(min(cantidad, num_containers - container_num + 1)):
                container_number = f'TEST{container_num:04d}ABC'
                
                # Fechas realistas según estado
                if estado in ['LIBERADO', 'PROGRAMADO', 'ASIGNADO', 'EN_RUTA', 'ARRIBADO']:
                    eta = now.date() - timedelta(days=random.randint(5, 10))
                    release_date = now.date() - timedelta(days=random.randint(1, 3))
                    demurrage_date = release_date + timedelta(days=random.randint(7, 14))
                else:
                    eta = now.date() + timedelta(days=random.randint(2, 7))
                    release_date = None
                    demurrage_date = None
                
                terminal = random.choice(terminals) if terminals else locations[0]
                cd = random.choice(cds) if cds else locations[-1]
                
                try:
                    # Crear sin vessel primero, luego actualizar
                    container = Container.objects.create(
                        container_number=container_number,
                        container_type=random.choice(container_types),
                        status=estado,
                        owner_company=company,
                        client=company,
                        
                        # Datos de importación (SIN vessel por ahora)
                        port='Valparaíso',
                        eta=eta,
                        release_date=release_date,
                        demurrage_date=demurrage_date,
                        free_days=random.randint(5, 10),
                        
                        # Terminal y CD
                        terminal=terminal,
                        cd_location=cd.name,
                        current_location=terminal if estado in ['LIBERADO', 'PROGRAMADO'] else None,
                        
                        # Pesos
                        cargo_weight=Decimal(str(random.randint(15000, 25000))),
                        total_weight=Decimal(str(random.randint(17000, 27000))),
                        
                        # Agencia y línea
                        agency=agency,
                        shipping_line=shipping_line,
                        
                        # Tiempos según estado
                        scheduled_date=now.date() if estado in ['PROGRAMADO', 'ASIGNADO', 'EN_RUTA', 'ARRIBADO'] else None,
                        tiempo_asignacion=now - timedelta(hours=random.randint(1, 12)) if estado in ['ASIGNADO', 'EN_RUTA', 'ARRIBADO'] else None,
                        tiempo_inicio_ruta=now - timedelta(hours=random.randint(1, 6)) if estado in ['EN_RUTA', 'ARRIBADO'] else None,
                        tiempo_llegada=now - timedelta(hours=1) if estado == 'ARRIBADO' else None,
                        
                        # Observaciones
                        observation_1=f'Contenedor de prueba {container_num}',
                        cargo_description='Mercadería general - TEST',
                    )
                    
                    # Actualizar vessel después de crear
                    container.vessel = vessel
                    container.save()
                    
                    containers_created.append((container, estado))
                    self.stdout.write(f'  ✅ {container_number} [{estado}]')
                    
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'  ❌ Error creando {container_number}: {e}'))
                    import traceback
                    traceback.print_exc()
                
                container_num += 1
        
        # 7. Crear Asignaciones para contenedores ASIGNADOS y EN_RUTA
        self.stdout.write('\n👥 Creando asignaciones...')
        assignments_created = 0
        
        for container, estado in containers_created:
            if estado in ['ASIGNADO', 'EN_RUTA', 'ARRIBADO'] and drivers:
                driver = random.choice(drivers)
                
                # Asegurarse de que exista TimeMatrix
                time_matrix = TimeMatrix.objects.filter(
                    from_location=container.terminal,
                    to_location__name__icontains=container.cd_location.split()[0] if container.cd_location else ''
                ).first()
                
                if not time_matrix and cds:
                    time_matrix = TimeMatrix.objects.filter(
                        from_location=container.terminal
                    ).first()
                
                if time_matrix:
                    assignment_estado = 'EN_CURSO' if estado in ['EN_RUTA', 'ARRIBADO'] else 'PENDIENTE'
                    
                    # Convertir date a datetime con timezone
                    if container.scheduled_date:
                        fecha_prog = timezone.make_aware(
                            timezone.datetime.combine(container.scheduled_date, timezone.datetime.min.time())
                        )
                    else:
                        fecha_prog = now
                    
                    assignment = Assignment.objects.create(
                        container=container,
                        driver=driver,
                        fecha_programada=fecha_prog,
                        fecha_inicio=container.tiempo_inicio_ruta if estado in ['EN_RUTA', 'ARRIBADO'] else None,
                        estado=assignment_estado,
                        origen=container.terminal,
                        destino=time_matrix.to_location,
                        tipo_asignacion='ENTREGA',
                        tiempo_estimado=time_matrix.get_total_time()
                    )
                    
                    # Actualizar conductor
                    if estado == 'ASIGNADO':
                        container.conductor_asignado = driver
                        container.save(update_fields=['conductor_asignado'])
                    
                    assignments_created += 1
                    self.stdout.write(f'  ✅ {container.container_number} → {driver.nombre} [{assignment_estado}]')
        
        # Resumen
        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.SUCCESS('  📊 RESUMEN DE DATOS GENERADOS'))
        self.stdout.write('='*70)
        self.stdout.write(f'📦 Contenedores creados: {len(containers_created)}')
        self.stdout.write(f'👥 Asignaciones creadas: {assignments_created}')
        self.stdout.write(f'📍 Ubicaciones disponibles: {len(locations)}')
        self.stdout.write(f'🚗 Conductores disponibles: {len(drivers)}')
        self.stdout.write(f'⏱️  Rutas configuradas: {TimeMatrix.objects.count()}')
        
        # Estadísticas por estado
        self.stdout.write('\n📈 Distribución de Estados:')
        from django.db.models import Count
        status_counts = Container.objects.filter(container_number__startswith='TEST').values('status').annotate(count=Count('id'))
        for item in status_counts:
            self.stdout.write(f'  • {item["status"]}: {item["count"]}')
        
        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.SUCCESS('✅ DATOS DE PRUEBA GENERADOS EXITOSAMENTE'))
        self.stdout.write('='*70)
        self.stdout.write('\n💡 Próximos pasos:')
        self.stdout.write('  1. Acceder al admin: http://localhost:8000/admin/')
        self.stdout.write('  2. Ver contenedores en diferentes estados')
        self.stdout.write('  3. Probar asignación de conductores con: assign_driver API')
        self.stdout.write('  4. Simular flujo completo de entrega')
        self.stdout.write('\n')
