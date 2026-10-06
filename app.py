"""Dashboard de sistematización de la IX Escuela de Jóvenes Ruralistas.

Punto de entrada de Streamlit. La lógica vive en `core/` y las vistas en
`paginas/`.

Ejecución:
    streamlit run app.py
"""

from __future__ import annotations

import streamlit as st

from core.config import (
    ICONO_APP,
    PAGINAS,
    PIE_PAGINA,
    TITULO_APP,
)
from core.datos import (
    Filtros,
    cargar_o_mostrar_error,
    construir_contexto,
    etiquetas_de_becarios,
    opciones_de_filtros,
)
from core.graficos import aplicar_tema_css, establecer_modo_documento
from paginas import (
    asistencia,
    becarios,
    encuestas,
    evaluaciones,
    linea_final,
    participacion,
    resumen,
)

st.set_page_config(
    page_title=TITULO_APP,
    page_icon=ICONO_APP,
    layout="wide",
    initial_sidebar_state="expanded",
)

_PAGINAS_RENDER = {
    "resumen": resumen.mostrar,
    "participacion": participacion.mostrar,
    "becarios": becarios.mostrar,
    "encuestas": encuestas.mostrar,
    "asistencia": asistencia.mostrar,
    "evaluaciones": evaluaciones.mostrar,
    "linea_final": linea_final.mostrar,
}


def _construir_filtros(libro) -> Filtros:
    """Lee la selección del sidebar y la convierte en un objeto `Filtros`."""
    regiones, generos = opciones_de_filtros(libro)

    region = st.selectbox("Región", ["Todas", *regiones])
    genero = st.selectbox("Género", ["Todos", *generos])

    st.markdown("---")
    st.markdown("### Filtro individual")

    etiquetas = etiquetas_de_becarios(libro.becarios)
    seleccion = st.multiselect(
        "Seleccionar becario(s)",
        options=etiquetas["Etiqueta"].tolist(),
        default=[],
        help="Selecciona uno o varios becarios para ver sus datos individuales.",
    )
    emails: tuple[str, ...] = ()
    if seleccion:
        emails = tuple(etiquetas[etiquetas["Etiqueta"].isin(seleccion)]["Email"].tolist())

    return Filtros(region=region, genero=genero, emails=emails)


def main() -> None:
    """Renderiza el sidebar y la página activa."""
    libro = cargar_o_mostrar_error()
    if libro is None:
        return

    with st.sidebar:
        st.markdown(f"# {ICONO_APP} IX Escuela")
        st.markdown("### Jóvenes Ruralistas")
        st.markdown("---")

        etiquetas_paginas = [etiqueta for etiqueta, _ in PAGINAS]
        seleccion = st.radio("Navegación", etiquetas_paginas, label_visibility="collapsed")
        clave_pagina = dict(PAGINAS)[seleccion]

        st.markdown("---")
        oscuro = st.toggle("Modo oscuro", value=True)
        documento = st.toggle(
            "Modo documento",
            value=False,
            help=(
                "Fondo blanco y texto oscuro en los gráficos. Actívalo antes de "
                "descargar o capturar las imágenes que vayas a pegar en Word o en "
                "un PDF; con el tema oscuro el texto se ve mal sobre papel blanco."
            ),
        )
        establecer_modo_documento(documento)
        aplicar_tema_css(oscuro)

        if documento:
            st.info(
                "Modo documento activo. Descarga las imágenes con la cámara del "
                "gráfico y pégalas en tu informe."
            )

        st.markdown("---")
        filtros = _construir_filtros(libro)

        st.markdown("---")
        st.caption(PIE_PAGINA)

    contexto = construir_contexto(libro, filtros)
    _PAGINAS_RENDER[clave_pagina](contexto, oscuro=oscuro)


if __name__ == "__main__":
    main()
