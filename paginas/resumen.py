"""Página de resumen general del programa."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from core.config import (
    NOMBRES_SESIONES,
    PALETA,
    RANGO_CALIFICACION,
)
from core.datos import Contexto, es_respuesta_util
from core.graficos import con_valores, graficar, plantilla
from paginas.comunes import (
    encabezado_filtros,
    mostrar_conocimientos_antes_despues,
)


def _conteo_genero(becarios: pd.DataFrame) -> go.Figure:
    conteo = becarios["Genero"].value_counts()
    figura = go.Figure(
        data=[
            go.Pie(
                labels=conteo.index,
                values=conteo.values,
                hole=0.45,
                marker_colors=[PALETA[1], PALETA[0], PALETA[5]][: len(conteo)],
                textinfo="percent+label",
                textfont_size=13,
                pull=[0.03] + [0] * (len(conteo) - 1),
            )
        ]
    )
    plantilla(figura, 380)
    figura.update_layout(title="Distribución por Género")
    return figura


def _conteo_pais(becarios: pd.DataFrame) -> go.Figure:
    tabla = becarios["Pais"].value_counts().reset_index()
    tabla.columns = ["País", "Cantidad"]
    figura = px.bar(
        tabla,
        x="País",
        y="Cantidad",
        text="Cantidad",
        color="Cantidad",
        color_continuous_scale=["#90CAF9", "#1565C0"],
    )
    plantilla(figura, 380)
    figura.update_layout(title="Becarios por País", showlegend=False, coloraxis_showscale=False)
    return con_valores(figura)


def _participantes_por_sesion(asistencia: pd.DataFrame) -> go.Figure:
    tabla = asistencia.groupby("Fecha_str")["Nombre"].nunique().reset_index()
    tabla.columns = ["Fecha", "Participantes"]
    figura = px.bar(
        tabla,
        x="Fecha",
        y="Participantes",
        text="Participantes",
        color_discrete_sequence=[PALETA[3]],
    )
    plantilla(figura, 380)
    figura.update_layout(title="Participantes por Sesión")
    return con_valores(figura)


def _calificacion_por_sesion(encuestas: pd.DataFrame) -> go.Figure:
    tabla = encuestas.groupby("Sesion_num")["Calif_num"].mean().reset_index()
    tabla.columns = ["Sesion", "Calificacion"]
    tabla["Etiqueta"] = tabla["Sesion"].map(
        lambda s: f"S{int(s)} {NOMBRES_SESIONES.get(int(s), '')}"
    )
    figura = go.Figure()
    figura.add_trace(
        go.Scatter(
            x=tabla["Etiqueta"],
            y=tabla["Calificacion"],
            mode="lines+markers+text",
            line=dict(color=PALETA[0], width=3),
            marker=dict(size=10),
            text=[f"{v:.2f}" for v in tabla["Calificacion"]],
            textposition="top center",
            textfont=dict(size=11),
        )
    )
    plantilla(figura, 380)
    figura.update_layout(
        title="Calificación Promedio por Sesión", yaxis_range=list(RANGO_CALIFICACION)
    )
    return figura


def _evolucion_asistencia(asistencia: pd.DataFrame) -> go.Figure:
    tabla = asistencia.groupby("Fecha_str")["Nombre"].nunique().reset_index()
    tabla.columns = ["Fecha", "Participantes"]
    figura = go.Figure()
    figura.add_trace(
        go.Scatter(
            x=tabla["Fecha"],
            y=tabla["Participantes"],
            mode="lines+markers+text",
            line=dict(color=PALETA[3], width=3),
            marker=dict(size=10),
            text=tabla["Participantes"],
            textposition="top center",
            textfont=dict(size=11),
        )
    )
    plantilla(figura, 380)
    figura.update_layout(title="Evolución de Asistencia por Sesión")
    return figura


def _top_categorias(
    encuestas: pd.DataFrame, columna: str, titulo: str, color: str
) -> go.Figure | None:
    validas = encuestas[encuestas[columna].apply(es_respuesta_util)]
    if validas.empty:
        return None
    tabla = validas[columna].value_counts().head(5).reset_index()
    tabla.columns = ["Categoría", "Cantidad"]
    figura = px.bar(
        tabla,
        x="Cantidad",
        y="Categoría",
        orientation="h",
        text="Cantidad",
        color_discrete_sequence=[color],
    )
    plantilla(figura, 320)
    figura.update_layout(title=titulo, margin=dict(t=50))
    return con_valores(figura)


def _calidad_de_datos(contexto: Contexto) -> None:
    """Indicadores de completitud que explican por qué algunos números bajan."""
    encuestas = contexto.encuestas
    total = len(encuestas)
    if total == 0:
        return
    sin_calificacion = int(encuestas["Calif_num"].isna().sum())
    equipos = contexto.libro.equipos
    equipos_sin_nombre = int(equipos["Nombre_equipo"].isna().sum())

    st.markdown("#### Calidad de los datos")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Encuestas analizadas", total)
    with c2:
        st.metric(
            "Sin calificación",
            f"{sin_calificacion} ({sin_calificacion / total * 100:.0f}%)",
        )
    with c3:
        st.metric("Grupos sin nombre de equipo", equipos_sin_nombre)

    if sin_calificacion:
        st.caption(
            "Las encuestas sin calificación se excluyen de los promedios; "
            "por eso el promedio por sesión puede basarse en menos respuestas "
            "que el total mostrado."
        )


def mostrar(contexto: Contexto, *, oscuro: bool = True) -> None:
    """Renderiza la página de resumen general."""
    st.title("Resumen General · IX Escuela de Jóvenes Ruralistas")
    encabezado_filtros(contexto)
    st.markdown("---")

    libro = contexto.libro
    total_sesiones = int(libro.sesiones["N_Sesion"].nunique())
    total_equipos = int(libro.equipos["Grupo"].nunique())

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Becarios", len(contexto.becarios))
    with c2:
        st.metric("Mentores", len(libro.mentores))
    with c3:
        st.metric("Sesiones", total_sesiones)
    with c4:
        st.metric("Encuestas", len(contexto.encuestas))

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Representantes", len(libro.representantes))
    with c2:
        st.metric("Equipos", total_equipos)
    with c3:
        st.metric("Registros de asistencia", f"{len(contexto.asistencia):,}")
    with c4:
        participantes = contexto.asistencia["Nombre"].nunique() if len(contexto.asistencia) else 0
        st.metric("Participantes únicos", participantes)

    st.markdown("---")

    c1, c2 = st.columns(2)
    with c1:
        graficar(_conteo_genero(contexto.becarios))
    with c2:
        graficar(_conteo_pais(contexto.becarios))

    c1, c2 = st.columns(2)
    with c1:
        if len(contexto.asistencia):
            graficar(_participantes_por_sesion(contexto.asistencia))
        else:
            st.info("No hay datos de asistencia con los filtros seleccionados.")
    with c2:
        if len(contexto.encuestas):
            graficar(_calificacion_por_sesion(contexto.encuestas))
        else:
            st.info("No hay datos de encuestas con los filtros seleccionados.")

    c1, c2 = st.columns(2)
    with c1:
        if len(contexto.asistencia):
            graficar(_evolucion_asistencia(contexto.asistencia))
        else:
            st.info("No hay datos de asistencia.")
    with c2:
        if len(contexto.becarios):
            mostrar_conocimientos_antes_despues(contexto, oscuro=oscuro)
        else:
            st.info("No hay becarios con los filtros seleccionados.")

    st.markdown("---")

    c1, c2 = st.columns(2)
    with c1:
        figura = _top_categorias(
            contexto.encuestas,
            "Cat_Ideas",
            "Top 5 · Temas más aprendidos",
            PALETA[0],
        )
        if figura is not None:
            graficar(figura)
        else:
            st.info("No hay respuestas abiertas de ideas aprendidas.")
    with c2:
        figura = _top_categorias(
            contexto.encuestas,
            "Cat_Mejora",
            "Top 5 · Sugerencias de mejora",
            PALETA[2],
        )
        if figura is not None:
            graficar(figura)
        else:
            st.info("No hay sugerencias de mejora registradas.")

    st.markdown("---")
    _calidad_de_datos(contexto)
