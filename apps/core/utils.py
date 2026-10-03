"""
Utilidades de normalización de nombres de cliente.

Regla: un cliente solo puede existir en UNA forma canónica (title case),
así "ANDINA" / "andina" / "Andina Retail" colapsan a "Andina Retail",
"LA DIVISA" a "La Divisa", etc. Aplicar SIEMPRE al escribir `cliente`
(importadores y vistas) y al filtrar por cliente (`?cliente=`).

Nota (2026-10-03): el catálogo es genérico y sin marcas reales — soptraloc
es un producto independiente, la normalización no debe codificar clientes
ni proveedores específicos de una operación.
"""

# Conectores que van en minúscula salvo en la primera palabra.
_CONECTORES = {
    'de', 'del', 'la', 'las', 'los', 'y', 'e', 'o', 'a', 'al',
    'para', 'por', 'en', 'con', 'el', 'un', 'una', 'su', 'sus',
}

# Siglas/marcas que se conservan en mayúsculas tal cual.
# Solo figuras jurídicas genéricas: nunca marcas reales (producto independiente).
_SIGLAS = {
    'SA', 'S.A.', 'S.A', 'LTDA', 'Ltda.', 'EIRL',
    'SPA', 'S.P.A.', 'USA', 'EU',
}

# Aliases/typos comunes → forma canónica (antes del title case genérico).
# Ejemplos ficticios (sin marcas reales): sirven de plantilla para que un
# deployment agregue sus propios mapeos.
_ALIASES = {
    # Marca de ejemplo: Andina (typos comunes)
    'andina': 'Andina', 'andna': 'Andina', 'andyna': 'Andina', 'andina retail': 'Andina Retail',
    # Marca de ejemplo: Pacífico
    'pacifico': 'Pacífico', 'pacificco': 'Pacífico', 'pacificfoo': 'Pacífico',
    # Marca de ejemplo: Bío Bío (nombre con tilde)
    'bio bio': 'Bío Bío', 'biobio': 'Bío Bío',
    # Línea naviera de ejemplo
    'novamar': 'Novamar', 'nova mar': 'Novamar', 'nmar': 'Novamar',
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
    # 'N/A', 'NA', '-' etc. significan 'sin dato': no son un cliente real.
    # Así la programación hereda el cliente que el contenedor ya trae (de la liberación)
    # en vez de pisarlo con el literal 'N/A'.
    if texto.lower() in {'n/a', 'na', '-', 'sin dato', 'ninguno', 'sn'}:
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