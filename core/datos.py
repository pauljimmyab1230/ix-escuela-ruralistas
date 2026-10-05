"""Capa de acceso a datos del dashboard.

Envuelve :mod:`src.datos` con caché de Streamlit y un manejo de errores que
muestra un mensaje accionable en lugar de un traceback.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import streamlit as st

from src.datos import (
    Filtros,
    LibroSistematizacion,
    aplicar_filtros_becarios,
    es_respuesta_util,
    filtrar_por_emails,
    matriz_conocimiento_linea_base,
    matriz_conocimiento_linea_final,
    promedio_conocimiento_linea_base,
    promedio_conocimiento_linea_final,
    tabla_expectativas_vs_resultados,
)

RUTA_LIBRO = Path(__file__).resolve().parent.parent / "Sistematizacion_nueva.xlsx"


@st.cache_data(show_spinner="Cargando datos de la sistematización...")
def cargar_libro_cacheado(ruta: str, hora_modificacion: float) -> LibroSistematizacion:
    """Carga el libro con caché; se invalida si el archivo cambia en disco."""
    from src.datos import cargar_libro

    return cargar_libro(ruta)


@st.cache_data(show_spinner=False)
def encuestas_por_sesion(libro: LibroSistematizacion) -> pd.DataFrame:
    """Encuestas de satisfacción sin la sesión 1 (bienvenida)."""
    datos = libro.encuestas.copy()
    datos = datos[datos["Sesion_num"] > 1].copy()
    return datos


@st.cache_data(show_spinner=False)
def opciones_de_filtros(libro: LibroSistematizacion) -> tuple[list[str], list[str]]:
    """Regiones y géneros disponibles para el sidebar."""
    regiones = sorted(libro.becarios["Region"].dropna().astype(str).unique().tolist())
    generos = sorted(libro.becarios["Genero"].dropna().astype(str).unique().tolist())
    return regiones, generos


@st.cache_data(show_spinner=False)
def etiquetas_de_becarios(becarios: pd.DataFrame) -> pd.DataFrame:
    """Pares (etiqueta para la UI, email) del selector individual."""
    datos = becarios[["Nombre", "Email"]].copy()
    datos["Nombre"] = datos["Nombre"].astype(str)
    datos["Email"] = datos["Email"].astype(str)
    datos["Etiqueta"] = datos["Nombre"]
    return datos.sort_values("Nombre")[["Etiqueta", "Email"]]


def cargar_o_mostrar_error(ruta: str | Path | None = None) -> LibroSistematizacion | None:
    """Carga el libro y, si falla, muestra el problema en la UI."""
    ruta_real = Path(ruta) if ruta else RUTA_LIBRO
    if not ruta_real.exists():
        st.error(
            f"No se encontró el libro de datos en `{ruta_real}`. "
            "Coloca `Sistematizacion_nueva.xlsx` en la raíz del proyecto o "
            "indica la ruta correcta."
        )
        return None

    try:
        hora = ruta_real.stat().st_mtime
        return cargar_libro_cacheado(str(ruta_real), hora)
    except Exception as exc:
        st.error(f"No se pudo leer el libro de datos: {exc}")
        with st.expander("Detalle técnico"):
            st.code(str(exc))
        return None


def filtrar_becarios(libro: LibroSistematizacion, filtros: Filtros) -> pd.DataFrame:
    """Becarios que cumplen los filtros globales e individuales."""
    return aplicar_filtros_becarios(libro.becarios, filtros)


def correos_filtrados(becarios: pd.DataFrame) -> list[str]:
    """Correos normalizados de los becarios que superan el filtro."""
    return becarios["Email"].dropna().astype(str).str.strip().str.lower().tolist()


def filtrar_por_correos(
    df: pd.DataFrame, columna: str, filtros: Filtros, becarios_filtrados: pd.DataFrame
) -> pd.DataFrame:
    """Restringe un DataFrame a los becarios visibles con los filtros activos."""
    if not filtros.activos:
        return df.copy()
    return filtrar_por_emails(df, columna, correos_filtrados(becarios_filtrados))


@dataclass
class Contexto:
    """Conjunto de tablas ya filtradas que reciben las páginas del dashboard."""

    libro: LibroSistematizacion
    filtros: Filtros
    becarios: pd.DataFrame
    asistencia: pd.DataFrame
    encuestas: pd.DataFrame
    examen: pd.DataFrame
    entregables: pd.DataFrame
    linea_final: pd.DataFrame

    @property
    def hay_filtros(self) -> bool:
        return self.filtros.activos

    @property
    def resumen_filtros(self) -> list[str]:
        return self.filtros.resumen()

    @property
    def total_becarios(self) -> int:
        return len(self.becarios)


def construir_contexto(libro: LibroSistematizacion, filtros: Filtros) -> Contexto:
    """Filtra todas las tablas relevantes según la selección del sidebar."""
    becarios = filtrar_becarios(libro, filtros)
    asistencia = filtrar_por_correos(libro.asistencia, "Correo electrónico", filtros, becarios)
    encuestas = filtrar_por_correos(encuestas_por_sesion(libro), "Correo", filtros, becarios)
    examen = filtrar_por_correos(libro.examen, "Correo", filtros, becarios)
    entregables = filtrar_por_correos(libro.entregables, "Correo", filtros, becarios)
    linea_final = libro.linea_final.copy()
    if filtros.activos:
        linea_final = filtrar_por_correos(linea_final, "Correo_norm", filtros, becarios)
    return Contexto(
        libro=libro,
        filtros=filtros,
        becarios=becarios,
        asistencia=asistencia,
        encuestas=encuestas,
        examen=examen,
        entregables=entregables,
        linea_final=linea_final,
    )


__all__ = [
    "Contexto",
    "Filtros",
    "LibroSistematizacion",
    "cargar_o_mostrar_error",
    "construir_contexto",
    "correos_filtrados",
    "encuestas_por_sesion",
    "es_respuesta_util",
    "etiquetas_de_becarios",
    "filtrar_becarios",
    "filtrar_por_correos",
    "matriz_conocimiento_linea_base",
    "matriz_conocimiento_linea_final",
    "opciones_de_filtros",
    "promedio_conocimiento_linea_base",
    "promedio_conocimiento_linea_final",
    "tabla_expectativas_vs_resultados",
]
