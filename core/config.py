"""Constantes de configuración del dashboard."""

from __future__ import annotations

# Paleta de colores de las series de gráficos.
PALETA: list[str] = [
    "#2196F3",
    "#E91E63",
    "#FF9800",
    "#4CAF50",
    "#9C27B0",
    "#00BCD4",
    "#FF5722",
    "#607D8B",
    "#795548",
    "#F44336",
]

# Acento de la identidad visual.
COLOR_ACENTO = "#4CAF50"

# Alturas estándar de los gráficos.
ALTO_GRAFICO = 420
ALTO_GRAFICO_PEQUENO = 380
ALTO_GRAFICO_MINIMO = 250

# Escala de conocimiento autopercibido (0 = nada, 3 = avanzado).
ESCALA_CONOCIMIENTO_MAX = 3.0
UMBRAL_NIVEL_INTERMEDIO = 2.0

# Evaluación del examen inicial.
PUNTAJE_MAXIMO_EXAMEN = 20
UMBRAL_APROBACION_EXAMEN = 18

# Evaluación de planes de emprendimiento.
PUNTAJE_MAXIMO_PLAN = 50

# Rango visible del eje de calificación (1-5).
RANGO_CALIFICACION = (3.0, 5.5)
RANGO_CALIFICACION_COLOR = (3.5, 5.0)

# Nombres de las sesiones del programa, por número.
NOMBRES_SESIONES: dict[int, str] = {
    1: "Bienvenida",
    2: "Realidad DAR",
    3: "Agroecología",
    4: "Género e Interculturalidad",
    5: "CANVAS T1",
    6: "CANVAS T2",
    7: "CANVAS T3",
    8: "CANVAS T4",
    9: "Simulacro",
    10: "Sustentación y Clausura",
}

# Etiquetas cortas de las dimensiones de conocimiento.
CONOCIMIENTOS_CORTOS: list[str] = [
    "Des. Agrario",
    "Agroecología",
    "Género",
    "Interculturalidad",
    "Formalización",
    "CANVA",
    "Comercialización",
    "Form. Proyectos",
    "Fondos",
]

# Páginas del sidebar, en orden.
PAGINAS: list[tuple[str, str]] = [
    ("🏠 Resumen General", "resumen"),
    ("📊 Participación", "participacion"),
    ("👥 Becarios", "becarios"),
    ("📋 Encuestas", "encuestas"),
    ("📅 Asistencia", "asistencia"),
    ("📝 Evaluaciones", "evaluaciones"),
    ("📈 Línea Base vs Final", "linea_final"),
]

TITULO_APP = "IX Escuela de Jóvenes Ruralistas"
ICONO_APP = "🌱"
PIE_PAGINA = "IX Escuela de Jóvenes Ruralistas 2026 | Ypard / EJR"
