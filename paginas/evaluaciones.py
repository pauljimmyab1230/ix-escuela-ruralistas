"""Página de evaluaciones: examen, entregables y planes de emprendimiento."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from core.config import (
    PALETA,
    PUNTAJE_MAXIMO_EXAMEN,
    PUNTAJE_MAXIMO_PLAN,
    UMBRAL_APROBACION_EXAMEN,
)
from core.datos import Contexto
from core.graficos import con_valores, graficar, plantilla
from src import indicadores as ind


def _seccion_examen(contexto: Contexto, oscuro: bool) -> None:
    datos = contexto.examen.copy()
    datos["Puntaje"] = pd.to_numeric(datos["Puntuacion"], errors="coerce")
    datos = datos.dropna(subset=["Puntaje"])

    if datos.empty:
        st.info("No hay exámenes registrados con los filtros seleccionados.")
        return

    estadisticas = ind.estadisticas_examen(contexto.libro)
    aprobados = int((datos["Puntaje"] >= UMBRAL_APROBACION_EXAMEN).sum())

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Exámenes", estadisticas["n"])
    with c2:
        st.metric(
            "Promedio",
            f"{estadisticas['Promedio']:.2f}/{PUNTAJE_MAXIMO_EXAMEN}",
        )
    with c3:
        st.metric("Mediana", f"{estadisticas['Mediana']:.1f}/{PUNTAJE_MAXIMO_EXAMEN}")
    with c4:
        st.metric("Desviación estándar", f"{estadisticas['Desviacion']:.2f}")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Aprobados", f"{aprobados}/{len(datos)}")
    with c2:
        st.metric("% Aprobados", f"{aprobados / len(datos) * 100:.0f}%")
    with c3:
        st.metric("Rango", f"{estadisticas['Minimo']:.0f} - {estadisticas['Maximo']:.0f}")

    c1, c2 = st.columns(2)
    with c1:
        figura = px.histogram(
            datos,
            x="Puntaje",
            nbins=10,
            text_auto=True,
            color_discrete_sequence=[PALETA[0]],
        )
        figura.add_vline(
            x=UMBRAL_APROBACION_EXAMEN,
            line_dash="dash",
            line_color="#4CAF50",
            annotation_text=f"Aprobado: {UMBRAL_APROBACION_EXAMEN}",
            annotation_position="top right",
        )
        plantilla(figura, 380, oscuro=oscuro)
        figura.update_layout(title="Distribución de Puntajes", bargap=0.05)
        graficar(figura)

    with c2:
        ordenado = datos.sort_values("Puntaje", ascending=True)
        figura = px.bar(
            ordenado,
            x="Puntaje",
            y="Nombre",
            orientation="h",
            text="Puntaje",
            color_discrete_sequence=[PALETA[0]],
        )
        figura.add_vline(x=UMBRAL_APROBACION_EXAMEN, line_dash="dash", line_color="#4CAF50")
        plantilla(figura, 380, oscuro=oscuro)
        figura.update_layout(title="Puntajes por Participante")
        graficar(con_valores(figura, oscuro=oscuro))

    st.markdown("---")
    st.subheader("Acierto por pregunta")

    acierto = ind.acierto_por_pregunta(contexto.examen)
    if acierto.empty:
        st.info("No hay respuestas por pregunta.")
        return

    acierto = acierto.copy()
    acierto["Etiqueta"] = [
        f"P{i + 1} · {texto[:60]}{'…' if len(texto) > 60 else ''}"
        for i, texto in enumerate(acierto["Pregunta"])
    ]
    figura = px.bar(
        acierto.sort_values("Pct_Acierto"),
        x="Pct_Acierto",
        y="Etiqueta",
        orientation="h",
        text="Pct_Acierto",
        color="Pct_Acierto",
        color_continuous_scale="RdYlGn",
        range_color=[0, 100],
    )
    plantilla(figura, max(360, len(acierto) * 34), oscuro=oscuro)
    figura.update_layout(
        title="Porcentaje de acierto por pregunta (menor a mayor)",
        coloraxis_showscale=False,
        xaxis_range=[0, 105],
    )
    figura.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    graficar(figura)

    mejor = acierto.iloc[-1]
    peor = acierto.iloc[0]
    c1, c2 = st.columns(2)
    with c1:
        st.success(
            f"**Mayor acierto** ({mejor['Pct_Acierto']:.1f}%): {str(mejor['Pregunta'])[:120]}"
        )
    with c2:
        st.warning(f"**Menor acierto** ({peor['Pct_Acierto']:.1f}%): {str(peor['Pregunta'])[:120]}")

    with st.expander("Clave de respuestas deducida"):
        st.caption(
            "La respuesta correcta de cada pregunta se deduce de la opción más "
            "elegida. La suma de respuestas no modales coincide con los errores "
            "totales implícitos en el puntaje, lo que confirma la clave."
        )
        st.dataframe(
            acierto[["Pregunta", "RespuestaCorrecta", "Aciertos", "Respuestas"]],
            width="stretch",
            hide_index=True,
        )


def _seccion_entregables(contexto: Contexto, oscuro: bool) -> None:
    datos = contexto.entregables.copy()
    if datos.empty:
        st.info("No hay entregables con los filtros seleccionados.")
        return

    columnas = [f"Entregable_{i}" for i in range(1, 6)]
    columnas = [c for c in columnas if c in datos.columns]
    conteos = [int(datos[c].notna().sum()) for c in columnas]

    figura = go.Figure(
        data=[
            go.Bar(
                x=columnas,
                y=conteos,
                marker_color=PALETA[: len(columnas)],
                text=conteos,
                textposition="outside",
            )
        ]
    )
    plantilla(figura, 380, oscuro=oscuro)
    figura.update_layout(title="Notas por Entregable")
    graficar(figura)

    datos["Prom"] = pd.to_numeric(datos["Promedio"], errors="coerce")
    promedios = datos["Prom"].dropna()
    if promedios.empty:
        st.info("Ningún entregable tiene promedio calculado.")
        return

    c1, c2 = st.columns(2)
    with c1:
        st.metric("Con promedio", len(promedios))
    with c2:
        st.metric("Promedio general", f"{promedios.mean():.1f}")

    figura = px.histogram(
        datos,
        x="Prom",
        nbins=10,
        text_auto=True,
        color_discrete_sequence=[PALETA[1]],
    )
    plantilla(figura, 380, oscuro=oscuro)
    figura.update_layout(title="Distribución de Promedios", bargap=0.05)
    graficar(figura)


def _seccion_planes(contexto: Contexto, oscuro: bool) -> None:
    datos = contexto.libro.planes.copy()
    datos["P"] = pd.to_numeric(datos["Puntaje"], errors="coerce")
    datos = datos.dropna(subset=["P"])

    if datos.empty:
        st.info("No hay evaluaciones de planes de emprendimiento.")
        return

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Evaluaciones", len(datos))
    with c2:
        st.metric("Promedio", f"{datos['P'].mean():.1f}/{PUNTAJE_MAXIMO_PLAN}")
    with c3:
        st.metric("Jurados", datos["Jurado"].nunique())

    c1, c2 = st.columns(2)
    with c1:
        por_grupo = datos.groupby("Grupo")["P"].mean().reset_index()
        figura = px.bar(
            por_grupo,
            x="Grupo",
            y="P",
            text="P",
            color="P",
            color_continuous_scale="RdYlGn",
        )
        plantilla(figura, 380, oscuro=oscuro)
        figura.update_layout(
            title="Puntaje por Grupo",
            coloraxis_showscale=False,
            yaxis_range=[0, PUNTAJE_MAXIMO_PLAN * 1.1],
        )
        figura.update_traces(texttemplate="%{text:.1f}", textposition="outside")
        graficar(figura)

    with c2:
        por_jurado = datos.groupby("Jurado")["P"].mean().reset_index()
        figura = px.bar(
            por_jurado,
            x="Jurado",
            y="P",
            text="P",
            color_discrete_sequence=[PALETA[4]],
        )
        plantilla(figura, 380, oscuro=oscuro)
        figura.update_layout(
            title="Puntaje por Jurado",
            yaxis_range=[0, PUNTAJE_MAXIMO_PLAN * 1.1],
        )
        figura.update_traces(texttemplate="%{text:.1f}", textposition="outside")
        graficar(figura)

    figura = px.density_heatmap(
        datos,
        x="Grupo",
        y="Jurado",
        z="P",
        text_auto=".0f",
        color_continuous_scale="RdYlGn",
    )
    plantilla(figura, 350, oscuro=oscuro)
    figura.update_layout(title="Calor: Puntajes por Grupo y Jurado")
    graficar(figura)

    st.markdown("---")
    st.subheader("Ranking final de planes de emprendimiento")

    ranking = ind.ranking_planes(contexto.libro)
    if ranking.empty:
        st.info("Sin evaluaciones de planes.")
        return

    figura = px.bar(
        ranking,
        x="Promedio",
        y="Grupo",
        orientation="h",
        text="Promedio",
        color="Promedio",
        color_continuous_scale="RdYlGn",
        range_color=[0, PUNTAJE_MAXIMO_PLAN],
    )
    plantilla(figura, max(320, len(ranking) * 38), oscuro=oscuro)
    figura.update_layout(
        title="Ranking final por puntaje promedio",
        coloraxis_showscale=False,
        xaxis_range=[0, PUNTAJE_MAXIMO_PLAN * 1.08],
    )
    figura.update_traces(texttemplate="%{text:.2f}", textposition="outside")
    graficar(figura)

    st.dataframe(
        ranking,
        width="stretch",
        hide_index=True,
        column_config={
            "Puesto": st.column_config.NumberColumn("Puesto", format="%d"),
            "Grupo": "Grupo",
            "Promedio": st.column_config.NumberColumn(
                "Promedio", help=f"Puntaje promedio sobre {PUNTAJE_MAXIMO_PLAN}"
            ),
            "Evaluaciones": "Jurados",
        },
    )


def _seccion_personas(contexto: Contexto, oscuro: bool) -> None:
    """Evaluación de mentores y de representantes de comunidad."""
    libro = contexto.libro
    if libro.eval_mentores.empty:
        st.info("No hay evaluaciones de mentores ni representantes.")
        return

    for etiqueta, tabla, indice_texto in (
        ("Mentores", ind.evaluacion_mentores(libro), ind.COLUMNA_TEXTO_MENTOR),
        (
            "Representantes de comunidad",
            ind.evaluacion_representantes(libro),
            ind.COLUMNA_TEXTO_REPRESENTANTE,
        ),
    ):
        st.subheader(f"Evaluación de {etiqueta.lower()}")
        if tabla.empty:
            st.info(f"Sin respuestas de {etiqueta.lower()}.")
            continue

        st.caption(f"Base: {len(tabla)} respuestas.")
        por_dimension, por_persona = ind.resumen_evaluacion(tabla)

        c1, c2 = st.columns(2)
        with c1:
            figura = px.bar(
                por_dimension,
                x="Promedio",
                y="Dimensión",
                orientation="h",
                text="Promedio",
                color="Promedio",
                color_continuous_scale="RdYlGn",
                range_color=[1, 5],
            )
            plantilla(figura, max(300, len(por_dimension) * 46), oscuro=oscuro)
            figura.update_layout(
                title="Promedio por dimensión",
                coloraxis_showscale=False,
                xaxis_range=[0, 5.3],
            )
            figura.update_traces(texttemplate="%{text:.2f}", textposition="outside")
            graficar(figura)

        with c2:
            figura = px.bar(
                por_persona,
                x="Promedio",
                y="Persona",
                orientation="h",
                text="Promedio",
                color_discrete_sequence=[PALETA[4]],
            )
            plantilla(figura, max(300, len(por_persona) * 34), oscuro=oscuro)
            figura.update_layout(title="Promedio por persona evaluada", xaxis_range=[0, 5.3])
            figura.update_traces(texttemplate="%{text:.2f}", textposition="outside")
            graficar(figura)

        comentarios = ind.comentarios_evaluacion(libro, indice_texto)
        if comentarios:
            with st.expander(f"Comentarios ({len(comentarios)})"):
                for texto in comentarios:
                    st.markdown(f"- {texto}")

        st.markdown("---")


def mostrar(contexto: Contexto, *, oscuro: bool = True) -> None:
    """Renderiza la página de evaluaciones."""
    st.title("Evaluaciones")
    encabezado = contexto.resumen_filtros
    if encabezado:
        st.markdown(" | ".join(encabezado))
    st.markdown("---")

    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "Examen inicial",
            "Entregables",
            "Planes de emprendimiento",
            "Mentores y representantes",
        ]
    )
    with tab1:
        _seccion_examen(contexto, oscuro)
    with tab2:
        _seccion_entregables(contexto, oscuro)
    with tab3:
        _seccion_planes(contexto, oscuro)
    with tab4:
        _seccion_personas(contexto, oscuro)
