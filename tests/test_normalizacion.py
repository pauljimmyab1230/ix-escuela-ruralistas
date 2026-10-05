"""Pruebas de las utilidades de normalización."""

import pandas as pd

from src.normalizacion import (
    CONOCIMIENTOS_CORTOS,
    a_minusculas_sin_acentos,
    a_serie_numerica,
    columnas_conocimiento,
    limpiar_email,
    parsear_fecha,
    quitar_acentos,
)


class TestQuitarAcentos:
    def test_elimina_tilde_de_la_i(self):
        assert quitar_acentos("Agroecología") == "Agroecologia"

    def test_elimina_varios_acentos(self):
        assert quitar_acentos("Formulación de proyectos") == "Formulacion de proyectos"

    def test_convierte_no_string(self):
        assert quitar_acentos(123) == "123"

    def test_deja_ascii_igual(self):
        assert quitar_acentos("CANVAS") == "CANVAS"


class TestMinusculasSinAcentos:
    def test_combina_minusc_y_acentos(self):
        assert a_minusculas_sin_acentos("  Agroecología  ") == "agroecologia"

    def test_none_devuelve_cadena_vacia(self):
        assert a_minusculas_sin_acentos(None) == ""

    def test_nan_devuelve_cadena_vacia(self):
        assert a_minusculas_sin_acentos(float("nan")) == ""


class TestParsearFecha:
    def test_formato_dia_mes_anio(self):
        assert parsear_fecha("20/06/2026") == "2026-06-20"

    def test_formato_iso(self):
        assert parsear_fecha("2026-06-20") == "2026-06-20"

    def test_tolera_espacio_no_separable(self):
        assert parsear_fecha("20/06/2026\xa014:30") == "2026-06-20"

    def test_tolera_espacio_fino(self):
        assert parsear_fecha("04/07/2026\u202f09:00") == "2026-07-04"

    def test_valor_invalido_devuelve_none(self):
        assert parsear_fecha("no es fecha") is None

    def test_none_devuelve_none(self):
        assert parsear_fecha(None) is None


class TestSerieNumerica:
    def test_convierte_y_marca_invalidos(self):
        serie = pd.Series(["5", "-", "3.5", "nada"])
        resultado = a_serie_numerica(serie)
        assert resultado.iloc[0] == 5
        assert pd.isna(resultado.iloc[1])
        assert resultado.iloc[2] == 3.5
        assert pd.isna(resultado.iloc[3])


class TestLimpiezaEmail:
    def test_normaliza_a_minusculas_sin_bordes(self):
        serie = pd.Series(["  Ana@Ejemplo.COM ", "Luis@ejemplo.com"])
        assert limpiar_email(serie).tolist() == ["ana@ejemplo.com", "luis@ejemplo.com"]


class TestColumnasConocimiento:
    def test_detecta_el_prefijo(self):
        df = pd.DataFrame(
            {
                "Nombre": ["a"],
                "Conoc_Agroecología": [1],
                "Conoc_Género": [2],
                "Otra": [3],
            }
        )
        assert columnas_conocimiento(df) == ["Conoc_Agroecología", "Conoc_Género"]

    def test_nueve_dimensiones_de_referencia(self):
        assert len(CONOCIMIENTOS_CORTOS) == 9
