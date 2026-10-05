"""Generación de tablas resumen y reportes del pipeline de sistematización.

Sustituye la lógica repetida de `categorizar_final.py` y
`categorizar_linea_base.py`, dejando la escritura de resultados en un solo lugar.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

import pandas as pd

from src.categorias import Esquema, clasificar_serie
from src.datos import COLUMNAS_CATEGORIA_ENCUESTAS, COLUMNAS_TEXTO_ENCUESTAS
from src.normalizacion import columnas_conocimiento

# Escalas de las preguntas cerradas de la encuesta por sesión.
ESCALA_LIKERT5 = {
    "Muy de acuerdo": 5,
    "De acuerdo": 4,
    "Neutral": 3,
    "En desacuerdo": 2,
    "Muy en desacuerdo": 1,
}
ESCALA_APRENDIO = {"Mucho": 5, "Bastante": 4, "Regular": 3, "Poco": 2, "Nada": 1}
ESCALA_CLARO = {"Muy claro": 5, "Claro": 4, "poco claro": 2, "Poco claro": 2}
ESCALA_FACILITADOR = {"Excelente": 5, "Regular": 3, "deficiente": 1}


def tabla_frecuencias(serie: Iterable[Any], etiqueta: str = "Frecuencia") -> pd.Series:
    """Convierte una serie de categorías (posiblemente multi-etiqueta) en frecuencias."""
    contador: Counter[str] = Counter()
    for valor in serie:
        if valor is None or pd.isna(valor):
            continue
        texto = str(valor).strip()
        if not texto or texto.startswith("Sin respuesta"):
            continue
        for categoria in texto.split("|"):
            categoria = categoria.strip()
            if categoria:
                contador[categoria] += 1
    serie_resultado = pd.Series(contador, name=etiqueta, dtype="int64")
    return serie_resultado.sort_values(ascending=False)


def tabla_cruzada(df: pd.DataFrame, columna_categoria: str) -> pd.DataFrame:
    """Tabla de contingencia categoría x sesión, con columna Total."""
    tabla = pd.crosstab(df[columna_categoria], df["Sesion"])
    tabla["Total"] = tabla.sum(axis=1)
    return tabla.sort_values("Total", ascending=False)


def metricas_por_sesion(df: pd.DataFrame) -> pd.DataFrame:
    """Promedios de las preguntas cerradas de la encuesta, por sesión."""
    resultado = (
        df.groupby("Sesion")
        .agg(
            n_encuestados=("Sesion", "count"),
            Calificacion=("Calif_Num", "mean"),
            Aprendizaje=("Aprendio_Num", "mean"),
            Claridad=("Claro_Num", "mean"),
            Utilidad=("Util_Num", "mean"),
            Facilitador=("Facil_Num", "mean"),
            Conocia_Pct=("Conocia_Bin", "mean"),
        )
        .round(2)
    )
    resultado["Conocia_Pct"] = (resultado["Conocia_Pct"] * 100).round(1)
    return resultado


def metricas_generales(df: pd.DataFrame) -> pd.DataFrame:
    """Satisfacción y metodología agregadas por sesión (solo donde hay datos)."""
    resultado = (
        df.groupby("Sesion")
        .agg(
            n=("Sat_Num", "count"),
            Satisfaccion=("Sat_Num", "mean"),
            Metodologia=("Metodo_Num", "mean"),
        )
        .round(2)
    )
    return resultado[resultado["n"] > 0]


def participacion_por_sesion(df: pd.DataFrame, columnas_texto: Mapping[str, str]) -> pd.DataFrame:
    """Porcentaje de respuesta válida de cada pregunta abierta, por sesión."""
    datos: dict[str, Any] = {"n_encuestados": df.groupby("Sesion").size()}
    for clave, columna in columnas_texto.items():
        datos[f"%Respondio_{clave.capitalize()}"] = df.groupby("Sesion")[columna].apply(
            lambda grupo: (
                round(sum(1 for v in grupo if es_texto_valido(v)) / len(grupo) * 100, 1)
                if len(grupo)
                else 0.0
            )
        )
    return pd.DataFrame(datos)


def es_texto_valido(valor: Any) -> bool:
    """Indica si un valor conserva texto util para analizar."""
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return False
    return bool(str(valor).strip())


def agregar_metricas_cerradas(
    df: pd.DataFrame,
    columna_satisfaccion: str,
    columna_metodologia: str,
    columna_utilidad: str,
    columna_claridad: str,
    columna_aprendio: str,
    columna_facilitador: str,
    columna_conocia: str,
    columna_calificacion: str,
) -> pd.DataFrame:
    """Añade las versiones numéricas de las preguntas cerradas a la encuesta."""
    salida = df.copy()
    salida["Sat_Num"] = pd.to_numeric(
        salida[columna_satisfaccion].map(ESCALA_LIKERT5), errors="coerce"
    )
    salida["Metodo_Num"] = pd.to_numeric(
        salida[columna_metodologia].map(ESCALA_LIKERT5), errors="coerce"
    )
    salida["Util_Num"] = salida[columna_utilidad].map(ESCALA_LIKERT5).astype(float)
    salida["Claro_Num"] = salida[columna_claridad].map(ESCALA_CLARO).astype(float)
    salida["Aprendio_Num"] = salida[columna_aprendio].map(ESCALA_APRENDIO).astype(float)
    salida["Facil_Num"] = salida[columna_facilitador].map(ESCALA_FACILITADOR).astype(float)
    salida["Calif_Num"] = pd.to_numeric(salida[columna_calificacion], errors="coerce")
    salida["Conocia_Bin"] = salida[columna_conocia].apply(
        lambda v: 1 if str(v).strip().lower() == "si" else 0
    )
    return salida


def escribir_hojas(
    ruta_salida: str | Path,
    hojas: Mapping[str, pd.DataFrame],
    *,
    anexar: bool = False,
) -> Path:
    """Escribe cada DataFrame en una hoja del libro indicado.

    Con ``anexar=True`` conserva las hojas existentes que no se sobreescriben.
    """
    ruta = Path(ruta_salida)
    existe = ruta.exists()
    modo = "a" if anexar and existe else "w"
    argumentos: dict[str, Any] = {"engine": "openpyxl", "mode": modo}
    if modo == "a":
        argumentos["if_sheet_exists"] = "replace"
    with pd.ExcelWriter(ruta, **argumentos) as escritor:
        for nombre, df in hojas.items():
            # El índice solo se escribe cuando aporta información: las tablas
            # resumen lo llevan (categorías, sesiones, regiones) y los datos
            # crudos usan un índice de fila que no interesa.
            conservar_indice = not isinstance(df.index, pd.RangeIndex)
            df.to_excel(escritor, sheet_name=nombre, index=conservar_indice)
    return ruta


def resumen_por_categoria(
    df: pd.DataFrame, columna_categoria: str, top: int | None = None
) -> pd.DataFrame:
    """Frecuencia de categorías con porcentaje sobre respuestas válidas."""
    validas = df[df[columna_categoria].apply(_es_categoria_util)]
    conteo = validas[columna_categoria].value_counts()
    if top is not None:
        conteo = conteo.head(top)
    tabla = conteo.reset_index()
    tabla.columns = ["Categoria", "Cantidad"]
    total = len(validas) or 1
    tabla["%"] = (tabla["Cantidad"] / total * 100).round(1)
    return tabla


def _es_categoria_util(valor: Any) -> bool:
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return False
    texto = str(valor).strip()
    return texto not in {"Sin respuesta", "Sin respuesta / Satisfecho"}


def resumen_conocimiento_por_region(becarios: pd.DataFrame) -> pd.DataFrame:
    """Promedio de conocimiento autopercibido por región."""
    columnas = columnas_conocimiento(becarios)
    tabla = becarios.groupby("Region")[columnas].mean().round(2)
    tabla.columns = [c.replace("Conoc_", "") for c in columnas]
    return tabla.sort_values(by=tabla.columns[0], ascending=False)


def resumen_niveles_conocimiento(becarios: pd.DataFrame) -> pd.Series:
    """Promedio global de cada dimensión de conocimiento."""
    columnas = columnas_conocimiento(becarios)
    serie = becarios[columnas].mean().round(2).sort_values(ascending=False)
    serie.index = [c.replace("Conoc_", "") for c in serie.index]
    return serie


def aplicar_esquemas_a_encuestas(
    df: pd.DataFrame,
    esquemas: Mapping[str, Esquema],
    columna_sesion: str = "Sesion",
) -> pd.DataFrame:
    """Añade las columnas `Cat_*` a la tabla de encuestas."""
    salida = df.copy()
    for clave, columna_texto in COLUMNAS_TEXTO_ENCUESTAS.items():
        esquema = esquemas[clave]
        salida[COLUMNAS_CATEGORIA_ENCUESTAS[clave]] = clasificar_serie(
            salida[columna_texto], esquema
        )
    return salida
