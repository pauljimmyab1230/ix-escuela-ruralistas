"""Página de participación: inscritos, activos, certificados, asistencia y retención."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from core.config import NOMBRES_SESIONES, PALETA
from core.datos import Contexto
from core.graficos import con_valores, graficar, plantilla
from paginas.comunes import encabezado_filtros
from src import indicadores as ind


def _etiqueta_sesion(fecha: str, numero: float | None) -> str:
    if pd.isna(numero):
        return fecha
    return f"S{int(numero)} · {NOMBRES_SESIONES.get(int(numero), '')}"


def _embudo_participacion(resumen: dict[str, int], oscuro: bool) -> go.Figure:
    """Embudo inscritos -> activos -> certificados."""
    etiquetas = ["Inscritos", "Activos", "Certificados"]
    valores = [resumen[e] for e in etiquetas]
    colores = [PALETA[0], PALETA[3], PALETA[2]]

    figura = go.Figure(
        go.Funnel(
            y=etiquetas,
            x=valores,
            textinfo="value+percent initial",
            marker=dict(color=colores),
            textposition="inside",
        )
    )
    plantilla(figura, 380, oscuro=oscuro)
    figura.update_layout(
        title="Participación: inscritos, activos y certificados",
        yaxis=dict(categoryorder="array", categoryarray=etiquetas),
    )
    return figura


def _detalle_criterios(resumen: dict[str, int]) -> None:
    """Explica de dónde sale cada número para que el informe sea auditable."""
    st.caption(
        f"**Inscritos** = becarios en el registro ({resumen['Inscritos']}). "
        f"**Activos** = asistieron al menos a una sesión ({resumen['Activos']}). "
        f"**Certificados** = aprobaron el examen, entregaron al menos un "
        f"entregable con nota y superaron el "
        f"{ind.UMBRAL_ASISTENCIA_CERTIFICADO * 100:.0f}% de asistencia "
        f"({resumen['Certificados']})."
    )


def _asistencia_por_sesion(tabla: pd.DataFrame, oscuro: bool) -> None:
    if tabla.empty:
        st.info("No hay registros de asistencia de becarios.")
        return

    tabla = tabla.copy()
    tabla["Etiqueta"] = [
        _etiqueta_sesion(f, s) for f, s in zip(tabla["Fecha"], tabla["Sesion"], strict=True)
    ]

    figura = px.bar(
        tabla,
        x="Etiqueta",
        y="Asistentes",
        text="Asistentes",
        color_discrete_sequence=[PALETA[3]],
    )
    plantilla(figura, 400, oscuro=oscuro)
    figura.update_layout(title="Asistencia de becarios por sesión (n)")
    graficar(con_valores(figura, oscuro=oscuro))

    figura = px.bar(
        tabla,
        x="Etiqueta",
        y="Pct_Inscritos",
        text="Pct_Inscritos",
        color_discrete_sequence=[PALETA[0]],
    )
    plantilla(figura, 400, oscuro=oscuro)
    figura.update_layout(
        title="Asistencia de becarios por sesión (% sobre inscritos)",
        yaxis_range=[0, 100],
    )
    figura.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    graficar(figura)


def _retencion_por_sesion(tabla: pd.DataFrame, oscuro: bool) -> None:
    if tabla.empty:
        return

    tabla = tabla.copy()
    tabla["Etiqueta"] = [
        _etiqueta_sesion(f, s) for f, s in zip(tabla["Fecha"], tabla["Sesion"], strict=True)
    ]

    figura = go.Figure()
    figura.add_trace(
        go.Scatter(
            x=tabla["Etiqueta"],
            y=tabla["Retencion"],
            mode="lines+markers+text",
            line=dict(color=PALETA[1], width=3),
            marker=dict(size=11),
            text=[f"{v:.1f}%" for v in tabla["Retencion"]],
            textposition="top center",
            textfont=dict(size=11),
        )
    )
    plantilla(figura, 400, oscuro=oscuro)
    figura.update_layout(
        title="Tasa de retención por sesión (vs. asistentes de la sesión 1)",
        yaxis_range=[0, max(120, float(tabla["Retencion"].max()) * 1.15)],
    )
    figura.add_hline(y=100, line_dash="dash", line_color="#aaa", annotation_text="Base sesión 1")
    graficar(figura)


def mostrar(contexto: Contexto, *, oscuro: bool = True) -> None:
    """Renderiza la página de participación."""
    st.title("Participación")
    st.markdown(
        "Indicadores de cobertura y permanencia. Todos los porcentajes se "
        "calculan sobre los becarios inscritos, sin mentores, representantes "
        "ni invitados."
    )
    encabezado_filtros(contexto)
    st.markdown("---")

    libro = contexto.libro
    resumen = ind.resumen_participacion(libro)
    tabla = ind.asistencia_por_sesion(libro)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Inscritos", resumen["Inscritos"])
    with c2:
        st.metric("Activos", resumen["Activos"])
    with c3:
        st.metric("Certificados", resumen["Certificados"])
    with c4:
        tasa = resumen["Certificados"] / resumen["Inscritos"] * 100 if resumen["Inscritos"] else 0
        st.metric("Tasa de certificación", f"{tasa:.0f}%")

    _detalle_criterios(resumen)
    st.markdown("---")

    c1, c2 = st.columns(2)
    with c1:
        graficar(_embudo_participacion(resumen, oscuro))
    with c2:
        if not tabla.empty:
            st.markdown("**Resumen por sesión**")
            mostrar_tabla = tabla.rename(
                columns={
                    "Sesion": "Sesión",
                    "Asistentes": "Asistentes (n)",
                    "Pct_Inscritos": "% inscritos",
                    "Retencion": "Retención %",
                }
            )
            st.dataframe(
                mostrar_tabla[["Sesión", "Fecha", "Asistentes (n)", "% inscritos", "Retención %"]],
                width="stretch",
                hide_index=True,
            )
        else:
            st.info("Sin datos de asistencia.")

    st.markdown("---")
    st.subheader("Asistencia por sesión")
    _asistencia_por_sesion(tabla, oscuro)

    st.markdown("---")
    st.subheader("Retención")
    _retencion_por_sesion(tabla, oscuro)
    st.caption(
        "La retención compara los asistentes de cada sesión con los de la "
        "sesión 1. Un valor por encima del 100% indica que hubo más personas "
        "que en la apertura, no que se haya superado el total de inscritos."
    )
