"""Página de análisis de asistencia."""

from __future__ import annotations

import plotly.express as px
import streamlit as st

from core.config import PALETA
from core.datos import Contexto
from core.graficos import con_valores, graficar, plantilla
from paginas.comunes import encabezado_filtros


def mostrar(contexto: Contexto, *, oscuro: bool = True) -> None:
    """Renderiza la página de asistencia."""
    st.title("Análisis de Asistencia")
    encabezado_filtros(contexto)
    st.markdown("---")

    asistencia = contexto.asistencia
    if asistencia.empty:
        st.warning("No hay registros de asistencia con los filtros seleccionados.")
        return

    total_registros = len(asistencia)
    sesiones = asistencia["Fecha_str"].nunique()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total de registros", f"{total_registros:,}")
    with c2:
        st.metric("Participantes únicos", asistencia["Nombre"].nunique())
    with c3:
        st.metric("Sesiones", sesiones)
    with c4:
        promedio = total_registros // sesiones if sesiones else 0
        st.metric("Promedio por sesión", f"{promedio:,}")

    st.markdown("---")
    tab1, tab2 = st.tabs(["Por sesión", "Por participante"])

    with tab1:
        por_participantes = asistencia.groupby("Fecha_str")["Nombre"].nunique().reset_index()
        por_participantes.columns = ["Fecha", "Participantes"]
        figura = px.bar(
            por_participantes,
            x="Fecha",
            y="Participantes",
            text="Participantes",
            color_discrete_sequence=[PALETA[3]],
        )
        plantilla(figura, 420, oscuro=oscuro)
        figura.update_layout(title="Participantes Únicos por Sesión")
        graficar(con_valores(figura, oscuro=oscuro))

        por_registros = asistencia.groupby("Fecha_str").size().reset_index()
        por_registros.columns = ["Fecha", "Registros"]
        figura = px.bar(
            por_registros,
            x="Fecha",
            y="Registros",
            text="Registros",
            color_discrete_sequence=[PALETA[0]],
        )
        plantilla(figura, 420, oscuro=oscuro)
        figura.update_layout(title="Total de Registros por Sesión")
        graficar(con_valores(figura, oscuro=oscuro))

    with tab2:
        tope = st.slider("Mostrar top", 10, 50, 20)
        tabla = asistencia["Nombre"].value_counts().head(tope).reset_index()
        tabla.columns = ["Nombre", "Registros"]
        figura = px.bar(
            tabla,
            x="Registros",
            y="Nombre",
            orientation="h",
            text="Registros",
            color_discrete_sequence=[PALETA[4]],
        )
        plantilla(figura, max(400, tope * 25), oscuro=oscuro)
        figura.update_layout(title=f"Top {tope} participantes con más asistencia")
        graficar(con_valores(figura, oscuro=oscuro))
