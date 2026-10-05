"""Página de análisis de becarios."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from core.config import (
    ESCALA_CONOCIMIENTO_MAX,
    PALETA,
    UMBRAL_NIVEL_INTERMEDIO,
)
from core.datos import Contexto
from core.graficos import con_valores, graficar, plantilla
from paginas.comunes import encabezado_filtros
from src.datos import columnas_conocimiento


def _datos_personales(becario: pd.Series, columnas: list[str]) -> None:
    """Ficha del becario seleccionado, sin usar `st.metric` para texto."""
    campos = [
        ("Nombre", becario.get("Nombre")),
        ("Edad", becario.get("Edad")),
        ("Región", becario.get("Region")),
        ("Género", becario.get("Genero")),
        ("País", becario.get("Pais")),
        ("Nivel educativo", becario.get("Nivel educativo")),
        ("Lengua materna", becario.get("Lengua materna")),
        ("Vínculo rural", becario.get("Vinculo_Rural")),
    ]
    columnas_ui = st.columns(4)
    for indice, (etiqueta, valor) in enumerate(campos):
        with columnas_ui[indice % 4]:
            st.markdown(
                f'<div class="dato-personal"><small>{etiqueta}</small><br>'
                f"<strong>{valor if pd.notna(valor) else '—'}</strong></div>",
                unsafe_allow_html=True,
            )

    st.markdown("**Conocimientos autopercibidos:**")
    for columna in columnas:
        nombre = columna.replace("Conoc_", "")
        valor = becario[columna]
        if pd.isna(valor):
            continue
        nivel = int(valor)
        barra = "█" * nivel + "░" * (int(ESCALA_CONOCIMIENTO_MAX) - nivel)
        st.markdown(f"- {nombre}: **{nivel}/{int(ESCALA_CONOCIMIENTO_MAX)}** {barra}")


def mostrar(contexto: Contexto, *, oscuro: bool = True) -> None:
    """Renderiza la página de análisis de becarios."""
    st.title("Análisis de Becarios")
    encabezado_filtros(contexto)
    st.markdown("---")

    becarios = contexto.becarios
    if becarios.empty:
        st.warning("No hay becarios que cumplan los filtros seleccionados.")
        return

    tab1, tab2, tab3, tab4 = st.tabs(
        ["Demografía", "Conocimientos", "Emprendimiento", "Preguntas abiertas"]
    )

    with tab1:
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Total", len(becarios))
        with c2:
            edad_media = becarios["Edad"].mean()
            st.metric("Edad promedio", f"{edad_media:.1f}" if pd.notna(edad_media) else "—")
        with c3:
            st.metric("Con vínculo rural", int((becarios["Vinculo_Rural"] == "Si").sum()))

        c1, c2 = st.columns(2)
        with c1:
            conteo = becarios["Genero"].value_counts()
            figura = go.Figure(
                data=[
                    go.Pie(
                        labels=conteo.index,
                        values=conteo.values,
                        hole=0.45,
                        marker_colors=[PALETA[1], PALETA[0], PALETA[5]][: len(conteo)],
                        textinfo="percent+label+value",
                        textfont_size=12,
                        pull=[0.03] + [0] * (len(conteo) - 1),
                    )
                ]
            )
            plantilla(figura, 380, oscuro=oscuro)
            figura.update_layout(title="Distribución por Género")
            graficar(figura)

        with c2:
            figura = px.histogram(
                becarios,
                x="Edad",
                nbins=12,
                text_auto=True,
                color_discrete_sequence=[PALETA[0]],
            )
            if becarios["Edad"].notna().any():
                figura.add_vline(
                    x=edad_media,
                    line_dash="dash",
                    line_color="red",
                    annotation_text=f"Promedio: {edad_media:.1f}",
                    annotation_position="top right",
                )
            plantilla(figura, 380, oscuro=oscuro)
            figura.update_layout(title="Distribución por Edad", bargap=0.05)
            graficar(figura)

        c1, c2 = st.columns(2)
        for columna, titulo, color in (
            ("Nivel educativo", "Nivel Educativo", PALETA[3]),
            ("Lengua materna", "Lengua Materna", PALETA[4]),
        ):
            with c1 if columna == "Nivel educativo" else c2:
                tabla = becarios[columna].value_counts().reset_index()
                tabla.columns = [columna, "Cantidad"]
                figura = px.bar(
                    tabla,
                    x=columna,
                    y="Cantidad",
                    text="Cantidad",
                    color_discrete_sequence=[color],
                )
                plantilla(figura, 350, oscuro=oscuro)
                figura.update_layout(title=titulo)
                graficar(con_valores(figura, oscuro=oscuro))

        c1, c2 = st.columns(2)
        with c1:
            conteo = becarios["Vinculo_Rural"].value_counts()
            figura = go.Figure(
                data=[
                    go.Pie(
                        labels=conteo.index,
                        values=conteo.values,
                        hole=0.45,
                        marker_colors=[PALETA[3], PALETA[1], PALETA[5]][: len(conteo)],
                        textinfo="percent+label",
                        textfont_size=12,
                    )
                ]
            )
            plantilla(figura, 350, oscuro=oscuro)
            figura.update_layout(title="Vínculo con el Ámbito Rural")
            graficar(figura)
        with c2:
            tabla = becarios["Tiempo_Vinculo_Rural"].value_counts().reset_index()
            tabla.columns = ["Tiempo", "Cantidad"]
            figura = px.bar(
                tabla,
                x="Tiempo",
                y="Cantidad",
                text="Cantidad",
                color_discrete_sequence=[PALETA[5]],
            )
            plantilla(figura, 350, oscuro=oscuro)
            figura.update_layout(title="Tiempo de Vínculo Rural")
            graficar(con_valores(figura, oscuro=oscuro))

    with tab2:
        columnas = columnas_conocimiento(becarios)
        nombres = [c.replace("Conoc_", "") for c in columnas]
        promedios = [becarios[c].mean() for c in columnas]

        figura = go.Figure(
            data=[
                go.Bar(
                    x=nombres,
                    y=promedios,
                    marker_color=PALETA[: len(nombres)],
                    text=[f"{v:.2f}" for v in promedios],
                    textposition="outside",
                    hovertemplate="%{x}<br>Promedio: %{y:.2f}/"
                    f"{int(ESCALA_CONOCIMIENTO_MAX)}<extra></extra>",
                )
            ]
        )
        plantilla(figura, 450, oscuro=oscuro)
        figura.update_layout(
            title=(
                f"Nivel de Conocimiento Promedio (0=Nada, {int(ESCALA_CONOCIMIENTO_MAX)}=Avanzado)"
            ),
            yaxis_range=[0, ESCALA_CONOCIMIENTO_MAX + 0.5],
        )
        figura.add_hline(
            y=UMBRAL_NIVEL_INTERMEDIO,
            line_dash="dash",
            line_color="#aaa",
            annotation_text="Nivel intermedio",
        )
        figura.update_xaxes(tickangle=-25)
        graficar(figura)

        if becarios["Region"].nunique() > 1:
            top_regiones = becarios["Region"].value_counts().head(6).index
            subconjunto = becarios[becarios["Region"].isin(top_regiones)]
            matriz = subconjunto.groupby("Region")[columnas].mean()
            matriz.columns = nombres
            figura = px.imshow(
                matriz,
                text_auto=".1f",
                color_continuous_scale="RdYlGn",
                aspect="auto",
            )
            plantilla(figura, 400, oscuro=oscuro)
            figura.update_layout(title="Conocimientos por Región (Top 6)")
            graficar(figura)

    with tab3:
        columnas_emp = [
            "Ha_Emprendido_Rural",
            "Tiene_Emprendimiento",
            "Ha_Hecho_Canvas",
            "Ha_Capacitacion",
            "Ha_Accedido_Fondos",
            "Ha_Liderado",
        ]
        etiquetas_emp = [
            "Ha emprendido",
            "Tiene emprendimiento",
            "Ha hecho CANVAS",
            "Ha recibido capacitación",
            "Ha accedido a fondos",
            "Ha liderado",
        ]

        figura = make_subplots(
            rows=2,
            cols=3,
            specs=[[{"type": "pie"}] * 3] * 2,
            subplot_titles=etiquetas_emp,
            horizontal_spacing=0.08,
            vertical_spacing=0.15,
        )
        for indice, columna in enumerate(columnas_emp):
            fila, columna_grafico = indice // 3 + 1, indice % 3 + 1
            conteo = becarios[columna].value_counts()
            figura.add_trace(
                go.Pie(
                    labels=conteo.index,
                    values=conteo.values,
                    hole=0.4,
                    marker_colors=[PALETA[3], PALETA[1], PALETA[5]][: len(conteo)],
                    textinfo="percent",
                    textfont_size=10,
                ),
                row=fila,
                col=columna_grafico,
            )
        plantilla(figura, 500, oscuro=oscuro)
        figura.update_layout(title="Experiencia y Emprendimiento", showlegend=False)
        graficar(figura)

        for columna, nombre in (
            ("Comodidad_Publico", "Comodidad hablando en público"),
            ("Capacidad_Liderazgo", "Capacidad de liderazgo"),
            ("Comodidad_Equipo", "Comodidad trabajando en equipo"),
        ):
            conteo = becarios[columna].value_counts().reset_index()
            conteo.columns = ["Respuesta", "Cantidad"]
            figura = px.bar(
                conteo,
                x="Cantidad",
                y="Respuesta",
                orientation="h",
                text="Cantidad",
                color_discrete_sequence=[PALETA[0]],
            )
            plantilla(figura, 250, oscuro=oscuro)
            figura.update_layout(title=nombre, margin=dict(t=40, b=10))
            graficar(con_valores(figura, oscuro=oscuro))

    with tab4:
        for columna, nombre, color in (
            ("Cat_QueEsperaAprender", "Qué Esperaba Aprender", PALETA[0]),
            ("Cat_TemasInteres", "Temas de Interés", PALETA[1]),
            ("Cat_QueEsperaLograr", "Qué Esperaba Lograr", PALETA[2]),
        ):
            if columna not in becarios.columns:
                continue
            conteo = becarios[columna].value_counts().reset_index()
            conteo.columns = ["Categoría", "Cantidad"]
            figura = px.bar(
                conteo,
                x="Cantidad",
                y="Categoría",
                orientation="h",
                text="Cantidad",
                color_discrete_sequence=[color],
            )
            plantilla(figura, max(280, len(conteo) * 38), oscuro=oscuro)
            figura.update_layout(title=f"{nombre} ({len(becarios)} respuestas)", margin=dict(t=50))
            graficar(con_valores(figura, oscuro=oscuro))

    if contexto.filtros.emails and len(contexto.filtros.emails) == 1:
        st.markdown("---")
        st.subheader("Perfil individual del becario")
        _datos_personales(becarios.iloc[0], columnas)
