"""Página de encuestas de satisfacción por sesión."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from core.config import (
    NOMBRES_SESIONES,
    PALETA,
    RANGO_CALIFICACION,
    RANGO_CALIFICACION_COLOR,
)
from core.datos import Contexto, es_respuesta_util
from core.graficos import con_valores, graficar, plantilla
from src import indicadores as ind


def _nombre_sesion(numero: float | int) -> str:
    return NOMBRES_SESIONES.get(int(numero), f"Sesión {int(numero)}")


def mostrar(contexto: Contexto, *, oscuro: bool = True) -> None:
    """Renderiza la página de encuestas."""
    st.title("Encuestas de Satisfacción por Sesión")
    st.markdown("Resultados de las encuestas (sin la sesión 1 · bienvenida)")
    st.markdown("---")

    encuestas = contexto.encuestas
    if encuestas.empty:
        st.warning("No hay encuestas con los filtros seleccionados.")
        return

    opciones = sorted(encuestas["Sesion_num"].dropna().unique().tolist())
    sesiones_elegidas = st.multiselect(
        "Sesiones",
        opciones,
        default=opciones,
        format_func=lambda s: f"S{int(s)} · {_nombre_sesion(s)}",
    )
    encuestas = encuestas[encuestas["Sesion_num"].isin(sesiones_elegidas)]

    if encuestas.empty:
        st.info("Ninguna sesión seleccionada tiene encuestas.")
        return

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Encuestas", len(encuestas))
    with c2:
        promedio = encuestas["Calif_num"].mean()
        st.metric(
            "Calificación promedio",
            f"{promedio:.2f}/5" if pd.notna(promedio) else "N/A",
        )
    with c3:
        st.metric("Sesiones", len(sesiones_elegidas))
    with c4:
        st.metric(
            "Respuestas abiertas",
            int(encuestas["Cat_Ideas"].apply(es_respuesta_util).sum()),
        )

    st.markdown("---")
    tab1, tab2, tab3, tab4 = st.tabs(
        ["Calificación", "Categorías abiertas", "Detalle por sesión", "Escalas por sesión"]
    )

    with tab1:
        tabla = encuestas.groupby("Sesion_num")["Calif_num"].mean().reset_index()
        tabla.columns = ["Sesion", "Cal"]
        tabla["Etiqueta"] = tabla["Sesion"].map(lambda s: f"S{int(s)} · {_nombre_sesion(s)[:18]}")
        figura = px.bar(
            tabla,
            x="Etiqueta",
            y="Cal",
            text="Cal",
            color="Cal",
            color_continuous_scale="RdYlGn",
            range_color=list(RANGO_CALIFICACION_COLOR),
        )
        plantilla(figura, 420, oscuro=oscuro)
        figura.update_layout(
            title="Calificación Promedio por Sesión",
            yaxis_range=list(RANGO_CALIFICACION),
            coloraxis_showscale=False,
        )
        figura.update_traces(
            texttemplate="%{text:.2f}",
            textposition="outside",
            textfont_size=12,
        )
        graficar(figura)

    with tab2:
        for columna, nombre, color in (
            ("Cat_Ideas", "Ideas aprendidas", PALETA[0]),
            ("Cat_Gusto", "Lo que más gustó", PALETA[1]),
            ("Cat_Mejora", "Aspectos a mejorar", PALETA[2]),
            ("Cat_Profundizar", "Temas a profundizar", PALETA[3]),
        ):
            validas = encuestas[encuestas[columna].apply(es_respuesta_util)]
            if validas.empty:
                st.info(f"Sin respuestas válidas en «{nombre}».")
                continue
            conteo = validas[columna].value_counts().reset_index()
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
            figura.update_layout(
                title=f"{nombre} ({len(validas)} respuestas válidas)",
                margin=dict(t=50),
            )
            graficar(con_valores(figura, oscuro=oscuro))

    with tab3:
        for sesion in sesiones_elegidas:
            subconjunto = encuestas[encuestas["Sesion_num"] == sesion]
            with st.expander(f"S{int(sesion)} · {_nombre_sesion(sesion)}", expanded=False):
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.metric("Encuestas", len(subconjunto))
                with c2:
                    promedio = subconjunto["Calif_num"].mean()
                    st.metric(
                        "Calificación",
                        f"{promedio:.2f}/5" if pd.notna(promedio) else "N/A",
                    )
                with c3:
                    st.metric(
                        "Respuestas abiertas",
                        int(subconjunto["Cat_Ideas"].apply(es_respuesta_util).sum()),
                    )

                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("**Ideas aprendidas:**")
                    conteo = subconjunto[subconjunto["Cat_Ideas"].apply(es_respuesta_util)][
                        "Cat_Ideas"
                    ].value_counts()
                    if conteo.empty:
                        st.caption("Sin respuestas.")
                    for categoria, cantidad in conteo.items():
                        st.markdown(f"- {categoria}: **{cantidad}**")
                with c2:
                    st.markdown("**Lo que más gustó:**")
                    conteo = subconjunto[subconjunto["Cat_Gusto"].apply(es_respuesta_util)][
                        "Cat_Gusto"
                    ].value_counts()
                    if conteo.empty:
                        st.caption("Sin respuestas.")
                    for categoria, cantidad in conteo.items():
                        st.markdown(f"- {categoria}: **{cantidad}**")

    with tab4:
        st.subheader("Utilidad, claridad y aprendizaje por sesión")
        escalas = ind.escalas_por_sesion(contexto.libro)
        if escalas.empty:
            st.info("No hay escalas de satisfacción registradas.")
            return

        escalas = escalas[escalas["Sesion"].isin(sesiones_elegidas)].copy()
        if escalas.empty:
            st.info("Ninguna sesión seleccionada tiene escalas registradas.")
            return

        escalas["Etiqueta"] = escalas["Sesion"].map(
            lambda s: f"S{int(s)} · {_nombre_sesion(s)[:16]}"
        )

        for columna, etiqueta, color in (
            ("Utilidad", "Utilidad de los temas y talleres", PALETA[0]),
            ("Claridad", "Claridad del tema desarrollado", PALETA[3]),
            ("Aprendizaje", "Aprendizaje percibido", PALETA[2]),
        ):
            if columna not in escalas.columns:
                continue
            valido = escalas.dropna(subset=[columna])
            if valido.empty:
                st.info(f"Sin respuestas de «{etiqueta}».")
                continue

            figura = px.bar(
                valido,
                x="Etiqueta",
                y=columna,
                text=columna,
                color_discrete_sequence=[color],
            )
            plantilla(figura, 380, oscuro=oscuro)
            figura.update_layout(
                title=f"{etiqueta} (promedio 1-5)",
                yaxis_range=[0, 5.4],
            )
            figura.update_traces(texttemplate="%{text:.2f}", textposition="outside")
            graficar(figura)
            st.caption(
                "n de respuestas por sesión: "
                + ", ".join(
                    f"S{int(s)}={int(n)}"
                    for s, n in zip(valido["Sesion"], valido[f"{columna}_n"], strict=True)
                    if pd.notna(n)
                )
            )

        st.markdown("---")
        st.subheader("Satisfacción y metodología")
        hay_satisfaccion = (
            "Satisfaccion" in escalas.columns and escalas["Satisfaccion"].notna().any()
        )
        if not hay_satisfaccion:
            st.info(
                "La satisfacción general y la metodología solo se preguntaron "
                "en la sesión de bienvenida; no hay serie temporal que comparar."
            )
        else:
            for columna, etiqueta, color in (
                ("Satisfaccion", "Satisfacción con la participación", PALETA[1]),
                ("Metodologia", "Metodología y acompañamiento", PALETA[4]),
            ):
                valido = escalas.dropna(subset=[columna])
                if valido.empty:
                    continue
                figura = px.bar(
                    valido,
                    x="Etiqueta",
                    y=columna,
                    text=columna,
                    color_discrete_sequence=[color],
                )
                plantilla(figura, 360, oscuro=oscuro)
                figura.update_layout(title=f"{etiqueta} (promedio 1-5)", yaxis_range=[0, 5.4])
                figura.update_traces(texttemplate="%{text:.2f}", textposition="outside")
                graficar(figura)
