"""
Utilidades de normalización de nombres de cliente.

Regla: un cliente solo puede existir en UNA forma canónica (title case),
así "EASY" / "easy" / "WalMart" / "walmart" colapsan a "Walmart",
"LA DIVISA" a "La Divisa", etc. Aplicar SIEMPRE al escribir `cliente`
(importadores y vistas) y al filtrar por cliente (`?cliente=`).
"""

# Conectores que van en minúscula salvo en la primera palabra.
_CONECTORES = {
    'de', 'del', 'la', 'las', 'los', 'y', 'e', 'o', 'a', 'al',
    'para', 'por', 'en', 'con', 'el', 'un', 'una', 'su', 'sus',
}

# Siglas/marcas que se conservan en mayúsculas tal cual.
_SIGLAS = {
    'CCTI', 'SAI', 'SA', 'S.A.', 'S.A', 'LTDA', 'Ltda.', 'EIRL',
    'SPA', 'S.P.A.', 'USA', 'EU', 'CNC', 'DPD', 'BCO',
    # Agencias de aduana (siempre en mayúsculas, no son clientes)
    'BROWNE',
}

# Aliases/typos comunes → forma canónica (antes del title case genérico).
_ALIASES = {
    # Walmart
    'walmart': 'Walmart', 'wallmart': 'Walmart', 'walmaart': 'Walmart', 'wal mart': 'Walmart',
    'wal-mart': 'Walmart', 'walm': 'Walmart',
    # Easy
    'easy': 'Easy', 'ezy': 'Easy', 'easi': 'Easy',
    # La Divisa
    'la divisa': 'La Divisa', 'ladivisa': 'La Divisa', 'la divissa': 'La Divisa',
    # Cencosud / Jumbo / Santa Isabel
    'cencosud': 'Cencosud', 'jumbo': 'Jumbo', 'santa isabel': 'Santa Isabel',
    # SAI / logística
    'sai': 'SAI', 'san antonio intl': 'SAI',
    # Líneas
    'maersk': 'Maersk', 'maersk line': 'Maersk Line', 'msk': 'Maersk',
    'hamburg sud': 'Hamburg Süd', 'hamburgsud': 'Hamburg Süd',
    'ccti': 'CCTI', 'cct': 'CCTI',
}


def normalizar_cliente(valor) -> str:
    """Devuelve la forma canónica del nombre de cliente.

    - Colapsa espacios múltiples y recorta extremos.
    - Aliases/typos conocidos se resuelven a su forma canónica.
    - Title case por palabra (conectores en minúscula salvo la primera).
    - Siglas conocidas preservadas en mayúsculas.
    """
    if valor is None:
        return ''
    texto = ' '.join(str(valor).split())  # colapsa espacios
    if not texto:
        return ''
    clave = texto.lower()
    if clave in _ALIASES:
        return _ALIASES[clave]
    palabras = texto.split(' ')
    resultado = []
    for i, palabra in enumerate(palabras):
        # Quitar puntuación de cierre solo para decidir sigla (mantener la palabra real).
        sin_punto = palabra.rstrip('.')
        clave_sigla = (sin_punto + '.') if palabra.endswith('.') else sin_punto
        if sin_punto.upper() in _SIGLAS or clave_sigla.upper() in _SIGLAS:
            resultado.append(palabra.upper())
        elif palabra.lower() in _CONECTORES and i > 0:
            resultado.append(palabra.lower())
        else:
            resultado.append(palabra.lower().capitalize())
    return ' '.join(resultado)