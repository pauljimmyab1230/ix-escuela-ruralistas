"""Pruebas de integración de los scripts de línea de comandos del pipeline.

Se usan libros sintéticos con la forma de las exportaciones de Google Forms
para comprobar el recorrido completo sin depender de datos reales.
"""

from __future__ import annotations

from pathlib import Path

import analisis_cualitativo
import categorizar_final
import categorizar_linea_base
import pandas as pd


def _construir_encuestas(ruta: Path) -> Path:
    """Crea un libro con la forma de `encuestas por clase.xlsx`."""
    filas = [
        {
            0: 1,
            1: "ana@ejemplo.com",
            2: "ana",
            3: "20/06/2026 10:00",
            4: "Ana Pérez",
            5: "Muy de acuerdo",
            6: "Muy claro",
            7: "Mucho",
            8: "Si",
            9: "Excelente",
            10: 5,
            11: "aprendí a hacer compost y manejar el suelo",
            12: "las dinámicas y el kahoot",
            13: "un poco más de tiempo",
            14: "quiero profundizar en agroecología",
            15: "Muy de acuerdo",
            16: "Muy de acuerdo",
        },
        {
            0: 2,
            1: "luis@ejemplo.com",
            2: "luis",
            3: "04/07/2026 09:30",
            4: "Luis Torres",
            5: "De acuerdo",
            6: "Claro",
            7: "Bastante",
            8: "No",
            9: "Regular",
            10: "-",
            11: "el modelo canvas y la propuesta de valor",
            12: "la buena explicación del facilitador",
            13: "estuvo excelente",
            14: "los fondos concursables",
            15: "De acuerdo",
            16: "De acuerdo",
        },
        {
            0: 3,
            1: "sofia@ejemplo.com",
            2: "sofia",
            3: "20/06/2026 11:00",
            4: "Sofía Ramos",
            5: "Neutral",
            6: "Poco claro",
            7: "Regular",
            8: "Si",
            9: "Excelente",
            10: 4,
            11: "aprendí a dar charlas en público",
            12: "todo me gustó",
            13: "",
            14: "ninguno",
            15: "Neutral",
            16: "De acuerdo",
        },
    ]
    df = pd.DataFrame(filas)
    df.columns = [f"Col_{i}" for i in range(df.shape[1])]

    sesiones = pd.DataFrame(
        {
            "N_Sesion": [5, 7, 9],
            "Fecha": [
                pd.Timestamp("2026-06-20"),
                pd.Timestamp("2026-07-04"),
                pd.Timestamp("2026-07-18"),
            ],
            "Tema": ["CANVAS T1", "CANVAS T3", "Simulacro"],
        }
    )

    with pd.ExcelWriter(ruta, engine="openpyxl") as escritor:
        df.to_excel(escritor, sheet_name="Hoja1", index=False)
        sesiones.to_excel(escritor, sheet_name="Hoja2", index=False)
    return ruta


def _construir_linea_base(ruta: Path) -> Path:
    """Crea un libro con la forma del formulario de línea base."""
    total_columnas = 45
    fila = dict.fromkeys(range(total_columnas))
    fila.update(
        {
            2: "Ana Pérez",
            3: 22,
            4: "Femenino",
            5: "Cusco",
            6: "Cusco",
            7: "Quechua",
            8: "Universitario",
            11: "Si",
            13: "No",
            15: "Si",
            17: "Más de 5 años",
            27: "Si",
            28: "No",
            29: "Agricultura",
            30: "No",
            31: "Si",
            32: "No",
            33: "Si",
            34: "Cómodo",
            35: "Si",
            36: "Muy cómodo",
            37: "No",
            38: None,
            39: "Si",
            40: "Alianzas",
            41: "emprendimiento y agroecología",
            42: "innovación tecnológica",
            43: "desarrollar mi emprendimiento",
            44: "Si",
        }
    )
    for i in range(18, 27):
        fila[i] = "Intermedio"

    df = pd.DataFrame([fila])
    df.columns = [f"Col_{i}" for i in range(total_columnas)]
    df.to_excel(ruta, sheet_name="Respuestas de formulario 1", index=False)
    return ruta


class TestCategorizarFinal:
    def test_genera_las_hojas_esperadas(self, tmp_path: Path):
        entrada = _construir_encuestas(tmp_path / "entrada.xlsx")
        salida = tmp_path / "salida.xlsx"

        codigo = categorizar_final.main(["--entrada", str(entrada), "--salida", str(salida)])
        assert codigo == 0
        assert salida.exists()

        hojas = pd.ExcelFile(salida).sheet_names
        esperadas = {
            "Procesado",
            "Resumen_Ideas",
            "Resumen_Gusto",
            "Resumen_Mejora",
            "Resumen_Profundizar",
            "Metricas_Sesion",
            "Generales_Programa",
            "Participacion",
        }
        assert esperadas.issubset(set(hojas))

    def test_no_escribe_la_misma_hoja_dos_veces(self, tmp_path: Path):
        """Regresión: antes `Procesado` se escribía en un doble `to_excel`."""
        entrada = _construir_encuestas(tmp_path / "entrada.xlsx")
        salida = tmp_path / "salida.xlsx"
        categorizar_final.main(["--entrada", str(entrada), "--salida", str(salida)])
        hojas = pd.ExcelFile(salida).sheet_names
        assert hojas.count("Procesado") == 1

    def test_categoriza_con_reglas_actuales(self, tmp_path: Path):
        entrada = _construir_encuestas(tmp_path / "entrada.xlsx")
        salida = tmp_path / "salida.xlsx"
        categorizar_final.main(["--entrada", str(entrada), "--salida", str(salida)])
        procesado = pd.read_excel(salida, sheet_name="Procesado")

        por_nombre = dict(zip(procesado["Nombre"], procesado["Cat_Ideas"], strict=True))
        assert por_nombre["Ana Pérez"] == "Agroecologia y Suelos"
        assert por_nombre["Luis Torres"] == "Modelo CANVAS"
        # "dar charlas" no debe caer en Desarrollo Agrario Rural.
        assert por_nombre["Sofía Ramos"] == "Storytelling y Pitch"

    def test_calificacion_invalida_no_revienta(self, tmp_path: Path):
        entrada = _construir_encuestas(tmp_path / "entrada.xlsx")
        salida = tmp_path / "salida.xlsx"
        assert categorizar_final.main(["--entrada", str(entrada), "--salida", str(salida)]) == 0
        metricas = pd.read_excel(salida, sheet_name="Metricas_Sesion")
        assert "Calificacion" in metricas.columns

    def test_archivo_inexistente_falla_con_codigo(self, tmp_path: Path):
        codigo = categorizar_final.main(["--entrada", str(tmp_path / "no_existe.xlsx")])
        assert codigo == 1

    def test_columnas_insuficientes_falla(self, tmp_path: Path):
        ruta = tmp_path / "corto.xlsx"
        with pd.ExcelWriter(ruta, engine="openpyxl") as escritor:
            pd.DataFrame({"a": [1], "b": [2]}).to_excel(escritor, sheet_name="Hoja1", index=False)
            pd.DataFrame({"N_Sesion": [1], "Fecha": ["2026-01-01"]}).to_excel(
                escritor, sheet_name="Hoja2", index=False
            )
        assert categorizar_final.main(["--entrada", str(ruta)]) == 1


class TestAnalisisCualitativo:
    def test_escribe_el_reporte(self, tmp_path: Path):
        entrada = _construir_encuestas(tmp_path / "entrada.xlsx")
        salida = tmp_path / "informes" / "reporte.txt"

        codigo = analisis_cualitativo.main(["--entrada", str(entrada), "--salida", str(salida)])
        assert codigo == 0
        assert salida.exists()

        contenido = salida.read_text(encoding="utf-8")
        assert "ANALISIS CUALITATIVO" in contenido
        assert "SESION 5" in contenido
        assert "CANVAS T1" in contenido

    def test_limita_el_numero_de_citas(self, tmp_path: Path):
        entrada = _construir_encuestas(tmp_path / "entrada.xlsx")
        salida = tmp_path / "reporte.txt"
        analisis_cualitativo.main(
            ["--entrada", str(entrada), "--salida", str(salida), "--max-citas", "1"]
        )
        assert salida.exists()

    def test_archivo_inexistente_falla_con_codigo(self, tmp_path: Path):
        codigo = analisis_cualitativo.main(["--entrada", str(tmp_path / "no_existe.xlsx")])
        assert codigo == 1


class TestCategorizarLineaBase:
    def test_genera_las_hojas_esperadas(self, tmp_path: Path):
        entrada = _construir_linea_base(tmp_path / "linea_base.xlsx")
        salida = tmp_path / "salida.xlsx"

        codigo = categorizar_linea_base.main(["--entrada", str(entrada), "--salida", str(salida)])
        assert codigo == 0

        hojas = pd.ExcelFile(salida).sheet_names
        assert {
            "Procesado",
            "Freq_Aprender",
            "Freq_Intereses",
            "Freq_Lograr",
            "Niveles_Conocimiento",
            "Conocimiento_x_Region",
        }.issubset(set(hojas))

    def test_categorizacion_multiple_en_aprender(self, tmp_path: Path):
        entrada = _construir_linea_base(tmp_path / "linea_base.xlsx")
        salida = tmp_path / "salida.xlsx"
        categorizar_linea_base.main(["--entrada", str(entrada), "--salida", str(salida)])
        procesado = pd.read_excel(salida, sheet_name="Procesado")
        valor = str(procesado.loc[0, "Cat_Aprender"])
        assert "Emprendimiento y Negocios" in valor
        assert "Agroecologia y Agricultura Sostenible" in valor

    def test_promedio_de_conocimiento_en_escala_1_4(self, tmp_path: Path):
        entrada = _construir_linea_base(tmp_path / "linea_base.xlsx")
        salida = tmp_path / "salida.xlsx"
        categorizar_linea_base.main(["--entrada", str(entrada), "--salida", str(salida)])
        procesado = pd.read_excel(salida, sheet_name="Procesado")
        promedio = float(procesado.loc[0, "Promedio_Conocimiento"])
        assert 1.0 <= promedio <= 4.0

    def test_archivo_inexistente_falla_con_codigo(self, tmp_path: Path):
        codigo = categorizar_linea_base.main(["--entrada", str(tmp_path / "no_existe.xlsx")])
        assert codigo == 1
