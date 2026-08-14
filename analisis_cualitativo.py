import pandas as pd
import re
from collections import Counter, defaultdict

df = pd.read_excel(r'C:\Users\paulj\Downloads\IX escuela\encuestas por clase.xlsx', sheet_name='Hoja1')
df2 = pd.read_excel(r'C:\Users\paulj\Downloads\IX escuela\encuestas por clase.xlsx', sheet_name='Hoja2')

# Normalizar fechas
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
map_fecha_sesion.update({
    pd.to_datetime('2026-06-20').date(): 5,
    pd.to_datetime('2026-07-04').date(): 7,
})
df['Sesion'] = df['Fecha'].map(map_fecha_sesion)

# Temas por sesion
sesion_mapa = df2.groupby('N_Sesion')['Tema'].apply(lambda x: list(x.dropna())).to_dict()

# Columnas de texto
col_ideas = df.columns[11]
col_gusto = df.columns[12]
col_mejora = df.columns[13]
col_profundizar = df.columns[14]

def textos_limpios(series):
    """Filtra respuestas validas"""
    textos = []
    for v in series:
        if pd.isna(v): continue
        t = str(v).strip()
        if t in ['-', '', 'Mucho', 'poco', 'regular', 'Nada', 'ninguno', 'ninguna',
                 'Ninguno', 'Ninguna', 'Nada', 'sin respuesta', 'sin comentarios']:
            continue
        textos.append(t)
    return textos

# ============================================================
# GUARDAR REPORTE
# ============================================================
output_path = r'C:\Users\paulj\Downloads\IX escuela\analisis_sesiones.txt'
out_lines = []

def p(text=""):
    out_lines.append(text)

p("=" * 80)
p("ANALISIS CUALITATIVO DE ENCUESTAS POR SESION")
p("IX Escuela de Jovenes Ruralistas")
p("=" * 80)

for sesion in range(1, 10):
    mask = df['Sesion'] == sesion
    subset = df[mask]
    n = len(subset)
    temas = sesion_mapa.get(sesion, [])
    
    p()
    p("=" * 70)
    p(f"SESION {sesion} - {n} encuestados")
    p("=" * 70)
    p("Temas desarrollados:")
    for t in temas:
        p(f"  - {t}")
    
    # --- IDEAS APRENDIDAS ---
    p()
    p(">> IDEAS Y CONCEPTOS APRENDIDOS:")
    ideas = textos_limpios(subset[col_ideas])
    if ideas:
        p(f"  ({len(ideas)} respuestas)")
        for i, txt in enumerate(ideas[:7], 1):
            p(f"  {i}. {txt[:200]}")
        if len(ideas) > 7:
            p(f"  ... y {len(ideas)-7} respuestas mas")
    else:
        p("  (sin respuestas)")

    # --- LO QUE MAS GUSTO ---
    p()
    p(">> LO QUE MAS GUSTO:")
    gustos = textos_limpios(subset[col_gusto])
    if gustos:
        p(f"  ({len(gustos)} respuestas)")
        for i, txt in enumerate(gustos[:7], 1):
            p(f"  {i}. {txt[:200]}")
        if len(gustos) > 7:
            p(f"  ... y {len(gustos)-7} respuestas mas")
    else:
        p("  (sin respuestas)")

    # --- ASPECTOS A MEJORAR ---
    p()
    p(">> ASPECTOS A MEJORAR / SUGERENCIAS:")
    mejoras = textos_limpios(subset[col_mejora])
    if mejoras:
        p(f"  ({len(mejoras)} respuestas)")
        for i, txt in enumerate(mejoras[:7], 1):
            p(f"  {i}. {txt[:200]}")
        if len(mejoras) > 7:
            p(f"  ... y {len(mejoras)-7} respuestas mas")
    else:
        p("  (sin respuestas)")

    # --- TEMAS A PROFUNDIZAR ---
    p()
    p(">> TEMAS QUE GUSTARIA PROFUNDIZAR:")
    profundiza = textos_limpios(subset[col_profundizar])
    if profundiza:
        p(f"  ({len(profundiza)} respuestas)")
        for i, txt in enumerate(profundiza[:7], 1):
            p(f"  {i}. {txt[:200]}")
        if len(profundiza) > 7:
            p(f"  ... y {len(profundiza)-7} respuestas mas")
    else:
        p("  (sin respuestas)")

with open(output_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(out_lines))

print(f"Reporte guardado en: {output_path}")
