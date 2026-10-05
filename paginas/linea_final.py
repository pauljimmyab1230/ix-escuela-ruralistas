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
from src import indicadores as ind
from src.datos import (
    matriz_conocimiento_linea_base,
    matriz_conocimiento_linea_final,
    tabla_expectativas_vs_resultados,
)
from src.indicadores import (
    PREFIJO_ACTORES,
    PREFIJO_COMODIDAD_PUBLICO,
    PREFIJO_LIDERAZGO,
)
from src.normalizacion import ESCALA_ACTORES, ESCALA_COMODIDAD, ESCALA_LIDERAZGO


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


def _cambio_habilidades(contexto: Contexto, oscuro: bool) -> None:
    """Cambio en las tres habilidades blandas medidas antes y después."""
    st.subheader("Cambio en habilidades blandas")

    resumen = ind.comparacion_habilidades(contexto.libro)
    if resumen.empty:
        st.info("No hay datos comparables de habilidades blandas.")
        return

    st.caption(
        "Escala ordinal de comodidad: 1 = muy incómodo … 5 = muy cómodo. "
        "Liderazgo y reconocimiento de actores: 0 = no, 1 = tal vez / más o "
        "menos, 2 = sí."
    )

    tabla = resumen.rename(
        columns={
            "Habilidad": "Habilidad",
            "LineaBase_Prom": "Línea base (prom.)",
            "LineaBase_n": "n base",
            "LineaFinal_Prom": "Línea final (prom.)",
            "LineaFinal_n": "n final",
            "Pareado_Prom": "Pareado (prom.)",
            "Pareado_n": "n pareado",
        }
    )
    columnas_visibles = [
        "Habilidad",
        "Línea base (prom.)",
        "n base",
        "Línea final (prom.)",
        "n final",
        "Pareado (prom.)",
        "n pareado",
    ]
    st.dataframe(tabla[columnas_visibles], width="stretch", hide_index=True)

    definiciones = [
        ("Comodidad para hablar en público", PREFIJO_COMODIDAD_PUBLICO, ESCALA_COMODIDAD),
        ("Capacidad de liderazgo", PREFIJO_LIDERAZGO, ESCALA_LIDERAZGO),
        (
            "Reconocimiento de actores de la comunidad",
            PREFIJO_ACTORES,
            ESCALA_ACTORES,
        ),
    ]

    for etiqueta, prefijo, escala in definiciones:
        try:
            distribucion = ind.distribucion_habilidad(contexto.libro, prefijo, escala)
        except KeyError:
            continue
        if distribucion.empty:
            continue

        largo = distribucion.melt(id_vars="Nivel", var_name="Medición", value_name="Cantidad")
        figura = px.bar(
            largo,
            x="Nivel",
            y="Cantidad",
            color="Medición",
            barmode="group",
            text="Cantidad",
            color_discrete_sequence=[PALETA[0], PALETA[1]],
        )
        plantilla(figura, 360, oscuro=oscuro)
        figura.update_layout(
            title=f"{etiqueta}: antes y después",
            legend=dict(orientation="h", y=-0.25),
        )
        graficar(con_valores(figura, oscuro=oscuro))

    st.caption(
        "La columna «Pareado» compara solo a quienes respondieron las dos "
        "mediciones; el número exacto se indica en cada fila."
    )


def mostrar(contexto: Contexto, *, oscuro: bool = True) -> None:
    """Renderiza la página de línea base vs línea final."""
    st.title("Comparación: Línea Base vs Línea Final")
    st.markdown("Evolución de los conocimientos autopercibidos antes y después del programa.")
    encabezado_filtros(contexto)
    st.markdown("---")

    libro = contexto.libro
    poblaciones = ind.poblaciones_de_mediciones(libro)
    total_base = poblaciones["Linea base"]
    total_final = poblaciones["Linea final"]
    comunes = poblaciones["Ambas mediciones"]

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Línea Base", f"{total_base} becarios")
    with c2:
        st.metric("Línea Final", f"{total_final} respuestas")
    with c3:
        st.metric("Con ambas mediciones", f"{comunes} becarios")
    with c4:
        tasa = (total_final / total_base * 100) if total_base else 0
        st.metric("Tasa de respuesta", f"{tasa:.0f}%")

    st.warning(
        "**Las dos mediciones tienen muestras distintas.** La línea base "
        f"cubre a {total_base} becarios inscritos y la línea final a "
        f"{total_final} personas que respondieron el formulario de cierre; "
        f"solo {comunes} aparecen en ambas. Los promedios comparados de las "
        "dos primeras gráficas se calculan sobre cada muestra por separado, "
        "por lo que reflejan tanto el cambio real como la diferencia de "
        "quién respondió. Los mapas de calor individuales y la comparación "
        "pareada usan únicamente a los que tienen ambas mediciones."
    )

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
    _cambio_habilidades(contexto, oscuro)

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
