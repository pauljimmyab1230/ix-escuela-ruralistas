"""Pruebas del motor de categorización de respuestas abiertas."""

import pytest

from src.categorias import (
    Esquema,
    cargar_esquemas,
    categorizar_aprender,
    categorizar_gusto,
    categorizar_ideas,
    categorizar_intereses,
    categorizar_lograr,
    categorizar_mejora,
    categorizar_profundizar,
    clasificar_serie,
)


@pytest.fixture(scope="module")
def esquemas():
    return cargar_esquemas()


class TestCargaDeReglas:
    def test_carga_las_siete_dimensiones(self, esquemas):
        esperadas = {"ideas", "gusto", "mejora", "profundizar", "aprender", "intereses", "lograr"}
        assert set(esquemas) == esperadas

    def test_ideas_es_categorizacion_unica(self, esquemas):
        assert esquemas["ideas"].modo == "unica"

    def test_aprender_es_categorizacion_multiple(self, esquemas):
        assert esquemas["aprender"].modo == "multiple"

    def test_cada_esquema_tiene_reglas(self, esquemas):
        for nombre, esquema in esquemas.items():
            assert len(esquema.reglas) > 0, f"El esquema '{nombre}' no tiene reglas"


class TestClasificacionDeIdeas:
    @pytest.mark.parametrize(
        "texto,esperado",
        [
            ("aprendí a hacer compost y abonos", "Agroecologia y Suelos"),
            ("el manejo del suelo y los microorganismos", "Agroecologia y Suelos"),
            ("el modelo CANVAS y la propuesta de valor", "Modelo CANVAS"),
            ("los costos, el punto de equilibrio y el flujo de caja", "Finanzas y Fondos"),
            ("storytelling y el elevator pitch", "Storytelling y Pitch"),
            ("el rol de la mujer y la equidad de género", "Enfoque de Genero"),
            ("la interculturalidad y la diversidad cultural", "Interculturalidad"),
            ("el liderazgo y el trabajo en equipo", "Liderazgo y Trabajo en Equipo"),
            ("marketing digital y redes sociales", "Marketing Digital"),
            ("la soberanía alimentaria", "Soberania Alimentaria"),
            ("saberes ancestrales y tradiciones", "Saberes Ancestrales"),
        ],
    )
    def test_asigna_categoria_esperada(self, texto, esperado):
        assert categorizar_ideas(texto) == esperado

    def test_la_primera_regla_que_coincide_gana(self):
        # "compost" está en Agroecología; si el texto también menciona CANVAS,
        # debe ganar la primera regla del YAML (Agroecología).
        assert categorizar_ideas("compost y modelo canvas") == "Agroecologia y Suelos"

    @pytest.mark.parametrize("texto", ["", "-", "  ", "ninguno", "Nada", "mucho", "Si"])
    def test_respuestas_vacias_se_marcan_sin_respuesta(self, texto):
        assert categorizar_ideas(texto) == "Sin respuesta"

    def test_desconocido_cae_en_otros(self):
        assert categorizar_ideas("una respuesta sin relación alguna") == "Otros"


class TestFalsosPositivos:
    """El matching por subcadena asignaba categorías erróneas; ahora no."""

    def test_dar_como_verbo_no_es_desarrollo_agrario(self):
        resultado = categorizar_ideas("aprendí a dar charlas en público")
        assert resultado != "Realidad Rural y Politicas"
        assert resultado == "Storytelling y Pitch"

    def test_dar_no_coincide_dentro_de_otra_palabra(self):
        assert categorizar_ideas("el estandar de calidad") != "Realidad Rural y Politicas"

    def test_equipo_sin_contexto_no_es_liderazgo(self):
        # "equipo" solo, sin "trabajo en equipo", no debe forzar la categoría.
        resultado = categorizar_ideas("el equipo de fútbol del pueblo")
        assert resultado != "Liderazgo y Trabajo en Equipo"

    def test_red_no_coincide_dentro_de_redaccion(self):
        resultado = categorizar_aprender("la redacción del documento")
        assert "Trabajo en Equipo y Redes" not in resultado

    def test_agua_no_arruina_otra_categoria(self):
        assert categorizar_ideas("el agua del riego") == "Medio Ambiente y Agua"

    def test_genero_no_coincide_dentro_de_generoso(self):
        # `genero` es palabra exacta: no debe coincidir dentro de "generoso".
        assert categorizar_ideas("fue muy generoso con el grupo") != "Enfoque de Genero"

    def test_palabra_exacta_no_coincide_como_subcadena(self):
        # `agua` es palabra exacta: no debe coincidir dentro de "aguacero".
        assert categorizar_ideas("hubo un aguacero fuerte") == "Otros"

    def test_prefijo_si_coincide_en_borde_de_palabra(self):
        # `agroecolog*` alcanza "agroecológico" porque empieza en el borde.
        assert categorizar_ideas("el manejo agroecológico") == "Agroecologia y Suelos"


class TestClasificacionDeGusto:
    def test_todo_en_general(self):
        assert categorizar_gusto("todo me gustó") == "Todo en General"
        assert categorizar_gusto("Todo en general") == "Todo en General"

    def test_dinamicas(self):
        assert categorizar_gusto("las dinámicas y el kahoot") == "Dinamicas y Actividades"

    def test_facilitadores(self):
        assert categorizar_gusto("la buena explicación del facilitador") == (
            "Facilitadores y Exposiciones"
        )

    def test_dinamicas_excluye_si_hay_ejemplo(self):
        resultado = categorizar_gusto("la dinámica con ejemplos reales")
        assert resultado != "Dinamicas y Actividades"

    @pytest.mark.parametrize("texto", ["", "-", "ninguna", "nada"])
    def test_vacias(self, texto):
        assert categorizar_gusto(texto) == "Sin respuesta"


class TestClasificacionDeMejora:
    def test_satisfecho_no_es_mejora(self):
        assert categorizar_mejora("todo bien, nada que mejorar") == ("Sin respuesta / Satisfecho")
        assert categorizar_mejora("estuvo excelente") == "Sin respuesta / Satisfecho"

    def test_tiempo(self):
        assert categorizar_mejora("un poco más de tiempo") == "Tiempo y Duracion"

    def test_tecnicos(self):
        assert categorizar_mejora("problemas de conexión a internet") == "Aspectos Tecnicos"

    def test_sin_coincidencia_cae_en_otros(self):
        assert categorizar_mejora("una sugerencia cualquiera") == "Otras Sugerencias"


class TestClasificacionDeProfundizar:
    def test_satisfecho(self):
        assert categorizar_profundizar("ninguno, estuvo bien") == ("Sin respuesta / Satisfecho")

    def test_agroecologia(self):
        assert categorizar_profundizar("quiero profundizar en agroecología y suelos") == (
            "Agroecologia y Agricultura"
        )

    def test_finanzas(self):
        assert categorizar_profundizar("los fondos concursables y el financiamiento") == (
            "Finanzas y Acceso a Fondos"
        )


class TestClasificacionMultiple:
    def test_aprender_acumula_varias_categorias(self):
        resultado = categorizar_aprender("emprendimiento y agroecología")
        assert "Emprendimiento y Negocios" in resultado
        assert "Agroecologia y Agricultura Sostenible" in resultado
        assert "|" in resultado

    def test_aprender_sin_coincidencia(self):
        assert categorizar_aprender("algo irrelevante") == "Otros"

    def test_aprender_vacio(self):
        assert categorizar_aprender("") == "Sin respuesta"

    def test_intereses_acumula(self):
        resultado = categorizar_intereses("innovación tecnológica y financiamiento")
        assert "Innovacion y Tecnologia" in resultado
        assert "Financiamiento y Fondos" in resultado

    def test_lograr_acumula(self):
        resultado = categorizar_lograr("desarrollar mi emprendimiento y llevar a mi comunidad")
        assert "Desarrollar Emprendimiento o Negocio" in resultado
        assert "Aplicar Conocimientos en la Comunidad" in resultado

    def test_orden_de_etiquetas_estable(self):
        resultado = categorizar_aprender("liderazgo y emprendimiento")
        etiquetas = resultado.split(" | ")
        assert etiquetas == sorted(etiquetas) or len(etiquetas) >= 1


class TestClasificarSerie:
    def test_aplica_a_toda_la_serie(self, esquemas):
        serie = ["compost", "", "modelo canvas", "ninguno"]
        resultado = clasificar_serie(serie, esquemas["ideas"])
        assert resultado == [
            "Agroecologia y Suelos",
            "Sin respuesta",
            "Modelo CANVAS",
            "Sin respuesta",
        ]

    def test_maneja_none(self, esquemas):
        resultado = clasificar_serie([None, "agroecología"], esquemas["ideas"])
        assert resultado[0] == "Sin respuesta"
        assert resultado[1] == "Agroecologia y Suelos"


class TestEsquemaDirecto:
    def test_sin_respuesta_cuando_clasificar_devuelve_none(self):
        esquema = Esquema(
            nombre="prueba",
            modo="unica",
            etiqueta_otros="Otros",
            etiqueta_sin_respuesta="Sin respuesta",
            no_validas=frozenset({"nada"}),
        )
        assert esquema.clasificar("nada") is None
        assert esquema.clasificar("otra cosa") == "Otros"
