"""Genera el reporte cualitativo de las encuestas, agrupado por sesión.

Extrae las respuestas abiertas válidas de cada sesión y las presenta como
material de lectura para la sistematización.

Uso:
    python analisis_cualitativo.py --entrada datos/encuestas_por_clase.xlsx
    python analisis_cualitativo.py --entrada datos/x.xlsx --salida informe.txt
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

from src.normalizacion import parsear_fecha
from src.reportes import es_texto_valido

# Columnas de la exportación cruda de Google Forms, en orden.
COLUMNAS_CRUDAS: dict[str, int] = {
    "fecha_hora": 3,
    "ideas_texto": 11,
    "gusto_texto": 12,
    "mejora_texto": 13,
    "profundizar_texto": 14,
}

MINIMO_COLUMNAS = max(COLUMNAS_CRUDAS.values()) + 1

# Cuántas respuestas se citan por bloque antes de resumir el resto.
MAXIMO_CITAS = 7

# Fechas que no aparecen en la hoja de sesiones pero que sí pertenecen a una.
EXCEPCIONES_FECHA_SESION: dict[str, int] = {
    "2026-06-20": 5,
    "2026-07-04": 7,
}

SESIONES_A_REVISAR = range(1, 10)

TITULOS: dict[str, str] = {
    "ideas_texto": "IDEAS Y CONCEPTOS APRENDIDOS",
    "gusto_texto": "LO QUE MAS GUSTO",
    "mejora_texto": "ASPECTOS A MEJORAR / SUGERENCIAS",
    "profundizar_texto": "TEMAS QUE GUSTARIA PROFUNDIZAR",
}


def _nombre(df: pd.DataFrame, clave: str) -> str:
    return str(df.columns[COLUMNAS_CRUDAS[clave]])


def _textos_validos(serie: pd.Series) -> list[str]:
    salida: list[str] = []
    for valor in serie:
        if not es_texto_valido(valor):
            continue
        texto = str(valor).strip()
        if texto.lower() in {
            "-",
            "mucho",
            "poco",
            "regular",
            "nada",
            "ninguno",
            "ninguna",
            "sin respuesta",
            "sin comentarios",
        }:
            continue
        salida.append(texto)
    return salida


def _parsear_argumentos(argv: list[str] | None = None) -> argparse.Namespace:
    raiz = Path(__file__).resolve().parent
    analizador = argparse.ArgumentParser(
        description="Genera el reporte cualitativo por sesión de la IX Escuela."
    )
    analizador.add_argument(
        "--entrada",
        default=str(raiz / "datos" / "encuestas_por_clase.xlsx"),
        help="Libro con las hojas de respuestas crudas (Hoja1 / Hoja2).",
    )
    analizador.add_argument("--hoja-datos", default="Hoja1")
    analizador.add_argument("--hoja-sesiones", default="Hoja2")
    analizador.add_argument(
        "--salida",
        default=str(raiz / "informes" / "analisis_sesiones.txt"),
        help="Archivo de texto donde se escribe el reporte.",
    )
    analizador.add_argument(
        "--max-citas",
        type=int,
        default=MAXIMO_CITAS,
        help="Máximo de respuestas citadas por bloque.",
    )
    return analizador.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parsear_argumentos(argv)
    ruta_entrada = Path(args.entrada)
    if not ruta_entrada.exists():
        print(f"No se encontró el archivo de entrada: {ruta_entrada}", file=sys.stderr)
        return 1

    df = pd.read_excel(ruta_entrada, sheet_name=args.hoja_datos)
    hoja_sesiones = pd.read_excel(ruta_entrada, sheet_name=args.hoja_sesiones)

    if df.shape[1] < MINIMO_COLUMNAS:
        print(
            f"La hoja '{args.hoja_datos}' tiene {df.shape[1]} columnas y se "
            f"esperaban al menos {MINIMO_COLUMNAS}.",
            file=sys.stderr,
        )
        return 1

    col_fecha = _nombre(df, "fecha_hora")
    df["Fecha_str"] = df[col_fecha].apply(parsear_fecha)
    df["Fecha"] = pd.to_datetime(df["Fecha_str"], errors="coerce").dt.date

    mapa_fecha_sesion: dict[object, int] = {}
    if {"N_Sesion", "Fecha"}.issubset(hoja_sesiones.columns):
        pares = hoja_sesiones[["N_Sesion", "Fecha"]].drop_duplicates()
        pares["Fecha"] = pd.to_datetime(pares["Fecha"], errors="coerce").dt.date
        mapa_fecha_sesion = dict(zip(pares["Fecha"], pares["N_Sesion"], strict=True))
    for fecha_iso, numero in EXCEPCIONES_FECHA_SESION.items():
        mapa_fecha_sesion[pd.to_datetime(fecha_iso).date()] = numero
    df["Sesion"] = df["Fecha"].map(mapa_fecha_sesion)

    temas_por_sesion: dict[int, list[str]] = {}
    if {"N_Sesion", "Tema"}.issubset(hoja_sesiones.columns):
        temas_por_sesion = (
            hoja_sesiones.groupby("N_Sesion")["Tema"].apply(lambda s: list(s.dropna())).to_dict()
        )

    lineas: list[str] = []

    def escribir(texto: str = "") -> None:
        lineas.append(texto)

    escribir("=" * 80)
    escribir("ANALISIS CUALITATIVO DE ENCUESTAS POR SESION")
    escribir("IX Escuela de Jovenes Ruralistas")
    escribir("=" * 80)

    for sesion in SESIONES_A_REVISAR:
        subconjunto = df[df["Sesion"] == sesion]
        escribir()
        escribir("=" * 70)
        escribir(f"SESION {sesion} - {len(subconjunto)} encuestados")
        escribir("=" * 70)
        temas = temas_por_sesion.get(sesion, [])
        if temas:
            escribir("Temas desarrollados:")
            for tema in temas:
                escribir(f"  - {tema}")

        for clave, titulo in TITULOS.items():
            escribir()
            escribir(f">> {titulo}:")
            textos = _textos_validos(subconjunto[_nombre(df, clave)])
            if not textos:
                escribir("  (sin respuestas)")
                continue
            escribir(f"  ({len(textos)} respuestas)")
            for i, texto in enumerate(textos[: args.max_citas], 1):
                escribir(f"  {i}. {texto[:200]}")
            if len(textos) > args.max_citas:
                escribir(f"  ... y {len(textos) - args.max_citas} respuestas mas")

    ruta_salida = Path(args.salida)
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    ruta_salida.write_text("\n".join(lineas), encoding="utf-8")
    print(f"Reporte guardado en: {ruta_salida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
