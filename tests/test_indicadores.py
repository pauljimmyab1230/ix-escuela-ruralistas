"""Pruebas de los indicadores derivados del libro de sistematización."""

from pathlib import Path

import pandas as pd
import pytest

from src import indicadores as ind
from src.datos import cargar_libro
from src.normalizacion import (
    ESCALA_ACTORES,
    ESCALA_COMODIDAD,
    ESCALA_LIDERAZGO,
    a_ordinal,
    clasificar_rango_edad,
    mapear_fechas_cercanas,
    normalizar_especialidad,
    normalizar_region,
    normalizar_si_no,
)

RUTA_LIBRO = Path(__file__).resolve().parent.parent / "Sistematizacion_nueva.xlsx"


@pytest.fixture(scope="module")
def libro():
    return cargar_libro(RUTA_LIBRO)


class TestNormalizacionDeRespuestas:
    @pytest.mark.parametrize(
        "valor,esperado",
        [
            ("Si", "Sí"),
            ("si", "Sí"),
            ("SI", "Sí"),
            ("Sí", "Sí"),
            ("Sí ", "Sí"),
            ("No", "No"),
            ("No pertenezco", "No"),
            ("Ninguna", None),
            ("-", None),
            ("", None),
            (None, None),
        ],
    )
    def test_normalizar_si_no(self, valor, esperado):
        assert normalizar_si_no(valor) == esperado

    @pytest.mark.parametrize(
        "valor,esperado",
        [
            ("Junin", "Junín"),
            ("Junín", "Junín"),
            ("Cuzco", "Cusco"),
            ("Cusco", "Cusco"),
            ("La libertad", "La Libertad"),
            ("Lima", "Lima"),
            ("-", None),
        ],
    )
    def test_normalizar_region(self, valor, esperado):
        assert normalizar_region(valor) == esperado

    @pytest.mark.parametrize(
        "valor,esperado",
        [
            ("Ingeniería Ambiental", "Ingeniería Ambiental"),
            ("Ingeniería Ambiental ", "Ingeniería Ambiental"),
            ("Ing Ambiental", "Ingeniería Ambiental"),
            ("Ingeneieria ambiental", "Ingeniería Ambiental"),
            ("Agronomía ", "Agronomía"),
            ("-", None),
            ("", None),
        ],
    )
    def test_normalizar_especialidad(self, valor, esperado):
        assert normalizar_especialidad(valor) == esperado

    @pytest.mark.parametrize(
        "edad,esperado",
        [(18, "18-20"), (22, "21-23"), (25, "24-26"), (30, "30 o más"), (None, None)],
    )
    def test_clasificar_rango_edad(self, edad, esperado):
        assert clasificar_rango_edad(edad) == esperado


class TestEscalasOrdinales:
    @pytest.mark.parametrize(
        "valor,escala,esperado",
        [
            ("Muy cómodo(a)", ESCALA_COMODIDAD, 5.0),
            ("Cómodo(a)", ESCALA_COMODIDAD, 4.0),
            ("Neutral / Ni cómodo(a) ni incómodo(a)", ESCALA_COMODIDAD, 3.0),
            ("Muy incómodo(a)", ESCALA_COMODIDAD, 1.0),
            ("Sí", ESCALA_LIDERAZGO, 2.0),
            ("Tal vez", ESCALA_LIDERAZGO, 1.0),
            ("Si", ESCALA_ACTORES, 2.0),
            ("", ESCALA_ACTORES, None),
        ],
    )
    def test_a_ordinal(self, valor, escala, esperado):
        assert a_ordinal(valor, escala) == esperado


class TestMapeoDeFechas:
    def test_empareja_por_proximidad(self):
        calendario = {
            pd.Timestamp("2026-06-06"): 3,
            pd.Timestamp("2026-06-13"): 4,
        }
        fechas = pd.Series([pd.Timestamp("2026-06-05"), pd.Timestamp("2026-06-13")])
        resultado = mapear_fechas_cercanas(fechas, calendario, tolerancia_dias=2)
        assert resultado.tolist() == [3, 4]

    def test_fuera_de_tolerancia_devuelve_none(self):
        calendario = {pd.Timestamp("2026-06-06"): 3}
        fechas = pd.Series([pd.Timestamp("2026-07-01")])
        resultado = mapear_fechas_cercanas(fechas, calendario, tolerancia_dias=2)
        assert resultado.tolist() == [None]

    def test_calendario_vacio(self):
        fechas = pd.Series([pd.Timestamp("2026-06-05")])
        resultado = mapear_fechas_cercanas(fechas, {})
        assert resultado.tolist() == [None]

    def test_fecha_invalida_devuelve_none(self):
        calendario = {pd.Timestamp("2026-06-06"): 3}
        fechas = pd.Series([pd.NaT])
        resultado = mapear_fechas_cercanas(fechas, calendario)
        assert resultado.tolist() == [None]


class TestParticipacion:
    def test_tiene_los_tres_indicadores(self, libro):
        resumen = ind.resumen_participacion(libro)
        assert set(resumen) == {"Inscritos", "Activos", "Certificados"}

    def test_inscritos_es_el_total_del_registro(self, libro):
        resumen = ind.resumen_participacion(libro)
        assert resumen["Inscritos"] == len(libro.becarios)

    def test_activos_no_supera_a_los_inscritos(self, libro):
        resumen = ind.resumen_participacion(libro)
        assert 0 <= resumen["Activos"] <= resumen["Inscritos"]

    def test_certificados_no_supera_a_los_activos(self, libro):
        resumen = ind.resumen_participacion(libro)
        assert resumen["Certificados"] <= resumen["Activos"]

    def test_la_asistencia_se_recorta_a_becarios(self, libro):
        total = libro.asistencia["Correo electrónico"].nunique()
        solo_becarios = ind.asistencia_de_becarios(libro)["Correo_norm"].nunique()
        assert solo_becarios < total, "El recorte a becarios debe filtrar ajenos"

    def test_asistencia_por_sesion_todas_mapeadas(self, libro):
        tabla = ind.asistencia_por_sesion(libro)
        assert len(tabla) == 10
        assert tabla["Sesion"].notna().all()
        assert set(tabla["Sesion"].astype(int)) == set(range(1, 11))

    def test_porcentaje_sobre_inscritos(self, libro):
        tabla = ind.asistencia_por_sesion(libro)
        inscritos = len(libro.becarios)
        esperado = (tabla["Asistentes"] / inscritos * 100).round(1)
        assert (tabla["Pct_Inscritos"] == esperado).all()

    def test_retencion_vs_sesion_1(self, libro):
        tabla = ind.asistencia_por_sesion(libro)
        assert tabla["Retencion"].iloc[0] == 100.0
        esperado = (tabla["Asistentes"] / tabla["Asistentes"].iloc[0] * 100).round(1)
        assert (tabla["Retencion"] == esperado).all()


class TestPerfil:
    def test_rangos_de_edad_cubren_a_todos(self, libro):
        rangos = ind.perfil_por_rangos_de_edad(libro.becarios)
        assert int(rangos.sum()) == int(libro.becarios["Edad"].notna().sum())

    def test_region_peru_solo_peru(self, libro):
        regiones = ind.perfil_por_region_peru(libro.becarios)
        assert not regiones.empty
        assert "Nariño" not in regiones.index
        assert "Cundinamarca" not in regiones.index

    def test_especialidad_unificada(self, libro):
        especialidades = ind.perfil_por_especialidad(libro.becarios)
        assert "Ingeniería Ambiental" in especialidades.index
        assert "Ing Ambiental" not in especialidades.index

    def test_emprendimiento_previo_tiene_indicadores(self, libro):
        tabla = ind.perfil_emprendimiento_previo(libro.becarios)
        assert not tabla.empty
        assert set(tabla.columns) == {"Indicador", "Sí", "No"}
        assert (tabla["Sí"] + tabla["No"] <= len(libro.becarios)).all()

    def test_redes_jovenes(self, libro):
        tabla = ind.perfil_redes_jovenes(libro.becarios)
        assert set(tabla["Pertenece"]).issubset({"Sí", "No"})

    def test_redes_mencionadas_sin_descartadas(self, libro):
        menciones = ind.redes_mencionadas(libro.becarios)
        for etiqueta in menciones.index:
            assert not str(etiqueta).lower().startswith("ningun")


class TestHabilidades:
    def test_comparacion_incluye_tres_habilidades(self, libro):
        tabla = ind.comparacion_habilidades(libro)
        assert len(tabla) == 3
        assert set(tabla.columns) >= {
            "Habilidad",
            "LineaBase_Prom",
            "LineaFinal_Prom",
            "Pareado_n",
        }

    def test_pareados_no_superan_a_la_linea_final(self, libro):
        tabla = ind.comparacion_habilidades(libro)
        assert (tabla["Pareado_n"] <= tabla["LineaFinal_n"]).all()

    def test_distribucion_tiene_las_dos_mediciones(self, libro):
        tabla = ind.distribucion_habilidad(libro, ind.PREFIJO_COMODIDAD_PUBLICO, ESCALA_COMODIDAD)
        assert set(tabla.columns) == {"Nivel", "Línea base", "Línea final"}
        assert tabla["Línea base"].sum() > 0
        assert tabla["Línea final"].sum() > 0


class TestExamen:
    def test_estadisticas_completas(self, libro):
        stats = ind.estadisticas_examen(libro)
        assert stats["n"] > 0
        assert 0 <= stats["Promedio"] <= 20
        assert stats["Minimo"] <= stats["Mediana"] <= stats["Maximo"]
        assert stats["Desviacion"] >= 0

    def test_acierto_por_pregunta_en_rango(self, libro):
        tabla = ind.acierto_por_pregunta(libro.examen)
        assert not tabla.empty
        assert tabla["Pct_Acierto"].between(0, 100).all()
        assert (tabla["Aciertos"] <= tabla["Respuestas"]).all()

    def test_esta_ordenado_de_menor_a_mayor_acierto(self, libro):
        tabla = ind.acierto_por_pregunta(libro.examen)
        assert tabla["Pct_Acierto"].is_monotonic_increasing

    def test_la_clave_es_la_moda(self, libro):
        clave = ind.clave_de_respuestas(libro.examen)
        assert clave
        for pregunta, correcta in clave.items():
            moda = libro.examen[pregunta].dropna().astype(str).value_counts().index[0]
            assert correcta == moda


class TestEscalasDeSatisfaccion:
    def test_escalas_por_sesion_tiene_columnas_basicas(self, libro):
        tabla = ind.escalas_por_sesion(libro)
        assert "Sesion" in tabla.columns
        assert "Utilidad" in tabla.columns
        assert "Claridad" in tabla.columns
        assert "Aprendizaje" in tabla.columns

    def test_valores_en_escala_1_5(self, libro):
        tabla = ind.escalas_por_sesion(libro)
        for columna in ("Utilidad", "Claridad", "Aprendizaje"):
            validos = tabla[columna].dropna()
            assert validos.between(1, 5).all()


class TestEvaluacionDePersonas:
    def test_mentores(self, libro):
        tabla = ind.evaluacion_mentores(libro)
        assert not tabla.empty
        assert "Persona" in tabla.columns
        assert len(tabla.columns) > 1

    def test_representantes(self, libro):
        tabla = ind.evaluacion_representantes(libro)
        assert not tabla.empty

    def test_resumen_por_dimension_y_persona(self, libro):
        tabla = ind.evaluacion_mentores(libro)
        dimension, personas = ind.resumen_evaluacion(tabla)
        assert set(dimension.columns) == {"Dimensión", "Promedio"}
        assert set(personas.columns) == {"Persona", "Promedio"}
        assert dimension["Promedio"].between(1, 5).all()

    def test_comentarios(self, libro):
        comentarios = ind.comentarios_evaluacion(libro, ind.COLUMNA_TEXTO_MENTOR)
        assert isinstance(comentarios, list)


class TestPlanesYEntregables:
    def test_ranking_tiene_puestos_consecutivos(self, libro):
        ranking = ind.ranking_planes(libro)
        assert not ranking.empty
        assert list(ranking["Puesto"]) == list(range(1, len(ranking) + 1))
        assert ranking["Promedio"].is_monotonic_decreasing

    def test_cobertura_de_entregables(self, libro):
        tabla = ind.cobertura_entregables(libro)
        assert not tabla.empty
        assert tabla["Cobertura_pct"].between(0, 100).all()
        assert set(tabla.columns) == {
            "Entregable",
            "Presentados",
            "Cobertura_pct",
            "Promedio",
        }
