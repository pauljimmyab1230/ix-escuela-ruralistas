"""Carga, validación y normalización del libro de sistematización.

Concentra el conocimiento sobre la estructura de `Sistematizacion_nueva.xlsx`
para que ni el dashboard ni el pipeline dependan de índices de posición.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from src.normalizacion import (
    NIVEL_A_NUMERO,
    a_serie_numerica,
    columnas_conocimiento,
    limpiar_email,
    parsear_fecha,
)

RUTA_LIBRO_POR_OMISION = Path(__file__).resolve().parent.parent / "Sistematizacion_nueva.xlsx"

# Nombres de hoja del libro.
HOJA_BECARIOS = "01a.Becarios"
HOJA_MENTORES = "01b.Mentores"
HOJA_REPRESENTANTES = "01c.Representantes"
HOJA_EQUIPOS = "02.Equipos"
HOJA_MODULOS = "03.Modulos"
HOJA_SESIONES = "04.Sesiones"
HOJA_ASISTENCIA = "05.Asistencia"
HOJA_ENCUESTAS = "06.Encuestas"
HOJA_LINEA_BASE = "07.LineaBase"
HOJA_LINEA_FINAL = "08.LineaFinal"
HOJA_EXAMEN = "09.Examen"
HOJA_ENTREGABLES = "10.Entregables"
HOJA_PLANES = "11.PlanesEmprendimiento"
HOJA_EVAL_MENTORES = "12.EvalMentores"
HOJA_BITACORA = "13.BitacoraTrabajo"

# Columnas que el dashboard y el pipeline exigen en cada hoja.
COLUMNAS_REQUERIDAS: dict[str, list[str]] = {
    HOJA_BECARIOS: ["Email", "Nombre", "Edad", "Genero", "Pais", "Region"],
    HOJA_ASISTENCIA: ["Nombre", "Correo electrónico", "Fecha"],
    HOJA_ENCUESTAS: ["Correo", "Nombre", "Sesion", "Calificacion"],
    HOJA_EXAMEN: ["Correo", "Nombre", "Puntuacion"],
    HOJA_ENTREGABLES: ["Correo", "Nombre", "Promedio"],
    HOJA_PLANES: ["Grupo", "Jurado", "Puntaje"],
}

# Columnas de la línea final, identificadas por patrón en lugar de por posición.
PREFIJO_CONOCIMIENTO_LF = "Cual considera que es su nivel de conocimiento sobre"
COLUMNA_CORREO_LF = "Dirección de correo electrónico"
COLUMNA_NOMBRE_LF = "Nombres y Apellidos"

# Columnas de texto abiertas que alimentan la categorización.
COLUMNAS_TEXTO_ENCUESTAS = {
    "ideas": "Ideas_Texto",
    "gusto": "Gusto_Texto",
    "mejora": "Mejora_Texto",
    "profundizar": "Profundizar_Texto",
}

COLUMNAS_CATEGORIA_ENCUESTAS = {
    "ideas": "Cat_Ideas",
    "gusto": "Cat_Gusto",
    "mejora": "Cat_Mejora",
    "profundizar": "Cat_Profundizar",
}

# Mapa de categorías de "qué esperaba aprender" (línea base) a nombres cortos
# comparables con los de "qué aprendió" (línea final).
MAPEO_ESPERABA: dict[str, str] = {
    "Agroecología": "Agroecología",
    "Emprendimiento rural": "Emprendimiento",
    "Herramientas prácticas": "Herramientas",
    "General / Otros": "Otros",
    "Investigación": "Investigación",
    "Formulación de proyectos": "Formulación",
    "Liderazgo juvenil": "Liderazgo",
}

MAPEO_APRENDIO: dict[str, str] = {
    "Agroecologia y Suelos": "Agroecología",
    "Emprendimiento Rural": "Emprendimiento",
    "Conocimientos y Herramientas": "Herramientas",
    "Realidad Rural y Politicas": "Realidad Rural",
    "Formulacion de Proyectos": "Formulación",
    "Interculturalidad": "Interculturalidad",
    "Liderazgo y Habilidades": "Liderazgo",
    "Modelo CANVAS": "CANVAS",
}

# Valores que la UI debe tratar como "sin respuesta útil".
ETIQUETAS_VACIAS = ("Sin respuesta", "Sin respuesta / Satisfecho")


class ErrorEstructuraLibro(ValueError):
    """Se lanza cuando el libro no tiene las hojas o columnas esperadas."""


@dataclass
class LibroSistematizacion:
    """Contenedor tipado de las hojas del libro de sistematización."""

    ruta: Path
    becarios: pd.DataFrame
    mentores: pd.DataFrame
    representantes: pd.DataFrame
    equipos: pd.DataFrame
    modulos: pd.DataFrame
    sesiones: pd.DataFrame
    asistencia: pd.DataFrame
    encuestas: pd.DataFrame
    linea_base: pd.DataFrame
    linea_final: pd.DataFrame
    examen: pd.DataFrame
    entregables: pd.DataFrame
    planes: pd.DataFrame
    eval_mentores: pd.DataFrame
    bitacora: pd.DataFrame

    def nombres_de_hojas(self) -> list[str]:
        return [
            "Becarios",
            "Mentores",
            "Representantes",
            "Equipos",
            "Módulos",
            "Sesiones",
            "Asistencia",
            "Encuestas",
            "Línea Base",
            "Línea Final",
            "Examen",
            "Entregables",
            "Planes de Emprendimiento",
            "Evaluación de Mentores",
            "Bitácora de Trabajo",
        ]


def _exigir_columnas(df: pd.DataFrame, hoja: str, requeridas: Iterable[str]) -> None:
    faltantes = [c for c in requeridas if c not in df.columns]
    if faltantes:
        raise ErrorEstructuraLibro(
            f"La hoja '{hoja}' no tiene las columnas esperadas: {faltantes}. "
            f"Columnas encontradas: {list(df.columns)}"
        )


def _columnas_conocimiento_lf(df: pd.DataFrame) -> list[str]:
    """Devuelve las columnas de conocimiento de la línea final por patrón."""
    encontradas = [c for c in df.columns if str(c).startswith(PREFIJO_CONOCIMIENTO_LF)]
    if len(encontradas) < 9:
        raise ErrorEstructuraLibro(
            f"Se esperaban 9 columnas de conocimiento en Línea Final y hay {len(encontradas)}."
        )
    return encontradas


def cargar_libro(ruta: str | Path | None = None) -> LibroSistematizacion:
    """Carga el libro completo y valida su estructura.

    Lanza :class:`ErrorEstructuraLibro` si falta alguna hoja o columna crítica.
    """
    ruta_real = Path(ruta) if ruta else RUTA_LIBRO_POR_OMISION
    if not ruta_real.exists():
        raise FileNotFoundError(f"No se encontró el libro de sistematización en: {ruta_real}")

    def leer(hoja: str) -> pd.DataFrame:
        try:
            return pd.read_excel(ruta_real, sheet_name=hoja)
        except ValueError as exc:
            raise ErrorEstructuraLibro(f"Falta la hoja '{hoja}' en {ruta_real.name}.") from exc

    hojas = {
        HOJA_BECARIOS: leer(HOJA_BECARIOS),
        HOJA_MENTORES: leer(HOJA_MENTORES),
        HOJA_REPRESENTANTES: leer(HOJA_REPRESENTANTES),
        HOJA_EQUIPOS: leer(HOJA_EQUIPOS),
        HOJA_MODULOS: leer(HOJA_MODULOS),
        HOJA_SESIONES: leer(HOJA_SESIONES),
        HOJA_ASISTENCIA: leer(HOJA_ASISTENCIA),
        HOJA_ENCUESTAS: leer(HOJA_ENCUESTAS),
        HOJA_LINEA_BASE: leer(HOJA_LINEA_BASE),
        HOJA_LINEA_FINAL: leer(HOJA_LINEA_FINAL),
        HOJA_EXAMEN: leer(HOJA_EXAMEN),
        HOJA_ENTREGABLES: leer(HOJA_ENTREGABLES),
        HOJA_PLANES: leer(HOJA_PLANES),
        HOJA_EVAL_MENTORES: leer(HOJA_EVAL_MENTORES),
        HOJA_BITACORA: leer(HOJA_BITACORA),
    }

    for hoja, requeridas in COLUMNAS_REQUERIDAS.items():
        _exigir_columnas(hojas[hoja], hoja, requeridas)

    asistencia = hojas[HOJA_ASISTENCIA].copy()
    asistencia["Fecha_str"] = asistencia["Fecha"].apply(lambda v: parsear_fecha(v) or str(v)[:10])

    encuestas = hojas[HOJA_ENCUESTAS].copy()
    encuestas["Calif_num"] = a_serie_numerica(encuestas["Calificacion"])
    encuestas["Sesion_num"] = a_serie_numerica(encuestas["Sesion"])

    linea_final = hojas[HOJA_LINEA_FINAL].copy()
    linea_final["Correo_norm"] = limpiar_email(linea_final[COLUMNA_CORREO_LF])

    return LibroSistematizacion(
        ruta=ruta_real,
        becarios=hojas[HOJA_BECARIOS],
        mentores=hojas[HOJA_MENTORES],
        representantes=hojas[HOJA_REPRESENTANTES],
        equipos=hojas[HOJA_EQUIPOS],
        modulos=hojas[HOJA_MODULOS],
        sesiones=hojas[HOJA_SESIONES],
        asistencia=asistencia,
        encuestas=encuestas,
        linea_base=hojas[HOJA_LINEA_BASE],
        linea_final=linea_final,
        examen=hojas[HOJA_EXAMEN],
        entregables=hojas[HOJA_ENTREGABLES],
        planes=hojas[HOJA_PLANES],
        eval_mentores=hojas[HOJA_EVAL_MENTORES],
        bitacora=hojas[HOJA_BITACORA],
    )


# ---------------------------------------------------------------------------
# Filtros
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Filtros:
    """Selección de región, género y becarios concretos."""

    region: str = "Todas"
    genero: str = "Todos"
    emails: tuple[str, ...] = ()

    @property
    def activos(self) -> bool:
        return self.region != "Todas" or self.genero != "Todos" or bool(self.emails)

    def resumen(self) -> list[str]:
        partes: list[str] = []
        if self.region != "Todas":
            partes.append(f"Región: {self.region}")
        if self.genero != "Todos":
            partes.append(f"Género: {self.genero}")
        if self.emails:
            partes.append(f"Becarios: {len(self.emails)}")
        return partes


def aplicar_filtros_becarios(becarios: pd.DataFrame, filtros: Filtros) -> pd.DataFrame:
    """Aplica los filtros globales a la tabla de becarios."""
    resultado = becarios.copy()
    if filtros.region != "Todas":
        resultado = resultado[resultado["Region"] == filtros.region]
    if filtros.genero != "Todos":
        resultado = resultado[resultado["Genero"] == filtros.genero]
    if filtros.emails:
        resultado = resultado[resultado["Email"].isin(filtros.emails)]
    return resultado


def aplicar_filtro_emails(df: pd.DataFrame, columna: str, filtros: Filtros) -> pd.DataFrame:
    """Restringe un DataFrame por los correos seleccionados, si hay filtros."""
    if not filtros.activos:
        return df.copy()
    seleccionados = {e.strip().lower() for e in (filtros.emails if filtros.emails else [])}
    if not seleccionados:
        # Sin selección individual: usar los becarios que ya pasaron el filtro
        # de región/género. El llamante debe resolverlo antes.
        return df.copy()
    serie = limpiar_email(df[columna])
    return df[serie.isin(seleccionados)].copy()


def filtrar_por_emails(df: pd.DataFrame, columna: str, emails: Iterable[str]) -> pd.DataFrame:
    """Restringe un DataFrame a los correos indicados (comparación normalizada)."""
    objetivo = {str(e).strip().lower() for e in emails}
    serie = limpiar_email(df[columna])
    return df[serie.isin(objetivo)].copy()


def es_respuesta_util(valor: Any) -> bool:
    """Indica si un valor de texto merece mostrarse como respuesta abierta."""
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return False
    texto = str(valor).strip()
    return texto not in ETIQUETAS_VACIAS


# ---------------------------------------------------------------------------
# Línea base vs línea final
# ---------------------------------------------------------------------------


def nombres_linea_final(libro: LibroSistematizacion) -> pd.Series:
    return libro.linea_final[COLUMNA_NOMBRE_LF]


def correos_linea_final(libro: LibroSistematizacion) -> pd.Series:
    return libro.linea_final["Correo_norm"]


def matriz_conocimiento_linea_base(becarios: pd.DataFrame) -> pd.DataFrame:
    """Matriz becario x conocimiento (0-3) de la línea base."""
    columnas = columnas_conocimiento(becarios)
    matriz = becarios[["Nombre", *columnas]].copy()
    matriz.columns = ["Nombre"] + [c.replace("Conoc_", "") for c in columnas]
    return matriz.set_index("Nombre")


def matriz_conocimiento_linea_final(libro: LibroSistematizacion) -> pd.DataFrame:
    """Matriz becario x conocimiento (0-3) de la línea final, ya normalizada."""
    columnas = _columnas_conocimiento_lf(libro.linea_final)
    nombres = libro.linea_final[COLUMNA_NOMBRE_LF]
    crudo = libro.linea_final[columnas].replace(NIVEL_A_NUMERO) - 1
    crudo.columns = [c.replace("Conoc_", "") for c in columnas_conocimiento(libro.becarios)]
    return pd.DataFrame(crudo.values, index=nombres.values, columns=crudo.columns)


def promedio_conocimiento_linea_base(becarios: pd.DataFrame) -> list[float]:
    return [float(becarios[c].mean()) for c in columnas_conocimiento(becarios)]


def promedio_conocimiento_linea_final(libro: LibroSistematizacion) -> list[float]:
    columnas = _columnas_conocimiento_lf(libro.linea_final)
    mapeado = libro.linea_final[columnas].replace(NIVEL_A_NUMERO)
    return [
        float((serie - 1).mean()) if serie.notna().any() else 0.0 for _, serie in mapeado.items()
    ]


def tabla_expectativas_vs_resultados(libro: LibroSistematizacion) -> pd.DataFrame:
    """Compara 'qué esperaba aprender' con 'qué aprendió' por categoría."""
    esperaba = (
        libro.becarios["Cat_QueEsperaAprender"].map(MAPEO_ESPERABA).value_counts().reset_index()
    )
    esperaba.columns = ["Categoria", "Esperaba"]

    aprendio = libro.linea_final["Cat_Aprendido"].map(MAPEO_APRENDIO).value_counts().reset_index()
    aprendio.columns = ["Categoria", "Aprendio"]

    comparacion = pd.merge(esperaba, aprendio, on="Categoria", how="outer").fillna(0)
    comparacion["Esperaba"] = comparacion["Esperaba"].astype(int)
    comparacion["Aprendio"] = comparacion["Aprendio"].astype(int)
    comparacion["Diff"] = comparacion["Aprendio"] - comparacion["Esperaba"]
    return comparacion.sort_values("Esperaba", ascending=True).reset_index(drop=True)
