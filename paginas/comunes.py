"""Bloques de gráficos compartidos entre varias páginas."""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from core.config import (
    ALTO_GRAFICO_PEQUENO,
    CONOCIMIENTOS_CORTOS,
    ESCALA_CONOCIMIENTO_MAX,
    PALETA,
    UMBRAL_NIVEL_INTERMEDIO,
)
from core.datos import Contexto
from core.graficos import graficar, plantilla
from src.datos import (
    promedio_conocimiento_linea_base,
    promedio_conocimiento_linea_final,
)


def figura_conocimientos_antes_despues(
    contexto: Contexto, *, altura: int = ALTO_GRAFICO_PEQUENO, oscuro: bool = True
) -> go.Figure:
    """Barras agrupadas con el conocimiento autopercibido inicial y final."""
    base = promedio_conocimiento_linea_base(contexto.becarios)
    final = promedio_conocimiento_linea_final(contexto.libro)

    figura = go.Figure()
    figura.add_trace(
        go.Bar(
            name="Línea Base",
            x=CONOCIMIENTOS_CORTOS,
            y=base,
            marker_color=PALETA[0],
            text=[f"{v:.2f}" for v in base],
            textposition="outside",
        )
    )
    figura.add_trace(
        go.Bar(
            name="Línea Final",
            x=CONOCIMIENTOS_CORTOS,
            y=final,
            marker_color=PALETA[1],
            text=[f"{v:.2f}" for v in final],
            textposition="outside",
        )
    )
    plantilla(figura, altura, oscuro=oscuro)
    figura.update_layout(
        title="Conocimientos: Antes vs Después",
        barmode="group",
        yaxis_range=[0, ESCALA_CONOCIMIENTO_MAX + 0.8],
    )
    figura.add_hline(
        y=UMBRAL_NIVEL_INTERMEDIO,
        line_dash="dash",
        line_color="#aaa",
        annotation_text="Nivel intermedio",
    )
    figura.update_xaxes(tickangle=-25)
    return figura


def mostrar_conocimientos_antes_despues(
    contexto: Contexto, *, oscuro: bool = True, altura: int = ALTO_GRAFICO_PEQUENO
) -> None:
    """Publica la comparación de conocimientos en la página activa."""
    figura = figura_conocimientos_antes_despues(contexto, altura=altura, oscuro=oscuro)
    graficar(figura)


def figura_cambio_conocimientos(contexto: Contexto, *, oscuro: bool = True) -> go.Figure:
    """Diferencia por dimensión entre la línea final y la línea base."""
    base = promedio_conocimiento_linea_base(contexto.becarios)
    final = promedio_conocimiento_linea_final(contexto.libro)
    diferencia = [f - b for f, b in zip(final, base, strict=True)]
    colores = [PALETA[3] if d > 0 else PALETA[1] for d in diferencia]

    figura = go.Figure(
        data=[
            go.Bar(
                x=CONOCIMIENTOS_CORTOS,
                y=diferencia,
                marker_color=colores,
                text=[f"{d:+.2f}" for d in diferencia],
                textposition="outside",
            )
        ]
    )
    plantilla(figura, ALTO_GRAFICO_PEQUENO, oscuro=oscuro)
    figura.update_layout(title="Cambio: Línea Final - Línea Base")
    figura.add_hline(y=0, line_dash="solid", line_color="#aaa")
    figura.update_xaxes(tickangle=-25)
    return figura


def encabezado_filtros(contexto: Contexto) -> None:
    """Muestra los filtros activos y cuántos becarios quedan a la vista."""
    if not contexto.resumen_filtros:
        return
    partes = " | ".join(contexto.resumen_filtros)
    st.markdown(
        f"**Filtros activos:** {partes} | **Mostrando:** {contexto.total_becarios} becarios"
    )
