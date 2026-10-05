"""Pruebas de carga, validación y filtrado del libro de sistematización."""

from pathlib import Path

import pandas as pd
import pytest

from src.datos import (
    ErrorEstructuraLibro,
    Filtros,
    aplicar_filtros_becarios,
    cargar_libro,
    es_respuesta_util,
    filtrar_por_emails,
    matriz_conocimiento_linea_base,
    matriz_conocimiento_linea_final,
    promedio_conocimiento_linea_base,
    promedio_conocimiento_linea_final,
    tabla_expectativas_vs_resultados,
)

RUTA_LIBRO = Path(__file__).resolve().parent.parent / "Sistematizacion_nueva.xlsx"


@pytest.fixture(scope="module")
def libro():
    return cargar_libro(RUTA_LIBRO)


class TestCarga:
    def test_carga_las_quince_hojas(self, libro):
        assert len(libro.nombres_de_hojas()) == 15

    def test_becarios_y_linea_final_con_registros(self, libro):
        assert len(libro.becarios) > 0
        assert len(libro.linea_final) > 0

    def test_normaliza_correo_en_linea_final(self, libro):
        assert "Correo_norm" in libro.linea_final.columns
        assert libro.linea_final["Correo_norm"].str.lower().equals(libro.linea_final["Correo_norm"])

    def test_calif_num_es_numerica(self, libro):
        assert pd.api.types.is_numeric_dtype(libro.encuestas["Calif_num"])

    def test_fecha_str_normalizada(self, libro):
        assert libro.asistencia["Fecha_str"].str.match(r"\d{4}-\d{2}-\d{2}").all()

    def test_archivo_inexistente_lanza_error(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            cargar_libro(tmp_path / "no_existe.xlsx")

    def test_hoja_faltante_lanza_error_de_estructura(self, tmp_path):
        ruta = tmp_path / "vacio.xlsx"
        pd.DataFrame({"a": [1]}).to_excel(ruta, sheet_name="01a.Becarios", index=False)
        with pytest.raises(ErrorEstructuraLibro):
            cargar_libro(ruta)


class TestFiltros:
    def test_sin_filtros_devuelve_todo(self, libro):
        assert len(aplicar_filtros_becarios(libro.becarios, Filtros())) == len(libro.becarios)

    def test_filtra_por_region(self, libro):
        region = libro.becarios["Region"].dropna().iloc[0]
        resultado = aplicar_filtros_becarios(libro.becarios, Filtros(region=region))
        assert set(resultado["Region"].unique()) == {region}
        assert len(resultado) < len(libro.becarios)

    def test_filtra_por_genero(self, libro):
        genero = libro.becarios["Genero"].dropna().iloc[0]
        resultado = aplicar_filtros_becarios(libro.becarios, Filtros(genero=genero))
        assert set(resultado["Genero"].unique()) == {genero}

    def test_filtra_por_email_individual(self, libro):
        email = libro.becarios["Email"].dropna().iloc[0]
        resultado = aplicar_filtros_becarios(libro.becarios, Filtros(emails=(email,)))
        assert list(resultado["Email"]) == [email]

    def test_filtros_acumulativos(self, libro):
        fila = libro.becarios.dropna(subset=["Region", "Genero", "Email"]).iloc[0]
        filtros = Filtros(region=fila["Region"], genero=fila["Genero"], emails=(fila["Email"],))
        resultado = aplicar_filtros_becarios(libro.becarios, filtros)
        assert len(resultado) == 1

    def test_resumen_lista_solo_los_activos(self):
        assert Filtros().resumen() == []
        assert Filtros(region="Cusco").resumen() == ["Región: Cusco"]
        assert len(Filtros(region="Cusco", genero="Femenino").resumen()) == 2

    def test_activos_detecta_cualquier_filtro(self):
        assert not Filtros().activos
        assert Filtros(genero="Femenino").activos
        assert Filtros(emails=("a@b.c",)).activos


class TestFiltradoPorCorreos:
    def test_comparacion_insensible_a_mayusculas_y_bordes(self):
        df = pd.DataFrame({"Correo": ["  Ana@Ejemplo.com ", "luis@ejemplo.com"]})
        resultado = filtrar_por_emails(df, "Correo", ["ana@ejemplo.com"])
        assert len(resultado) == 1

    def test_sin_coincidencias_devuelve_vacio(self):
        df = pd.DataFrame({"Correo": ["a@b.c"]})
        assert filtrar_por_emails(df, "Correo", ["otro@b.c"]).empty


class TestMatricesDeConocimiento:
    def test_matriz_base_tiene_nueve_columnas(self, libro):
        matriz = matriz_conocimiento_linea_base(libro.becarios)
        assert matriz.shape[1] == 9
        assert matriz.shape[0] == len(libro.becarios)

    def test_matriz_final_normalizada_a_cero_tres(self, libro):
        matriz = matriz_conocimiento_linea_final(libro)
        valores = matriz.stack().dropna()
        assert valores.min() >= 0
        assert valores.max() <= 3

    def test_promedios_en_el_mismo_rango(self, libro):
        base = promedio_conocimiento_linea_base(libro.becarios)
        final = promedio_conocimiento_linea_final(libro)
        assert len(base) == 9
        assert len(final) == 9
        assert all(0 <= v <= 3 for v in base)
        assert all(0 <= v <= 3 for v in final)


class TestExpectativasVsResultados:
    def test_tiene_columnas_de_comparacion(self, libro):
        tabla = tabla_expectativas_vs_resultados(libro)
        assert set(tabla.columns) == {"Categoria", "Esperaba", "Aprendio", "Diff"}

    def test_la_diferencia_es_consistente(self, libro):
        tabla = tabla_expectativas_vs_resultados(libro)
        assert (tabla["Diff"] == tabla["Aprendio"] - tabla["Esperaba"]).all()

    def test_todas_las_categorias_tienen_nombre(self, libro):
        tabla = tabla_expectativas_vs_resultados(libro)
        assert tabla["Categoria"].notna().all()
        assert not (tabla["Categoria"].str.strip() == "").any()

    def test_no_se_pierden_categorias_por_encoding(self, libro):
        """Antes las claves con encoding corrupto descartaban categorías."""
        tabla = tabla_expectativas_vs_resultados(libro)
        esperadas = {
            "Agroecología",
            "Emprendimiento",
            "Herramientas",
            "Formulación",
            "Liderazgo",
            "Investigación",
            "Otros",
        }
        assert esperadas.issubset(set(tabla["Categoria"]))


class TestRespuestaUtil:
    @pytest.mark.parametrize(
        "valor,esperado",
        [
            ("una respuesta", True),
            ("Sin respuesta", False),
            ("Sin respuesta / Satisfecho", False),
            (None, False),
            (float("nan"), False),
        ],
    )
    def test_casos(self, valor, esperado):
        assert es_respuesta_util(valor) is esperado
