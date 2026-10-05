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
