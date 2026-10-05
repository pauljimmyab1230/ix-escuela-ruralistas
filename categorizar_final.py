"""Categoriza las encuestas por sesión y genera las tablas resumen.

Es la puerta de entrada al pipeline de encuestas. Toda la lógica vive en
:mod:`src`; aquí solo se resuelven rutas, se leen los formularios crudos y se
escriben los resultados.

Uso:
    python categorizar_final.py --entrada datos/encuestas_por_clase.xlsx
    python categorizar_final.py --entrada datos/x.xlsx --salida datos/salida.xlsx
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

from src.categorias import cargar_esquemas
from src.datos import COLUMNAS_CATEGORIA_ENCUESTAS, COLUMNAS_TEXTO_ENCUESTAS
from src.normalizacion import parsear_fecha
from src.reportes import (
    agregar_metricas_cerradas,
    aplicar_esquemas_a_encuestas,
    escribir_hojas,
    metricas_generales,
    metricas_por_sesion,
    participacion_por_sesion,
    tabla_cruzada,
)

# Columnas de la exportación cruda de Google Forms, en orden.
# Se validan por posición porque la cabecera trae el texto completo de cada
# pregunta y varía entre formularios.
COLUMNAS_CRUDAS: dict[str, int] = {
    "numero": 0,
    "correo": 1,
    "usuario": 2,
    "fecha_hora": 3,
    "nombre": 4,
    "utilidad": 5,
    "claridad": 6,
    "aprendizaje": 7,
    "conocia_tema": 8,
    "facilitador": 9,
    "calificacion": 10,
    "ideas_texto": 11,
    "gusto_texto": 12,
    "mejora_texto": 13,
    "profundizar_texto": 14,
    "metodologia": 15,
    "satisfaccion": 16,
}

# Nombres legibles que se asignan a las columnas de la exportación cruda.
NOMBRES_AMIGABLES: dict[str, str] = {
    "numero": "#",
    "correo": "Correo",
    "usuario": "Usuario",
    "fecha_hora": "FechaHora",
    "nombre": "Nombre",
    "utilidad": "Utilidad",
    "claridad": "Claridad",
    "aprendizaje": "Aprendizaje",
    "conocia_tema": "Conocia_Tema",
    "facilitador": "Facilitador",
    "calificacion": "Calificacion",
    "ideas_texto": "Ideas_Texto",
    "gusto_texto": "Gusto_Texto",
    "mejora_texto": "Mejora_Texto",
    "profundizar_texto": "Profundizar_Texto",
    "metodologia": "Metodologia",
    "satisfaccion": "Satisfaccion",
}

# Mínimo de columnas que debe tener la exportación cruda.
MINIMO_COLUMNAS = max(COLUMNAS_CRUDAS.values()) + 1

# Fechas que no aparecen en la hoja de sesiones pero que sí pertenecen a una.
# Se conservan como excepciones documentadas del mapeo fecha -> sesión.
EXCEPCIONES_FECHA_SESION: dict[str, int] = {
    "2026-06-20": 5,
    "2026-07-04": 7,
}


def _resolver_ruta(ruta: str | None, predeterminada: Path) -> Path:
    return Path(ruta) if ruta else predeterminada


def _renombrar_columnas(df: pd.DataFrame) -> pd.DataFrame:
    """Renombra las columnas posicionales de la exportación cruda."""
    nombres = {
        str(df.columns[indice]): etiqueta
        for clave, indice in COLUMNAS_CRUDAS.items()
        for etiqueta in [NOMBRES_AMIGABLES[clave]]
    }
    return df.rename(columns=nombres)


def _parsear_argumentos(argv: list[str] | None = None) -> argparse.Namespace:
    raiz = Path(__file__).resolve().parent
    analizador = argparse.ArgumentParser(
        description="Categoriza las encuestas por sesión de la IX Escuela."
    )
    analizador.add_argument(
        "--entrada",
        default=str(raiz / "datos" / "encuestas_por_clase.xlsx"),
        help="Libro con las hojas de respuestas crudas (Hoja1 / Hoja2).",
    )
    analizador.add_argument(
        "--hoja-datos", default="Hoja1", help="Hoja con las respuestas de la encuesta."
    )
    analizador.add_argument(
        "--hoja-sesiones", default="Hoja2", help="Hoja con el mapa de sesiones y fechas."
    )
    analizador.add_argument(
        "--salida",
        default=None,
        help="Libro de salida. Por defecto se anexa al libro de entrada.",
    )
    analizador.add_argument(
        "--reglas",
        default=str(raiz / "reglas_categorias.yaml"),
        help="Archivo YAML con las reglas de categorización.",
    )
    analizador.add_argument(
        "--hoja-salida", default="Procesado", help="Nombre de la hoja de datos procesados."
    )
    return analizador.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parsear_argumentos(argv)
    ruta_entrada = _resolver_ruta(args.entrada, Path(args.entrada))
    if not ruta_entrada.exists():
        print(f"No se encontró el archivo de entrada: {ruta_entrada}", file=sys.stderr)
        return 1

    print(f"Leyendo {ruta_entrada} ...")
    try:
        df = pd.read_excel(ruta_entrada, sheet_name=args.hoja_datos)
        hoja_sesiones = pd.read_excel(ruta_entrada, sheet_name=args.hoja_sesiones)
    except ValueError as exc:
        print(f"No se pudo leer el libro de entrada: {exc}", file=sys.stderr)
        return 1

    if df.shape[1] < MINIMO_COLUMNAS:
        print(
            f"La hoja '{args.hoja_datos}' tiene {df.shape[1]} columnas y se "
            f"esperaban al menos {MINIMO_COLUMNAS}.",
            file=sys.stderr,
        )
        return 1

    # Se renombra por posición una sola vez: de aquí en adelante todo el
    # pipeline trabaja con nombres legibles, no con índices.
    df = _renombrar_columnas(df)

    # --- Fechas y sesión -------------------------------------------------
    df["Fecha_str"] = df["FechaHora"].apply(parsear_fecha)
    df["Fecha"] = pd.to_datetime(df["Fecha_str"], errors="coerce").dt.date

    mapa_fecha_sesion: dict[object, int] = {}
    if {"N_Sesion", "Fecha"}.issubset(hoja_sesiones.columns):
        pares = hoja_sesiones[["N_Sesion", "Fecha"]].drop_duplicates()
        pares["Fecha"] = pd.to_datetime(pares["Fecha"], errors="coerce").dt.date
        mapa_fecha_sesion = dict(zip(pares["Fecha"], pares["N_Sesion"], strict=True))
    else:
        print(
            "Aviso: la hoja de sesiones no tiene columnas N_Sesion/Fecha; "
            "solo se usarán las excepciones documentadas.",
            file=sys.stderr,
        )

    for fecha_iso, numero in EXCEPCIONES_FECHA_SESION.items():
        mapa_fecha_sesion[pd.to_datetime(fecha_iso).date()] = numero

    df["Sesion"] = df["Fecha"].map(mapa_fecha_sesion)

    # --- Categorización -------------------------------------------------
    esquemas = cargar_esquemas(args.reglas)
    df = aplicar_esquemas_a_encuestas(df, esquemas)

    # --- Preguntas cerradas ---------------------------------------------
    df = agregar_metricas_cerradas(
        df,
        columna_satisfaccion="Satisfaccion",
        columna_metodologia="Metodologia",
        columna_utilidad="Utilidad",
        columna_claridad="Claridad",
        columna_aprendio="Aprendizaje",
        columna_facilitador="Facilitador",
        columna_conocia="Conocia_Tema",
        columna_calificacion="Calificacion",
    )

    # --- Salida ---------------------------------------------------------
    salidas: dict[str, pd.DataFrame] = {args.hoja_salida: df}

    for clave, columna in COLUMNAS_CATEGORIA_ENCUESTAS.items():
        salidas[f"Resumen_{clave.capitalize()}"] = tabla_cruzada(df, columna)

    salidas["Metricas_Sesion"] = metricas_por_sesion(df)
    salidas["Generales_Programa"] = metricas_generales(df)
    salidas["Participacion"] = participacion_por_sesion(df, COLUMNAS_TEXTO_ENCUESTAS)

    ruta_salida = Path(args.salida) if args.salida else ruta_entrada
    escribir_hojas(ruta_salida, salidas, anexar=ruta_salida == ruta_entrada)

    print(f"Archivo guardado en: {ruta_salida}")
    for nombre in salidas:
        print(f"  - {nombre}")

    print("\n=== CATEGORIAS DE IDEAS (frecuencia total) ===")
    for valor, cuenta in df["Cat_Ideas"].value_counts().head(15).items():
        print(f"  {valor}: {cuenta}")

    print("\n=== METRICAS PROMEDIO POR SESION ===")
    metricas = metricas_por_sesion(df)
    for sesion, fila in metricas.iterrows():
        print(
            f"  Sesion {int(sesion)}: n={int(fila['n_encuestados'])}, "
            f"Calif={fila['Calificacion']}/5, Apre={fila['Aprendizaje']}/5, "
            f"Clar={fila['Claridad']}/5, Util={fila['Utilidad']}/5, "
            f"Facil={fila['Facilitador']}/5, Conocia={fila['Conocia_Pct']}%"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
