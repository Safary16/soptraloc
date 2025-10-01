"""
Management command para resetear contenedores a estado inicial POR_ARRIBAR.
Limpia todos los datos operativos para empezar el flujo desde cero.
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.containers.models import Container
from apps.drivers.models import Driver


class Command(BaseCommand):
    help = 'Resetea todos los contenedores a estado inicial POR_ARRIBAR para testing del flujo completo'

    def add_arguments(self, parser):
        parser.add_argument(
            '--keep',
            type=int,
            default=10,
            help='Número de contenedores a mantener (default: 10)'
        )

    @transaction.atomic
    def handle(self, *args, **options):
        keep_count = options['keep']
        
        self.stdout.write(self.style.WARNING('🔄 Iniciando reset a estado inicial...'))
        
        # Obtener contenedores más recientes
        containers = Container.objects.order_by('-created_at')[:keep_count]
        keep_ids = list(containers.values_list('id', flat=True))
        
        # Eliminar contenedores antiguos
        deleted_count, _ = Container.objects.exclude(id__in=keep_ids).delete()
        if deleted_count > 0:
            self.stdout.write(f'🗑️  Eliminados {deleted_count} contenedores antiguos')
        
        # Liberar todos los conductores
        Driver.objects.filter(contenedor_asignado__isnull=False).update(
            contenedor_asignado=None,
            estado='OPERATIVO'
        )
        self.stdout.write('✓ Conductores liberados')
        
        # Resetear contenedores a estado inicial
        reset_count = 0
        for container in Container.objects.all():
            # Limpiar campos operativos
            container.status = 'POR_ARRIBAR'
            container.current_position = 'EN_PISO'
            container.conductor_asignado = None
            
            # Limpiar fechas de liberación y programación
            container.release_date = None
            container.release_time = None
            container.scheduled_date = None
            container.scheduled_time = None
            container.cd_arrival_date = None
            container.cd_arrival_time = None
            container.discharge_date = None
            container.discharge_time = None
            container.return_date = None
            container.has_eir = False
            
            # Limpiar tiempos operativos
            container.tiempo_asignacion = None
            container.tiempo_inicio_ruta = None
            container.tiempo_llegada = None
            container.tiempo_descarga = None
            container.tiempo_finalizacion = None
            container.duracion_ruta = None
            container.duracion_descarga = None
            container.duracion_total = None
            
            # Limpiar posición
            container.position_updated_at = None
            
            container.save()
            reset_count += 1
            
        self.stdout.write(self.style.SUCCESS(f'✅ {reset_count} contenedores reseteados a POR_ARRIBAR'))
        self.stdout.write(self.style.SUCCESS('🎯 Sistema listo para testing del flujo completo desde cero'))
        
        # Mostrar resumen
        self.stdout.write('\n📊 Estado actual:')
        self.stdout.write(f'   Contenedores: {Container.objects.count()}')
        self.stdout.write(f'   Estado: POR_ARRIBAR (listos en nave, sin liberar)')
        self.stdout.write(f'   Conductores disponibles: {Driver.objects.filter(is_active=True).count()}')
        self.stdout.write('\n💡 Próximos pasos del flujo:')
        self.stdout.write('   1️⃣  Subir horarios de liberación → LIBERADO')
        self.stdout.write('   2️⃣  Exportar liberados para cliente')
        self.stdout.write('   3️⃣  Subir programación del cliente → PROGRAMADO')
        self.stdout.write('   4️⃣  Asignar conductores → ASIGNADO')
        self.stdout.write('   5️⃣  Iniciar rutas → EN_RUTA')
        self.stdout.write('   6️⃣  Marcar arribos → ARRIBADO')
        self.stdout.write('   7️⃣  Finalizar operación → FINALIZADO')
