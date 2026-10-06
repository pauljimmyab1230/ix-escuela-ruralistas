"""Plantilla de gráficos y estilos del dashboard.

Centraliza el tema claro/oscuro y el modo documento para que el selector del
sidebar afecte por igual al CSS y a los gráficos de Plotly.

Dos detalles importantes para exportar imágenes:

- El fondo de la figura es **opaco**. Si fuera transparente, Word y el PDF
  componen el PNG sobre blanco y el texto claro queda ilegible.
- El estilo del título se re-aplica al publicar el gráfico, porque
  ``fig.update_layout(title="texto")`` reemplaza el objeto título completo y
  borra la fuente definida en :func:`plantilla`.
"""

from __future__ import annotations

from typing import Any

from core.config import ALTO_GRAFICO, COLOR_ACENTO

# Colores según el tema activo.
TEMA_OSCURO = {
    "plantilla": "plotly_dark",
    "texto": "#e0e0e0",
    "rejilla": "rgba(255,255,255,0.08)",
    "fondo_grafico": "#0e1117",
    "fondo_sidebar": "linear-gradient(180deg, #0a0d14 0%, #111827 50%, #1a1d24 100%)",
    "titulo_sidebar": COLOR_ACENTO,
    "texto_sidebar": "rgba(255,255,255,0.9)",
    "borde_sidebar": "rgba(255,255,255,0.1)",
}

TEMA_CLARO = {
    "plantilla": "plotly_white",
    "texto": "#1a1a1a",
    "rejilla": "rgba(0,0,0,0.08)",
    "fondo_grafico": "#ffffff",
    "fondo_sidebar": "linear-gradient(180deg, #1a237e 0%, #283593 50%, #3949ab 100%)",
    "titulo_sidebar": "#ffffff",
    "texto_sidebar": "rgba(255,255,255,0.92)",
    "borde_sidebar": "rgba(255,255,255,0.25)",
}

# Tema pensado para pegar la imagen en un documento de texto (Word, PDF).
TEMA_DOCUMENTO = {
    "plantilla": "plotly_white",
    "texto": "#1a1a1a",
    "rejilla": "rgba(0,0,0,0.10)",
    "fondo_grafico": "#ffffff",
    "fondo_sidebar": "linear-gradient(180deg, #1a237e 0%, #283593 50%, #3949ab 100%)",
    "titulo_sidebar": "#ffffff",
    "texto_sidebar": "rgba(255,255,255,0.92)",
    "borde_sidebar": "rgba(255,255,255,0.25)",
}

# Ajustes del título que `update_layout(title="texto")` tiende a borrar.
_ESTILO_TITULO = {
    "font": dict(size=16, color=COLOR_ACENTO),
    "x": 0.5,
    "xanchor": "center",
}

_MODO_DOCUMENTO = False


def establecer_modo_documento(activo: bool) -> None:
    """Activa el tema de exportación para documentos."""
    global _MODO_DOCUMENTO
    _MODO_DOCUMENTO = bool(activo)


def modo_documento_activo() -> bool:
    """Indica si el tema de exportación para documentos está activo."""
    return _MODO_DOCUMENTO


def colores_de_tema(oscuro: bool, documento: bool | None = None) -> dict[str, str]:
    """Devuelve la paleta de estilo para el tema indicado."""
    usar_documento = _MODO_DOCUMENTO if documento is None else documento
    if usar_documento:
        return TEMA_DOCUMENTO
    return TEMA_OSCURO if oscuro else TEMA_CLARO


def aplicar_tema_css(oscuro: bool) -> None:
    """Inyecta los estilos globales del dashboard según el tema activo."""
    import streamlit as st

    tema = colores_de_tema(oscuro)
    st.markdown(
        f"""
        <style>
            .stMetric {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 15px 20px; border-radius: 12px; color: white;
                box-shadow: 0 4px 15px rgba(0,0,0,0.3);
            }}
            .stMetric label {{
                color: rgba(255,255,255,0.85) !important;
                font-size: 0.85rem !important;
            }}
            .stMetric [data-testid="stMetricValue"] {{
                color: white !important; font-size: 1.8rem !important;
                font-weight: 700 !important;
            }}
            .stMetric [data-testid="stMetricValue"] p {{
                overflow-wrap: anywhere;
            }}
            .block-container {{ padding-top: 1rem; }}
            h1 {{
                border-bottom: 3px solid {COLOR_ACENTO};
                padding-bottom: 10px;
                color: {tema["texto"]};
            }}
            h2, h3, h4, h5 {{ color: {tema["texto"]}; }}
            .stTabs [data-baseweb="tab"] {{
                border-radius: 8px 8px 0 0; padding: 10px 20px; font-weight: 600;
            }}
            .stTabs [aria-selected="true"] {{
                background-color: {COLOR_ACENTO} !important; color: white !important;
            }}
            div[data-testid="stSidebar"] {{
                background: {tema["fondo_sidebar"]} !important;
            }}
            div[data-testid="stSidebar"] .stRadio label,
            div[data-testid="stSidebar"] .stSelectbox label,
            div[data-testid="stSidebar"] .stMultiSelect label,
            div[data-testid="stSidebar"] .stSlider label {{
                color: {tema["texto_sidebar"]} !important;
            }}
            div[data-testid="stSidebar"] h1 {{
                color: {tema["titulo_sidebar"]} !important;
                border-bottom: 2px solid rgba(76,175,80,0.3);
            }}
            div[data-testid="stSidebar"] hr {{
                border-color: {tema["borde_sidebar"]};
            }}
            .dato-personal {{
                padding: 0.55rem 0.9rem;
                border-left: 3px solid {COLOR_ACENTO};
                background: rgba(76,175,80,0.10);
                border-radius: 0 8px 8px 0;
                margin-bottom: 0.35rem;
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _asegurar_estilo_titulo(fig: Any) -> None:
    """Re-aplica la fuente del título si fue sobrescrita.

    ``fig.update_layout(title="texto")`` reemplaza el objeto ``title`` completo
    y elimina la fuente, el tamaño y la posición. Aquí se restauran sin tocar
    el texto que la página haya definido.
    """
    titulo = getattr(fig.layout, "title", None)
    if titulo is None or not getattr(titulo, "text", None):
        return
    fig.update_layout(title=dict(text=titulo.text, **_ESTILO_TITULO))


def plantilla(fig: Any, altura: int = ALTO_GRAFICO, oscuro: bool = True) -> Any:
    """Aplica la identidad visual común a una figura de Plotly."""
    tema = colores_de_tema(oscuro)
    fig.update_layout(
        template=tema["plantilla"],
        font=dict(family="Segoe UI, sans-serif", size=12, color=tema["texto"]),
        title=dict(text=None, **_ESTILO_TITULO),
        margin=dict(t=50, b=40, l=40, r=20),
        height=altura,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.25,
            xanchor="center",
            x=0.5,
            font_size=11,
        ),
        # Fondo opaco: con transparencia, Word y el PDF componen el PNG sobre
        # blanco y el texto claro del tema oscuro queda ilegible.
        plot_bgcolor=tema["fondo_grafico"],
        paper_bgcolor=tema["fondo_grafico"],
    )
    fig.update_xaxes(showgrid=True, gridwidth=0.5, gridcolor=tema["rejilla"])
    fig.update_yaxes(showgrid=True, gridwidth=0.5, gridcolor=tema["rejilla"])
    return fig


def con_valores(fig: Any, oscuro: bool = True) -> Any:
    """Muestra el valor numérico sobre cada barra o punto."""
    tema = colores_de_tema(oscuro)
    fig.update_traces(
        textposition="outside",
        textfont_size=11,
        textfont_color=tema["texto"],
    )
    return fig


def graficar(fig: Any, *, usar_anchura_completa: bool = True) -> None:
    """Publica una figura en Streamlit sin los avisos de API deprecada."""
    import streamlit as st

    _asegurar_estilo_titulo(fig)
    st.plotly_chart(fig, width="stretch" if usar_anchura_completa else "content")
