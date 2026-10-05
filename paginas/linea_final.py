"""Página de comparación entre línea base y línea final."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from core.config import (
    CONOCIMIENTOS_CORTOS,
    ESCALA_CONOCIMIENTO_MAX,
    PALETA,
)
from core.datos import Contexto
from core.graficos import con_valores, graficar, plantilla
from paginas.comunes import (
    encabezado_filtros,
    figura_cambio_conocimientos,
    figura_conocimientos_antes_despues,
)
from src.datos import (
    matriz_conocimiento_linea_base,
    matriz_conocimiento_linea_final,
    tabla_expectativas_vs_resultados,
)


def _heatmap(matriz: pd.DataFrame, titulo: str, oscuro: bool, *, diferencia: bool) -> go.Figure:
    escala = "RdBu" if diferencia else "RdYlGn"
    rango = (-3, 3) if diferencia else (0, int(ESCALA_CONOCIMIENTO_MAX))
    formato = "+.0f" if diferencia else ".0f"
    figura = px.imshow(
        matriz,
        text_auto=formato,
        color_continuous_scale=escala,
        zmin=rango[0],
        zmax=rango[1],
        aspect="auto",
        labels=dict(x="Conocimiento", y="Becario", color="Cambio" if diferencia else "Nivel"),
    )
    plantilla(figura, max(400, len(matriz) * 25), oscuro=oscuro)
    figura.update_layout(
        title=titulo,
        coloraxis_colorbar_title="Cambio" if diferencia else "Nivel",
    )
    return figura


def _expectativas_vs_resultados(contexto: Contexto, oscuro: bool) -> None:
    st.subheader("Comparativa: qué esperaba aprender vs qué aprendió")
    comparacion = tabla_expectativas_vs_resultados(contexto.libro)
    if comparacion.empty:
        st.info("No hay datos para comparar expectativas y resultados.")
        return

    st.caption(
        "Atención a los denominadores: «Esperaba» se alimenta de "
        f"{len(contexto.libro.becarios)} respuestas de línea base y «Aprendió» "
        f"de {len(contexto.libro.linea_final)} de línea final. Las diferencias "
        "absolutas reflejan tanto la cobertura como el contenido."
    )

    figura = go.Figure()
    figura.add_trace(
        go.Bar(
            name="Esperaba aprender (línea base)",
            y=comparacion["Categoria"],
            x=comparacion["Esperaba"],
            orientation="h",
            marker_color=PALETA[0],
            text=comparacion["Esperaba"],
            textposition="outside",
        )
    )
    figura.add_trace(
        go.Bar(
            name="Aprendió (línea final)",
            y=comparacion["Categoria"],
            x=comparacion["Aprendio"],
            orientation="h",
            marker_color=PALETA[1],
            text=comparacion["Aprendio"],
            textposition="outside",
        )
    )
    plantilla(figura, max(350, len(comparacion) * 45), oscuro=oscuro)
    figura.update_layout(title="Expectativas vs Resultados", barmode="group")
    graficar(figura)

    colores = [PALETA[3] if d > 0 else PALETA[6] if d < 0 else "#888" for d in comparacion["Diff"]]
    figura = go.Figure(
        data=[
            go.Bar(
                y=comparacion["Categoria"],
                x=comparacion["Diff"],
                orientation="h",
                marker_color=colores,
                text=[f"{d:+d}" for d in comparacion["Diff"]],
                textposition="outside",
            )
        ]
    )
    plantilla(figura, max(300, len(comparacion) * 40), oscuro=oscuro)
    figura.update_layout(
        title="Diferencia: Aprendió - Esperaba (verde = superó, rojo = por debajo)"
    )
    figura.add_vline(x=0, line_dash="solid", line_color="#aaa")
    graficar(figura)


def mostrar(contexto: Contexto, *, oscuro: bool = True) -> None:
    """Renderiza la página de línea base vs línea final."""
    st.title("Comparación: Línea Base vs Línea Final")
    st.markdown("Evolución de los conocimientos autopercibidos antes y después del programa.")
    encabezado_filtros(contexto)
    st.markdown("---")

    libro = contexto.libro
    total_base = len(contexto.becarios)
    total_final = len(contexto.linea_final)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Línea Base", f"{total_base} becarios")
    with c2:
        st.metric("Línea Final", f"{total_final} respuestas")
    with c3:
        tasa = (total_final / total_base * 100) if total_base else 0
        st.metric("Tasa de respuesta", f"{tasa:.0f}%")

    st.markdown("---")

    figura = figura_conocimientos_antes_despues(contexto, altura=480, oscuro=oscuro)
    graficar(figura)

    graficar(figura_cambio_conocimientos(contexto, oscuro=oscuro))

    st.markdown("---")
    st.subheader("Mapas de calor individuales")

    if total_base == 0:
        st.warning("No hay becarios con los filtros seleccionados.")
        return

    matriz_base = matriz_conocimiento_linea_base(contexto.becarios)
    matriz_base.columns = CONOCIMIENTOS_CORTOS
    graficar(
        _heatmap(
            matriz_base,
            "Línea Base: nivel de conocimiento por becario (0-3)",
            oscuro,
            diferencia=False,
        )
    )

    matriz_final = matriz_conocimiento_linea_final(libro)
    if total_final:
        matriz_final.columns = CONOCIMIENTOS_CORTOS
        graficar(
            _heatmap(
                matriz_final,
                "Línea Final: nivel de conocimiento por becario (0-3)",
                oscuro,
                diferencia=False,
            )
        )
    else:
        st.info("No hay respuestas de línea final con los filtros seleccionados.")

    comunes = sorted(set(matriz_base.index) & set(matriz_final.index))
    if comunes:
        diferencia = matriz_final.loc[comunes].astype(float) - matriz_base.loc[comunes].astype(
            float
        )
        graficar(
            _heatmap(
                diferencia,
                "Cambio individual: Línea Final - Línea Base (verde = mejoró)",
                oscuro,
                diferencia=True,
            )
        )
        st.caption(f"Solo se comparan los {len(comunes)} becarios presentes en ambas mediciones.")
    else:
        st.info("No hay becarios presentes en ambas mediciones para comparar.")

    st.markdown("---")
    _expectativas_vs_resultados(contexto, oscuro)

    st.subheader("Categorías de la Línea Final")
    for columna, nombre, color in (
        ("Cat_Aprendido", "Qué aprendieron", PALETA[0]),
        ("Cat_TemasFinal", "Temas de interés", PALETA[1]),
        ("Cat_Logrado", "Qué lograron", PALETA[2]),
    ):
        if contexto.linea_final.empty or columna not in contexto.linea_final.columns:
            continue
        conteo = contexto.linea_final[columna].value_counts().reset_index()
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
        figura.update_layout(title=nombre, margin=dict(t=50))
        graficar(con_valores(figura, oscuro=oscuro))
