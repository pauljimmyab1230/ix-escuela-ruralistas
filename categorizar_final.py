import pandas as pd
import numpy as np
import re
import unicodedata
import warnings
warnings.filterwarnings('ignore')

def rm_accents(t):
    """Remove Spanish accents for keyword matching"""
    return unicodedata.normalize('NFKD', t).encode('ascii', 'ignore').decode('ascii')

# ============================================================
# 1. CARGAR DATOS
# ============================================================
df = pd.read_excel(r'C:\Users\paulj\Downloads\IX escuela\encuestas por clase.xlsx', sheet_name='Hoja1')
df2 = pd.read_excel(r'C:\Users\paulj\Downloads\IX escuela\encuestas por clase.xlsx', sheet_name='Hoja2')

col_fecha = df.columns[3]
def parse_fecha(val):
    if pd.isna(val): return None
    s = str(val).replace('\xa0', ' ').replace('\u202f', ' ').strip()
    m = re.match(r'(\d{2})/(\d{2})/(\d{4})', s)
    if m: return f'{m.group(3)}-{m.group(2)}-{m.group(1)}'
    m = re.match(r'(\d{4})-(\d{2})-(\d{2})', s)
    if m: return f'{m.group(1)}-{m.group(2)}-{m.group(3)}'
    return None

df['Fecha_str'] = df[col_fecha].apply(parse_fecha)
df['Fecha'] = pd.to_datetime(df['Fecha_str']).dt.date
sesion_fecha = df2[['N_Sesion', 'Fecha']].drop_duplicates()
sesion_fecha['Fecha'] = pd.to_datetime(sesion_fecha['Fecha']).dt.date
map_fecha_sesion = dict(zip(sesion_fecha['Fecha'], sesion_fecha['N_Sesion']))
map_fecha_sesion.update({pd.to_datetime('2026-06-20').date(): 5, pd.to_datetime('2026-07-04').date(): 7})
df['Sesion'] = df['Fecha'].map(map_fecha_sesion)

# Nombre sesion
sesion_nombre = df2.groupby('N_Sesion')['Tema'].apply(lambda x: ' | '.join(x.dropna())).to_dict()

# ============================================================
# 2. FUNCION: texto valido
# ============================================================
def es_valido(val):
    if pd.isna(val): return False
    t = str(val).strip()
    if t in ['-', '', 'Mucho', 'poco', 'regular', 'Nada', 'ninguno', 'ninguna', 'Ninguno', 'Ninguna',
             'sin respuesta', 'sin comentarios', 'Ningun', 'Ningún', 'Ns', 'ns', 'Si', 'si', 'No', 'no']:
        return False
    return True

# ============================================================
# 3. CATEGORIZACION MANUAL por analisis de contenido real
# Basado en la lectura de todos los comentarios
# ============================================================

def cat_ideas(txt):
    """Categorias para IDEAS APRENDIDAS - basado en contenido real de respuestas"""
    if not es_valido(txt): return 'Sin respuesta'
    t = rm_accents(txt.lower().strip())
    
    # Agroecologia y manejo de suelos
    if any(p in t for p in ['agroecologia', 'agroecol', 'suelo', 'abono', 'compost', 'bioabono',
                              'biol', 'microorganismo', 'bioinsumo', 'fertilizante',
                              'control biolog', 'plaga', 'agricultura sostenible',
                              'agricultura ecologica', 'cultivo organico', 'rotacion',
                              'asociacion de cultivo', 'sinergia', 'policultivo',
                              'conservacion de suelo', 'biodiversidad', 'sostenibilidad',
                              'ecoamigable', 'fertilizacion', 'tecnificar', 'tecnificacion',
                              'organico', 'organica', 'manejo integrado']):
        return 'Agroecologia y Suelos'
    
    # Saberes ancestrales y tradicionales
    if any(p in t for p in ['saber ancestral', 'ancestral', 'tradicion', 'conocimiento tradicional',
                              'valorizacion de tradiciones', 'colle', 'rivera']):
        return 'Saberes Ancestrales'
    
    # Genero (incluye acentos)
    if any(p in t for p in ['genero', 'mujer', 'feminizacion rural', 'femenino',
                              'equidad de genero', 'rol de la mujer', 'ideologia de genero',
                              'transversalizacion del genero', 'explotador de genero',
                              'identidad de genero', 'interseccionalidad',
                              'sensibilidad de genero']):
        return 'Enfoque de Genero'
    
    # Interculturalidad
    if any(p in t for p in ['intercultural', 'interculturalidad', 'multicultural',
                              'multiculturalidad', 'diversidad cultural', 'diversidad',
                              'inclusion', 'inclusivo', 'pertenencia', 'autopercepcion',
                              'pertinencia cultural', 'identidad cultural',
                              'identificacion cultural']):
        return 'Interculturalidad'
    
    # DAR / Realidad rural / Politicas publicas
    if any(p in t for p in ['dar', 'realidad del dar', 'reforma agraria', 'agricultura cientifica',
                              'envejecimiento de la poblacion rural', 'diagnostico de juventudes',
                              'juventud', 'joven rural', 'juventudes andinas', 'politica publica',
                              'iniciativa', 'problematica agricola', 'limitaciones',
                              'diferencias agrarias', 'brecha', 'programa social rural',
                              'desarrollo rural', 'comunidad', 'comunicacion intercultural',
                              'comunicacion estrategica', 'mecanismo participativo',
                              'agricultura familiar', 'toma de decisiones',
                              'modernizacion cientifica', 'historia del ruralismo',
                              'programa que apoyan', 'evolucion del tema agrario',
                              'agricultura de exportacion', 'historia de la agricultura']):
        return 'Realidad Rural y Politicas'
    
    # CANVAS - Modelo de negocio
    if any(p in t for p in ['canvas', 'canva', 'modelo canva', 'propuesta de valor',
                              'segmento de cliente', 'cliente', 'canales',
                              'modelo de negocio', 'problema', 'solucion',
                              'actividades clave', 'recursos clave', 'socio clave',
                              'alianza', 'cadena de valor', 'modelo camva']):
        return 'Modelo CANVAS'
    
    # Emprendimiento / Innovacion
    if any(p in t for p in ['emprend', 'negocio', 'idea de negocio', 'oportunidad',
                              'innovacion', 'innovacion tecnologica', 'innovacion rural',
                              'desarrollo de negocios', 'comercializacion',
                              'identificacion de oportunidades', 'mercado',
                              'analisis de mercado', 'identidad territorial',
                              'startup', 'star up', 'cosecha', 'ganaderia', 'mineria',
                              'produccion', 'inteligencia artificial',
                              'agricultura con inteligencia', 'tecnificacion']):
        return 'Emprendimiento Rural'
    
    # Storytelling / Pitch
    if any(p in t for p in ['storytelling', 'story', 'pitch', 'elevator pitch', 'speech',
                              'spitch', 'sustentacion', 'presentacion', 'hablar en publico',
                              'narrativa', 'discurso', 'feedback']):
        return 'Storytelling y Pitch'
    
    # Finanzas / Costos / Fondos
    if any(p in t for p in ['finanza', 'financiamiento', 'financiero', 'costo', 'gasto',
                              'ingreso', 'egreso', 'punto de equilibrio', 'presupuesto',
                              'ganancia', 'perdida', 'flujo de caja', 'ahorro',
                              'capital', 'inversion', 'economia circular',
                              'estado de ganancia', 'estado financiero',
                              'contabilidad', 'educacion financiera',
                              'registrar la marca', 'promperu',
                              'fondo', 'credito', 'procompite', 'capital concursable',
                              'acompanamiento para fondos', 'planificacion estrategica',
                              'diseno de marca', 'tributar', 'impuesto']):
        return 'Finanzas y Fondos'
    
    # Liderazgo
    if any(p in t for p in ['lidera', 'liderazgo', 'perseverancia', 'trabajo en equipo',
                              'equipo', 'colaboracion', 'participacion', 'grupal',
                              'creatividad']):
        return 'Liderazgo y Trabajo en Equipo'
    
    # Casos de exito
    if any(p in t for p in ['caso de exito', 'experiencia', 'testimonio', 'inspirador',
                              'motivacion', 'ejemplo', 'referente', 'exito', 'internacional']):
        return 'Casos de Exito'
    
    # Marketing
    if any(p in t for p in ['marketing', 'marketing digital', 'redes', 'publicidad']):
        return 'Marketing Digital'
    
    # Soberania alimentaria
    if any(p in t for p in ['soberania alimentaria', 'soberania agroalimentaria']):
        return 'Soberania Alimentaria'
    
    # Agua y medio ambiente (nueva)
    if any(p in t for p in ['agua', 'cambio climatico', 'recurso natural', 'ambiente']):
        return 'Medio Ambiente y Agua'
    
    return 'Otros'

def cat_gusto(txt):
    """Categorias para LO QUE MAS GUSTO"""
    if not es_valido(txt): return 'Sin respuesta'
    t = rm_accents(txt.lower().strip())
    
    # Check for "todo" patterns first
    if t in ['todo', 'todas', 'ambos', 'todas me gustaron', 'todo me gusto', 'todo en general', 'todo completo', 'todas las clases']:
        return 'Todo en General'
    
    if any(p in t for p in ['dinamica', 'taller', 'actividad', 'juego',
                              'divertido', 'participativo', 'interactivo', 'grupal',
                              'dibujar', 'kahoot', 'quiz']) and \
       not any(p in t for p in ['ejemplo', 'experiencia']):
        return 'Dinamicas y Actividades'
    
    if any(p in t for p in ['facilitador', 'profesor', 'expositor', 'ponente', 'instructor',
                              'monitor', 'explicacion', 'explico', 'explicaron',
                              'forma de explicar', 'didactico', 'claro', 'claridad',
                              'buena explicacion', 'excelente explicacion',
                              'buena ponencia', 'antropologa', 'exposicion',
                              'ponencia', 'exposiciones', 'ponentes']):
        return 'Facilitadores y Exposiciones'
    
    if any(p in t for p in ['compartir', 'experiencia', 'participante', 'companero',
                              'conpanero', 'convivir', 'intercambio', 'dialogo',
                              'conocerse', 'retroalimentacion', 'interaccion',
                              'encuentro', 'diversidad de ideas', 'opinione',
                              'opiniones distintas']):
        return 'Compartir Experiencias'
    
    if any(p in t for p in ['caso', 'ejemplo', 'exito', 'testimonio', 'inspiracion',
                              'motivacion', 'historia', 'real', 'historias',
                              'caso concreto', 'experiencia real']):
        return 'Casos y Ejemplos Reales'
    
    # Content-related: specific learning, concepts, topics mentioned
    if any(p in t for p in ['tema', 'contenido', 'aprendizaje', 'aprender',
                              'conocimiento', 'informacion', 'interesante',
                              'detalle', 'curiosidad', 'dato', 'conocer como',
                              'conocer como influye', 'seguir aprendiendo',
                              'concepto', 'fertilizacion', 'conservacion de suelo',
                              'microorganismo', 'contabilidad', 'identidad de genero',
                              'rol de la mujer', 'emprendimiento',
                              'desarrollo de negocios', 'desarrollo rural',
                              'agroecologia', 'lean start', 'plan de negocios',
                              'innovacion', 'identidad territorial',
                              'financiamiento', 'evaluacion de finanza',
                              'propuesta de valor', 'modelo canva', 'canvas',
                              'storytelling', 'elevator pitch', 'costos fijo',
                              'punto de equilibrio', 'presupuesto', 'ahorro',
                              'flujo de caja', 'costos variable']):
        return 'Contenido de la Sesion'
    
    if any(p in t for p in ['metodologia', 'estructura', 'organizacion', 'programa',
                              'planificacion']):
        return 'Metodologia'
    
    if any(p in t for p in ['material', 'diapositiva', 'recurso', 'video', 'apoyo visual',
                              'libro', 'recomendacion del libro']):
        return 'Materiales y Recursos'
    
    if any(p in t for p in ['ambiente', 'clima', 'confianza', 'respeto', 'comodo',
                              'acogedor', 'hospitalario', 'buen ambiente']):
        return 'Ambiente y Clima'
    
    if any(p in t for p in ['trabajo en equipo', 'trabajo grupal', 'grupo', 'trabajar en grupo',
                              'coordin', 'trabajar con mi equipo']):
        return 'Trabajo en Equipo'
    
    if any(p in t for p in ['practico', 'practica', 'aplicacion', 'aplicar', 'hands-on']):
        return 'Actividades Practicas'
    
    return 'Otros'

def cat_mejora(txt):
    """Categorias para ASPECTOS A MEJORAR"""
    if not es_valido(txt): return 'Sin respuesta / Satisfecho'
    t = rm_accents(txt.lower().strip())
    
    if any(p in t for p in ['nada', 'todo bien', 'ninguno', 'ninguna', 'no hay',
                              'sin comentarios', 'correcto', 'esta bien', 'estuvo bien',
                              'excelente', 'muy buena', 'muy bueno', 'perfecto',
                              'todo estuvo', 'no tengo observacion', 'sin observacion',
                              'no hay nada', 'buena', 'no se']):
        return 'Sin respuesta / Satisfecho'
    
    if any(p in t for p in ['tiempo', 'duracion', 'horario', 'hora', 'extenso',
                              'largo', 'corto', 'breve', 'mas tiempo', 'poco tiempo',
                              'optimizar el tiempo', 'tiempo se debe controlar',
                              'exceder', 'puntualidad', 'rapidez']):
        return 'Tiempo y Duracion'
    
    if any(p in t for p in ['internet', 'conexion', 'virtual', 'plataforma', 'zoom',
                              'tecnico', 'audio', 'video', 'microfono', 'sonido',
                              'conectividad', 'carro', 'se conectan']):
        return 'Aspectos Tecnicos'
    
    if any(p in t for p in ['dinamica', 'actividad', 'taller', 'interactivo',
                              'juego', 'kahoot', 'quiz', 'participativo']):
        return 'Mas Dinamicas e Interactividad'
    
    if any(p in t for p in ['participacion', 'intervencion', 'pregunta', 'dialogo',
                              'debate', 'opinion', 'comentario', 'dudas',
                              'intercambio de ideas', 'interactuar']):
        return 'Mas Participacion e Intercambio'
    
    if any(p in t for p in ['ejemplo', 'caso', 'practico', 'aplicacion', 'real',
                              'vivencial', 'aterrizar']):
        return 'Mas Ejemplos y Aplicacion Practica'
    
    if any(p in t for p in ['grupo', 'trabajo en equipo', 'equipo de trabajo',
                              'agrupar']):
        return 'Trabajo en Equipo'
    
    if any(p in t for p in ['material', 'diapositiva', 'guia', 'documento', 'cuaderno',
                              'apoyo']):
        return 'Materiales de Apoyo'
    
    if any(p in t for p in ['explicacion', 'claro', 'profundizar', 'detalle',
                              'complejo', 'dificil', 'confuso', 'entender',
                              'didactico']):
        return 'Claridad y Profundidad'
    
    if any(p in t for p in ['organizacion', 'logistica', 'programacion', 'comunicacion',
                              'planificacion', 'seriedad']):
        return 'Organizacion y Logistica'
    
    if any(p in t for p in ['exposicion', 'ponente', 'facilitador', 'monitoreo']):
        return 'Facilitadores y Exposiciones'
    
    return 'Otras Sugerencias'

def cat_profundizar(txt):
    """Categorias para TEMAS A PROFUNDIZAR"""
    if not es_valido(txt): return 'Sin respuesta'
    t = rm_accents(txt.lower().strip())
    
    if any(p in t for p in ['ninguno', 'ninguna', 'nada', 'todo bien', 'todo ok',
                              'excelente', 'sin observacion', 'no hay']):
        return 'Sin respuesta / Satisfecho'
    
    if any(p in t for p in ['agroecologia', 'agroecol', 'suelo', 'abono', 'compost',
                              'bioinsumo', 'control biologic', 'agricultura',
                              'organico', 'biodiversidad', 'conservacion',
                              'agricultura familiar', 'soberania alimentaria',
                              'sistema agroforestal', 'agroeconomia', 'manejo de suelo',
                              'exportacion', 'reforma agraria', 'data de exportaciones',
                              'produccion agroecologica']):
        return 'Agroecologia y Agricultura'
    
    if any(p in t for p in ['canva', 'canvas', 'modelo de negocio', 'propuesta de valor',
                              'modelo canova']):
        return 'Modelo CANVAS'
    
    if any(p in t for p in ['finanza', 'presupuesto', 'costo', 'ingreso', 'egreso',
                              'punto de equilibrio', 'flujo', 'credito',
                              'financiamiento', 'fondo', 'procompite', 'capital',
                              'inversion', 'presupuestar', 'banco',
                              'acceso a financiamiento']):
        return 'Finanzas y Acceso a Fondos'
    
    if any(p in t for p in ['emprend', 'negocio', 'cliente', 'mercado', 'marketing',
                              'venta', 'comercializacion', 'idea de negocio',
                              'innovacion', 'tecnologica', 'desarrollo de producto']):
        return 'Emprendimiento e Innovacion'
    
    if any(p in t for p in ['genero', 'mujer', 'equidad', 'igualdad', 'enfoque de genero',
                              'feminino']):
        return 'Enfoque de Genero'
    
    if any(p in t for p in ['intercultural', 'interculturalidad', 'diversidad',
                              'indigena', 'comunidad indigena']):
        return 'Interculturalidad'
    
    if any(p in t for p in ['storytelling', 'pitch', 'speech', 'presentacion',
                              'sustentacion', 'hablar en publico', 'spitch',
                              'elevator']):
        return 'Storytelling y Pitch'
    
    if any(p in t for p in ['lidera', 'liderazgo', 'equipo', 'trabajo en equipo',
                              'liderar']):
        return 'Liderazgo y Trabajo en Equipo'
    
    if any(p in t for p in ['caso', 'exito', 'experiencia real', 'testimonio',
                              'inspirador', 'emprendedor']):
        return 'Casos de Exito'
    
    if any(p in t for p in ['proyecto', 'plan de negocio', 'formulacion',
                              'evaluacion de proyecto', 'gestion de proyecto',
                              'operatividad', 'requisito']):
        return 'Formulacion de Proyectos'
    
    if any(p in t for p in ['tecnologia', 'digital', 'herramienta', 'app', 'software',
                              'plataforma']):
        return 'Tecnologia y Herramientas'
    
    if any(p in t for p in ['ambiente', 'cambio climatico', 'sostenible', 'recurso natural',
                              'agua']):
        return 'Medio Ambiente'
    
    if any(p in t for p in ['practico', 'taller', 'dinamica', 'participacion',
                              'interactivo', 'grupal']):
        return 'Talleres y Actividades Practicas'
    
    if any(p in t for p in ['derecho', 'legal', 'reglamento', 'normativa',
                              'derechos colectivos']):
        return 'Aspectos Legales y Derechos'
    
    if any(p in t for p in ['tiempo', 'horario', 'exposicion', 'monitoreo']):
        return 'Organizacion del Programa'
    
    return 'Otros'

# ============================================================
# 4. APLICAR CATEGORIZACION
# ============================================================
col_ideas = df.columns[11]
col_gusto = df.columns[12]
col_mejora = df.columns[13]
col_profundizar = df.columns[14]

df['Cat_Ideas'] = df[col_ideas].apply(cat_ideas)
df['Cat_Gusto'] = df[col_gusto].apply(cat_gusto)
df['Cat_Mejora'] = df[col_mejora].apply(cat_mejora)
df['Cat_Profundizar'] = df[col_profundizar].apply(cat_profundizar)

# ============================================================
# 5. DATOS DE SATISFACCION Y CALIFICACION
# ============================================================
likert5 = {'Muy de acuerdo': 5, 'De acuerdo': 4, 'Neutral': 3, 'En desacuerdo': 2, 'Muy en desacuerdo': 1}
aprendio_map = {'Mucho': 5, 'Bastante': 4, 'Regular': 3, 'Poco': 2, 'Nada': 1}
claro_map = {'Muy claro': 5, 'Claro': 4, 'poco claro': 2, 'Poco claro': 2}
facil_map = {'Excelente': 5, 'Regular': 3, 'deficiente': 1}

col_sat = df.columns[16]      # Me siento satisfecho(a) con mi participación...
col_calif = df.columns[10]     # ¿Qué calificación le otorgas a la sesión? (1-5)
col_aprendio = df.columns[7]   # ¿Cuánto consideras que aprendiste?
col_claro = df.columns[6]      # ¿Qué tan claro fue el tema desarrollado?
col_util = df.columns[5]       # Los temas y talleres fueron útiles...
col_conocia = df.columns[8]    # Antes de esta sesión, ¿conocías este tema?
col_facil = df.columns[9]      # El facilitador explicó los temas de manera clara.
col_metodo = df.columns[15]    # La metodología y acompañamiento...

df['Sat_Num'] = pd.to_numeric(df[col_sat].map(likert5), errors='coerce')
df['Calif_Num'] = pd.to_numeric(df[col_calif], errors='coerce')
df['Aprendio_Num'] = df[col_aprendio].map(aprendio_map).astype(float)
df['Claro_Num'] = df[col_claro].map(claro_map).astype(float)
df['Util_Num'] = df[col_util].map(likert5).astype(float)
df['Facil_Num'] = df[col_facil].map(facil_map).astype(float)
df['Metodo_Num'] = pd.to_numeric(df[col_metodo].map(likert5), errors='coerce')
# Conocia es binario: Si/No
df['Conocia_Bin'] = df[col_conocia].apply(lambda x: 1 if str(x).strip().lower() == 'si' else 0)

# ============================================================
# 6. TABLAS RESUMEN
# ============================================================
# Asegurar que Sesion es entero
df['Sesion'] = df['Sesion'].fillna(0).astype(int)

# Tabla 1: Ideas por sesion
t1 = pd.crosstab(df['Cat_Ideas'], df['Sesion'])
t1['Total'] = t1.sum(axis=1)
t1 = t1.sort_values('Total', ascending=False)

# Tabla 2: Gusto por sesion
t2 = pd.crosstab(df['Cat_Gusto'], df['Sesion'])
t2['Total'] = t2.sum(axis=1)
t2 = t2.sort_values('Total', ascending=False)

# Tabla 3: Mejora por sesion
t3 = pd.crosstab(df['Cat_Mejora'], df['Sesion'])
t3['Total'] = t3.sum(axis=1)
t3 = t3.sort_values('Total', ascending=False)

# Tabla 4: Profundizar por sesion
t4 = pd.crosstab(df['Cat_Profundizar'], df['Sesion'])
t4['Total'] = t4.sum(axis=1)
t4 = t4.sort_values('Total', ascending=False)

# Tabla 5: Metricas promedio por sesion
metricas = df.groupby('Sesion').agg(
    n_encuestados=('Sesion', 'count'),
    Calificacion=('Calif_Num', 'mean'),
    Aprendizaje=('Aprendio_Num', 'mean'),
    Claridad=('Claro_Num', 'mean'),
    Utilidad=('Util_Num', 'mean'),
    Facilitador=('Facil_Num', 'mean'),
    Conocia_Pct=('Conocia_Bin', 'mean')
).round(2)
metricas['Conocia_Pct'] = (metricas['Conocia_Pct'] * 100).round(1)

# Tabla 5b: Metricas generales del programa (no por sesion, solo sesion 1 tiene)
generales = df.groupby('Sesion').agg(
    n=('Sat_Num', 'count'),
    Satisfaccion=('Sat_Num', 'mean'),
    Metodologia=('Metodo_Num', 'mean')
).round(2)
# Solo sesion 1 tiene datos reales
generales = generales[generales['n'] > 0]

# Tabla 6: Participacion (cuantos respondieron cada pregunta abierta)
def pct_respuesta(col):
    def calc_pct(grp):
        total = len(grp)
        validos = sum(1 for v in grp if es_valido(v))
        return round(validos / total * 100, 1)
    return df.groupby('Sesion')[col].apply(calc_pct)

participacion = pd.DataFrame({
    'n_encuestados': df.groupby('Sesion').size(),
    '%Respondio_Ideas': pct_respuesta(col_ideas),
    '%Respondio_Gusto': pct_respuesta(col_gusto),
    '%Respondio_Mejora': pct_respuesta(col_mejora),
    '%Respondio_Profundizar': pct_respuesta(col_profundizar),
})

# ============================================================
# 7. GUARDAR EN EXCEL
# ============================================================
with pd.ExcelWriter(r'C:\Users\paulj\Downloads\IX escuela\encuestas por clase.xlsx',
                    engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
    
    # Hoja Procesado: datos originales + categorias
    out = df[df.columns[:17]].copy()
    out.columns = [f'Col_{i}' for i in range(17)]
    out['Sesion'] = df['Sesion']
    out['Fecha'] = df['Fecha']
    out['Cat_Ideas'] = df['Cat_Ideas']
    out['Cat_Gusto'] = df['Cat_Gusto']
    out['Cat_Mejora'] = df['Cat_Mejora']
    out['Cat_Profundizar'] = df['Cat_Profundizar']
    # Renombrar las columnas originales con nombre legible
    rename_map = {
        'Col_0': '#',
        'Col_1': 'Correo',
        'Col_2': 'Usuario',
        'Col_3': 'FechaHora',
        'Col_4': 'Nombre',
        'Col_5': 'Utilidad',
        'Col_6': 'Claridad',
        'Col_7': 'Aprendizaje',
        'Col_8': 'Conocia_Tema',
        'Col_9': 'Facilitador',
        'Col_10': 'Calificacion',
        'Col_11': 'Ideas_Texto',
        'Col_12': 'Gusto_Texto',
        'Col_13': 'Mejora_Texto',
        'Col_14': 'Profundizar_Texto',
        'Col_15': 'Metodologia',
        'Col_16': 'Satisfaccion',
    }
    out = out.rename(columns=rename_map)
    out.to_excel(writer, sheet_name='Procesado', index=False)
    out.to_excel(writer, sheet_name='Procesado', index=False)
    
    # Hojas de resumen
    t1.to_excel(writer, sheet_name='Resumen_Ideas')
    t2.to_excel(writer, sheet_name='Resumen_Gusto')
    t3.to_excel(writer, sheet_name='Resumen_Mejora')
    t4.to_excel(writer, sheet_name='Resumen_Profundizar')
    metricas.to_excel(writer, sheet_name='Metricas_Sesion')
    generales.to_excel(writer, sheet_name='Generales_Programa')
    participacion.to_excel(writer, sheet_name='Participacion')

print("ARCHIVO GUARDADO: encuestas por clase.xlsx")
print("Hojas:")
print("  - Procesado (datos con categoria unica por respuesta)")
print("  - Resumen_Ideas (frecuencia por sesion)")
print("  - Resumen_Gusto")
print("  - Resumen_Mejora")
print("  - Resumen_Profundizar")
print("  - Metricas_Sesion (promedios por sesion: calif, aprendiz, claridad, util, facilitador)")
print("  - Generales_Programa (satisfaccion y metodologia global, solo sesion 1)")
print("  - Participacion (% que respondio cada pregunta por sesion)")

print("\n=== CATEGORIAS DE IDEAS (frecuencia total) ===")
for v, c in df['Cat_Ideas'].value_counts().head(15).items():
    print(f"  {v}: {c}")

print("\n=== CATEGORIAS DE GUSTO (frecuencia total) ===")
for v, c in df['Cat_Gusto'].value_counts().head(15).items():
    print(f"  {v}: {c}")

print("\n=== CATEGORIAS DE MEJORA (frecuencia total) ===")
for v, c in df['Cat_Mejora'].value_counts().head(15).items():
    print(f"  {v}: {c}")

print("\n=== CATEGORIAS DE PROFUNDIZAR (frecuencia total) ===")
for v, c in df['Cat_Profundizar'].value_counts().head(15).items():
    print(f"  {v}: {c}")

print("\n=== METRICAS PROMEDIO POR SESION ===")
for ses, row in metricas.iterrows():
    calif = row['Calificacion'] if pd.notna(row['Calificacion']) else '-'
    apre  = row['Aprendizaje'] if pd.notna(row['Aprendizaje']) else '-'
    cla   = row['Claridad'] if pd.notna(row['Claridad']) else '-'
    uti   = row['Utilidad'] if pd.notna(row['Utilidad']) else '-'
    fac   = row['Facilitador'] if pd.notna(row['Facilitador']) else '-'
    print(f"  Sesion {int(ses)}: n={int(row['n_encuestados'])}, Calif={calif}/5, Apre={apre}/5, Clar={cla}/5, Util={uti}/5, Facil={fac}/5, Conocia={row['Conocia_Pct']}%")

print("\n=== METRICAS GENERALES (solo sesion 1 tiene respuestas) ===")
for ses, row in generales.iterrows():
    print(f"  Sesion {int(ses)}: n={int(row['n'])}, Satisfaccion={row['Satisfaccion']}/5, Metodologia={row['Metodologia']}/5")
