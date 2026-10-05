"""Motor de categorización de respuestas abiertas.

Las reglas viven en `reglas_categorias.yaml`. Este módulo las compila a
expresiones regulares con límite de palabra para evitar los falsos positivos
del matching por subcadena (por ejemplo, que ``"dar"`` coincida dentro de
``"aprendí a dar charlas"``).

Convención de patrones declarados en el YAML:
    ``palabra``          -> ``\\bpalabra\\b``
    ``prefijo*``         -> ``\\bprefijo\\w*``
    ``frase compuesta``  -> ``\\bfrase\\s+compuesta\\b``
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from src.normalizacion import a_minusculas_sin_acentos, quitar_acentos

RUTA_REGLAS_POR_OMISION = Path(__file__).resolve().parent.parent / "reglas_categorias.yaml"


def _compilar_patron(patron: str) -> re.Pattern[str]:
    """Compila un patrón de regla a una expresión regular con límite de palabra."""
    texto = a_minusculas_sin_acentos(patron)
    if not texto:
        # Patrón vacío: nunca coincide.
        return re.compile(r"(?!)")

    if texto.endswith("*"):
        cuerpo = re.escape(texto[:-1])
        return re.compile(r"\b" + cuerpo + r"\w*")
    palabras = texto.split()
    cuerpo = r"\s+".join(re.escape(p) for p in palabras)
    return re.compile(r"\b" + cuerpo + r"\b")


@dataclass(frozen=True)
class Regla:
    """Una categoría con sus patrones de coincidencia."""

    categoria: str
    patrones: tuple[re.Pattern[str], ...]
    excluye: tuple[re.Pattern[str], ...] = ()

    def coincide(self, texto_normalizado: str) -> bool:
        if not texto_normalizado:
            return False
        if any(p.search(texto_normalizado) for p in self.excluye):
            return False
        return any(p.search(texto_normalizado) for p in self.patrones)


@dataclass(frozen=True)
class Esquema:
    """Conjunto de reglas para una dimensión de categorización."""

    nombre: str
    modo: str  # "unica" | "multiple"
    etiqueta_otros: str
    etiqueta_sin_respuesta: str
    reglas: tuple[Regla, ...] = field(default_factory=tuple)
    respuesta_total: tuple[re.Pattern[str], ...] = ()
    etiqueta_total: str = ""
    no_validas: frozenset[str] = frozenset()

    def clasificar(self, valor: Any) -> str | None:
        """Clasifica un valor crudo.

        Devuelve la categoría asignada, o ``None`` si la respuesta no es válida
        y debe etiquetarse como ``etiqueta_sin_respuesta``.
        """
        texto = a_minusculas_sin_acentos(valor)
        if not texto or texto in self.no_validas:
            return None

        # Las respuestas de "sin observación / satisfecho" se detectan como
        # frases con límite de palabra, para que "todo bien, nada que mejorar"
        # cuente como satisfecho y "no hay dudas, quiero más ejemplos" no.
        if self.respuesta_total and any(p.search(texto) for p in self.respuesta_total):
            return self.etiqueta_total

        if self.modo == "unica":
            for regla in self.reglas:
                if regla.coincide(texto):
                    return regla.categoria
            return self.etiqueta_otros

        etiquetas = [r.categoria for r in self.reglas if r.coincide(texto)]
        if not etiquetas:
            return self.etiqueta_otros
        return " | ".join(etiquetas)


def _construir_regla(datos: dict[str, Any]) -> Regla:
    patrones = tuple(_compilar_patron(p) for p in datos.get("patrones", []))
    excluye = tuple(_compilar_patron(p) for p in datos.get("excluye", []))
    return Regla(
        categoria=str(datos["categoria"]),
        patrones=patrones,
        excluye=excluye,
    )


def cargar_esquemas(ruta: str | Path | None = None) -> dict[str, Esquema]:
    """Carga y compila todas las reglas del archivo YAML."""
    ruta_real = Path(ruta) if ruta else RUTA_REGLAS_POR_OMISION
    with open(ruta_real, encoding="utf-8") as archivo:
        crudo: dict[str, Any] = yaml.safe_load(archivo)

    no_validas = {
        nombre: frozenset(a_minusculas_sin_acentos(v) for v in valores)
        for nombre, valores in (crudo.get("no_validas") or {}).items()
    }
    sin_respuesta_global = str(crudo.get("sin_respuesta", "Sin respuesta"))
    # Cada esquema puede pertenecer a un grupo de respuestas no válidas y
    # declarar su propia etiqueta para "sin respuesta".
    grupo_por_esquema = {
        "ideas": "encuestas",
        "gusto": "encuestas",
        "mejora": "encuestas",
        "profundizar": "encuestas",
        "aprender": "linea_base",
        "intereses": "linea_base",
        "lograr": "linea_base",
    }

    esquemas: dict[str, Esquema] = {}
    for nombre, bloque in crudo.items():
        if not isinstance(bloque, dict) or "reglas" not in bloque:
            continue
        propias = frozenset(a_minusculas_sin_acentos(v) for v in (bloque.get("no_validas") or []))
        compartidas = no_validas.get(grupo_por_esquema.get(nombre, ""), frozenset())
        esquemas[nombre] = Esquema(
            nombre=nombre,
            modo=str(bloque.get("modo", "unica")),
            etiqueta_otros=str(bloque.get("etiqueta_otros", "Otros")),
            etiqueta_sin_respuesta=str(bloque.get("sin_respuesta", sin_respuesta_global)),
            reglas=tuple(_construir_regla(r) for r in bloque.get("reglas", [])),
            respuesta_total=tuple(
                _compilar_patron(v) for v in (bloque.get("respuesta_total") or [])
            ),
            etiqueta_total=str(bloque.get("etiqueta_total", "")),
            no_validas=compartidas | propias,
        )
    return esquemas


@lru_cache(maxsize=1)
def esquemas_por_omision() -> dict[str, Esquema]:
    """Carga las reglas del YAML por defecto una sola vez por proceso."""
    return cargar_esquemas()


def clasificar_serie(serie: Iterable[Any], esquema: Esquema) -> list[str]:
    """Clasifica una serie de respuestas con un esquema dado."""
    return [esquema.clasificar(v) or esquema.etiqueta_sin_respuesta for v in serie]


# ---------------------------------------------------------------------------
# Funciones de conveniencia con la interfaz histórica del pipeline.
# ---------------------------------------------------------------------------


def categorizar_ideas(valor: Any) -> str:
    """Categoriza una respuesta de "ideas y conceptos aprendidos"."""
    esquema = esquemas_por_omision()["ideas"]
    return esquema.clasificar(valor) or esquema.etiqueta_sin_respuesta


def categorizar_gusto(valor: Any) -> str:
    """Categoriza una respuesta de "lo que más gustó"."""
    esquema = esquemas_por_omision()["gusto"]
    return esquema.clasificar(valor) or esquema.etiqueta_sin_respuesta


def categorizar_mejora(valor: Any) -> str:
    """Categoriza una respuesta de "aspectos a mejorar"."""
    esquema = esquemas_por_omision()["mejora"]
    return esquema.clasificar(valor) or esquema.etiqueta_sin_respuesta


def categorizar_profundizar(valor: Any) -> str:
    """Categoriza una respuesta de "temas que gustaría profundizar"."""
    esquema = esquemas_por_omision()["profundizar"]
    return esquema.clasificar(valor) or esquema.etiqueta_sin_respuesta


def categorizar_aprender(valor: Any) -> str:
    """Categoriza "qué espera aprender" (línea base, multi-etiqueta)."""
    esquema = esquemas_por_omision()["aprender"]
    return esquema.clasificar(valor) or esquema.etiqueta_sin_respuesta


def categorizar_intereses(valor: Any) -> str:
    """Categoriza "temas de interés" (línea base, multi-etiqueta)."""
    esquema = esquemas_por_omision()["intereses"]
    return esquema.clasificar(valor) or esquema.etiqueta_sin_respuesta


def categorizar_lograr(valor: Any) -> str:
    """Categoriza "qué espera lograr" (línea base, multi-etiqueta)."""
    esquema = esquemas_por_omision()["lograr"]
    return esquema.clasificar(valor) or esquema.etiqueta_sin_respuesta


def normalizar_categoria(texto: str) -> str:
    """Quita acentos de una etiqueta de categoría para compararla."""
    return quitar_acentos(str(texto)).strip()
