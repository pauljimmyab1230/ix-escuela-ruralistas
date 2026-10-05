"""Indicadores derivados del libro de sistematización.

Reúne los cálculos que alimentan los cuadros del dashboard: participación,
asistencia, retención, perfil demográfico, comparación de habilidades,
examen, escalas de satisfacción, evaluación de mentores y ranking de planes.

Todos los recortes a población se hacen por correo electrónico normalizado,
para no mezclar becarios con mentores, representantes o invitados.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from src.datos import (
    LibroSistematizacion,
)
from src.normalizacion import (
    ESCALA_ACTORES,
    ESCALA_COMODIDAD,
    ESCALA_LIDERAZGO,
    RANGOS_EDAD,
    a_ordinal,
    clasificar_rango_edad,
    limpiar_email,
    mapear_fechas_cercanas,
    normalizar_especialidad,
    normalizar_region,
    normalizar_si_no,
)

# Umbral de asistencia para considerar que un becario puede certificarse.
UMBRAL_ASISTENCIA_CERTIFICADO = 0.75

# Nota mínima de aprobación del examen inicial.
NOTA_APROBACION_EXAMEN = 18

# Prefijos para localizar columnas de la línea final sin depender del texto completo.
PREFIJO_COMODIDAD_PUBLICO = "¿Qué tan cómodo (a) se siente hablando en público"
PREFIJO_LIDERAZGO = "¿Considera que tiene capacidad de liderazgo"
PREFIJO_ACTORES = "¿ya logras reconocer a los actores"

# Columnas de la evaluación de mentores y representantes.
COLUMNAS_EVAL_MENTOR = (3, 4, 5, 6, 7, 8)
COLUMNAS_EVAL_REPRESENTANTE = (11, 12, 13, 14, 15, 16)
COLUMNA_NOMBRE_MENTOR = 2
COLUMNA_NOMBRE_REPRESENTANTE = 10
COLUMNA_TEXTO_MENTOR = 9
COLUMNA_TEXTO_REPRESENTANTE = 17

# Escala Likert genérica de las evaluaciones.
ESCALA_LIKERT: dict[str, int] = {
    "muy en desacuerdo": 1,
    "en desacuerdo": 2,
    "neutral": 3,
    "de acuerdo": 4,
    "muy de acuerdo": 5,
    "totalmente de acuerdo": 5,
    "nunca": 1,
    "casi nunca": 2,
    "a veces": 3,
    "casi siempre": 4,
    "siempre": 5,
    "muy insatisfecho": 1,
    "insatisfecho": 2,
    "ni satisfecho ni insatisfecho": 3,
    "satisfecho": 4,
    "muy satisfecho": 5,
}


def _columna_por_prefijo(df: pd.DataFrame, prefijo: str) -> str:
    """Devuelve la primera columna que empieza por `prefijo`."""
    for columna in df.columns:
        if str(columna).startswith(prefijo):
            return str(columna)
    raise KeyError(f"No se encontró ninguna columna que empiece por: {prefijo}")


def _likert(valor: Any) -> float | None:
    from src.normalizacion import a_minusculas_sin_acentos

    texto = a_minusculas_sin_acentos(valor)
    if not texto:
        return None
    return ESCALA_LIKERT.get(texto)


# ---------------------------------------------------------------------------
# Participación
# ---------------------------------------------------------------------------


def correos_de_becarios(libro: LibroSistematizacion) -> set[str]:
    """Conjunto de correos normalizados de los becarios inscritos."""
    return set(limpiar_email(libro.becarios["Email"]).dropna())


def asistencia_de_becarios(libro: LibroSistematizacion) -> pd.DataFrame:
    """Registros de asistencia que corresponden a becarios inscritos.

    La hoja de asistencia incluye mentores, representantes e invitados; sin
    este recorte los porcentajes de participación quedan inflados.
    """
    asistencia = libro.asistencia.copy()
    asistencia["Correo_norm"] = limpiar_email(asistencia["Correo electrónico"])
    objetivos = correos_de_becarios(libro)
    return asistencia[asistencia["Correo_norm"].isin(objetivos)].copy()


def resumen_participacion(libro: LibroSistematizacion) -> dict[str, int]:
    """Inscritos, activos y certificados.

    - **Inscritos**: todos los becarios del registro.
    - **Activos**: asistieron al menos a una sesión.
    - **Certificados**: aprobaron el examen, entregaron al menos un
      entregable con nota y superan el umbral de asistencia.
    """
    becarios = libro.becarios
    inscritos = len(becarios)

    asistencia = asistencia_de_becarios(libro)
    activos = int(asistencia["Correo_norm"].nunique())

    sesiones_totales = int(libro.sesiones["N_Sesion"].nunique()) or 1
    asistencias_por_becario = asistencia.groupby("Correo_norm")["Fecha_str"].nunique()
    tasa_asistencia = asistencias_por_becario / sesiones_totales

    examen = libro.examen.copy()
    examen["Correo_norm"] = limpiar_email(examen["Correo"])
    examen["Puntaje"] = pd.to_numeric(examen["Puntuacion"], errors="coerce")
    aprobados = set(examen.loc[examen["Puntaje"] >= NOTA_APROBACION_EXAMEN, "Correo_norm"])

    entregables = libro.entregables.copy()
    entregables["Correo_norm"] = limpiar_email(entregables["Correo"])
    columnas_entregable = [c for c in entregables.columns if str(c).startswith("Entregable_")]
    con_entregable = set(
        entregables.loc[entregables[columnas_entregable].notna().any(axis=1), "Correo_norm"]
    )

    candidatos = set(tasa_asistencia[tasa_asistencia >= UMBRAL_ASISTENCIA_CERTIFICADO].index)
    certificados = candidatos & aprobados & con_entregable

    return {
        "Inscritos": inscritos,
        "Activos": activos,
        "Certificados": len(certificados),
    }


def asistencia_por_sesion(libro: LibroSistematizacion) -> pd.DataFrame:
    """Asistencia de becarios por sesión, en número y porcentaje.

    El porcentaje se calcula sobre los inscritos y la retención sobre los
    asistentes de la primera sesión, según la convención acordada.
    """
    asistencia = asistencia_de_becarios(libro)
    if asistencia.empty:
        return pd.DataFrame(columns=["Fecha", "Sesion", "Asistentes", "Pct_Inscritos", "Retencion"])

    inscritos = len(libro.becarios) or 1
    tabla = (
        asistencia.groupby("Fecha_str")["Correo_norm"]
        .nunique()
        .reset_index()
        .rename(columns={"Fecha_str": "Fecha", "Correo_norm": "Asistentes"})
        .sort_values("Fecha")
        .reset_index(drop=True)
    )

    sesiones = libro.sesiones[["N_Sesion", "Fecha"]].drop_duplicates().copy()
    calendario = dict(
        zip(
            pd.to_datetime(sesiones["Fecha"], errors="coerce"),
            sesiones["N_Sesion"],
            strict=False,
        )
    )
    # El calendario y la asistencia pueden diferir en un día; se empareja por
    # proximidad en lugar de exigir igualdad exacta.
    tabla["Sesion"] = mapear_fechas_cercanas(
        pd.to_datetime(tabla["Fecha"], errors="coerce"), calendario, tolerancia_dias=2
    )
    tabla["Pct_Inscritos"] = (tabla["Asistentes"] / inscritos * 100).round(1)

    primera = float(tabla["Asistentes"].iloc[0]) if len(tabla) else 0.0
    tabla["Retencion"] = (tabla["Asistentes"] / primera * 100).round(1) if primera else 0.0
    return tabla


# ---------------------------------------------------------------------------
# Perfil demográfico
# ---------------------------------------------------------------------------


def perfil_por_rangos_de_edad(becarios: pd.DataFrame) -> pd.Series:
    """Distribución de edades agrupada en rangos."""
    rangos = becarios["Edad"].apply(clasificar_rango_edad)
    orden = [etiqueta for etiqueta, _, _ in RANGOS_EDAD]
    return rangos.value_counts().reindex(orden).fillna(0).astype(int)


def perfil_por_region_peru(becarios: pd.DataFrame) -> pd.Series:
    """Distribución por región, solo para becarios del Perú."""
    peru = becarios[becarios["Pais"].astype(str).str.strip().str.lower() == "perú"]
    regiones = peru["Region"].apply(normalizar_region)
    return regiones.dropna().value_counts()


def perfil_por_especialidad(becarios: pd.DataFrame) -> pd.Series:
    """Distribución por especialidad o carrera, con etiquetas unificadas."""
    columna = "Especialidad (Carrera)"
    if columna not in becarios.columns:
        return pd.Series(dtype="int64")
    especialidades = becarios[columna].apply(normalizar_especialidad)
    return especialidades.dropna().value_counts()


def perfil_por_pais(becarios: pd.DataFrame) -> pd.Series:
    """Distribución por país."""
    return becarios["Pais"].astype(str).str.strip().replace("", pd.NA).dropna().value_counts()


def perfil_redes_jovenes(becarios: pd.DataFrame) -> pd.DataFrame:
    """Pertenencia a redes juveniles."""
    columna = "Parte_Red_Jovenes"
    if columna not in becarios.columns:
        return pd.DataFrame(columns=["Pertenece", "Cantidad"])
    pertenece = becarios[columna].apply(normalizar_si_no)
    conteo = pertenece.dropna().value_counts().reset_index()
    conteo.columns = ["Pertenece", "Cantidad"]
    return conteo


def redes_mencionadas(becarios: pd.DataFrame) -> pd.Series:
    """Nombres de las redes juveniles mencionadas por los becarios."""
    nombres = "Nombre_Red_Jovenes"
    if nombres not in becarios.columns:
        return pd.Series(dtype="int64")
    descartadas = {"-", "", ".", "nan", "None", "Ninguna", "NINGUNA", "No pertenezco"}
    validos = becarios[nombres].astype(str).str.strip()
    validos = validos[~validos.isin(descartadas)]
    validos = validos[~validos.str.lower().str.startswith("ningun")]
    return validos.value_counts()


def perfil_emprendimiento_previo(becarios: pd.DataFrame) -> pd.DataFrame:
    """Experiencia emprendedora previa de los becarios."""
    columnas = [
        ("Ha_Emprendido_Rural", "Ha emprendido en el ámbito rural"),
        ("Tiene_Emprendimiento", "Tiene un emprendimiento actualmente"),
        ("Ha_Hecho_Canvas", "Ha elaborado un modelo CANVAS"),
        ("Ha_Capacitacion", "Ha recibido capacitación en negocios"),
        ("Ha_Accedido_Fondos", "Ha accedido a fondos concursables"),
        ("Ha_Liderado", "Ha liderado actividades o proyectos"),
    ]
    filas = []
    for columna, etiqueta in columnas:
        if columna not in becarios.columns:
            continue
        valores = becarios[columna].apply(normalizar_si_no)
        conteo = valores.dropna().value_counts()
        filas.append(
            {
                "Indicador": etiqueta,
                "Sí": int(conteo.get("Sí", 0)),
                "No": int(conteo.get("No", 0)),
            }
        )
    return pd.DataFrame(filas)


# ---------------------------------------------------------------------------
# Línea base vs línea final
# ---------------------------------------------------------------------------


def poblaciones_de_mediciones(libro: LibroSistematizacion) -> dict[str, int]:
    """Tamaños de las muestras de línea base, línea final y su intersección."""
    correos_base = set(limpiar_email(libro.becarios["Email"]).dropna())
    correos_final = set(libro.linea_final["Correo_norm"].dropna())
    return {
        "Linea base": len(correos_base),
        "Linea final": len(correos_final),
        "Ambas mediciones": len(correos_base & correos_final),
    }


def _serie_ordenada(serie: pd.Series, escala: dict[str, int]) -> pd.Series:
    return serie.apply(lambda v: a_ordinal(v, escala))


def comparacion_habilidades(libro: LibroSistematizacion) -> pd.DataFrame:
    """Comparación antes/después de tres habilidades blandas.

    Devuelve una fila por habilidad con el promedio ordinal de la línea base
    (todos los inscritos) y de la línea final (quienes respondieron), más la
    comparación pareada de quienes tienen ambas mediciones.
    """
    definiciones = [
        (
            "Comodidad para hablar en público",
            "Comodidad_Publico",
            PREFIJO_COMODIDAD_PUBLICO,
            ESCALA_COMODIDAD,
        ),
        (
            "Capacidad de liderazgo",
            "Capacidad_Liderazgo",
            PREFIJO_LIDERAZGO,
            ESCALA_LIDERAZGO,
        ),
        (
            "Reconocimiento de actores de la comunidad",
            "Conoce_Actores_Comunidad",
            PREFIJO_ACTORES,
            ESCALA_ACTORES,
        ),
    ]

    correos_base = set(limpiar_email(libro.becarios["Email"]).dropna())
    filas = []
    for etiqueta, columna_base, prefijo_lf, escala in definiciones:
        base = _serie_ordenada(libro.becarios[columna_base], escala).dropna()

        try:
            columna_lf = _columna_por_prefijo(libro.linea_final, prefijo_lf)
        except KeyError:
            continue
        final = _serie_ordenada(libro.linea_final[columna_lf], escala).dropna()

        pareados = libro.linea_final[libro.linea_final["Correo_norm"].isin(correos_base)]
        final_pareado = _serie_ordenada(pareados[columna_lf], escala).dropna()

        filas.append(
            {
                "Habilidad": etiqueta,
                "LineaBase_Prom": round(float(base.mean()), 2) if len(base) else None,
                "LineaBase_n": len(base),
                "LineaFinal_Prom": round(float(final.mean()), 2) if len(final) else None,
                "LineaFinal_n": len(final),
                "Pareado_Prom": (
                    round(float(final_pareado.mean()), 2) if len(final_pareado) else None
                ),
                "Pareado_n": len(final_pareado),
                "Escala_min": min(escala.values()),
                "Escala_max": max(escala.values()),
            }
        )
    return pd.DataFrame(filas)


def distribucion_habilidad(
    libro: LibroSistematizacion, prefijo_lf: str, escala: dict[str, int]
) -> pd.DataFrame:
    """Distribución de respuestas de una habilidad, antes y después."""
    definiciones = {
        PREFIJO_COMODIDAD_PUBLICO: "Comodidad_Publico",
        PREFIJO_LIDERAZGO: "Capacidad_Liderazgo",
        PREFIJO_ACTORES: "Conoce_Actores_Comunidad",
    }
    columna_base = definiciones[prefijo_lf]
    columna_lf = _columna_por_prefijo(libro.linea_final, prefijo_lf)

    base = _serie_ordenada(libro.becarios[columna_base], escala)
    final = _serie_ordenada(libro.linea_final[columna_lf], escala)

    niveles = sorted(set(escala.values()))
    etiquetas = {v: k.capitalize() for k, v in escala.items()}
    tabla = pd.DataFrame(
        {
            "Nivel": [etiquetas.get(n, str(n)) for n in niveles],
            "Línea base": [int((base == n).sum()) for n in niveles],
            "Línea final": [int((final == n).sum()) for n in niveles],
        }
    )
    return tabla


# ---------------------------------------------------------------------------
# Examen
# ---------------------------------------------------------------------------


def estadisticas_examen(libro: LibroSistematizacion) -> dict[str, float | int]:
    """Promedio, mediana, desviación y extremos del puntaje del examen."""
    puntajes = pd.to_numeric(libro.examen["Puntuacion"], errors="coerce").dropna()
    if puntajes.empty:
        return {
            "n": 0,
            "Promedio": float("nan"),
            "Mediana": float("nan"),
            "Desviacion": float("nan"),
            "Minimo": float("nan"),
            "Maximo": float("nan"),
        }
    return {
        "n": len(puntajes),
        "Promedio": round(float(puntajes.mean()), 2),
        "Mediana": round(float(puntajes.median()), 2),
        "Desviacion": round(float(puntajes.std(ddof=1)), 2) if len(puntajes) > 1 else 0.0,
        "Minimo": round(float(puntajes.min()), 2),
        "Maximo": round(float(puntajes.max()), 2),
    }


def _columnas_de_preguntas(examen: pd.DataFrame) -> list[str]:
    """Columnas de respuestas del examen: todo lo que no sea identificación."""
    excluidas = {"Marca_temporal", "Correo", "Nombre", "Puntuacion"}
    return [str(c) for c in examen.columns if str(c) not in excluidas]


def clave_de_respuestas(examen: pd.DataFrame) -> dict[str, str]:
    """Respuesta correcta de cada pregunta, deducida por la moda.

    La suma de respuestas no modales coincide exactamente con los errores
    totales implícitos en el puntaje, lo que confirma que la moda es la clave.
    """
    clave: dict[str, str] = {}
    for columna in _columnas_de_preguntas(examen):
        conteo = examen[columna].dropna().astype(str).value_counts()
        if not conteo.empty:
            clave[columna] = str(conteo.index[0])
    return clave


def acierto_por_pregunta(examen: pd.DataFrame) -> pd.DataFrame:
    """Porcentaje de acierto por pregunta, ordenado de menor a mayor acierto."""
    clave = clave_de_respuestas(examen)
    filas = []
    for columna, correcta in clave.items():
        respuestas = examen[columna].dropna().astype(str)
        aciertos = int((respuestas == correcta).sum())
        filas.append(
            {
                "Pregunta": columna,
                "RespuestaCorrecta": correcta,
                "Aciertos": aciertos,
                "Respuestas": len(respuestas),
                "Pct_Acierto": round(aciertos / len(respuestas) * 100, 1)
                if len(respuestas)
                else 0.0,
            }
        )
    return pd.DataFrame(filas).sort_values("Pct_Acierto").reset_index(drop=True)


# ---------------------------------------------------------------------------
# Satisfacción y escalas por sesión
# ---------------------------------------------------------------------------

# Traducción de las etiquetas de cada escala a un valor numérico 1-5.
_ESCALAS_ENCUESTA = {
    "Utilidad": {
        "Muy de acuerdo": 5,
        "De acuerdo": 4,
        "Neutral": 3,
        "En desacuerdo": 2,
        "Muy en desacuerdo": 1,
    },
    "Claridad": {"Muy claro": 5, "Claro": 4, "Poco claro": 2, "poco claro": 2},
    "Aprendizaje": {"Mucho": 5, "Bastante": 4, "Regular": 3, "Poco": 2, "Nada": 1},
    "Satisfaccion": {
        "Muy de acuerdo": 5,
        "De acuerdo": 4,
        "Neutral": 3,
        "En desacuerdo": 2,
        "Muy en desacuerdo": 1,
    },
    "Metodologia": {
        "Muy de acuerdo": 5,
        "De acuerdo": 4,
        "Neutral": 3,
        "En desacuerdo": 2,
        "Muy en desacuerdo": 1,
    },
    "Facilitador": {"Excelente": 5, "Regular": 3, "deficiente": 1},
}


def escalas_por_sesion(libro: LibroSistematizacion) -> pd.DataFrame:
    """Promedio de utilidad, claridad, aprendizaje, satisfacción y metodología."""
    encuestas = libro.encuestas.copy()
    filas: dict[str, Any] = {"Sesion": sorted(encuestas["Sesion_num"].dropna().unique())}

    for nombre, escala in _ESCALAS_ENCUESTA.items():
        if nombre not in encuestas.columns:
            continue
        numerico = encuestas[nombre].map(escala).astype(float)
        agrupado = encuestas.assign(_n=numerico).groupby("Sesion_num")["_n"].mean().round(2)
        filas[nombre] = [agrupado.get(s, float("nan")) for s in filas["Sesion"]]

        respuestas = encuestas.assign(_n=numerico).groupby("Sesion_num")["_n"].count()
        filas[f"{nombre}_n"] = [int(respuestas.get(s, 0)) for s in filas["Sesion"]]

    return pd.DataFrame(filas)


# ---------------------------------------------------------------------------
# Evaluación de mentores y representantes
# ---------------------------------------------------------------------------


def _tabla_evaluacion(
    libro: LibroSistematizacion,
    columnas: tuple[int, ...],
    columna_nombre: int,
) -> pd.DataFrame:
    """Matriz de respuestas Likert de una evaluación, con la persona evaluada."""
    datos = libro.eval_mentores
    if datos.empty:
        return pd.DataFrame()

    nombres = datos.iloc[:, columna_nombre].astype(str).str.strip()
    etiquetas = [str(datos.columns[i]).strip() for i in columnas]

    matriz = pd.DataFrame(
        {
            etiqueta: datos.iloc[:, i].apply(_likert)
            for i, etiqueta in zip(columnas, etiquetas, strict=True)
        }
    )
    matriz.insert(0, "Persona", nombres)
    return matriz


def evaluacion_mentores(libro: LibroSistematizacion) -> pd.DataFrame:
    """Evaluación de mentores: respuestas por mentor y por dimensión."""
    return _tabla_evaluacion(libro, COLUMNAS_EVAL_MENTOR, COLUMNA_NOMBRE_MENTOR)


def evaluacion_representantes(libro: LibroSistematizacion) -> pd.DataFrame:
    """Evaluación de representantes de comunidad."""
    return _tabla_evaluacion(libro, COLUMNAS_EVAL_REPRESENTANTE, COLUMNA_NOMBRE_REPRESENTANTE)


def resumen_evaluacion(
    tabla: pd.DataFrame, columna_persona: str = "Persona"
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Devuelve (promedio por dimensión, promedio por persona)."""
    if tabla.empty:
        return tabla, tabla
    columnas = [c for c in tabla.columns if c != columna_persona]
    por_dimension = tabla[columnas].mean().round(2).reset_index()
    por_dimension.columns = ["Dimensión", "Promedio"]
    por_dimension = por_dimension.sort_values("Promedio", ascending=False)

    por_persona = tabla.groupby(columna_persona)[columnas].mean().mean(axis=1)
    por_persona = (
        por_persona.round(2)
        .reset_index()
        .rename(columns={columna_persona: "Persona", 0: "Promedio"})
        .sort_values("Promedio", ascending=False)
        .reset_index(drop=True)
    )
    return por_dimension, por_persona


def comentarios_evaluacion(libro: LibroSistematizacion, indice_columna: int) -> list[str]:
    """Comentarios abiertos de una evaluación."""
    datos = libro.eval_mentores
    if datos.empty:
        return []
    serie = datos.iloc[:, indice_columna].dropna().astype(str).str.strip()
    return [t for t in serie if t and t not in {"-", ".", "nan"}]


# ---------------------------------------------------------------------------
# Planes de emprendimiento
# ---------------------------------------------------------------------------


def ranking_planes(libro: LibroSistematizacion) -> pd.DataFrame:
    """Ranking final de planes por promedio de puntaje de los jurados."""
    planes = libro.planes.copy()
    planes["Puntaje_num"] = pd.to_numeric(planes["Puntaje"], errors="coerce")
    planes = planes.dropna(subset=["Puntaje_num"])
    if planes.empty:
        return pd.DataFrame(columns=["Grupo", "Promedio", "Evaluaciones", "Puesto"])

    tabla = (
        planes.groupby("Grupo")["Puntaje_num"]
        .agg(["mean", "count"])
        .reset_index()
        .rename(columns={"mean": "Promedio", "count": "Evaluaciones"})
    )
    tabla["Promedio"] = tabla["Promedio"].round(2)
    tabla = tabla.sort_values("Promedio", ascending=False).reset_index(drop=True)
    tabla["Puesto"] = range(1, len(tabla) + 1)
    return tabla[["Puesto", "Grupo", "Promedio", "Evaluaciones"]]


def cobertura_entregables(libro: LibroSistematizacion) -> pd.DataFrame:
    """Cobertura y nota media por entregable."""
    datos = libro.entregables
    columnas = [c for c in datos.columns if str(c).startswith("Entregable_")]
    filas = []
    for columna in columnas:
        serie = pd.to_numeric(datos[columna], errors="coerce")
        filas.append(
            {
                "Entregable": columna,
                "Presentados": int(serie.notna().sum()),
                "Cobertura_pct": round(serie.notna().sum() / len(datos) * 100, 1)
                if len(datos)
                else 0.0,
                "Promedio": round(float(serie.mean()), 2) if serie.notna().any() else None,
            }
        )
    return pd.DataFrame(filas)
