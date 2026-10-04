# ============================================================
# SIMULACIÓN GPS REALISTA + DECISIÓN DE ASIGNACIÓN — soptraloc prod
# Tiempos promedio documentados (misión punto 1):
#   - Velocidad urbana:     35 km/h (rango 30-40). Fuente: CONASET
#     (límite urbano 50, camiones operan ~30-40 real) + generadores repo (30-45).
#   - Autopista:            75 km/h (rango 70-80). Fuente: límite legal
#     camiones carretera 100 (rural) / autopistas urbanas ~80-100; operativo 70-80.
#   - Hora punta (7-10, 17-20): factor 0.55 sobre velocidad base (→ ~19-41 km/h).
#   - Noche (23-06):        factor 1.10 (poco tráfico).
#   - Fin de semana:        factor 1.00.
#   - Factor de ruta:       1.3 (desvíos/calles, igual que generators.py).
#   - Drop & hook:          45 min (rango 30-60) — CDs permite_soltar_contenedor.
#   - Descarga con espera:  CD.tiempo_promedio_descarga_min (30/60/90/120).
# ============================================================
import os, json, math, random, time, sys
from datetime import timedelta
from decimal import Decimal

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django; django.setup()

from django.utils import timezone
from django.db import transaction

from apps.programaciones.models import Programacion, TiempoViaje
from apps.containers.models import Container
from apps.drivers.models import Driver
from apps.cds.models import CD
from apps.core.services.operations import OperationalFlowService

LOG = "/tmp/sim/sim_run.log"
EVID = "/tmp/sim/evidencia.json"
logf = open(LOG, "a", encoding="utf-8")

def log(msg):
    line = f"[{timezone.now().isoformat(timespec='seconds')}] {msg}"
    print(line, flush=True)
    logf.write(line + "\n"); logf.flush()

def fail(msg):
    log(f"❌ ABORT: {msg}")
    sys.exit(1)

def haversine_km(lat1, lng1, lat2, lng2):
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1); dl = math.radians(lng2 - lng1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2 * R * math.asin(math.sqrt(a))

# ---------- velocidades según hora (Santiago, GMT-3) ----------
def factor_hora(dt):
    h = dt.hour
    if 7 <= h <= 10 or 17 <= h <= 20:
        return 0.55          # hora punta
    if h <= 6 or h >= 23:
        return 1.10          # noche/madrugada
    return 1.00

def velocidad_efectiva(dist_km, dt):
    base = 75.0 if dist_km > 25 else 35.0   # autopista si ruta larga, si no urbano
    return base * factor_hora(dt)

# ---------- coordenadas de partida (puertos) ----------
PUERTOS = {
    'TPS':  (-33.03, -71.63),
    'STI':  (-33.575, -71.61),
    'ZEAL': (-33.05, -71.63),
    'CLEP': (-33.60, -71.58),
}

EVIDENCIA = {"asignaciones": [], "arribos": [], "vehiculos": [], "problemas": []}

def get_or_create_demo_driver(nombre):
    d = Driver.objects.filter(nombre=nombre).first()
    if d is None:
        d = Driver.objects.create(nombre=nombre, activo=True, presente=True,
                                  capacidad_ton=Decimal('28.00'), max_entregas_dia=3)
    return d

def crear_demo_programacion(driver, cd, ref, container_id, tipo='40HC',
                            peso_kg=15000, viaje='VSIM01', cliente='SIM Demo Cliente'):
    """Crea container SIM-DEMO + programación con asignación explícita (patrón seed)."""
    if Programacion.objects.filter(container__referencia=ref).exists():
        return Programacion.objects.get(container__referencia=ref)
    cont = Container.objects.create(
        container_id=container_id, tipo=tipo, tipo_carga='dry', nave='SIM NAVE',
        viaje=viaje, booking='9000000001', fecha_eta=timezone.now() + timedelta(days=2),
        peso_carga=Decimal(str(peso_kg)), contenido='SIM contenido', vendor=cliente,
        sello='100001', puerto='TPS', referencia=ref, cliente=cliente,
        comuna='Santiago', posicion_fisica='TPS', tipo_movimiento='retiro_directo',
        estado='programado',
    )
    prog = Programacion.objects.create(
        container=cont, cd=cd, driver=driver, fecha_programada=timezone.now(),
        cliente=cliente, direccion_entrega=cd.direccion, urgencia_servicio='NORMAL',
        observaciones='SIM demo GPS', ventana_horaria_inicio=timezone.now(),
        ventana_horaria_fin=timezone.now() + timedelta(hours=12),
    )
    cont.cambiar_estado('asignado', usuario='system_sim_gps')
    return prog

# ============================================================
# PASO A: definir lote de simulación (SÓLO drivers asignados)
# ============================================================
PROGS_A_SIMULAR = []   # (prog, origen_lat, origen_lng, label)

def registrar_prog(pid, origen, label):
    prog = Programacion.objects.select_related('container', 'cd', 'driver').get(pk=pid)
    if not prog.driver:
        fail(f"Prog {pid} sin conductor asignado — regla: NADA se mueve sin asignación")
    PROGS_A_SIMULAR.append((prog, origen[0], origen[1], label))

# 3 programaciones SIM- ya asignadas (asignación del mundo simulado)
registrar_prog(10, PUERTOS['TPS'],  'SIM-000001 → Maipú Logística 04 (espera 60 min)')
registrar_prog(20, PUERTOS['STI'],  'SIM-000013 → Lampa Logística 06 (espera 90 min)')
registrar_prog(27, PUERTOS['ZEAL'], 'SIM-000020 → Quilicura Logística 01 (espera 120 min)')

# Lote demo nuevo: drop&hook (CDs permite_soltar_contenedor=True)
cd_bodega = CD.objects.get(pk=1)      # CD Bodega Norte, soltar=True, descarga 30
cd_patio  = CD.objects.get(pk=5)      # Patio Central, soltar=True, descarga 20
d_valentina = get_or_create_demo_driver('SIM Valentina Díaz')
d_javiera   = get_or_create_demo_driver('SIM Javiera Muñoz')
p_demo1 = crear_demo_programacion(d_valentina, cd_bodega, 'SIM-DEMO-0001', 'DEMU 900001-7', peso_kg=18000)
p_demo2 = crear_demo_programacion(d_javiera,   cd_patio,  'SIM-DEMO-0002', 'DEMU 900002-5', peso_kg=12000)
for prog, label in ((p_demo1, 'SIM-DEMO-0001 → Bodega Norte (drop&hook 45 min)'),
                    (p_demo2, 'SIM-DEMO-0002 → Patio Central (drop&hook 45 min)')):
    if not prog.driver:
        fail(f"{label}: sin conductor")
    PROGS_A_SIMULAR.append((prog, PUERTOS['TPS'][0], PUERTOS['TPS'][1], label))

log(f"=== LOTE DE SIMULACIÓN: {len(PROGS_A_SIMULAR)} vehículos (todos asignados) ===")
for prog, ori_lat, ori_lng, label in PROGS_A_SIMULAR:
    log(f"  prog={prog.id} {prog.container.referencia} driver={prog.driver.nombre} "
        f"cd={prog.cd.nombre if prog.cd else None} estado_container={prog.container.estado}")

# ============================================================
# PASO B: iniciar ruta (en_ruta) + GPS simulado hasta geocerca → arribo
# ============================================================
def iniciar_ruta(prog, ori_lat, ori_lng):
    if prog.container.estado != 'en_ruta':
        OperationalFlowService.iniciar_transito(prog.container, usuario='system_sim_gps')
    if not prog.fecha_inicio_ruta:
        prog.fecha_inicio_ruta = timezone.now()
        prog.gps_inicio_lat = Decimal(str(round(ori_lat, 6)))
        prog.gps_inicio_lng = Decimal(str(round(ori_lng, 6)))
        prog.save(update_fields=['fecha_inicio_ruta', 'gps_inicio_lat', 'gps_inicio_lng'])

def simular_viaje(prog, ori_lat, ori_lng, label, paso_km_aprox=2.2):
    cd = prog.cd
    # Origen = posición GPS actual del driver (telemetría real del sistema);
    # si aún no hay GPS, usa la posición base (puerto) proporcionada.
    d = prog.driver
    if d and d.ultima_posicion_lat and d.ultima_posicion_lng:
        lat0, lng0 = float(d.ultima_posicion_lat), float(d.ultima_posicion_lng)
    else:
        lat0, lng0 = ori_lat, ori_lng
    lat1, lng1 = float(cd.lat), float(cd.lng)
    dist_total = haversine_km(lat0, lng0, lat1, lng1) * 1.3
    now = timezone.now()
    vel = velocidad_efectiva(dist_total, now)
    vel_kmh = max(vel, 10)
    dur_min = dist_total / vel_kmh * 60
    n_pasos = max(5, int(dist_total / paso_km_aprox))
    log(f"  ▶ {label}: origen=({lat0:.5f},{lng0:.5f}) CD=({lat1:.5f},{lng1:.5f}) "
        f"dist≈{dist_total:.1f} km vel≈{vel_kmh:.0f} km/h dur≈{dur_min:.0f} min pasos={n_pasos}")

    iniciar_ruta(prog, lat0, lng0)
    driver = prog.driver

    for i in range(1, n_pasos + 1):
        t = i / n_pasos
        # interpolar loxodrómica simple lat/lng + jitter mínimo realista
        lat = lat0 + (lat1 - lat0) * t + random.uniform(-0.0004, 0.0004)
        lng = lng0 + (lng1 - lng0) * t + random.uniform(-0.0004, 0.0004)
        driver.actualizar_posicion(round(lat, 6), round(lng, 6))
        if cd.contiene_en_geocerca(lat, lng):
            log(f"  🎯 {label}: DENTRO de geocerca en paso {i} ({lat:.6f},{lng:.6f}) → registrar_arribo")
            return lat, lng, dur_min
        time.sleep(0.25)   # ritmo de telemetría realista sin alargar la demo

    # último punto: forzar dentro de geocerca (radio) para asegurar arribo
    lat, lng = lat1 + random.uniform(-0.0003, 0.0003), lng1 + random.uniform(-0.0003, 0.0003)
    driver.actualizar_posicion(round(lat, 6), round(lng, 6))
    if cd.contiene_en_geocerca(lat, lng):
        log(f"  🎯 {label}: dentro de geocerca (punto final) → registrar_arribo")
        return lat, lng, dur_min
    return lat, lng, dur_min

arribos = []
for prog, ori_lat, ori_lng, label in PROGS_A_SIMULAR:
    try:
        lat, lng, dur_min = simular_viaje(prog, ori_lat, ori_lng, label)
        locked, creado = OperationalFlowService.registrar_arribo(
            prog, Decimal(str(round(lat, 6))), Decimal(str(round(lng, 6))),
            origen='geocerca', usuario='system_sim_gps')
        prog.refresh_from_db()
        if not creado:
            log(f"  ⚠️ {label}: arribo ya existía (idempotente), se salta")
        arribos.append({
            'programacion_id': prog.id, 'referencia': prog.container.referencia,
            'conductor': prog.driver.nombre if prog.driver else None,
            'cd': prog.cd.nombre if prog.cd else None,
            'lat': float(locked.gps_arribo_lat), 'lng': float(locked.gps_arribo_lng),
            'fecha_arribo': locked.fecha_arribo_cd.isoformat() if locked.fecha_arribo_cd else None,
            'origen': locked.origen_arribo,
            'duracion_estimada_min': round(dur_min, 1),
            'estado_container': locked.container.estado,
        })
        log(f"  ✅ ARRIBO registrado: {prog.container.referencia} → {prog.cd.nombre} "
            f"@ ({locked.gps_arribo_lat},{locked.gps_arribo_lng}) "
            f"hora {locked.fecha_arribo_cd.astimezone().strftime('%H:%M')} estado={locked.container.estado}")
    except Exception as e:
        import traceback
        EVIDENCIA['problemas'].append({'programacion': prog.id, 'error': str(e)})
        log(f"  ❌ Error en {label}: {type(e).__name__}: {e}")
        traceback.print_exc(limit=3)

EVIDENCIA['arribos'] = arribos
log(f"Arribos por geocerca: {len(arribos)}")

# ============================================================
# PASO C: POST-ARRIBO — drop&hook o descarga con espera
# ============================================================
for prog, ori_lat, ori_lng, label in PROGS_A_SIMULAR:
    try:
        prog.refresh_from_db()
        c = prog.container
        if c.estado != 'entregado':
            log(f"  ⏭ {label}: container estado={c.estado} (post-arribo no aplica)")
            continue
        cd = prog.cd
        if cd.permite_soltar_contenedor:
            # Drop & hook: 45 min (rango 30-60)
            prog.fecha_inicio_descarga = timezone.now()
            prog.save(update_fields=['fecha_inicio_descarga'])
            drop = OperationalFlowService.drop_container(prog, usuario='system_sim_gps')
            # drop_container retorna (locked, created, retorno_programacion)
            locked_d, created_d, retorno = drop
            log(f"  🔗 DROP&HOOK: {c.referencia} → {cd.nombre} soltado={created_d} "
                f"retorno_auto={retorno.id if retorno else None}")
            time.sleep(1)
            # cierre de descarga tras tiempo_promedio_descarga_min (el sistema usa
            # el estimado del CD como tiempo real ante reloj comprimido)
            locked, timing, hecho = OperationalFlowService.complete_discharge(
                prog, usuario='system_sim_gps', source='geocerca_drop')
            log(f"  ✅ DESCARGA cerrada: {c.referencia} estado={locked.container.estado} "
                f"tiempo_real_min={timing.tiempo_real_min if timing else None}")
        else:
            # Espera sobre camión: descarga con CD.tiempo_promedio_descarga_min
            prog.fecha_inicio_descarga = timezone.now()
            prog.save(update_fields=['fecha_inicio_descarga'])
            time.sleep(1)
            locked, timing = OperationalFlowService.mark_empty(
                prog, usuario='system_sim_gps', source='geocerca_descarga')
            log(f"  ✅ MARCADO VACÍO: {c.referencia} estado={locked.container.estado} "
                f"tiempo_real_min={timing.tiempo_real_min if timing else None} "
                f"conductor_liberado={locked.driver_id is None}")
    except Exception as e:
        import traceback
        EVIDENCIA['problemas'].append({'programacion': prog.id, 'post_arribo': str(e)})
        log(f"  ❌ Post-arribo {label}: {type(e).__name__}: {e}")
        traceback.print_exc(limit=3)

# ============================================================
# PASO D: evidencias finales
# ============================================================
from apps.programaciones.models import RegistroOperacion
for prog, *_ in PROGS_A_SIMULAR:
    prog.refresh_from_db()
    EVIDENCIA['vehiculos'].append({
        'driver': prog.driver.nombre if prog.driver else None,
        'patente': prog.driver.patente if prog.driver else None,
        'lat': float(prog.driver.ultima_posicion_lat) if prog.driver and prog.driver.ultima_posicion_lat else None,
        'lng': float(prog.driver.ultima_posicion_lng) if prog.driver and prog.driver.ultima_posicion_lng else None,
        'ultima_act': prog.driver.ultima_actualizacion_posicion.isoformat() if prog.driver and prog.driver.ultima_actualizacion_posicion else None,
    })

with open(EVID, 'w', encoding='utf-8') as f:
    json.dump(EVIDENCIA, f, ensure_ascii=False, indent=2, default=str)
log(f"Evidencia guardada: {EVID}")
log("=== FIN SIMULACIÓN ===")