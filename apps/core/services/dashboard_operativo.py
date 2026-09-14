"""
Servicio del Dashboard Operativo.
Unifica en un solo contrato lo que el operador necesita al abrir el panel:

- programadas_hoy / programadas_manana : contenedores programados del día y del siguiente.
- sin_asignar                        : programaciones pendientes SIN conductor.
- riesgo_ml                          : programaciones cuyo conductor asignado, según
                                       el perfil ML (factor típico del conductor en el
                                       histórico), probablemente NO cumpla el horario;
                                       se proponen alternativas ordenadas con la MISMA
                                       información (factor ML + cumplimiento + ocupación).
- vacios                             : contenedores vacíos (vacio / vacio_en_ruta) con
                                       su posición física.

Todos los nombres de campos son la fuente de verdad del frontend (executive_dashboard.html).
"""
from __future__ import annotations

from datetime import timedelta

from django.utils import timezone

from apps.containers.models import Container
from apps.drivers.models import Driver
from apps.programaciones.models import Programacion
from apps.core.services.learning_engine import OperationalLearningEngine

# Umbral de factor ML: >= 1.12 => conductor históricamente más lento que la referencia.
FACTOR_RIESGO_ML = 1.12
# Cuántas alternativas proponer por programación en riesgo.
MAX_ALTERNATIVAS = 3

ESTADOS_CONTAINER_ACTIVOS = [
    'programado', 'secuenciado', 'asignado', 'en_ruta',
    'entregado', 'soltado', 'descargado',
]


# --------------------------------------------------------------------------- #
# Helpers de serialización (un solo lugar para que el frontend no se bifurque)
# --------------------------------------------------------------------------- #
def _programacion_item(prog: Programacion) -> dict:
    return {
        'id': prog.id,
        'container_id': prog.container.container_id if prog.container else None,
        'container_id_formatted': prog.container.container_id_formatted if prog.container else None,
        'cliente': prog.cliente,
        'cd': prog.cd.nombre if prog.cd else None,
        'fecha_programada': prog.fecha_programada.isoformat() if prog.fecha_programada else None,
        'driver_id': prog.driver_id,
        'driver_nombre': prog.driver.nombre if prog.driver else None,
        'estado': prog.container.estado if prog.container else None,
        'eta_minutos': prog.eta_minutos,
    }


def _perfil_conductor(driver) -> dict | None:
    """Perfil ML del conductor (factor/label/confianza) con fallback seguro."""
    if not driver:
        return None
    try:
        perfil = OperationalLearningEngine.driver_profile(driver)
    except Exception:
        perfil = {
            'samples': 0, 'factor': 1.0,
            'label': 'sin_datos_suficientes', 'confidence': 0.0,
        }
    return {
        'factor_ml': perfil.get('factor', 1.0),
        'label_ml': perfil.get('label', 'sin_datos_suficientes'),
        'confianza_ml': perfil.get('confidence', 0.0),
        'samples_ml': perfil.get('samples', 0),
    }


def _alternativas_driver(prog: Programacion, excluir_driver_id=None) -> list[dict]:
    """
    Ordena conductores disponibles usando la MISMA información que el riesgo ML:
    factor propio del histórico (menor = más rápido), cumplimiento y ocupación.
    """
    candidatos = Driver.objects.filter(
        activo=True,
        presente=True,
    ).exclude(id=excluir_driver_id)

    ranking = []
    for driver in candidatos:
        perfil = _perfil_conductor(driver)
        # Ocupación: entregas del día / máximo permitido (0.0 si no hay máximo).
        if driver.max_entregas_dia:
            ocupacion = float(driver.num_entregas_dia) / float(driver.max_entregas_dia)
        else:
            ocupacion = 0.0
        ranking.append({
            'driver_id': driver.id,
            'driver_nombre': driver.nombre,
            'factor_ml': perfil['factor_ml'],
            'label_ml': perfil['label_ml'],
            'confianza_ml': perfil['confianza_ml'],
            'samples_ml': perfil['samples_ml'],
            'cumplimiento_porcentaje': float(driver.cumplimiento_porcentaje or 0),
            'ocupacion_porcentaje': round(ocupacion * 100, 1),
            'disponible': driver.esta_disponible,
        })

    # Menor factor ML primero; ante empate, mejor cumplimiento y menor ocupación.
    ranking.sort(key=lambda a: (
        a['factor_ml'],
        -a['cumplimiento_porcentaje'],
        a['ocupacion_porcentaje'],
    ))
    return ranking[:MAX_ALTERNATIVAS]


# --------------------------------------------------------------------------- #
# Secciones del dashboard
# --------------------------------------------------------------------------- #
def programadas_por_fecha(desde, hasta) -> list[dict]:
    """Programaciones activas cuya fecha cae entre [desde, hasta] (inclusive)."""
    qs = Programacion.objects.filter(
        fecha_programada__date__gte=desde,
        fecha_programada__date__lte=hasta,
        container__estado__in=ESTADOS_CONTAINER_ACTIVOS,
    ).select_related('container', 'driver', 'cd').order_by('fecha_programada')
    return [_programacion_item(p) for p in qs]


def sin_asignar(limit_horas=48) -> list[dict]:
    """Programaciones pendientes sin conductor, dentro de la ventana indicada."""
    limite = timezone.now() + timedelta(hours=limit_horas)
    qs = Programacion.objects.filter(
        driver__isnull=True,
        fecha_programada__lte=limite,
        container__estado__in=['programado', 'secuenciado'],
    ).select_related('container', 'cd').order_by('fecha_programada')
    items = []
    for prog in qs:
        horas = (prog.fecha_programada - timezone.now()).total_seconds() / 3600
        item = _programacion_item(prog)
        item['horas_restantes'] = round(horas, 1)
        item['prioridad'] = 'critica' if horas < 24 else 'alta'
        items.append(item)
    return items


def riesgo_ml(desde, hasta) -> list[dict]:
    """
    Programaciones hoy/mañana con conductor asignado cuyo perfil ML indica
    riesgo de no cumplir: factor del conductor >= FACTOR_RIESGO_ML
    (label 'más_lento_que_referencia').
    """
    qs = Programacion.objects.filter(
        fecha_programada__date__gte=desde,
        fecha_programada__date__lte=hasta,
        driver__isnull=False,
        container__estado__in=ESTADOS_CONTAINER_ACTIVOS,
    ).select_related('container', 'driver', 'cd').order_by('fecha_programada')

    en_riesgo = []
    for prog in qs:
        perfil = _perfil_conductor(prog.driver)
        if perfil['factor_ml'] < FACTOR_RIESGO_ML:
            continue  # Conductor cumple el umbral; no se reporta.
        item = _programacion_item(prog)
        item.update(perfil)
        item['motivo'] = (
            'Conductor histórico más lento que la referencia '
            f'(factor {perfil["factor_ml"]:.2f})'
        )
        item['alternativas'] = _alternativas_driver(prog, excluir_driver_id=prog.driver_id)
        en_riesgo.append(item)
    return en_riesgo


def vacios() -> list[dict]:
    """Contenedores vacíos (esperando retiro / en retorno) con su posición física."""
    qs = Container.objects.filter(
        estado__in=['vacio', 'vacio_en_ruta'],
    ).order_by('fecha_vacio')
    items = []
    for c in qs:
        items.append({
            'container_id': c.container_id,
            'container_id_formatted': c.container_id_formatted,
            'estado': c.estado,
            'posicion_fisica': c.posicion_fisica or 'Sin posición registrada',
            'cliente': c.cliente,
            'fecha_vacio': c.fecha_vacio.isoformat() if c.fecha_vacio else None,
            'fecha_vacio_ruta': c.fecha_vacio_ruta.isoformat() if c.fecha_vacio_ruta else None,
        })
    return items


def riesgo_encadenamiento(desde, hasta) -> list[dict]:
    """
    Riesgo de encadenamiento: para cada programación B (hoy/mañana) con conductor
    asignado, verifica la asignación ANTERIOR del mismo conductor (A) y calcula si
    la llegada estimada a B (fin de A + tiempo de viaje del tramo, vía Mapbox o
    cálculo haversine como fallback) supera su fecha_programada.
    Si llega tarde -> alerta con déficit en minutos y alternativas de cambio.
    """
    from math import asin, cos, radians, sin, sqrt

    # Caché por (origen, destino): evita llamadas repetidas a Mapbox en el bucle.
    _cache_tramo = {}

    def _haversine_km(lat1, lng1, lat2, lng2):
        R = 6371.0
        p1, p2 = radians(float(lat1)), radians(float(lat2))
        dp = radians(float(lat2) - float(lat1))
        dl = radians(float(lng2) - float(lng1))
        a = sin(dp/2)**2 + cos(p1)*cos(p2)*sin(dl/2)**2
        return 2 * R * asin(sqrt(a))

    def _tiempo_viaje_min(origen, destino):
        """Retorna (minutos, km, fuente). Mapbox primero; haversine como fallback."""
        try:
            from apps.core.services.mapbox import MapboxService
            ruta = MapboxService.calcular_ruta(
                float(origen[1]), float(origen[0]),
                float(destino[1]), float(destino[0]),
            )
            if ruta.get('success'):
                return (
                    float(ruta['duration_minutes']),
                    float(ruta.get('distance_km', 0)),
                    'mapbox',
                )
        except Exception:
            pass
        km = _haversine_km(origen[0], origen[1], destino[0], destino[1])
        # Velocidad urbana promedio de referencia (km/h) para el cálculo propio.
        velocidad_kmh = 35.0
        min_estim = km / velocidad_kmh * 60
        return round(min_estim, 1), round(km, 2), 'haversine'

    # Buffer operativo: carga/maniobra antes de partir a la siguiente entrega.
    BUFFER_MANIOBRA_MIN = 15.0

    qs = Programacion.objects.filter(
        fecha_programada__date__gte=desde,
        fecha_programada__date__lte=hasta,
        driver__isnull=False,
        container__estado__in=ESTADOS_CONTAINER_ACTIVOS,
    ).select_related('container', 'driver', 'cd').order_by('fecha_programada')

    en_riesgo = []
    for prog_b in qs:
        # Asignación inmediatamente anterior del mismo conductor (por fecha).
        anterior = Programacion.objects.filter(
            driver=prog_b.driver,
            fecha_programada__lt=prog_b.fecha_programada,
            container__estado__in=ESTADOS_CONTAINER_ACTIVOS,
        ).exclude(pk=prog_b.pk).order_by('-fecha_programada').select_related('cd', 'container').first()
        if not anterior or not anterior.cd:
            continue

        # Fin estimado de A: si está en ruta usamos fecha_inicio_ruta + ETA;
        # si no, fecha programada + ETA (o 60 min de referencia si no hay ETA).
        if anterior.estado == 'en_ruta' and anterior.fecha_inicio_ruta and anterior.eta_minutos:
            fin_a = anterior.fecha_inicio_ruta + timedelta(minutes=anterior.eta_minutos)
        elif anterior.fecha_programada:
            eta_a = anterior.eta_minutos or 60
            fin_a = anterior.fecha_programada + timedelta(minutes=eta_a)
        else:
            continue

        # Origen del tramo: CD de A (fin de la entrega anterior).
        origen = (float(anterior.cd.lat), float(anterior.cd.lng))
        # Destino del tramo: CD de B (punto donde debe estar para la 2ª entrega).
        destino = (float(prog_b.cd.lat), float(prog_b.cd.lng))

        clave_tramo = (origen, destino)
        viaje_min, km, fuente = _cache_tramo.get(
            clave_tramo, _tiempo_viaje_min(origen, destino)
        )
        _cache_tramo[clave_tramo] = (viaje_min, km, fuente)
        llegada_estimada = fin_a + timedelta(minutes=viaje_min + BUFFER_MANIOBRA_MIN)
        if timezone.is_naive(llegada_estimada):
            llegada_estimada = timezone.make_aware(llegada_estimada)
        if timezone.is_naive(prog_b.fecha_programada):
            prog_b.fecha_programada = timezone.make_aware(prog_b.fecha_programada)
        deficit = (llegada_estimada - prog_b.fecha_programada).total_seconds() / 60
        if deficit <= 0:
            continue  # Alcanza justo o sobra tiempo; no es riesgo.

        item = _programacion_item(prog_b)
        item.update({
            'asignacion_anterior_id': anterior.id,
            'contenedor_anterior': anterior.container.container_id_formatted if anterior.container else None,
            'fin_anterior_estimado': fin_a.isoformat(),
            'distancia_tramo_km': km,
            'viaje_tramo_min': round(viaje_min, 1),
            'fuente_tramo': fuente,
            'buffer_min': BUFFER_MANIOBRA_MIN,
            'llegada_estimada': llegada_estimada.isoformat(),
            'deficit_min': round(deficit, 1),
            'motivo': (
                f'Conductor termina {anterior.container.container_id_formatted or anterior.container.container_id} '
                f'aprox. {fin_a.strftime("%H:%M")}; tramo de {km} km ≈ {viaje_min:.0f} min '
                f'+ {BUFFER_MANIOBRA_MIN:.0f} min de maniobra'
                f' → llegaría {llegada_estimada.strftime("%H:%M")}, '
                f'{deficit:.0f} min después de la hora programada de esta entrega.'
            ),
        })
        item['alternativas'] = _alternativas_driver(prog_b, excluir_driver_id=prog_b.driver_id)
        en_riesgo.append(item)

    return en_riesgo


# --------------------------------------------------------------------------- #
# Orquestador único (fuente de verdad del endpoint /api/dashboard/operativo/)
# --------------------------------------------------------------------------- #
def construir_dashboard_operativo() -> dict:
    hoy = timezone.localdate()
    manana = hoy + timedelta(days=1)
    return {
        'success': True,
        'generado_en': timezone.now().isoformat(),
        'programadas_hoy': programadas_por_fecha(hoy, hoy),
        'programadas_manana': programadas_por_fecha(manana, manana),
        'sin_asignar': sin_asignar(),
        'riesgo_ml': riesgo_ml(hoy, manana),
        'riesgo_encadenamiento': riesgo_encadenamiento(hoy, manana),
        'vacios': vacios(),
    }