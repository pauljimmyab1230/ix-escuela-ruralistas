"""Pruebas de regresión del dashboard: cada página debe renderizar sin fallos."""

from __future__ import annotations

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

RUTA_APP = Path(__file__).resolve().parent.parent / "app.py"

PAGINAS = [
    ("🏠 Resumen General", 8),
    ("👥 Becarios", 15),
    ("📋 Encuestas", 5),
    ("📅 Asistencia", 3),
    ("📝 Evaluaciones", 7),
    ("📈 Línea Base vs Final", 10),
]


def _ejecutar(etiqueta: str) -> AppTest:
    at = AppTest.from_file(str(RUTA_APP), default_timeout=180)
    at.run()
    at.radio[0].set_value(etiqueta)
    at.run()
    return at


@pytest.mark.parametrize("etiqueta,graficos_esperados", PAGINAS)
def test_pagina_se_renderiza_sin_excepciones(etiqueta, graficos_esperados):
    at = _ejecutar(etiqueta)
    assert list(at.exception) == [], f"Excepciones en {etiqueta}: {list(at.exception)}"
    assert list(at.error) == [], f"Errores en {etiqueta}: {list(at.error)}"
    assert len(at.get("plotly_chart")) == graficos_esperados


def test_el_sidebar_ofrece_las_seis_paginas():
    at = AppTest.from_file(str(RUTA_APP), default_timeout=180)
    at.run()
    opciones = list(at.radio[0].options)
    assert [etiqueta for etiqueta, _ in PAGINAS] == opciones


def test_los_filtros_de_region_y_genero_no_revientan():
    at = AppTest.from_file(str(RUTA_APP), default_timeout=180)
    at.run()
    regiones = list(at.selectbox[0].options)
    assert "Todas" in regiones
    at.selectbox[0].set_value(regiones[-1])
    at.run()
    assert list(at.exception) == []


def test_el_modo_claro_tambien_renderiza():
    at = AppTest.from_file(str(RUTA_APP), default_timeout=180)
    at.run()
    at.toggle[0].set_value(False)
    at.run()
    assert list(at.exception) == []


def test_filtro_individual_por_becario():
    at = AppTest.from_file(str(RUTA_APP), default_timeout=180)
    at.run()
    etiquetas = list(at.multiselect[0].options)
    assert etiquetas, "El selector individual debe tener becarios"
    at.multiselect[0].set_value([etiquetas[0]])
    at.run()
    assert list(at.exception) == []
