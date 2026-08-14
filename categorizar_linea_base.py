import pandas as pd
import numpy as np
import re
from collections import Counter
import openpyxl
from openpyxl.utils import get_column_letter

# ============================================================
# 1. CARGAR DATOS
# ============================================================
df = pd.read_excel(r'C:\Users\paulj\Downloads\IX escuela\Linea Base IX escuela.xlsx', sheet_name='Respuestas de formulario 1')

# ============================================================
# 2. IDENTIFICAR COLUMNAS
# ============================================================
cols = df.columns.tolist()

col_nombre = cols[2]      # Nombres y Apellidos
col_edad = cols[3]        # Edad
col_genero = cols[4]      # Genero
col_procedencia = cols[5] # Lugar de procedencia
col_region = cols[6]      # Region
col_lengua = cols[7]      # Lengua materna
col_educacion = cols[8]   # Nivel educativo

col_organizacion = cols[11]  # Pertenece a alguna organizacion?
col_discapacidad = cols[13]  # Tiene alguna discapacidad?
col_vinculo_rural = cols[15] # Tiene relacion con actividades agrarias o rurales?
col_tiempo_vinculo = cols[17] # Cuanto tiempo lleva vinculado

# Conocimientos autopercibidos (cols 18-26)
conocimiento_cols = {
    'Desarrollo Agrario Rural': cols[18],
    'Agroecologia': cols[19],
    'Enfoque de Genero': cols[20],
    'Interculturalidad': cols[21],
    'Formalizacion del negocio': cols[22],
    'Herramienta canva': cols[23],
    'Comercializacion rural': cols[24],
    'Formulacion de proyectos': cols[25],
    'Fondos de financiamiento': cols[26],
}

col_participado_emprend = cols[27]  # Ha participado en algun emprendimiento rural?
col_tiene_emprend = cols[28]       # Actualmente tiene algun emprendimiento?
col_tipo_emprend = cols[29]        # Que tipo de emprendimiento?
col_ha_elaborado_canvas = cols[30] # Ha elaborado anteriormente un modelo canva?
col_capacitado_negocios = cols[31] # Ha recibido capacitaciones sobre negocios?
col_accedido_fondo = cols[32]      # Ha accedido a algun fondo concursable?
col_ha_liderado = cols[33]         # Ha liderado actividades o proyectos?
col_habla_publico = cols[34]       # Que tan comodo hablando en publico?
col_capacidad_liderazgo = cols[35] # Considera que tiene capacidad de liderazgo?
col_trabajo_equipo = cols[36]      # Que tan comodo trabajando en equipo?
col_red_jovenes = cols[37]         # Formas parte de una red de jovenes?
col_cual_red = cols[38]            # Cual es la red?
col_actores_comunidad = cols[39]   # Conoces a los actores de tu comunidad?
col_articulacion = cols[40]        # Que tipo de articulacion te gustaria fortalecer?

# Columnas abiertas a categorizar
col_aprender = cols[41]   # Que espera aprender
col_intereses = cols[42]  # Que temas le interesan mas
col_lograr = cols[43]     # Que esperas lograr
col_implementar = cols[44] # Te gustaria implementar tu plan de emprendimiento?

# ============================================================
# 3. FUNCIONES DE CATEGORIZACION
# ============================================================

def es_valido(val):
    if pd.isna(val):
        return False
    s = str(val).strip().lower()
    if s in ['-', '', '.', 'ninguno', 'ninguna', 'nada', 'todo', 'todo lo que se pueda',
             'mucho', 'si', 'no', 'ns', 'sin respuesta', 'sin comentarios',
             'aprender', 'conocimiento', 'mas conocimiento', 'ampliar mis conocimientos',
             'aprender bastante', 'todo los temas', 'oportunidades', 'innovacion',
             'investigacion', 'sostenibilidad', 'agroecologia', 'emprendimiento',
             'economia circular', 'agroinnovacion', 'agricola', 'emprendimientos']:
        return False
    return True

def categorizar_aprender(texto):
    """Categoriza lo que espera aprender en la escuela"""
    if not es_valido(texto):
        return 'Sin respuesta'
    t = str(texto).lower()
    categorias = []

    # Liderazgo y habilidades personales
    if any(p in t for p in ['lidera', 'liderazgo', 'habilidades', 'capacidades',
                              'crecer profesional', 'formacion profesional',
                              'fortalecer mis conocimientos', 'fortalecer mis capacidad']):
        categorias.append('Liderazgo y Desarrollo Personal')

    # Emprendimiento y negocios
    if any(p in t for p in ['emprend', 'negocio', 'plan de negocio', 'idea de negocio',
                              'modelo de negocio', 'mercado', 'marketing',
                              'comercializacion', 'marca', 'contabilidad']):
        categorias.append('Emprendimiento y Negocios')

    # Agroecologia y agricultura sostenible
    if any(p in t for p in ['agroecologia', 'agroecol', 'agricultura', 'agro',
                              'suelo', 'abono', 'compost', 'bioinsumo',
                              'producion agricola', 'produccion agricola',
                              'cultivo', 'ganaderia', 'sostenible',
                              'produccion sostenible', 'agricola',
                              'agropecuario', 'agroindustrial']):
        categorias.append('Agroecologia y Agricultura Sostenible')

    # Desarrollo rural sostenible
    if any(p in t for p in ['desarrollo rural', 'desarrollo agrario', 'desarrollo sostenible',
                              'desarrollo territorial', 'desarrollo comunitario',
                              'realidad rural', 'realidad del campo',
                              'comunidad', 'comunitario', 'rural',
                              'desarrollo de comunidades']):
        categorias.append('Desarrollo Rural y Comunitario')

    # Herramientas y conocimientos practicos
    if any(p in t for p in ['herramienta', 'conocimiento', 'herramientas',
                              'conocimientos', 'tecnicas', 'enfoques',
                              'metodologia', 'aprender', 'practico',
                              'practicas', 'fortalecer mis conocimientos']):
        categorias.append('Herramientas y Conocimientos Practicos')

    # Gestion de proyectos
    if any(p in t for p in ['proyecto', 'gestion de proyecto', 'formulacion',
                              'gestion de proyectos', 'plan de emprendimiento',
                              'implementar', 'ejecutar']):
        categorias.append('Gestion de Proyectos')

    # Innovacion y tecnologia
    if any(p in t for p in ['innovacion', 'innovacion agricola', 'innovacion social',
                              'tecnologia', 'transformacion', 'nuevas herramientas']):
        categorias.append('Innovacion y Tecnologia')

    # Investigacion
    if any(p in t for p in ['investigacion', 'investigar']):
        categorias.append('Investigacion')

    # Trabajo en equipo y redes
    if any(p in t for p in ['trabajo en equipo', 'equipo', 'red', 'redes',
                              'intercambiar', 'intercambio', 'compartir',
                              'participacion', 'joven', 'jovenes']):
        categorias.append('Trabajo en Equipo y Redes')

    # Sostenibilidad y medio ambiente
    if any(p in t for p in ['sostenibilidad', 'ambiental', 'medio ambiente',
                              'cuidado del ambiente', 'cambio climatico',
                              'conservacion', 'recurso natural']):
        categorias.append('Sostenibilidad y Medio Ambiente')

    # Financiamiento y fondos
    if any(p in t for p in ['financiamiento', 'fondo', 'fondos concursables',
                              'fondos concursante', 'capital', 'inversion',
                              'credito', 'financiero']):
        categorias.append('Financiamiento y Fondos')

    # Interculturalidad y genero
    if any(p in t for p in ['intercultural', 'interculturalidad', 'cultura',
                              'cultura', 'genero', 'mujer', 'equidad',
                              'identidad', 'territorio']):
        categorias.append('Interculturalidad y Genero')

    # Incidencia politica
    if any(p in t for p in ['incidencia', 'politica', 'politicas publicas',
                              'participacion politica', 'toma de decisiones']):
        categorias.append('Incidencia Politica')

    if not categorias:
        categorias.append('Otros')

    return ' | '.join(categorias)


def categorizar_intereses(texto):
    """Categoriza los temas que mas le interesan"""
    if not es_valido(texto):
        return 'Sin respuesta'
    t = str(texto).lower()
    categorias = []

    # Agroecologia y produccion sostenible
    if any(p in t for p in ['agroecologia', 'agroecol', 'agricultura sostenible',
                              'produccion sostenible', 'agricultura regenerativa',
                              'agricultura organica', 'organico', 'organica',
                              'bioinsumo', 'compost', 'suelo', 'abono',
                              'control biologico', 'sistema agroalimentario',
                              'agroforesteria', 'seguridad alimentaria',
                              'manejo de la tierra', 'principios de la agroecologia']):
        categorias.append('Agroecologia y Produccion Sostenible')

    # Emprendimiento y negocios rurales
    if any(p in t for p in ['emprend', 'negocio', 'agronegocio', 'mercado',
                              'comercializacion', 'marca', 'plan de negocio',
                              'marketing', 'marketing rural', 'marketing territorial',
                              'contabilidad', 'economia', 'economia circular',
                              'economia rural', 'negocios verdes',
                              'formulacion de proyectos de negocios',
                              'oportunidades de produccion']):
        categorias.append('Emprendimiento y Negocios Rurales')

    # Liderazgo y desarrollo juvenil
    if any(p in t for p in ['lidera', 'liderazgo', 'liderazgo juvenil',
                              'participacion juvenil', 'joven', 'juventud',
                              'jovenes', 'desarrollo juvenil']):
        categorias.append('Liderazgo y Desarrollo Juvenil')

    # Desarrollo rural y comunitario
    if any(p in t for p in ['desarrollo rural', 'desarrollo comunitario',
                              'desarrollo agrario', 'desarrollo sostenible',
                              'desarrollo economico rural', 'comunidad',
                              'comunitario', 'desarrollo de comunidades',
                              'arraigo rural', 'fortalecimiento comunitario']):
        categorias.append('Desarrollo Rural y Comunitario')

    # Medio ambiente y sostenibilidad
    if any(p in t for p in ['ambiente', 'ambiental', 'sostenibilidad',
                              'conservacion', 'biodiversidad', 'cambio climatico',
                              'recurso natural', 'gestion de recursos',
                              'ecosistema', 'agua', 'acceso al agua',
                              'educacion ambiental', 'manejo responsable del agua']):
        categorias.append('Medio Ambiente y Sostenibilidad')

    # Innovacion y tecnologia
    if any(p in t for p in ['innovacion', 'innovacion social', 'innovacion agricola',
                              'innovacion productiva', 'tecnologia',
                              'agroinnovacion', 'transformacion',
                              'nuevas innovaciones']):
        categorias.append('Innovacion y Tecnologia')

    # Investigacion
    if any(p in t for p in ['investigacion', 'investigacion rural']):
        categorias.append('Investigacion')

    # Financiamiento
    if any(p in t for p in ['financiamiento', 'fondo', 'fondos concursables',
                              'capital', 'inversion', 'credito', 'financiero',
                              'finanzas']):
        categorias.append('Financiamiento y Fondos')

    # Interculturalidad y genero
    if any(p in t for p in ['intercultural', 'interculturalidad', 'cultura',
                              'cultura', 'genero', 'mujer', 'equidad',
                              'territorio', 'identidad territorial']):
        categorias.append('Interculturalidad, Cultura y Territorio')

    # Incidencia politica y politicas publicas
    if any(p in t for p in ['incidencia', 'politica', 'politicas publicas',
                              'incidencia politica']):
        categorias.append('Incidencia Politica')

    # Gestion de proyectos
    if any(p in t for p in ['proyecto', 'gestion de proyecto', 'formulacion',
                              'gestion de proyectos', 'proyecto de triple impacto']):
        categorias.append('Gestion de Proyectos')

    if not categorias:
        categorias.append('Otros')

    return ' | '.join(categorias)


def categorizar_lograr(texto):
    """Categoriza lo que espera lograr al finalizar el programa"""
    if not es_valido(texto):
        return 'Sin respuesta'
    t = str(texto).lower()
    categorias = []

    # Desarrollar emprendimiento / negocio
    if any(p in t for p in ['emprend', 'negocio', 'plan de negocio',
                              'plan de emprendimiento', 'modelo de negocio',
                              'implementar mi emprendimiento', 'emprender',
                              'desarrollar un emprendimiento', 'mi emprendimiento',
                              'iniciar un emprendimiento', 'empezar un emprendimiento']):
        categorias.append('Desarrollar Emprendimiento o Negocio')

    # Aplicar conocimientos en la comunidad
    if any(p in t for p in ['aplicar', 'implementar', 'ejecutar', 'poner en practica',
                              'llevar a mi comunidad', 'aplicar en mi comunidad',
                              'contribuir', 'aportar', 'impacto positivo',
                              'generar impacto', 'agente de cambio',
                              'beneficiar a mi comunidad', 'cambio en mi comunidad',
                              'progreso', 'desarrollo de mi comunidad']):
        categorias.append('Aplicar Conocimientos en la Comunidad')

    # Fortalecer liderazgo y habilidades
    if any(p in t for p in ['lidera', 'liderazgo', 'fortalecer mis habilidades',
                              'fortalecer mis capacidades', 'capacidades personales',
                              'habilidades personales', 'crecer personal',
                              'formacion profesional', 'capacidad de liderar',
                              'ser un lider', 'ser capaz', 'fortalecer mi liderazgo']):
        categorias.append('Fortalecer Liderazgo y Habilidades')

    # Adquirir conocimientos y herramientas
    if any(p in t for p in ['conocimiento', 'conocimientos', 'aprender',
                              'herramientas', 'nuevos conocimientos',
                              'mayor conocimiento', 'ampliar conocimiento',
                              'adquirir conocimiento', 'fortalecer conocimiento',
                              'saber mas', 'aprendido', 'nuevas herramientas']):
        categorias.append('Adquirir Conocimientos y Herramientas')

    # Desarrollar proyecto
    if any(p in t for p in ['proyecto', 'proyecto sostenible', 'desarrollar un proyecto',
                              'proyectos rurales', 'proyectos sostenibles',
                              'plan de emprendimiento', 'culminar con un proyecto',
                              'mi proyecto', 'proyecto con mi comunidad']):
        categorias.append('Desarrollar un Proyecto')

    # Trabajo en equipo y redes
    if any(p in t for p in ['trabajo en equipo', 'equipo', 'red', 'redes',
                              'intercambiar', 'intercambio', 'compartir',
                              'participacion', 'formar parte de una red',
                              'trabajar en equipo', 'trabajar con un equipo']):
        categorias.append('Trabajo en Equipo y Redes')

    # Desarrollo rural y comunitario
    if any(p in t for p in ['desarrollo rural', 'desarrollo agrario',
                              'desarrollo comunitario', 'desarrollo sostenible',
                              'desarrollo territorial', 'iniciativa',
                              'comunidad', 'comunitario', 'comunal']):
        categorias.append('Desarrollo Rural y Comunitario')

    # Innovacion y emprendimiento sostenible
    if any(p in t for p in ['innovacion', 'innovacion social', 'sostenible',
                              'sostenibilidad', 'emprendimiento sostenible',
                              'vision estrategica']):
        categorias.append('Innovacion y Sostenibilidad')

    if not categorias:
        categorias.append('Otros')

    return ' | '.join(categorias)


# ============================================================
# 4. APLICAR CATEGORIZACION
# ============================================================
df['Cat_Aprender'] = df[col_aprender].apply(lambda x: categorizar_aprender(x) if es_valido(x) else 'Sin respuesta')
df['Cat_Intereses'] = df[col_intereses].apply(lambda x: categorizar_intereses(x) if es_valido(x) else 'Sin respuesta')
df['Cat_Lograr'] = df[col_lograr].apply(lambda x: categorizar_lograr(x) if es_valido(x) else 'Sin respuesta')

# ============================================================
# 5. CONOCIMIENTOS AUTOPERCIBIDOS (Nada/Basico/Intermedio/Avanzado -> 1-4)
# ============================================================
nivel_map = {'Nada': 1, 'Basico': 2, 'Intermedio': 3, 'Avanzado': 4}

for nombre, col in conocimiento_cols.items():
    df[f'Nivel_{nombre}'] = df[col].map(nivel_map).astype(float)

# Calcular promedio de conocimiento global
nivel_cols = [f'Nivel_{n}' for n in conocimiento_cols.keys()]
df['Promedio_Conocimiento'] = df[nivel_cols].mean(axis=1).round(1)

# ============================================================
# 6. TABLAS RESUMEN
# ============================================================

# Frecuencia de categorias
def freq_table(series, name):
    freq = {}
    for val in series.dropna():
        if val == 'Sin respuesta':
            continue
        for cat in val.split(' | '):
            cat = cat.strip()
            freq[cat] = freq.get(cat, 0) + 1
    return pd.Series(freq, name=name).sort_values(ascending=False)

freq_aprender = freq_table(df['Cat_Aprender'], 'Frecuencia')
freq_intereses = freq_table(df['Cat_Intereses'], 'Frecuencia')
freq_lograr = freq_table(df['Cat_Lograr'], 'Frecuencia')

# Perfiles demograficos basicos
df['Genero_Group'] = df[col_genero].apply(lambda x: 'Masculino' if str(x).strip().lower() == 'masculino' else ('Femenino' if str(x).strip().lower() == 'femenino' else 'Otro'))

# ============================================================
# 7. GUARDAR RESULTADOS
# ============================================================
with pd.ExcelWriter(r'C:\Users\paulj\Downloads\IX escuela\Linea Base IX escuela.xlsx',
                    engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:

    # Datos procesados
    out_cols = {
        'Nombres': df[col_nombre],
        'Edad': df[col_edad],
        'Genero': df[col_genero],
        'Region': df[col_region],
        'Procedencia': df[col_procedencia],
        'Lengua_Materna': df[col_lengua],
        'Nivel_Educativo': df[col_educacion],
        'Organizacion': df[col_organizacion],
        'Vinculo_Rural': df[col_vinculo_rural],
        'Tiempo_Vinculo': df[col_tiempo_vinculo],
        'Participado_Emprend': df[col_participado_emprend],
        'Tiene_Emprendimiento': df[col_tiene_emprend],
        'Tipo_Emprendimiento': df[col_tipo_emprend],
        'Ha_Elaborado_Canvas': df[col_ha_elaborado_canvas],
        'Capacitado_Negocios': df[col_capacitado_negocios],
        'Accedido_Fondo': df[col_accedido_fondo],
        'Ha_Liderado': df[col_ha_liderado],
        'Habla_Publico': df[col_habla_publico],
        'Capacidad_Liderazgo': df[col_capacidad_liderazgo],
        'Trabajo_Equipo': df[col_trabajo_equipo],
        'Red_Jovenes': df[col_red_jovenes],
        'Actores_Comunidad': df[col_actores_comunidad],
        'Promedio_Conocimiento': df['Promedio_Conocimiento'],
    }
    for nombre in conocimiento_cols.keys():
        out_cols[nombre] = df[conocimiento_cols[nombre]]

    out_cols['Aprender_Texto'] = df[col_aprender]
    out_cols['Cat_Aprender'] = df['Cat_Aprender']
    out_cols['Intereses_Texto'] = df[col_intereses]
    out_cols['Cat_Intereses'] = df['Cat_Intereses']
    out_cols['Lograr_Texto'] = df[col_lograr]
    out_cols['Cat_Lograr'] = df['Cat_Lograr']

    out = pd.DataFrame(out_cols)
    out.to_excel(writer, sheet_name='Procesado', index=False)

    # Tablas de frecuencia
    freq_aprender.to_excel(writer, sheet_name='Freq_Aprender')
    freq_intereses.to_excel(writer, sheet_name='Freq_Intereses')
    freq_lograr.to_excel(writer, sheet_name='Freq_Lograr')

    # Tabla de niveles de conocimiento
    nivel_summary = df[nivel_cols].mean().round(2).sort_values(ascending=False)
    nivel_summary.index = [n.replace('Nivel_', '') for n in nivel_summary.index]
    nivel_summary.to_excel(writer, sheet_name='Niveles_Conocimiento')

    # Datos de conocimiento por region
    region_kn = df.groupby(col_region)[nivel_cols].mean().round(2)
    region_kn.columns = [n.replace('Nivel_', '') for n in region_kn.columns]
    region_kn.to_excel(writer, sheet_name='Conocimiento_x_Region')

print("=== LINEA BASE PROCESADA ===")
print(f"Total registros: {len(df)}")
print(f"Hombres: {len(df[df['Genero_Group']=='Masculino'])}")
print(f"Mujeres: {len(df[df['Genero_Group']=='Femenino'])}")
print(f"Otro: {len(df[df['Genero_Group']=='Otro'])}")

print(f"\n=== CATEGORIAS: QUE ESPERA APRENDER ===")
for cat, val in freq_aprender.items():
    print(f"  {cat}: {val}")

print(f"\n=== CATEGORIAS: TEMAS DE INTERES ===")
for cat, val in freq_intereses.items():
    print(f"  {cat}: {val}")

print(f"\n=== CATEGORIAS: QUE ESPERA LOGRAR ===")
for cat, val in freq_lograr.items():
    print(f"  {cat}: {val}")

print(f"\n=== NIVELES DE CONOCIMIENTO AUTOPERCIBIDO (promedio 1-4) ===")
for n in nivel_summary.index:
    print(f"  {n}: {nivel_summary[n]}")
print(f"  Promedio general: {df['Promedio_Conocimiento'].mean():.2f}")

print(f"\n=== NUEVAS HOJAS EN Linea Base IX escuela.xlsx ===")
print("  - Procesado (datos con categorias)")
print("  - Freq_Aprender (frecuencia de categorias: que espera aprender)")
print("  - Freq_Intereses (frecuencia de categorias: temas de interes)")
print("  - Freq_Lograr (frecuencia de categorias: que espera lograr)")
print("  - Niveles_Conocimiento (promedio de conocimiento autopercibido)")
print("  - Conocimiento_x_Region (conocimiento promedio por region)")
