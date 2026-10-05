"""Utilidades compartidas de normalización de texto, fechas y mapeos.

Todas las funciones están en español y operan sobre texto sin acentos para que
las reglas de categorización puedan declararse como palabras planas.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any

import pandas as pd

# Mapeo de los niveles de conocimiento autopercibidos de la línea final al
# formato numérico 0-3 que usa la línea base.
NIVEL_A_NUMERO: dict[str, int] = {
    "Nada": 1,
    "Basico": 2,
    "Intermedio": 3,
    "Avanzado": 4,
}

# Escala numérica de la línea base (ya viene como 0-3 en el Excel).
ESCALA_CONOCIMIENTO_MIN = 0
ESCALA_CONOCIMIENTO_MAX = 3

# Nombres cortos de las 9 dimensiones de conocimiento, en el orden del Excel.
CONOCIMIENTOS_CORTOS: list[str] = [
    "Des. Agrario",
    "Agroecología",
    "Género",
    "Interculturalidad",
    "Formalización",
    "CANVA",
    "Comercialización",
    "Form. Proyectos",
    "Fondos",
]

# Nombres de las columnas `Conoc_*` que deben existir en la hoja de becarios.
PREFIJO_CONOCIMIENTO = "Conoc_"


def quitar_acentos(texto: str) -> str:
    """Devuelve `texto` en ASCII, eliminando acentos y diéresis.

    Ejemplo: ``quitar_acentos("Agroecología")`` -> ``"Agroecologia"``.
    """
    if not isinstance(texto, str):
        texto = str(texto)
    descompuesto = unicodedata.normalize("NFKD", texto)
    return descompuesto.encode("ascii", "ignore").decode("ascii")


def a_minusculas_sin_acentos(texto: Any) -> str:
    """Normaliza un valor cualquiera a minúsculas sin acentos y sin bordes."""
    if texto is None or (isinstance(texto, float) and pd.isna(texto)):
        return ""
    return quitar_acentos(str(texto)).lower().strip()


def parsear_fecha(valor: Any) -> str | None:
    """Interpreta una fecha en formato dd/mm/aaaa o aaaa-mm-dd.

    Tolera espacios no separables (U+00A0, U+202F) que suelen venir en las
    exportaciones de formularios. Devuelve ``None`` si no puede interpretarla.
    """
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return None
    texto = str(valor).replace("\xa0", " ").replace("\u202f", " ").strip()
    coincidencia = re.match(r"(\d{2})/(\d{2})/(\d{4})", texto)
    if coincidencia:
        dia, mes, anio = coincidencia.groups()
        return f"{anio}-{mes}-{dia}"
    coincidencia = re.match(r"(\d{4})-(\d{2})-(\d{2})", texto)
    if coincidencia:
        return coincidencia.group(0)
    return None


def es_numero(valor: Any) -> bool:
    """Indica si `valor` se puede convertir a número de forma limpia."""
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return False
    try:
        float(str(valor).strip())
    except (TypeError, ValueError):
        return False
    return True


def a_serie_numerica(serie: pd.Series) -> pd.Series:
    """Convierte una serie a numérico, volviendo `None` los valores inválidos."""
    return pd.to_numeric(serie, errors="coerce")


def limpiar_email(serie: pd.Series) -> pd.Series:
    """Normaliza una serie de correos a minúsculas sin espacios alrededor."""
    return serie.astype(str).str.strip().str.lower()


def columnas_conocimiento(df: pd.DataFrame) -> list[str]:
    """Devuelve las columnas `Conoc_*` en el orden en que aparecen."""
    return [c for c in df.columns if str(c).startswith(PREFIJO_CONOCIMIENTO)]


def aplicar_mapeo(serie: pd.Series, mapeo: dict[str, Any]) -> pd.Series:
    """Aplica un diccionario de traducción a una serie, conservando NaN."""
    return serie.map(mapeo)


# ---------------------------------------------------------------------------
# Normalización de respuestas categóricas del formulario
# ---------------------------------------------------------------------------

# Escala ordinal de comodidad, compartida entre línea base y línea final.
ESCALA_COMODIDAD: dict[str, int] = {
    "muy incomodo": 1,
    "incomodo": 2,
    "neutral": 3,
    "ni comodo ni incomodo": 3,
    "comodo": 4,
    "muy comodo": 5,
}

# Escala ordinal de capacidad de liderazgo.
ESCALA_LIDERAZGO: dict[str, int] = {
    "no": 0,
    "tal vez": 1,
    "si": 2,
}

# Escala ordinal de reconocimiento de actores de la comunidad.
ESCALA_ACTORES: dict[str, int] = {
    "no": 0,
    "mas o menos": 1,
    "poco": 1,
    "si": 2,
}

# Rangos de edad del perfil demográfico, en orden de aparición.
RANGOS_EDAD: list[tuple[str, int, int]] = [
    ("18-20", 18, 20),
    ("21-23", 21, 23),
    ("24-26", 24, 26),
    ("27-29", 27, 29),
    ("30 o más", 30, 200),
]

# Regiones con variantes de escritura que deben unificarse.
_ALIAS_REGIONES: dict[str, str] = {
    "junin": "Junín",
    "cuzco": "Cusco",
    "cusco": "Cusco",
    "la libertad": "La Libertad",
    "ancash": "Áncash",
    "apurimac": "Apurímac",
    "lima": "Lima",
    "puno": "Puno",
    "ayacucho": "Ayacucho",
    "piura": "Piura",
    "lambayeque": "Lambayeque",
    "loreto": "Loreto",
    "huancavelica": "Huancavelica",
    "pasco": "Pasco",
    "ucayali": "Ucayali",
    "cajamarca": "Cajamarca",
    "ica": "Ica",
    "amazonas": "Amazonas",
    "arequipa": "Arequipa",
}


def normalizar_si_no(valor: Any) -> str | None:
    """Reduce las variantes de Sí/No a un único valor canónico.

    El formulario acumula ``Si``, ``si``, ``SI``, ``Sí`` y respuestas libres;
    aquí se llevan a ``"Sí"`` / ``"No"`` y el resto queda como ``None``.
    """
    texto = a_minusculas_sin_acentos(valor)
    if not texto or texto in {"-", ".", "ns", "sin respuesta", "ninguno", "ninguna"}:
        return None
    if texto.startswith("no") or texto in {"ningun", "ninguna", "no pertenezco"}:
        return "No"
    if texto.startswith("si") or texto.startswith("mas o menos") or texto.startswith("poco"):
        return "Sí"
    return None


def a_ordinal(valor: Any, escala: dict[str, int]) -> float | None:
    """Convierte una etiqueta de escala en su valor ordinal, o ``None``."""
    texto = a_minusculas_sin_acentos(valor)
    if not texto:
        return None
    # Se recortan sufijos como "(a)" o "a" de "Cómodo(a)" / "Muy cómodo(a)".
    texto = texto.replace("(a)", "").replace("(a)", "").strip()
    for clave, numero in escala.items():
        if texto.startswith(clave):
            return float(numero)
    return None


def normalizar_region(valor: Any) -> str | None:
    """Unifica las variantes de escritura de una región."""
    texto = a_minusculas_sin_acentos(valor)
    if not texto or texto in {"-", ".", ""}:
        return None
    if texto in _ALIAS_REGIONES:
        return _ALIAS_REGIONES[texto]
    return str(valor).strip()


def clasificar_rango_edad(edad: Any) -> str | None:
    """Ubica una edad dentro de los rangos definidos del perfil."""
    try:
        numero = int(float(edad))
    except (TypeError, ValueError):
        return None
    for etiqueta, minimo, maximo in RANGOS_EDAD:
        if minimo <= numero <= maximo:
            return etiqueta
    return None


def mapear_fechas_cercanas(
    fechas: pd.Series,
    calendario: dict[Any, Any],
    tolerancia_dias: int = 2,
) -> pd.Series:
    """Asigna cada fecha al registro del calendario más próximo.

    El calendario del programa y la hoja de asistencia no siempre coinciden en
    el día exacto (por ejemplo, una sesión programada el 6 y registrada el 5).
    Con `tolerancia_dias` se tolera esa deriva sin perder la correspondencia.
    """
    if not calendario:
        return pd.Series([None] * len(fechas), index=fechas.index)

    claves = [pd.Timestamp(k) for k in calendario if pd.notna(k)]
    mapa = {pd.Timestamp(k): v for k, v in calendario.items() if pd.notna(k)}

    def resolver(valor: Any) -> Any:
        fecha = pd.to_datetime(valor, errors="coerce")
        if pd.isna(fecha):
            return None
        mejor: tuple[float, Any] | None = None
        for clave in claves:
            distancia = abs((fecha - clave).days)
            if distancia <= tolerancia_dias and (mejor is None or distancia < mejor[0]):
                mejor = (distancia, mapa[clave])
        return mejor[1] if mejor else None

    return fechas.apply(resolver)


# Variantes de escritura de especialidades que deben unificarse.
_ALIAS_ESPECIALIDADES: dict[str, str] = {
    "ingenieria ambiental": "Ingeniería Ambiental",
    "ing ambiental": "Ingeniería Ambiental",
    "ingeneieria ambiental": "Ingeniería Ambiental",
    "ingenieria ambiental y forestal": "Ingeniería Ambiental y Forestal",
    "ingenieria agroindustrial": "Ingeniería Agroindustrial",
    "ingenieria agroindustrial ": "Ingeniería Agroindustrial",
    "agronomia": "Agronomía",
    "agronomia ": "Agronomía",
    "economia": "Economía",
    "economia ": "Economía",
    "ciencias agrarias": "Ciencias Agrarias",
    "ingenieria industrial": "Ingeniería Industrial",
    "ingenieria forestal": "Ingeniería Forestal",
    "comercio internacional": "Comercio Internacional",
    "geografia y medio ambiente": "Geografía y Medio Ambiente",
    "periodismo": "Periodismo",
}


def normalizar_especialidad(valor: Any) -> str | None:
    """Unifica las variantes de escritura de una especialidad o carrera."""
    texto_limpio = str(valor).strip() if valor is not None else ""
    if not texto_limpio or texto_limpio in {"-", ".", "nan", "None"}:
        return None
    clave = a_minusculas_sin_acentos(texto_limpio)
    return _ALIAS_ESPECIALIDADES.get(clave, texto_limpio)
