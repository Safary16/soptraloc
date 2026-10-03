"""
Generadores de datos sintéticos para SoptraLoc.

Solo nombres ficticios, catálogos genéricos y algoritmos estándar
(ISO 6346, RUT chileno, patentes CL). Sin ninguna referencia a
clientes, proveedores ni operaciones reales.
"""
import random
from math import asin, cos, radians, sin, sqrt

# ---------------------------------------------------------------- ISO 6346
_ISO_LETTER_VALUES = {
    'A': 10, 'B': 12, 'C': 13, 'D': 14, 'E': 15, 'F': 16, 'G': 17, 'H': 18,
    'I': 19, 'J': 20, 'K': 21, 'L': 23, 'M': 24, 'N': 25, 'O': 26, 'P': 27,
    'Q': 28, 'R': 29, 'S': 30, 'T': 31, 'U': 32, 'V': 34, 'W': 35, 'X': 36,
    'Y': 37, 'Z': 38,
}
_ISO_WEIGHTS = [1, 2, 4, 8, 16, 32, 64, 128, 256, 512]

# Prefijos de propietario FICTICIOS (3 letras + U). Reservados para simulación.
OWNER_CODES = ['SOPU', 'ANRU', 'TRSU', 'LOGU', 'PACU', 'NOVU', 'CORD', 'AUSU']


def iso6346_check_digit(owner: str, serial: str) -> str:
    """Calcula el dígito verificador ISO 6346 (10 chars: 4 letras + 6 dígitos).

    owner: 4 letras (ej 'SOPU'); serial: 6 dígitos (ej '123456').
    """
    if len(owner) != 4 or not owner.isalpha():
        raise ValueError(f'Owner inválido: {owner!r}')
    if len(serial) != 6 or not serial.isdigit():
        raise ValueError(f'Serial inválido: {serial!r}')
    total = 0
    for i, ch in enumerate(owner.upper()):
        total += _ISO_LETTER_VALUES[ch] * _ISO_WEIGHTS[i]
    for i, ch in enumerate(serial):
        total += int(ch) * _ISO_WEIGHTS[4 + i]
    resto = total % 11
    # ISO 6346: remanente 10 → dígito 0
    return '0' if resto == 10 else str(resto)


def container_id(rng: random.Random) -> str:
    """Genera un container_id ISO 6346 válido, ej: 'SOPU 123456-7'."""
    owner = rng.choice(OWNER_CODES)
    serial = f'{rng.randint(0, 999999):06d}'
    return f'{owner} {serial}-{iso6346_check_digit(owner, serial)}'


# ------------------------------------------------------------------- RUT
def rut_valido(rng: random.Random) -> str:
    """Genera un RUT chileno con dígito verificador correcto."""
    cuerpo = rng.randint(1000000, 24999999)
    n = cuerpo
    serie = [2, 3, 4, 5, 6, 7, 2, 3]
    suma = 0
    for factor in serie:
        suma += (n % 10) * factor
        n //= 10
    resto = suma % 11
    dv = 11 - resto
    if dv == 11:
        dv = 0
    elif dv == 10:
        dv = 'K'
    return f'{cuerpo:,}'.replace(',', '.') + f'-{dv}'


def patente_cl(rng: random.Random) -> str:
    """Patente chilena: formato antiguo BBBB11 o nuevo BB·BB11."""
    consonantes = 'BCDFGHJKLMNPRSTVWXYZ'
    if rng.random() < 0.5:
        letras = ''.join(rng.choice(consonantes) for _ in range(4))
        return letras + f'{rng.randint(10, 99)}'
    # Formato nuevo: 2 letras · 2 letras · 2 dígitos
    return (rng.choice(consonantes) + rng.choice('AEIOU') + '·'
            + rng.choice(consonantes) + rng.choice('AEIOU') + f'{rng.randint(10, 99)}')


# ------------------------------------------------------------- Catálogos
CLIENTES = [
    'Comercial Los Aromos', 'Distribuidora Andina', 'Importadora Pacífico',
    'Supermercados del Valle', 'Ferretería Industrial Norte', 'Agro Bío Bío',
    'Textil Cordillera', 'Minera Austral', 'Construcciones del Maule',
    'Química Central', 'Papelera del Sur', 'Alimentos Coquimbo',
]

COMUNAS_RM = [
    ('Quilicura', -33.3671, -70.7295),
    ('Pudahuel', -33.4343, -70.7443),
    ('San Bernardo', -33.5922, -70.6994),
    ('Maipú', -33.5104, -70.7595),
    ('Colina', -33.2021, -70.6730),
    ('Lampa', -33.2860, -70.8759),
    ('Padre Hurtado', -33.5750, -70.7930),
    ('Melipilla', -33.6850, -71.2150),
    ('Talagante', -33.6640, -70.9300),
    ('Renca', -33.4040, -70.7260),
    ('Cerrillos', -33.5000, -70.7100),
    ('Buin', -33.7320, -70.7430),
]

PUERTOS = [
    ('Valparaíso', -33.0458, -71.6197),
    ('San Antonio', -33.5938, -71.6074),
]

NAVES = [
    'Pacific Star', 'Andes Pride', 'Cóndor Express', 'Meridian Bay',
    'Austral Sky', 'Salar Uno', 'Vicuña Austral', 'Tricahue',
]

DEPOSITOS = [
    'Depósito Central Pacífico', 'Terminal Andino', 'Depósito del Valle',
    'Patio Sur Logístico', 'Depósito Norte Verde', 'Terminal Austral',
]

CONTENIDOS = [
    ('textiles', 'dry'), ('electrónica', 'dry'), ('alimentos', 'reefer'),
    ('papel', 'dry'), ('vino embotellado', 'dry'), ('repuestos automotrices', 'dry'),
    ('plásticos', 'dry'), ('fruta congelada', 'reefer'), ('madera', 'open_top'),
    ('maquinaria', 'flat_rack'),
]

TIPOS_PESO = {
    '20': (18000, 24000), '40': (22000, 28000), '40HC': (22000, 28000), '45': (20000, 26000),
}


# -------------------------------------------------------------- Geografía
def haversine_km(lat1, lon1, lat2, lon2) -> float:
    R = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * R * asin(sqrt(a))


def distancia_puerto_cd(puerto_coords, cd_lat, cd_lng, factor=None) -> float:
    """Distancia aproximada puerto→CD. factor de ruta opcional (1.3 aprox.)."""
    base = haversine_km(puerto_coords[1], puerto_coords[2], float(cd_lat), float(cd_lng))
    return base * (factor if factor else 1.3)


# -------------------------------------------------------------- Perfiles
def tiempo_viaje_real(mapbox_min: int, rng: random.Random, driver_factor: float = 1.0,
                      hora_salida=None, dia_semana=None) -> int:
    """Simula un tiempo de viaje real a partir del estimado Mapbox.

    Factores: habilidad del conductor (fijo por conductor), hora punta,
    fin de semana y ruido gaussiano. Genera correlación realista para que
    el motor de aprendizaje encuentre patrones.
    """
    factor = driver_factor
    if hora_salida is not None:
        h = hora_salida.hour
        if 7 <= h <= 9 or 18 <= h <= 20:
            factor *= rng.uniform(1.15, 1.35)  # hora punta
        elif h <= 5 or h >= 23:
            factor *= rng.uniform(0.85, 0.95)  # madrugada
    if dia_semana is not None:
        if dia_semana >= 5:  # fin de semana
            factor *= rng.uniform(0.9, 1.0)
    factor *= rng.gauss(1.0, 0.08)
    return max(5, round(mapbox_min * factor))


def tiempo_operacion_real(estimado_min: int, rng: random.Random,
                          driver_factor: float = 1.0) -> int:
    """Simula la duración real de una operación (descarga/carga)."""
    factor = driver_factor * rng.gauss(1.0, 0.12)
    return max(5, round(estimado_min * factor))