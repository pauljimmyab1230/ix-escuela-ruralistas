"""Pruebas de la plantilla de gráficos y de la exportación para documentos."""

from __future__ import annotations

import plotly.graph_objects as go
import pytest

from core.graficos import (
    TEMA_CLARO,
    TEMA_DOCUMENTO,
    TEMA_OSCURO,
    _asegurar_estilo_titulo,
    colores_de_tema,
    con_valores,
    establecer_modo_documento,
    modo_documento_activo,
    plantilla,
)


@pytest.fixture(autouse=True)
def _restablecer_modo_documento():
    establecer_modo_documento(False)
    yield
    establecer_modo_documento(False)


def _figura_ejemplo() -> go.Figure:
    return go.Figure(data=[go.Bar(x=["a", "b"], y=[1, 2])])


class TestFondoOpaco:
    """El fondo debe ser opaco: Word compone lo transparente sobre blanco."""

    @pytest.mark.parametrize("oscuro", [True, False])
    def test_paper_bgcolor_no_es_transparente(self, oscuro):
        fig = plantilla(_figura_ejemplo(), oscuro=oscuro)
        fondo = fig.layout.paper_bgcolor
        assert fondo is not None
        assert "rgba(0,0,0,0)" not in str(fondo)
        assert str(fondo).startswith("#") or "rgb(" in str(fondo)

    @pytest.mark.parametrize("oscuro", [True, False])
    def test_plot_bgcolor_no_es_transparente(self, oscuro):
        fig = plantilla(_figura_ejemplo(), oscuro=oscuro)
        assert "rgba(0,0,0,0)" not in str(fig.layout.plot_bgcolor)

    def test_fondo_del_tema_se_usa_en_la_figura(self):
        fig = plantilla(_figura_ejemplo(), oscuro=True)
        assert str(fig.layout.paper_bgcolor).lower() == TEMA_OSCURO["fondo_grafico"]
        fig = plantilla(_figura_ejemplo(), oscuro=False)
        assert str(fig.layout.paper_bgcolor).lower() == TEMA_CLARO["fondo_grafico"]


class TestEstiloDelTitulo:
    """`update_layout(title='texto')` borra la fuente; debe poder restaurarse."""

    def test_update_layout_con_cadena_borra_la_fuente(self):
        fig = plantilla(_figura_ejemplo(), oscuro=True)
        fig.update_layout(title="Distribución por Género")
        # Comportamiento conocido de Plotly: se pierde el estilo.
        assert fig.layout.title.font is None or fig.layout.title.font.color is None

    def test_asegurar_estilo_restaura_fuente_y_posicion(self):
        fig = plantilla(_figura_ejemplo(), oscuro=True)
        fig.update_layout(title="Distribución por Género")
        _asegurar_estilo_titulo(fig)

        assert fig.layout.title.text == "Distribución por Género"
        assert fig.layout.title.font.color == "#4CAF50"
        assert fig.layout.title.font.size == 16
        assert fig.layout.title.x == 0.5

    def test_sin_titulo_no_hace_nada(self):
        fig = plantilla(_figura_ejemplo(), oscuro=True)
        _asegurar_estilo_titulo(fig)
        assert not fig.layout.title.text

    def test_conserva_titulos_largos(self):
        fig = plantilla(_figura_ejemplo(), oscuro=True)
        texto = "Acierto por pregunta (menor a mayor)"
        fig.update_layout(title=texto)
        _asegurar_estilo_titulo(fig)
        assert fig.layout.title.text == texto


class TestModoDocumento:
    def test_por_defecto_desactivado(self):
        assert modo_documento_activo() is False

    def test_activa_y_desactiva(self):
        establecer_modo_documento(True)
        assert modo_documento_activo() is True
        establecer_modo_documento(False)
        assert modo_documento_activo() is False

    def test_tema_documento_usa_fondo_blanco_y_texto_oscuro(self):
        assert TEMA_DOCUMENTO["fondo_grafico"] == "#ffffff"
        assert TEMA_DOCUMENTO["texto"] == "#1a1a1a"

    def test_colores_de_tema_respeta_el_modo(self):
        establecer_modo_documento(True)
        assert colores_de_tema(oscuro=True) is TEMA_DOCUMENTO
        assert colores_de_tema(oscuro=False) is TEMA_DOCUMENTO

        establecer_modo_documento(False)
        assert colores_de_tema(oscuro=True) is TEMA_OSCURO
        assert colores_de_tema(oscuro=False) is TEMA_CLARO

    def test_parametro_explicito_tiene_prioridad(self):
        establecer_modo_documento(False)
        assert colores_de_tema(oscuro=True, documento=True) is TEMA_DOCUMENTO

        establecer_modo_documento(True)
        assert colores_de_tema(oscuro=True, documento=False) is TEMA_OSCURO

    def test_figura_en_modo_documento_es_legible_sobre_blanco(self):
        establecer_modo_documento(True)
        fig = plantilla(_figura_ejemplo(), oscuro=True)
        fig.update_layout(title="Distribución por Género")
        _asegurar_estilo_titulo(fig)

        assert str(fig.layout.paper_bgcolor).lower() == "#ffffff"
        assert fig.layout.font.color == "#1a1a1a"
        # El título debe ser de color acento, no el gris claro del tema oscuro.
        assert fig.layout.title.font.color == "#4CAF50"


class TestValores:
    def test_con_valores_usa_el_color_del_tema(self):
        fig = con_valores(_figura_ejemplo(), oscuro=True)
        assert fig.data[0].textfont.color == TEMA_OSCURO["texto"]

    def test_con_valores_en_modo_documento(self):
        establecer_modo_documento(True)
        fig = con_valores(_figura_ejemplo(), oscuro=True)
        assert fig.data[0].textfont.color == TEMA_DOCUMENTO["texto"]
