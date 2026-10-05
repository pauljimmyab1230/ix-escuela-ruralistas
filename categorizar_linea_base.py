"""Procesa la línea base: categoriza respuestas abiertas y nivela conocimientos.

Uso:
    python categorizar_linea_base.py --entrada datos/linea_base.xlsx
    python categorizar_linea_base.py --entrada datos/x.xlsx --salida datos/salida.xlsx
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

from src.categorias import cargar_esquemas
from src.normalizacion import NIVEL_A_NUMERO
from src.reportes import escribir_hojas, resumen_niveles_conocimiento

# Columnas de la exportación cruda del formulario de línea base, en orden.
COLUMNAS_CRUDAS: dict[str, int] = {
    "nombre": 2,
    "edad": 3,
    "genero": 4,
    "procedencia": 5,
    "region": 6,
    "lengua": 7,
    "educacion": 8,
    "organizacion": 11,
    "discapacidad": 13,
    "vinculo_rural": 15,
    "tiempo_vinculo": 17,
    "participado_emprend": 27,
    "tiene_emprend": 28,
    "tipo_emprend": 29,
    "ha_elaborado_canvas": 30,
    "capacitado_negocios": 31,
    "accedido_fondo": 32,
    "ha_liderado": 33,
    "habla_publico": 34,
    "capacidad_liderazgo": 35,
    "trabajo_equipo": 36,
    "red_jovenes": 37,
    "cual_red": 38,
    "actores_comunidad": 39,
    "articulacion": 40,
    "aprender_texto": 41,
    "intereses_texto": 42,
    "lograr_texto": 43,
    "implementar_plan": 44,
}

# Los 9 conocimientos autopercibidos ocupan las columnas 18 a 26.
INICIO_CONOCIMIENTOS = 18
FIN_CONOCIMIENTOS = 26

MINIMO_COLUMNAS = FIN_CONOCIMIENTOS + 1

# Nombres legibles de los conocimientos, en el orden de las columnas.
NOMBRES_CONOCIMIENTOS: list[str] = [
    "Desarrollo Agrario Rural",
    "Agroecologia",
    "Enfoque de Genero",
    "Interculturalidad",
    "Formalizacion del negocio",
    "Herramienta canva",
    "Comercializacion rural",
    "Formulacion de proyectos",
    "Fondos de financiamiento",
]


def _nombre(df: pd.DataFrame, clave: str) -> str:
    return str(df.columns[COLUMNAS_CRUDAS[clave]])


def _columnas_conocimiento_crudas(df: pd.DataFrame) -> list[str]:
    return [str(df.columns[i]) for i in range(INICIO_CONOCIMIENTOS, FIN_CONOCIMIENTOS + 1)]


def _parsear_argumentos(argv: list[str] | None = None) -> argparse.Namespace:
    raiz = Path(__file__).resolve().parent
    analizador = argparse.ArgumentParser(
        description="Procesa la línea base de la IX Escuela de Jóvenes Ruralistas."
    )
    analizador.add_argument(
        "--entrada",
        default=str(raiz / "datos" / "linea_base.xlsx"),
        help="Libro con la exportación del formulario de línea base.",
    )
    analizador.add_argument(
        "--hoja",
        default="Respuestas de formulario 1",
        help="Hoja que contiene las respuestas.",
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
    return analizador.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parsear_argumentos(argv)
    ruta_entrada = Path(args.entrada)
    if not ruta_entrada.exists():
        print(f"No se encontró el archivo de entrada: {ruta_entrada}", file=sys.stderr)
        return 1

    print(f"Leyendo {ruta_entrada} (hoja '{args.hoja}') ...")
    df = pd.read_excel(ruta_entrada, sheet_name=args.hoja)

    if df.shape[1] < MINIMO_COLUMNAS:
        print(
            f"La hoja tiene {df.shape[1]} columnas y se esperaban al menos {MINIMO_COLUMNAS}.",
            file=sys.stderr,
        )
        return 1

    esquemas = cargar_esquemas(args.reglas)
    df["Cat_Aprender"] = [
        esquemas["aprender"].clasificar(v) or esquemas["aprender"].etiqueta_sin_respuesta
        for v in df[_nombre(df, "aprender_texto")]
    ]
    df["Cat_Intereses"] = [
        esquemas["intereses"].clasificar(v) or esquemas["intereses"].etiqueta_sin_respuesta
        for v in df[_nombre(df, "intereses_texto")]
    ]
    df["Cat_Lograr"] = [
        esquemas["lograr"].clasificar(v) or esquemas["lograr"].etiqueta_sin_respuesta
        for v in df[_nombre(df, "lograr_texto")]
    ]

    # Conocimientos autopercibidos: Nada/Basico/Intermedio/Avanzado -> 1-4.
    columnas_crudas = _columnas_conocimiento_crudas(df)
    for nombre, columna in zip(NOMBRES_CONOCIMIENTOS, columnas_crudas, strict=True):
        df[f"Nivel_{nombre}"] = df[columna].map(NIVEL_A_NUMERO).astype(float)

    columnas_nivel = [f"Nivel_{n}" for n in NOMBRES_CONOCIMIENTOS]
    df["Promedio_Conocimiento"] = df[columnas_nivel].mean(axis=1).round(1)

    # --- Tablas resumen -------------------------------------------------
    def frecuencias(columna: str) -> pd.Series:
        cuenta: dict[str, int] = {}
        for valor in df[columna].dropna():
            texto = str(valor).strip()
            if texto.startswith("Sin respuesta"):
                continue
            for categoria in texto.split("|"):
                categoria = categoria.strip()
                if categoria:
                    cuenta[categoria] = cuenta.get(categoria, 0) + 1
        serie = pd.Series(cuenta, name="Frecuencia", dtype="int64")
        return serie.sort_values(ascending=False)

    frecuencias_aprender = frecuencias("Cat_Aprender")
    frecuencias_intereses = frecuencias("Cat_Intereses")
    frecuencias_lograr = frecuencias("Cat_Lograr")

    genero = df[_nombre(df, "genero")].astype(str).str.strip().str.lower()
    df["Genero_Group"] = genero.map({"masculino": "Masculino", "femenino": "Femenino"}).fillna(
        "Otro"
    )

    # --- Salida ---------------------------------------------------------
    salidas: dict[str, pd.DataFrame] = {
        "Procesado": pd.DataFrame(
            {
                "Nombres": df[_nombre(df, "nombre")],
                "Edad": df[_nombre(df, "edad")],
                "Genero": df[_nombre(df, "genero")],
                "Region": df[_nombre(df, "region")],
                "Procedencia": df[_nombre(df, "procedencia")],
                "Lengua_Materna": df[_nombre(df, "lengua")],
                "Nivel_Educativo": df[_nombre(df, "educacion")],
                "Organizacion": df[_nombre(df, "organizacion")],
                "Vinculo_Rural": df[_nombre(df, "vinculo_rural")],
                "Tiempo_Vinculo": df[_nombre(df, "tiempo_vinculo")],
                "Participado_Emprend": df[_nombre(df, "participado_emprend")],
                "Tiene_Emprendimiento": df[_nombre(df, "tiene_emprend")],
                "Tipo_Emprendimiento": df[_nombre(df, "tipo_emprend")],
                "Ha_Elaborado_Canvas": df[_nombre(df, "ha_elaborado_canvas")],
                "Capacitado_Negocios": df[_nombre(df, "capacitado_negocios")],
                "Accedido_Fondo": df[_nombre(df, "accedido_fondo")],
                "Ha_Liderado": df[_nombre(df, "ha_liderado")],
                "Habla_Publico": df[_nombre(df, "habla_publico")],
                "Capacidad_Liderazgo": df[_nombre(df, "capacidad_liderazgo")],
                "Trabajo_Equipo": df[_nombre(df, "trabajo_equipo")],
                "Red_Jovenes": df[_nombre(df, "red_jovenes")],
                "Actores_Comunidad": df[_nombre(df, "actores_comunidad")],
                "Promedio_Conocimiento": df["Promedio_Conocimiento"],
                **{
                    nombre: df[columna]
                    for nombre, columna in zip(NOMBRES_CONOCIMIENTOS, columnas_crudas, strict=True)
                },
                "Aprender_Texto": df[_nombre(df, "aprender_texto")],
                "Cat_Aprender": df["Cat_Aprender"],
                "Intereses_Texto": df[_nombre(df, "intereses_texto")],
                "Cat_Intereses": df["Cat_Intereses"],
                "Lograr_Texto": df[_nombre(df, "lograr_texto")],
                "Cat_Lograr": df["Cat_Lograr"],
            }
        ),
        "Freq_Aprender": frecuencias_aprender,
        "Freq_Intereses": frecuencias_intereses,
        "Freq_Lograr": frecuencias_lograr,
        "Niveles_Conocimiento": resumen_niveles_conocimiento(
            pd.DataFrame(
                {
                    f"Conoc_{nombre}": df[columna].map(
                        {k: v - 1 for k, v in NIVEL_A_NUMERO.items()}
                    )
                    for nombre, columna in zip(NOMBRES_CONOCIMIENTOS, columnas_crudas, strict=True)
                }
            )
        ),
        "Conocimiento_x_Region": (
            pd.DataFrame(
                {
                    nombre: df[columna].map({k: v - 1 for k, v in NIVEL_A_NUMERO.items()})
                    for nombre, columna in zip(NOMBRES_CONOCIMIENTOS, columnas_crudas, strict=True)
                }
            )
            .assign(Region=df[_nombre(df, "region")])
            .groupby("Region")
            .mean()
            .round(2)
        ),
    }

    ruta_salida = Path(args.salida) if args.salida else ruta_entrada
    escribir_hojas(ruta_salida, salidas, anexar=ruta_salida == ruta_entrada)

    print("=== LINEA BASE PROCESADA ===")
    print(f"Total registros: {len(df)}")
    print(f"Hombres: {(df['Genero_Group'] == 'Masculino').sum()}")
    print(f"Mujeres: {(df['Genero_Group'] == 'Femenino').sum()}")
    print(f"Otro: {(df['Genero_Group'] == 'Otro').sum()}")

    for etiqueta, tabla in (
        ("QUE ESPERA APRENDER", frecuencias_aprender),
        ("TEMAS DE INTERES", frecuencias_intereses),
        ("QUE ESPERA LOGRAR", frecuencias_lograr),
    ):
        print(f"\n=== CATEGORIAS: {etiqueta} ===")
        for categoria, cuenta in tabla.items():
            print(f"  {categoria}: {cuenta}")

    print("\n=== NIVELES DE CONOCIMIENTO AUTOPERCIBIDO (promedio 1-4) ===")
    for nombre, columna in zip(NOMBRES_CONOCIMIENTOS, columnas_crudas, strict=True):
        promedio = df[columna].map(NIVEL_A_NUMERO).mean()
        print(f"  {nombre}: {promedio:.2f}")
    print(f"  Promedio general: {df['Promedio_Conocimiento'].mean():.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
