# IX Escuela de Jóvenes Ruralistas · Sistematización

Dashboard y pipeline de datos para la sistematización de la **IX Escuela de
Jóvenes Ruralistas 2026** (Ypard / EJR).

El proyecto reúne la información de becarios, mentores, sesiones, asistencia,
encuestas de satisfacción, evaluaciones y la comparación entre **línea base** y
**línea final** en un solo lugar, navegable desde el navegador.

---

## Requisitos

- Python 3.11 o superior
- `pip`

## Instalación

```bash
git clone https://github.com/pauljimmyab1230/ix-escuela-ruralistas.git
cd ix-escuela-ruralistas

python -m venv .venv
.venv\Scripts\activate            # Windows
# source .venv/bin/activate       # Linux / macOS

pip install -r requirements.txt
```

Para trabajar en el proyecto (tests y lint):

```bash
pip install -r requirements-dev.txt
```

## Ejecutar el dashboard

```bash
streamlit run app.py
```

Se abre en `http://localhost:8501`. `dashboard.py` se conserva como punto de
entrada heredado y hace lo mismo.

### Navegación

| Página | Contenido |
|---|---|
| 🏠 Resumen General | Indicadores globales, demografía, asistencia, calificaciones y calidad de los datos |
| 👥 Becarios | Demografía, conocimientos autopercibidos, experiencia emprendedora y preguntas abiertas |
| 📋 Encuestas | Satisfacción por sesión y categorías de las respuestas abiertas |
| 📅 Asistencia | Participación por sesión y por participante |
| 📝 Evaluaciones | Examen inicial, entregables y planes de emprendimiento |
| 📈 Línea Base vs Final | Evolución de conocimientos, mapas de calor individuales y expectativas vs resultados |

La barra lateral permite filtrar por **región**, **género** y por **becarios
concretos**, además de cambiar entre tema oscuro y claro.

---

## Estructura del proyecto

```
.
├── app.py                    # Punto de entrada de Streamlit
├── dashboard.py              # Compatibilidad con el punto de entrada antiguo
│
├── core/                     # Infraestructura del dashboard
│   ├── config.py             # Paleta, umbrales y nombres del programa
│   ├── datos.py              # Carga con caché, filtros y contexto de cada vista
│   └── graficos.py           # Tema claro/oscuro y plantilla de Plotly
│
├── paginas/                  # Una vista por archivo
│   ├── comunes.py            # Bloques de gráficos compartidos
│   ├── resumen.py
│   ├── becarios.py
│   ├── encuestas.py
│   ├── asistencia.py
│   ├── evaluaciones.py
│   └── linea_final.py
│
├── src/                      # Lógica de datos, independiente de la UI
│   ├── normalizacion.py      # Fechas, acentos, escalas y limpieza de textos
│   ├── categorias.py         # Motor de categorización de respuestas abiertas
│   ├── datos.py              # Modelo del libro de sistematización
│   └── reportes.py           # Tablas resumen y escritura de resultados
│
├── reglas_categorias.yaml    # Reglas de categorización, editables sin tocar código
│
├── categorizar_final.py      # CLI: categoriza las encuestas por sesión
├── categorizar_linea_base.py # CLI: procesa el formulario de línea base
├── analisis_cualitativo.py   # CLI: reporte cualitativo por sesión
│
├── tests/                    # Pruebas unitarias y de integración
├── Sistematizacion_nueva.xlsx
├── requirements.txt
├── requirements-dev.txt
└── pyproject.toml
```

---

## Libro de datos

`Sistematizacion_nueva.xlsx` es la fuente única de verdad del dashboard.
Tiene 15 hojas:

| Hoja | Contenido |
|---|---|
| `01a.Becarios` | Registro y línea base de los becarios |
| `01b.Mentores` | Mentores del programa |
| `01c.Representantes` | Representantes de comunidad |
| `02.Equipos` | Composición de los grupos de trabajo |
| `03.Modulos` | Módulos curriculares |
| `04.Sesiones` | Calendario, temas y facilitadores |
| `05.Asistencia` | Registros de acceso por sesión |
| `06.Encuestas` | Encuestas de satisfacción por sesión |
| `07.LineaBase` | Formulario de ingreso |
| `08.LineaFinal` | Formulario de cierre |
| `09.Examen` | Examen inicial |
| `10.Entregables` | Notas de los entregables |
| `11.PlanesEmprendimiento` | Evaluación de los planes por jurado |
| `12.EvalMentores` | Evaluación de mentores y representantes |
| `13.BitacoraTrabajo` | Bitácora semanal de los equipos |

La carga valida que existan las hojas y columnas críticas. Si algo falta, la
interfaz informa qué se esperaba en lugar de fallar con un `traceback`.

---

## Pipeline de datos

Los tres scripts de línea de comandos reciben y escriben rutas por argumento:
ya no dependen de rutas absolutas de una máquina concreta.

### 1. Categorizar encuestas por sesión

```bash
python categorizar_final.py \
  --entrada datos/encuestas_por_clase.xlsx \
  --hoja-datos Hoja1 \
  --hoja-sesiones Hoja2 \
  --salida datos/encuestas_procesadas.xlsx
```

Añade las columnas `Cat_Ideas`, `Cat_Gusto`, `Cat_Mejora` y `Cat_Profundizar`,
y genera las hojas `Resumen_*`, `Metricas_Sesion`, `Generales_Programa` y
`Participacion`. Si no se indica `--salida`, se anexa al libro de entrada.

### 2. Procesar la línea base

```bash
python categorizar_linea_base.py \
  --entrada datos/linea_base.xlsx \
  --hoja "Respuestas de formulario 1" \
  --salida datos/linea_base_procesada.xlsx
```

### 3. Reporte cualitativo

```bash
python analisis_cualitativo.py \
  --entrada datos/encuestas_por_clase.xlsx \
  --salida informes/analisis_sesiones.txt
```

---

## Reglas de categorización

Las categorías de las respuestas abiertas viven en
[`reglas_categorias.yaml`](reglas_categorias.yaml). Se pueden ajustar sin tocar
código Python.

Convención de patrones (se aplican sobre el texto en minúsculas y sin acentos):

| Escrito en el YAML | Significado | Ejemplo |
|---|---|---|
| `palabra` | Palabra completa | `agua` coincide en «el agua» pero no en «aguacero» |
| `prefijo*` | Prefijo de palabra | `agroecolog*` alcanza «agroecología» y «agroecológico» |
| `frase compuesta` | Frase completa | `trabajo en equipo` |

Dos modos de asignación:

- **`modo: unica`** — gana la primera regla que coincide. El orden del archivo
  es el orden de prioridad.
- **`modo: multiple`** — acumula todas las coincidencias, unidas con `|`.

Dentro de una regla, `excluye` descarta la coincidencia si el texto contiene
alguna de esas palabras (por ejemplo, la categoría «Dinámicas» se excluye si la
respuesta menciona un `ejemplo`).

Tras editar el YAML basta con volver a ejecutar el script correspondiente.

---

## Verificación

```bash
pytest              # pruebas
ruff check .        # lint
ruff format .       # formato
```

Las pruebas cubren la normalización de textos y fechas, el motor de
categorización (incluidos los falsos positivos por subcadena) y el filtrado del
libro de datos.

---

## Notas de calidad de los datos

El dashboard muestra un bloque de **calidad de los datos** en el resumen general.
Conviene tenerlo presente al interpretar los resultados:

- **Encuestas sin calificación.** Parte de las encuestas traen `-` o vacío en la
  calificación. Esas filas se excluyen de los promedios, por lo que el promedio
  por sesión puede basarse en menos respuestas que el total indicado.
- **Grupos sin nombre de equipo.** No todos los grupos de la hoja `02.Equipos`
  tienen `Nombre_equipo`.
- **Línea base y línea final tienen coberturas distintas.** La comparación
  «qué esperaba aprender» vs «qué aprendió» enfrenta el total de becarios con
  quienes respondieron el formulario de cierre. Las diferencias absolutas
  reflejan esa brecha además del contenido.

---

## Licencia

[Licencia MIT](LICENSE).
