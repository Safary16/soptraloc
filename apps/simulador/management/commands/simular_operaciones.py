"""
SIMULAR OPERACIONES — Genera un mundo sintético completo para SoptraLoc.

Crea (o limpia) datos ficticios: CDs de cliente/patio, conductores con
RUT/patente válidos, depósitos, y hasta N contenedores recorriendo el ciclo
FSM completo con timestamps coherentes, programaciones, eventos,
TiempoOperacion y TiempoViaje con ruido realista (hora punta, habilidad del
conductor, día de semana). El objetivo: poblar el sistema sin datos reales y
alimentar el motor de aprendizaje con historia plausible.

Marcadores de datos sintéticos (para --limpiar):
  - CD.codigo   startswith 'SIM-'
  - Driver.nombre startswith 'SIM '
  - Deposit.name  startswith 'SIM-'
  - Container.referencia startswith 'SIM-'

Uso:
  python manage.py simular_operaciones --contenedores 150 --dias 90 --seed 42
  python manage.py simular_operaciones --limpiar
"""
import hashlib
import random
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.cds.models import CD
from apps.containers.models import Container, Deposit
from apps.drivers.models import Driver
from apps.events.models import Event
from apps.programaciones.models import Programacion, TiempoOperacion, TiempoViaje
from apps.simulador.generators import (
    CLIENTES, COMUNAS_RM, CONTENIDOS, DEPOSITOS, NAVES, PUERTOS,
    container_id, distancia_puerto_cd, patente_cl, rut_valido,
    tiempo_operacion_real, tiempo_viaje_real,
)

TIPOS_CONTENEDOR = ['20', '40', '40HC', '40HC', '40HC', '45']
TIPOS_CARGA_EXTRA = ['dry', 'dry', 'reefer']

# Perfiles de conductor: factor propio de rapidez (para que el ML aprenda
# que algunos son más rápidos que otros).
PERFILES_CONDUCTOR = [
    ('SIM Camilo Rojas', 0.85), ('SIM Valentina Díaz', 0.90),
    ('SIM Matías Soto', 0.95), ('SIM Fernanda Lagos', 1.00),
    ('SIM Nicolás Paredes', 1.05), ('SIM Javiera Muñoz', 1.10),
    ('SIM Cristóbal Vera', 0.88), ('SIM Antonia Fuentes', 1.15),
    ('SIM Benjamín Castro', 0.92), ('SIM Isidora Reyes', 1.08),
]


def _velocidad_media_kmh():
    """Velocidad media ciudad ~ 30-45 km/h, con hora punta más lenta."""
    return random.uniform(30, 45)


class Command(BaseCommand):
    help = 'Genera un mundo sintético (CDs, conductores, depósitos, contenedores) para probar y entrenar ML'

    def add_arguments(self, parser):
        parser.add_argument('--contenedores', type=int, default=100,
                            help='Cantidad de contenedores a simular (default 100)')
        parser.add_argument('--dias', type=int, default=90,
                            help='Profundidad histórica en días (default 90)')
        parser.add_argument('--seed', type=int, default=None,
                            help='Semilla para reproducibilidad')
        parser.add_argument('--limpiar', action='store_true',
                            help='Borra todo el mundo sintético generado antes')

    def _limpiar(self):
        self.stdout.write(self.style.WARNING('🧹 Limpiando datos sintéticos...'))
        containers = Container.objects.filter(referencia__startswith='SIM-')
        ids = list(containers.values_list('id', flat=True))
        TiempoOperacion.objects.filter(container_id__in=ids).delete()
        prog_ids = list(Programacion.objects.filter(container_id__in=ids).values_list('id', flat=True))
        TiempoViaje.objects.filter(programacion_id__in=prog_ids).delete()
        containers.delete()  # cascada: programaciones + eventos
        CD.objects.filter(codigo__startswith='SIM-').delete()
        # Drivers: los marcados como simulados (nombre 'SIM ...')
        Driver.objects.filter(nombre__startswith='SIM ').delete()
        Deposit.objects.filter(name__startswith='SIM-').delete()
        self.stdout.write(self.style.SUCCESS(f'   {len(ids)} contenedores + mundo borrados.'))

    def _crear_mundo(self, rng):
        """CDs de cliente y patios ficticios (códigos SIM-*)."""
        n_cds = 10
        for i in range(n_cds):
            comuna, lat, lng = COMUNAS_RM[i % len(COMUNAS_RM)]
            es_patio = rng.random() < 0.25
            CD.objects.get_or_create(
                codigo=f'SIM-CD{i+1:02d}',
                defaults={
                    'nombre': f'{comuna} Logística {i+1:02d}' if not es_patio else f'Patio {comuna} {i+1:02d}',
                    'direccion': f'Camino Industrial {i+1:02d}, {comuna}, Región Metropolitana',
                    'comuna': comuna,
                    'tipo': 'patio' if es_patio else 'cliente',
                    'lat': Decimal(str(round(lat + rng.uniform(-0.01, 0.01), 6))),
                    'lng': Decimal(str(round(lng + rng.uniform(-0.01, 0.01), 6))),
                    'requiere_espera_carga': not es_patio and rng.random() < 0.6,
                    'permite_soltar_contenedor': rng.random() < 0.3,
                    'tiempo_promedio_descarga_min': rng.choice([30, 45, 60, 90, 120]),
                    'capacidad_vacios': 150 if es_patio else 0,
                    'activo': True,
                },
            )
        self.stdout.write(self.style.SUCCESS('   🌍 Mundo: CDs ficticios listos.'))

    def _crear_conductores(self):
        for nombre, factor in PERFILES_CONDUCTOR:
            Driver.objects.get_or_create(
                telefono=f'SIM-{nombre.split()[1]}',
                defaults={
                    'nombre': nombre,
                    'rut': rut_valido(random),
                    'patente': patente_cl(random),
                    'presente': True,
                    'activo': True,
                    'excluir_ml': False,  # DEBE alimentar el ML
                    'capacidad_ton': Decimal('28.00'),
                    'cumplimiento_porcentaje': Decimal(str(round(rng_factor_to_cumplimiento(factor), 2))),
                    'max_entregas_dia': 3,
                    'total_entregas': random.randint(50, 400),
                    'entregas_a_tiempo': 0,
                },
            )
        self.stdout.write(self.style.SUCCESS('   🚚 Conductores ficticios listos.'))

    def _crear_depositos(self):
        for nombre in DEPOSITOS:
            Deposit.objects.get_or_create(name=f'SIM-{nombre}', defaults={'activo': True})
        self.stdout.write(self.style.SUCCESS('   🏭 Depósitos ficticios listos.'))

    def _crear_contenedor(self, rng, dias, drivers, cds, clientes, patios, count):
        """Simula un contenedor con ciclo FSM parcial o completo."""
        cliente = rng.choice(clientes)
        cd = rng.choice([c for c in cds if c.tipo == 'cliente'] or cds)
        puerto_nombre, puerto_lat, puerto_lng = rng.choice(PUERTOS)
        nave = rng.choice(NAVES)
        tipo = rng.choice(TIPOS_CONTENEDOR)
        contenido, tipo_carga = rng.choice(CONTENIDOS)
        if rng.random() < 0.2:
            tipo_carga = rng.choice(TIPOS_CARGA_EXTRA)

        referencia = f'SIM-{count:06d}'
        ahora = timezone.now()
        antiguedad = timedelta(days=rng.uniform(0, dias))
        eta = ahora - antiguedad
        # Algunos aún por arribar (operación viva)
        if rng.random() < 0.15:
            eta = ahora + timedelta(days=rng.uniform(0, 3))

        distancia = distancia_puerto_cd((puerto_nombre, puerto_lat, puerto_lng),
                                        cd.lat, cd.lng)

        cont = Container(
            container_id=container_id(rng),
            tipo=tipo, tipo_carga=tipo_carga,
            nave=nave, viaje=f'V{rng.randint(1000, 9999)}E',
            booking=f'{rng.randint(10**9, 10**10 - 1)}',
            fecha_eta=eta,
            peso_carga=Decimal(str(rng.randint(12000, 25000))),
            contenido=contenido,
            vendor=cliente, sello=f'{rng.randint(10**5, 10**6 - 1)}',
            puerto=puerto_nombre, referencia=referencia,
            cliente=cliente, comuna=cd.comuna,
            posicion_fisica=rng.choice(['TPS', 'STI', 'PCE', 'ZEAL', 'CLEP']),
            tipo_movimiento=rng.choice(['automatico', 'retiro_directo']),
            deposito_devolucion=Deposit.objects.filter(name__startswith='SIM-').first().name
            if Deposit.objects.filter(name__startswith='SIM-').exists() else '',
        )
        # Walk del FSM con timestamps coherentes
        # distribución de estados finales (historia + operación viva)
        roll = rng.random()
        driver = rng.choice(drivers) if drivers else None

        def _avanza(estado, delta_hrs_min, delta_hrs_max):
            nonlocal eta
            eta = eta + timedelta(hours=rng.uniform(delta_hrs_min, delta_hrs_max))
            return eta

        # Fase puerto
        fecha_arribo = _avanza('arribo', 0, 48)
        cont.estado = 'por_arribar'
        cont.fecha_arribo = fecha_arribo
        cont.save()
        Event.objects.create(container=cont, event_type='import_embarque',
                             detalles={'simulado': True}, usuario='simulador')

        if roll < 0.06:
            return cont  # queda por_arribar

        fecha_liberacion = _avanza('liberado', 6, 72)
        cont.estado, cont.fecha_liberacion = 'liberado', fecha_liberacion
        cont.save()
        Event.objects.create(container=cont, event_type='cambio_estado',
                             detalles={'estado_anterior': 'por_arribar', 'estado_nuevo': 'liberado'},
                             usuario='simulador')
        if roll < 0.12:
            return cont

        if rng.random() < 0.8:
            fecha_sec = _avanza('secuenciado', 0, 36)
            cont.estado, cont.fecha_secuenciado = 'secuenciado', fecha_sec
            cont.secuenciado = True
            cont.save()
        if roll < 0.20:
            return cont

        # Programación
        fecha_prog = _avanza('programado', 0, 72)
        cont.estado, cont.fecha_programacion = 'programado', fecha_prog
        cont.save()
        # calculo ETA de viaje (Mapbox-like por distancia)
        velocidad = _velocidad_media_kmh()
        mapbox_min = int(distancia / velocidad * 60)
        prog = Programacion.objects.create(
            container=cont, cd=cd, driver=None,
            fecha_programada=fecha_prog + timedelta(hours=rng.uniform(2, 24)),
            cliente=cliente,
            direccion_entrega=cd.direccion,
            urgencia_servicio=rng.choice(['NORMAL', 'NORMAL', 'URGENTE']),
            requiere_seguimiento_especial=rng.random() < 0.1,
            ventana_horaria_inicio=fecha_prog,
            ventana_horaria_fin=fecha_prog + timedelta(hours=6),
            eta_minutos=mapbox_min,
            distancia_km=Decimal(str(round(distancia, 2))),
            ruta_firma=hashlib.sha256(
                f'{puerto_nombre}|{cd.comuna}|{distancia:.1f}'.encode()).hexdigest()[:16],
        )
        Event.objects.create(container=cont, event_type='programacion_manual',
                             detalles={'simulado': True}, usuario='simulador')
        if roll < 0.32:
            return cont

        # Asignación
        if driver:
            fecha_asig = _avanza('asignado', 0, 24)
            prog.driver = driver
            prog.fecha_asignacion = fecha_asig
            prog.patente_confirmada = driver.patente
            prog.save()
            cont.estado, cont.fecha_asignacion = 'asignado', fecha_asig
            cont.save()
            Event.objects.create(container=cont, event_type='asignacion_conductor',
                                 detalles={'driver_id': driver.id, 'driver_nombre': driver.nombre},
                                 usuario='simulador')
        if roll < 0.42 and driver:
            return cont

        # En ruta (puerto → CD)
        if driver:
            fecha_salida = _avanza('en_ruta', 0, 12)
            cont.estado, cont.fecha_inicio_ruta = 'en_ruta', fecha_salida
            cont.save()
            prog.fecha_inicio_ruta = fecha_salida
            prog.gps_inicio_lat = Decimal(str(round(puerto_lat, 6)))
            prog.gps_inicio_lng = Decimal(str(round(puerto_lng, 6)))
            prog.save()
            # TiempoViaje 1: puerto → CD
            mapbox_min = max(15, int(distancia / _velocidad_media_kmh() * 60))
            perfil = next(p for p in PERFILES_CONDUCTOR if p[0] == driver.nombre)
            real = tiempo_viaje_real(mapbox_min, rng, perfil[1], fecha_salida, fecha_salida.weekday())
            TiempoViaje.objects.create(
                conductor=driver, programacion=prog,
                origen_lat=Decimal(str(round(puerto_lat, 7))),
                origen_lon=Decimal(str(round(puerto_lng, 7))),
                destino_lat=cd.lat, destino_lon=cd.lng,
                origen_nombre=puerto_nombre, destino_nombre=cd.comuna,
                distancia_km=Decimal(str(round(distancia, 2))),
                tiempo_mapbox_min=mapbox_min, tiempo_real_min=real,
                hora_salida=fecha_salida,
                hora_llegada=fecha_salida + timedelta(minutes=real),
                hora_del_dia=fecha_salida.hour,
                dia_semana=fecha_salida.weekday(),
                ruta_firma=prog.ruta_firma,
            )
            Event.objects.create(container=cont, event_type='inicio_ruta',
                                 detalles={'simulado': True}, usuario='simulador')
        if roll < 0.52 and driver:
            return cont

        # Llegada CD + descarga
        if driver:
            fecha_arribo_cd = prog.fecha_inicio_ruta + timedelta(minutes=real)
            cont.estado, cont.fecha_entrega = 'entregado', fecha_arribo_cd
            cont.cd_entrega = cd
            cont.save()
            prog.fecha_arribo_cd = fecha_arribo_cd
            prog.gps_arribo_lat = cd.lat
            prog.gps_arribo_lng = cd.lng
            prog.origen_arribo = 'geocerca' if rng.random() < 0.7 else 'manual'
            prog.save()
            Event.objects.create(container=cont, event_type='arribo_cd',
                                 detalles={'cd': cd.nombre}, usuario='simulador')

            # TiempoOperacion: descarga_cd
            estimado = cd.tiempo_promedio_descarga_min
            inicio_desc = fecha_arribo_cd + timedelta(minutes=rng.uniform(0, 40))
            real_op = tiempo_operacion_real(estimado, rng, perfil[1])
            TiempoOperacion.objects.create(
                cd=cd, conductor=driver, container=cont,
                tipo_operacion='descarga_cd',
                tiempo_estimado_min=estimado, tiempo_real_min=real_op,
                hora_inicio=inicio_desc, hora_fin=inicio_desc + timedelta(minutes=real_op),
                anomalia=real_op > 3 * estimado,
            )
            prog.fecha_inicio_descarga = inicio_desc
            prog.eta_estimado_cierre_min = mapbox_min + estimado
            prog.eta_real_cierre_min = real + real_op
            prog.estado_final = 'ENTREGADO' if rng.random() < 0.9 else 'FALLIDO'
            prog.fecha_liberacion_conductor = inicio_desc + timedelta(minutes=real_op)
            prog.save()
        if roll < 0.68 and driver:
            return cont

        # Vacío → retorno
        if driver:
            fecha_vacio = _avanza('vacio', 1, 96)
            cont.estado, cont.fecha_vacio = 'descargado', fecha_vacio
            cont.save()
            if rng.random() < 0.5:
                cont.estado = 'vacio'
                cont.save()
                Event.objects.create(container=cont, event_type='contenedor_vacio',
                                     detalles={'simulado': True}, usuario='simulador')
            if roll < 0.82:
                return cont

            # Retorno: depósito o patio
            fecha_ret = _avanza('vacio_en_ruta', 1, 48)
            cont.estado, cont.fecha_vacio_ruta = 'vacio_en_ruta', fecha_ret
            cont.save()
            if rng.random() < 0.5 and patios:
                patio = rng.choice(patios)
                if patio.puede_recibir_vacios:
                    cont.retorno_destino_tipo = 'patio'
                    cont.retorno_destino_cd = patio
                    cont.estado, cont.fecha_en_patio = 'en_patio', fecha_ret + timedelta(hours=rng.uniform(1, 8))
                    patio.recibir_vacio()
                    cont.vacio_contabilizado = True
                    cont.save()
                    Event.objects.create(container=cont, event_type='devolucion_vacio',
                                         detalles={'destino': 'patio'}, usuario='simulador')
                    return cont
            # depósito
            deposito = Deposit.objects.filter(name__startswith='SIM-').first()
            cont.deposito_devolucion = deposito.name if deposito else ''
            cont.estado, cont.fecha_devolucion = 'devuelto', fecha_ret + timedelta(hours=rng.uniform(1, 10))
            cont.save()
            Event.objects.create(container=cont, event_type='devolucion_vacio',
                                 detalles={'destino': 'deposito'}, usuario='simulador')
        return cont

    def handle(self, *args, **options):
        if options['limpiar']:
            self._limpiar()
            return

        seed = options['seed'] or random.randint(0, 99999)
        rng = random.Random(seed)
        self.stdout.write(self.style.SUCCESS(f'🎲 Semilla: {seed}'))

        self._crear_mundo(rng)
        self._crear_conductores()
        self._crear_depositos()

        drivers = list(Driver.objects.filter(nombre__startswith='SIM '))
        cds = list(CD.objects.filter(codigo__startswith='SIM-'))
        patios = [c for c in cds if c.tipo == 'patio']

        n = options['contenedores']
        # Repoblar perfiles con entregas a tiempo coherentes tras crear drivers
        for d in drivers:
            cumpl = Decimal(d.cumplimiento_porcentaje)
            tot = d.total_entregas or 50
            d.entregas_a_tiempo = int(tot * float(cumpl) / 100)
            d.save(update_fields=['entregas_a_tiempo'])

        creados = 0
        for i in range(n):
            self._crear_contenedor(rng, options['dias'], drivers, cds, CLIENTES, patios, i + 1)
            creados += 1

        self.stdout.write(self.style.SUCCESS(
            f'\n✅ Mundo simulado listo: {creados} contenedores, {len(drivers)} conductores, '
            f'{len(cds)} CDs, {len(patios)} patios.'
        ))
        self.stdout.write(self.style.SUCCESS(
            f'   📊 TiempoOperacion: {TiempoOperacion.objects.count()} | '
            f'TiempoViaje: {TiempoViaje.objects.count()} | '
            f'Programaciones: {Programacion.objects.count()} | '
            f'Eventos: {Event.objects.count()}'
        ))


def rng_factor_to_cumplimiento(factor: float) -> float:
    """Un conductor más rápido (factor bajo) tiende a mayor cumplimiento."""
    return max(70.0, min(99.5, 100.0 - (factor - 0.9) * 30 + random.uniform(-5, 5)))