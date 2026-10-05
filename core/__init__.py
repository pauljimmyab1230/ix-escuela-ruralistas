"""Paquete de componentes del dashboard."""

from core.config import PALETA
from core.datos import Filtros, cargar_o_mostrar_error
from core.graficos import aplicar_tema_css, graficar, plantilla

__all__ = [
    "PALETA",
    "Filtros",
    "aplicar_tema_css",
    "cargar_o_mostrar_error",
    "graficar",
    "plantilla",
]
