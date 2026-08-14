import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import os

# ============================================================
# CONFIGURACION
# ============================================================
st.set_page_config(page_title="IX Escuela de Jovenes Ruralistas", page_icon="🌱", layout="wide", initial_sidebar_state="expanded")

# ============================================================
# TEMA: DARK/LIGHT
# ============================================================
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = True

st.markdown("""
<style>
    .stMetric {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 15px 20px; border-radius: 12px; color: white;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    .stMetric label { color: rgba(255,255,255,0.85) !important; font-size: 0.85rem !important; }
    .stMetric [data-testid="stMetricValue"] { color: white !important; font-size: 1.8rem !important; font-weight: 700 !important; }
    .block-container { padding-top: 1rem; }
    h1 { border-bottom: 3px solid #4CAF50; padding-bottom: 10px; }
    .stTabs [data-baseweb="tab"] { border-radius: 8px 8px 0 0; padding: 10px 20px; font-weight: 600; }
    .stTabs [aria-selected="true"] { background-color: #4CAF50 !important; color: white !important; }
    div[data-testid="stSidebar"] { background: linear-gradient(180deg, #0a0d14 0%, #111827 50%, #1a1d24 100%) !important; }
    div[data-testid="stSidebar"] .stRadio label, div[data-testid="stSidebar"] .stSelectbox label,
    div[data-testid="stSidebar"] .stMultiSelect label, div[data-testid="stSidebar"] .stSlider label { color: rgba(255,255,255,0.9) !important; }
    div[data-testid="stSidebar"] h1 { color: #4CAF50 !important; border-bottom: 2px solid rgba(76,175,80,0.3); }
    div[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.1); }
</style>
""", unsafe_allow_html=True)

# ============================================================
# COLORES Y PLANTILLA
# ============================================================
PALETTE = ['#2196F3', '#E91E63', '#FF9800', '#4CAF50', '#9C27B0', '#00BCD4', '#FF5722', '#607D8B', '#795548', '#F44336']

def template(fig, height=420):
    fig.update_layout(
        template='plotly_dark',
        font=dict(family='Segoe UI, sans-serif', size=12, color='#e0e0e0'),
        title=dict(font=dict(size=16, color='#4CAF50'), x=0.5, xanchor='center'),
        margin=dict(t=50, b=40, l=40, r=20),
        height=height,
        legend=dict(orientation='h', yanchor='bottom', y=-0.25, xanchor='center', x=0.5, font_size=11),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )
    fig.update_xaxes(showgrid=True, gridwidth=0.5, gridcolor='rgba(255,255,255,0.08)')
    fig.update_yaxes(showgrid=True, gridwidth=0.5, gridcolor='rgba(255,255,255,0.08)')
    return fig

def bar_text(fig, fmt='%.0f'):
    fig.update_traces(textposition='outside', textfont_size=11, textfont_color='#e0e0e0')
    return fig

# ============================================================
# CARGAR DATOS
# ============================================================
@st.cache_data
def cargar_datos():
    path = os.path.join(os.path.dirname(__file__), 'Sistematizacion_nueva.xlsx')
    d = {}
    d['becarios'] = pd.read_excel(path, sheet_name='01a.Becarios')
    d['mentores'] = pd.read_excel(path, sheet_name='01b.Mentores')
    d['representantes'] = pd.read_excel(path, sheet_name='01c.Representantes')
    d['equipos'] = pd.read_excel(path, sheet_name='02.Equipos')
    d['modulos'] = pd.read_excel(path, sheet_name='03.Modulos')
    d['sesiones'] = pd.read_excel(path, sheet_name='04.Sesiones')
    d['asistencia'] = pd.read_excel(path, sheet_name='05.Asistencia')
    d['encuestas'] = pd.read_excel(path, sheet_name='06.Encuestas')
    d['linea_final'] = pd.read_excel(path, sheet_name='08.LineaFinal')
    d['examen'] = pd.read_excel(path, sheet_name='09.Examen')
    d['entregables'] = pd.read_excel(path, sheet_name='10.Entregables')
    d['planes'] = pd.read_excel(path, sheet_name='11.PlanesEmprendimiento')
    d['eval_mentores'] = pd.read_excel(path, sheet_name='12.EvalMentores')
    d['bitacora'] = pd.read_excel(path, sheet_name='13.BitacoraTrabajo')
    d['asistencia']['Fecha_str'] = pd.to_datetime(d['asistencia']['Fecha']).dt.strftime('%Y-%m-%d')
    d['enc_f'] = d['encuestas'][d['encuestas']['Sesion'] > 1].copy()
    d['enc_f']['Calif_num'] = pd.to_numeric(d['enc_f']['Calificacion'], errors='coerce')
    return d

datos = cargar_datos()

sesion_nombres = {2: 'Realidad DAR', 3: 'Agroecologia', 4: 'Genero e Interculturalidad',
                  5: 'CANVAS T1', 6: 'CANVAS T2', 7: 'CANVAS T3', 8: 'CANVAS T4', 9: 'Simulacro'}

def filtrar(val):
    if pd.isna(val): return False
    return str(val).strip() not in ['Sin respuesta', 'Sin respuesta / Satisfecho']

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("# 🌱 IX Escuela")
    st.markdown("### Jovenes Ruralistas")
    st.markdown("---")
    pagina = st.radio("Navegacion", ["🏠 Resumen General", "👥 Becarios", "📋 Encuestas", "📅 Asistencia", "📝 Evaluaciones", "📈 Linea Base vs Final"], label_visibility="collapsed")
    st.markdown("---")
    
    # Toggle dark/light mode
    tema = st.toggle("Modo Oscuro", value=True)
    if not tema:
        st.markdown("""<style>
            div[data-testid="stSidebar"] { background: linear-gradient(180deg, #1a237e 0%, #283593 50%, #3949ab 100%) !important; }
            div[data-testid="stSidebar"] h1 { color: white !important; }
        </style>""", unsafe_allow_html=True)
    st.markdown("---")
    regiones = ['Todas'] + sorted(datos['becarios']['Region'].dropna().unique().tolist())
    region_filtro = st.selectbox("Region", regiones)
    generos = ['Todos'] + sorted(datos['becarios']['Genero'].dropna().unique().tolist())
    genero_filtro = st.selectbox("Genero", generos)
    
    st.markdown("---")
    st.markdown("### Filtro Individual")
    
    # Preparar lista de becarios para filtro
    becarios_lista = datos['becarios'][['Nombre', 'Email']].copy()
    becarios_lista['Label'] = becarios_lista['Nombre'] + ' (' + becarios_lista['Email'].str[:20] + '...)'
    becarios_lista = becarios_lista.sort_values('Nombre')
    
    becarios_seleccionados = st.multiselect(
        "Seleccionar Becario(s)",
        options=becarios_lista['Label'].tolist(),
        default=[],
        help="Selecciona uno o varios becarios para ver sus datos individuales"
    )
    
    if becarios_seleccionados:
        emails_seleccionados = becarios_lista[becarios_lista['Label'].isin(becarios_seleccionados)]['Email'].tolist()
    else:
        emails_seleccionados = None
    
    st.markdown("---")
    st.caption("IX Escuela de Jovenes Ruralistas 2026 | Ypard / EJR")

# Aplicar filtros globalmente
df_b = datos['becarios'].copy()
if region_filtro != 'Todas':
    df_b = df_b[df_b['Region'] == region_filtro]
if genero_filtro != 'Todos':
    df_b = df_b[df_b['Genero'] == genero_filtro]

# Filtro individual por becario
if emails_seleccionados:
    df_b = df_b[df_b['Email'].isin(emails_seleccionados)]

# Filtrar asistencia por becarios filtrados
emails_filtrados = set(df_b['Email'].dropna().str.strip().str.lower())
df_asist = datos['asistencia'].copy()
if emails_seleccionados or region_filtro != 'Todas' or genero_filtro != 'Todos':
    df_asist = df_asist[df_asist['Correo electrónico'].str.strip().str.lower().isin(emails_filtrados)]

# Filtrar encuestas por becarios filtrados
df_enc = datos['enc_f'].copy()
if emails_seleccionados or region_filtro != 'Todas' or genero_filtro != 'Todos':
    df_enc = df_enc[df_enc['Correo'].str.strip().str.lower().isin(emails_filtrados)]

# Filtrar examen
df_exam = datos['examen'].copy()
if emails_seleccionados or region_filtro != 'Todas' or genero_filtro != 'Todos':
    df_exam = df_exam[df_exam['Correo'].str.strip().str.lower().isin(emails_filtrados)]

# Filtrar entregables
df_ent = datos['entregables'].copy()
if emails_seleccionados or region_filtro != 'Todas' or genero_filtro != 'Todos':
    df_ent = df_ent[df_ent['Correo'].str.strip().str.lower().isin(emails_filtrados)]

# Filtrar linea final
df_lf = datos['linea_final'].copy()
if emails_seleccionados or region_filtro != 'Todas' or genero_filtro != 'Todos':
    df_lf = df_lf[df_lf.iloc[:, 1].astype(str).str.strip().str.lower().isin(emails_filtrados)]

# ============================================================
# RESUMEN GENERAL
# ============================================================
if pagina == "🏠 Resumen General":
    st.title("Resumen General - IX Escuela de Jovenes Ruralistas")
    
    # Indicador de filtros activos
    filtros_activos = []
    if region_filtro != 'Todas': filtros_activos.append(f"Region: {region_filtro}")
    if genero_filtro != 'Todos': filtros_activos.append(f"Genero: {genero_filtro}")
    if emails_seleccionados: filtros_activos.append(f"Becarios: {len(emails_seleccionados)}")
    if filtros_activos:
        st.markdown(f"**Filtros activos:** {' | '.join(filtros_activos)} | **Mostrando:** {len(df_b)} becarios")
    st.markdown("---")

    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Becarios", len(df_b))
    with c2: st.metric("Mentores", len(datos['mentores']))
    with c3: st.metric("Sesiones", 10)
    with c4: st.metric("Encuestas", len(df_enc))
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Representantes", len(datos['representantes']))
    with c2: st.metric("Equipos", 10)
    with c3: st.metric("Registros Asistencia", f"{len(df_asist):,}")
    with c4: st.metric("Participantes Unicos", df_asist['Nombre'].nunique() if len(df_asist) > 0 else 0)

    st.markdown("---")

    c1, c2 = st.columns(2)
    with c1:
        gen = df_b['Genero'].value_counts()
        fig = go.Figure(data=[go.Pie(labels=gen.index, values=gen.values, hole=0.45,
                                     marker_colors=[PALETTE[1], PALETTE[0]],
                                     textinfo='percent+label', textfont_size=13,
                                     pull=[0.03, 0])])
        fig = template(fig, 380)
        fig.update_layout(title='Distribucion por Genero')
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        pais = df_b['Pais'].value_counts().reset_index()
        pais.columns = ['Pais', 'Cantidad']
        fig = px.bar(pais, x='Pais', y='Cantidad', text='Cantidad', color='Cantidad',
                     color_continuous_scale=['#90CAF9', '#1565C0'])
        fig = template(fig, 380)
        fig.update_layout(title='Becarios por Pais', showlegend=False, coloraxis_showscale=False)
        bar_text(fig)
        st.plotly_chart(fig, use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        if len(df_asist) > 0:
            asist = df_asist.groupby('Fecha_str')['Nombre'].nunique().reset_index()
            asist.columns = ['Fecha', 'Participantes']
            fig = px.bar(asist, x='Fecha', y='Participantes', text='Participantes',
                         color_discrete_sequence=[PALETTE[3]])
            fig = template(fig, 380)
            fig.update_layout(title='Participantes por Sesion')
            bar_text(fig)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay datos de asistencia con los filtros seleccionados")

    with c2:
        if len(df_enc) > 0:
            cal = df_enc.groupby('Sesion')['Calif_num'].mean().reset_index()
            cal.columns = ['Sesion', 'Calificacion']
            cal['Label'] = cal['Sesion'].map(lambda x: f"S{x}")
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=cal['Label'], y=cal['Calificacion'], mode='lines+markers+text',
                                      line=dict(color=PALETTE[0], width=3), marker=dict(size=10),
                                      text=[f'{v:.2f}' for v in cal['Calificacion']],
                                      textposition='top center', textfont=dict(size=11, color='#e0e0e0')))
            fig = template(fig, 380)
            fig.update_layout(title='Calificacion Promedio por Sesion', yaxis_range=[3.5, 5.5])
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay datos de encuestas con los filtros seleccionados")

    st.markdown("---")

    # Fila 3: Evolución asistencia + Comparación LB vs LF
    c1, c2 = st.columns(2)
    with c1:
        if len(df_asist) > 0:
            asist_evol = df_asist.groupby('Fecha_str')['Nombre'].nunique().reset_index()
            asist_evol.columns = ['Fecha', 'Participantes']
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=asist_evol['Fecha'], y=asist_evol['Participantes'],
                                      mode='lines+markers+text', line=dict(color=PALETTE[3], width=3),
                                      marker=dict(size=10),
                                      text=asist_evol['Participantes'],
                                      textposition='top center', textfont=dict(size=11, color='#e0e0e0')))
            fig = template(fig, 380)
            fig.update_layout(title='Evolucion de Asistencia por Sesion')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay datos de asistencia")

    with c2:
        lb_cols = [c for c in df_b.columns if c.startswith('Conoc_')]
        lb_m = [df_b[c].mean() for c in lb_cols]
        cn_short = ['Des.Agrario', 'Agroecologia', 'Genero', 'Interculturalidad',
                    'Formalizacion', 'CANVA', 'Comercializ.', 'Form.Proyectos', 'Fondos']

        m = {'Nada': 1, 'Basico': 2, 'Intermedio': 3, 'Avanzado': 4}
        lf_m = []
        for c in range(9, 18):
            v = df_lf.iloc[:, c].map(m).dropna()
            lf_m.append(v.mean() if len(v) > 0 else 0)
        lf_mn = [(v-1) for v in lf_m]

        fig = go.Figure()
        fig.add_trace(go.Bar(name='Linea Base', x=cn_short, y=lb_m,
                              marker_color=PALETTE[0], text=[f'{v:.1f}' for v in lb_m], textposition='outside'))
        fig.add_trace(go.Bar(name='Linea Final', x=cn_short, y=lf_mn,
                              marker_color=PALETTE[1], text=[f'{v:.1f}' for v in lf_mn], textposition='outside'))
        fig = template(fig, 380)
        fig.update_layout(title='Conocimientos: Antes vs Despues', barmode='group', yaxis_range=[0, 3.8])
        fig.update_xaxes(tickangle=-35)
        st.plotly_chart(fig, use_container_width=True)

    # Fila 4: Top temas aprendidos + Top mejoras
    def filtrar(val):
        if pd.isna(val): return False
        return str(val).strip() not in ['Sin respuesta', 'Sin respuesta / Satisfecho']

    c1, c2 = st.columns(2)
    with c1:
        if len(df_enc) > 0:
            df_ideas = df_enc[df_enc['Cat_Ideas'].apply(filtrar)]
            if len(df_ideas) > 0:
                top_ideas = df_ideas['Cat_Ideas'].value_counts().head(5).reset_index()
                top_ideas.columns = ['Tema', 'Cantidad']
                fig = px.bar(top_ideas, x='Cantidad', y='Tema', orientation='h', text='Cantidad',
                             color_discrete_sequence=[PALETTE[0]])
                fig = template(fig, 320)
                fig.update_layout(title='Top 5 Temas Mas Aprendidos', margin=dict(t=50))
                bar_text(fig)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No hay datos de ideas")
        else:
            st.info("No hay datos de encuestas")

    with c2:
        if len(df_enc) > 0:
            df_mej = df_enc[df_enc['Cat_Mejora'].apply(filtrar)]
            if len(df_mej) > 0:
                top_mej = df_mej['Cat_Mejora'].value_counts().head(5).reset_index()
                top_mej.columns = ['Sugerencia', 'Cantidad']
                fig = px.bar(top_mej, x='Cantidad', y='Sugerencia', orientation='h', text='Cantidad',
                             color_discrete_sequence=[PALETTE[2]])
                fig = template(fig, 320)
                fig.update_layout(title='Top 5 Sugerencias de Mejora', margin=dict(t=50))
                bar_text(fig)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No hay datos de mejoras")
        else:
            st.info("No hay datos de encuestas")

# ============================================================
# BECARIOS
# ============================================================
elif pagina == "👥 Becarios":
    st.title("Analisis de Becarios")
    filtros_b = [f"**Region:** {region_filtro}", f"**Genero:** {genero_filtro}"]
    if emails_seleccionados:
        filtros_b.append(f"**Becarios seleccionados:** {len(emails_seleccionados)}")
    st.markdown(f"{' | '.join(filtros_b)} | **Mostrando:** {len(df_b)}")
    st.markdown("---")

    tab1, tab2, tab3, tab4 = st.tabs(["Demografia", "Conocimientos", "Emprendimiento", "Preguntas Abiertas"])

    with tab1:
        c1, c2, c3 = st.columns(3)
        with c1: st.metric("Total", len(df_b))
        with c2: st.metric("Edad Promedio", f"{df_b['Edad'].mean():.1f}")
        with c3: st.metric("Con Vinculo Rural", f"{(df_b['Vinculo_Rural']=='Si').sum()}")

        c1, c2 = st.columns(2)
        with c1:
            gen = df_b['Genero'].value_counts()
            fig = go.Figure(data=[go.Pie(labels=gen.index, values=gen.values, hole=0.45,
                                         marker_colors=[PALETTE[1], PALETTE[0]],
                                         textinfo='percent+label+value', textfont_size=12, pull=[0.03, 0])])
            fig = template(fig, 380)
            fig.update_layout(title='Distribucion por Genero')
            st.plotly_chart(fig, use_container_width=True)

        with c2:
            fig = px.histogram(df_b, x='Edad', nbins=12, text_auto=True, color_discrete_sequence=[PALETTE[0]])
            fig.add_vline(x=df_b['Edad'].mean(), line_dash="dash", line_color="red",
                         annotation_text=f"Promedio: {df_b['Edad'].mean():.1f}", annotation_position="top right")
            fig = template(fig, 380)
            fig.update_layout(title='Distribucion por Edad', bargap=0.05)
            st.plotly_chart(fig, use_container_width=True)

        c1, c2 = st.columns(2)
        with c1:
            edu = df_b['Nivel educativo'].value_counts().reset_index()
            edu.columns = ['Nivel', 'Cantidad']
            fig = px.bar(edu, x='Nivel', y='Cantidad', text='Cantidad', color_discrete_sequence=[PALETTE[3]])
            fig = template(fig, 350)
            fig.update_layout(title='Nivel Educativo')
            bar_text(fig)
            st.plotly_chart(fig, use_container_width=True)

        with c2:
            leng = df_b['Lengua materna'].value_counts().reset_index()
            leng.columns = ['Lengua', 'Cantidad']
            fig = px.bar(leng, x='Lengua', y='Cantidad', text='Cantidad', color_discrete_sequence=[PALETTE[4]])
            fig = template(fig, 350)
            fig.update_layout(title='Lengua Materna')
            bar_text(fig)
            st.plotly_chart(fig, use_container_width=True)

        c1, c2 = st.columns(2)
        with c1:
            vr = df_b['Vinculo_Rural'].value_counts()
            fig = go.Figure(data=[go.Pie(labels=vr.index, values=vr.values, hole=0.45,
                                         marker_colors=[PALETTE[3], PALETTE[1]],
                                         textinfo='percent+label', textfont_size=12)])
            fig = template(fig, 350)
            fig.update_layout(title='Vinculo con el Ambito Rural')
            st.plotly_chart(fig, use_container_width=True)

        with c2:
            ti = df_b['Tiempo_Vinculo_Rural'].value_counts().reset_index()
            ti.columns = ['Tiempo', 'Cantidad']
            fig = px.bar(ti, x='Tiempo', y='Cantidad', text='Cantidad', color_discrete_sequence=[PALETTE[5]])
            fig = template(fig, 350)
            fig.update_layout(title='Tiempo de Vinculo Rural')
            bar_text(fig)
            st.plotly_chart(fig, use_container_width=True)

    with tab2:
        cc = [c for c in df_b.columns if c.startswith('Conoc_')]
        cn = [c.replace('Conoc_', '') for c in cc]
        cm = [df_b[c].mean() for c in cc]

        fig = go.Figure(data=[go.Bar(x=cn, y=cm, marker_color=PALETTE[:len(cn)],
                                      text=[f'{v:.2f}' for v in cm], textposition='outside',
                                      hovertemplate='%{x}<br>Promedio: %{y:.2f}/3<extra></extra>')])
        fig = template(fig, 450)
        fig.update_layout(title='Nivel de Conocimiento Promedio (0=Nada, 3=Avanzado)', yaxis_range=[0, 3.5])
        fig.add_hline(y=2, line_dash="dash", line_color="#aaa", annotation_text="Nivel Intermedio")
        fig.update_xaxes(tickangle=-25)
        st.plotly_chart(fig, use_container_width=True)

        if len(df_b['Region'].unique()) > 1:
            top_r = df_b['Region'].value_counts().head(6).index
            df_top = df_b[df_b['Region'].isin(top_r)]
            hm = df_top.groupby('Region')[cc].mean()
            hm.columns = cn
            fig = px.imshow(hm, text_auto='.1f', color_continuous_scale='RdYlGn', aspect='auto')
            fig = template(fig, 400)
            fig.update_layout(title='Conocimientos por Region (Top 6)')
            st.plotly_chart(fig, use_container_width=True)

    with tab3:
        emp_cols = ['Ha_Emprendido_Rural', 'Tiene_Emprendimiento', 'Ha_Hecho_Canvas',
                    'Ha_Capacitacion', 'Ha_Accedido_Fondos', 'Ha_Liderado']
        emp_names = ['Ha emprendido', 'Tiene emprendimiento', 'Ha hecho CANVAS',
                     'Ha recibido capacitacion', 'Ha accedido fondos', 'Ha liderado']

        fig = make_subplots(rows=2, cols=3, specs=[[{'type': 'pie'}]*3]*2, subplot_titles=emp_names,
                           horizontal_spacing=0.08, vertical_spacing=0.15)
        for i, (col, name) in enumerate(zip(emp_cols, emp_names)):
            r, c = i//3+1, i%3+1
            counts = df_b[col].value_counts()
            fig.add_trace(go.Pie(labels=counts.index, values=counts.values, hole=0.4,
                                 marker_colors=[PALETTE[3], PALETTE[1]],
                                 textinfo='percent', textfont_size=10), row=r, col=c)
        fig = template(fig, 500)
        fig.update_layout(title='Experiencia y Emprendimiento', showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

        for col, nombre in [('Comodidad_Publico', 'Comodidad hablando en publico'),
                             ('Capacidad_Liderazgo', 'Capacidad de liderazgo'),
                             ('Comodidad_Equipo', 'Comodidad trabajando en equipo')]:
            counts = df_b[col].value_counts().reset_index()
            counts.columns = ['Respuesta', 'Cantidad']
            fig = px.bar(counts, x='Cantidad', y='Respuesta', orientation='h', text='Cantidad',
                         color_discrete_sequence=[PALETTE[0]])
            fig = template(fig, 250)
            fig.update_layout(title=nombre, margin=dict(t=40, b=10))
            bar_text(fig)
            st.plotly_chart(fig, use_container_width=True)

    with tab4:
        for col, nombre, color in [('Cat_QueEsperaAprender', 'Que Espera Aprender', PALETTE[0]),
                                     ('Cat_TemasInteres', 'Temas de Interes', PALETTE[1]),
                                     ('Cat_QueEsperaLograr', 'Que Espera Lograr', PALETTE[2])]:
            cats = df_b[col].value_counts().reset_index()
            cats.columns = ['Categoria', 'Cantidad']
            cats['%'] = (cats['Cantidad']/len(df_b)*100).round(1)
            fig = px.bar(cats, x='Cantidad', y='Categoria', orientation='h', text='Cantidad',
                         color_discrete_sequence=[color])
            fig = template(fig, max(280, len(cats)*38))
            fig.update_layout(title=f'{nombre} ({len(df_b)} respuestas)', margin=dict(t=50))
            bar_text(fig)
            st.plotly_chart(fig, use_container_width=True)
    
    # Perfil individual (solo si se selecciono 1 becario)
    if emails_seleccionados and len(emails_seleccionados) == 1:
        st.markdown("---")
        st.subheader("Perfil Individual del Becario")
        bec = df_b.iloc[0]
        
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.metric("Nombre", bec['Nombre'])
        with c2: st.metric("Edad", bec['Edad'])
        with c3: st.metric("Region", bec['Region'])
        with c4: st.metric("Genero", bec['Genero'])
        
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.metric("Pais", bec['Pais'])
        with c2: st.metric("Nivel Educativo", bec['Nivel educativo'])
        with c3: st.metric("Lengua Materna", bec['Lengua materna'])
        with c4: st.metric("Vinculo Rural", bec['Vinculo_Rural'])
        
        st.markdown("**Conocimientos Autopercibidos:**")
        for col in [c for c in df_b.columns if c.startswith('Conoc_')]:
            nombre_c = col.replace('Conoc_', '')
            valor = bec[col]
            barra = '█' * int(valor) + '░' * (3 - int(valor))
            st.markdown(f"- {nombre_c}: **{valor}/3** {barra}")

# ============================================================
# ENCUESTAS
# ============================================================
elif pagina == "📋 Encuestas":
    st.title("Encuestas de Satisfaccion por Sesion")
    st.markdown("Resultados de las encuestas (sin sesion 1 - bienvenida)")
    st.markdown("---")

    ses_f = st.multiselect("Sesiones", sorted(df_enc['Sesion'].unique()),
                            default=sorted(df_enc['Sesion'].unique()),
                            format_func=lambda x: f"S{x}: {sesion_nombres.get(x, '')}")
    df_enc = df_enc[df_enc['Sesion'].isin(ses_f)]

    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Encuestas", len(df_enc))
    with c2:
        cal = df_enc['Calif_num'].mean()
        st.metric("Calificacion Promedio", f"{cal:.2f}/5" if pd.notna(cal) else "N/A")
    with c3: st.metric("Sesiones", len(ses_f))
    with c4: st.metric("Respuestas Abiertas", int(df_enc['Cat_Ideas'].apply(filtrar).sum()))

    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["Calificacion", "Categorias Abiertas", "Detalle por Sesion"])

    with tab1:
        cal_s = df_enc.groupby('Sesion')['Calif_num'].mean().reset_index()
        cal_s.columns = ['Sesion', 'Cal']
        cal_s['Label'] = cal_s['Sesion'].map(lambda x: f"S{x}: {sesion_nombres.get(x, '')[:15]}")
        fig = px.bar(cal_s, x='Label', y='Cal', text='Cal', color='Cal',
                     color_continuous_scale='RdYlGn', range_color=[3.5, 5])
        fig = template(fig, 420)
        fig.update_layout(title='Calificacion Promedio por Sesion', yaxis_range=[3, 5.5],
                         coloraxis_showscale=False)
        fig.update_traces(texttemplate='%{text:.2f}', textposition='outside', textfont_size=12)
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        for col, nombre, color in [('Cat_Ideas', 'Ideas Aprendidas', PALETTE[0]),
                                     ('Cat_Gusto', 'Lo que Mas Gusto', PALETTE[1]),
                                     ('Cat_Mejora', 'Aspectos a Mejorar', PALETTE[2]),
                                     ('Cat_Profundizar', 'Temas a Profundizar', PALETTE[3])]:
            df_v = df_enc[df_enc[col].apply(filtrar)]
            cats = df_v[col].value_counts().reset_index()
            cats.columns = ['Categoria', 'Cantidad']
            cats['%'] = (cats['Cantidad']/len(df_v)*100).round(1)
            fig = px.bar(cats, x='Cantidad', y='Categoria', orientation='h', text='Cantidad',
                         color_discrete_sequence=[color])
            fig = template(fig, max(280, len(cats)*38))
            fig.update_layout(title=f'{nombre} ({len(df_v)} respuestas validas)', margin=dict(t=50))
            bar_text(fig)
            st.plotly_chart(fig, use_container_width=True)

    with tab3:
        for ses in ses_f:
            with st.expander(f"S{ses}: {sesion_nombres.get(ses, '')}", expanded=False):
                sub = df_enc[df_enc['Sesion'] == ses]
                c1, c2, c3 = st.columns(3)
                with c1: st.metric("Encuestas", len(sub))
                with c2:
                    c = sub['Calif_num'].mean()
                    st.metric("Calificacion", f"{c:.2f}/5" if pd.notna(c) else "N/A")
                with c3: st.metric("Respuestas Abiertas", int(sub['Cat_Ideas'].apply(filtrar).sum()))

                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("**Ideas aprendidas:**")
                    for cat, val in sub[sub['Cat_Ideas'].apply(filtrar)]['Cat_Ideas'].value_counts().items():
                        st.markdown(f"- {cat}: **{val}**")
                with c2:
                    st.markdown("**Lo que mas gusto:**")
                    for cat, val in sub[sub['Cat_Gusto'].apply(filtrar)]['Cat_Gusto'].value_counts().items():
                        st.markdown(f"- {cat}: **{val}**")

# ============================================================
# ASISTENCIA
# ============================================================
elif pagina == "📅 Asistencia":
    st.title("Analisis de Asistencia")
    st.markdown("---")

    df_a = df_asist.copy()

    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Total Registros", f"{len(df_a):,}")
    with c2: st.metric("Participantes Unicos", df_a['Nombre'].nunique())
    with c3: st.metric("Sesiones", df_a['Fecha_str'].nunique())
    with c4: st.metric("Promedio/Sesion", f"{len(df_a)//df_a['Fecha_str'].nunique():,}")

    st.markdown("---")

    tab1, tab2 = st.tabs(["Por Sesion", "Por Participante"])

    with tab1:
        af = df_a.groupby('Fecha_str')['Nombre'].nunique().reset_index()
        af.columns = ['Fecha', 'Participantes']
        fig = px.bar(af, x='Fecha', y='Participantes', text='Participantes',
                     color_discrete_sequence=[PALETTE[3]])
        fig = template(fig, 420)
        fig.update_layout(title='Participantes Unicos por Sesion')
        bar_text(fig)
        st.plotly_chart(fig, use_container_width=True)

        at = df_a.groupby('Fecha_str').size().reset_index()
        at.columns = ['Fecha', 'Registros']
        fig = px.bar(at, x='Fecha', y='Registros', text='Registros',
                     color_discrete_sequence=[PALETTE[0]])
        fig = template(fig, 420)
        fig.update_layout(title='Total Registros por Sesion')
        bar_text(fig)
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        n = st.slider("Mostrar Top", 10, 50, 20)
        top = df_a['Nombre'].value_counts().head(n).reset_index()
        top.columns = ['Nombre', 'Registros']
        fig = px.bar(top, x='Registros', y='Nombre', orientation='h', text='Registros',
                     color_discrete_sequence=[PALETTE[4]])
        fig = template(fig, max(400, n*25))
        fig.update_layout(title=f'Top {n} Participantes con Mas Asistencia')
        bar_text(fig)
        st.plotly_chart(fig, use_container_width=True)

# ============================================================
# EVALUACIONES
# ============================================================
elif pagina == "📝 Evaluaciones":
    st.title("Evaluaciones")
    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["Examen Inicial", "Entregables", "Planes de Emprendimiento"])

    with tab1:
        de = df_exam.copy()
        de['Puntaje'] = pd.to_numeric(de['Puntuacion'], errors='coerce')
        aprob = (de['Puntaje'] >= 18).sum()

        c1, c2, c3, c4 = st.columns(4)
        with c1: st.metric("Examenes", len(de))
        with c2: st.metric("Promedio", f"{de['Puntaje'].mean():.1f}/20")
        with c3: st.metric("Aprobados", f"{aprob}/{len(de)}")
        with c4: st.metric("% Aprobados", f"{aprob/len(de)*100:.0f}%")

        c1, c2 = st.columns(2)
        with c1:
            fig = px.histogram(de, x='Puntaje', nbins=10, text_auto=True, color_discrete_sequence=[PALETTE[0]])
            fig.add_vline(x=18, line_dash="dash", line_color="#4CAF50",
                         annotation_text="Aprobado: 18", annotation_position="top right")
            fig = template(fig, 380)
            fig.update_layout(title='Distribucion de Puntajes', bargap=0.05)
            st.plotly_chart(fig, use_container_width=True)

        with c2:
            ds = de.dropna(subset=['Puntaje']).sort_values('Puntaje', ascending=True)
            fig = px.bar(ds, x='Puntaje', y='Nombre', orientation='h', text='Puntaje',
                         color_discrete_sequence=[PALETTE[0]])
            fig.add_vline(x=18, line_dash="dash", line_color="#4CAF50")
            fig = template(fig, 380)
            fig.update_layout(title='Puntajes por Participante')
            bar_text(fig)
            st.plotly_chart(fig, use_container_width=True)

    with tab2:
        ent = df_ent.copy()
        ent_cols = ['Entregable_1', 'Entregable_2', 'Entregable_3', 'Entregable_4', 'Entregable_5']
        ec = [ent[c].notna().sum() for c in ent_cols]
        fig = go.Figure(data=[go.Bar(x=ent_cols, y=ec, marker_color=PALETTE[:5],
                                      text=ec, textposition='outside')])
        fig = template(fig, 380)
        fig.update_layout(title='Notas por Entregable')
        st.plotly_chart(fig, use_container_width=True)

        ent['Prom'] = pd.to_numeric(ent['Promedio'], errors='coerce')
        pv = ent['Prom'].dropna()
        if len(pv) > 0:
            c1, c2 = st.columns(2)
            with c1: st.metric("Con Promedio", len(pv))
            with c2: st.metric("Promedio General", f"{pv.mean():.1f}")
            fig = px.histogram(ent, x='Prom', nbins=10, text_auto=True, color_discrete_sequence=[PALETTE[1]])
            fig = template(fig, 380)
            fig.update_layout(title='Distribucion de Promedios', bargap=0.05)
            st.plotly_chart(fig, use_container_width=True)

    with tab3:
        dp = datos['planes'].copy()
        dp['P'] = pd.to_numeric(dp['Puntaje'], errors='coerce')

        c1, c2, c3 = st.columns(3)
        with c1: st.metric("Evaluaciones", len(dp))
        with c2: st.metric("Promedio", f"{dp['P'].mean():.1f}/50")
        with c3: st.metric("Jurados", dp['Jurado'].nunique())

        c1, c2 = st.columns(2)
        with c1:
            g = dp.groupby('Grupo')['P'].mean().reset_index()
            fig = px.bar(g, x='Grupo', y='P', text='P', color='P', color_continuous_scale='RdYlGn')
            fig = template(fig, 380)
            fig.update_layout(title='Puntaje por Grupo', coloraxis_showscale=False, yaxis_range=[0, 55])
            fig.update_traces(texttemplate='%{text:.1f}', textposition='outside')
            st.plotly_chart(fig, use_container_width=True)

        with c2:
            j = dp.groupby('Jurado')['P'].mean().reset_index()
            fig = px.bar(j, x='Jurado', y='P', text='P', color_discrete_sequence=[PALETTE[4]])
            fig = template(fig, 380)
            fig.update_layout(title='Puntaje por Jurado', yaxis_range=[0, 55])
            fig.update_traces(texttemplate='%{text:.1f}', textposition='outside')
            st.plotly_chart(fig, use_container_width=True)

        fig = px.density_heatmap(dp, x='Grupo', y='Jurado', z='P', text_auto='.0f',
                                 color_continuous_scale='RdYlGn')
        fig = template(fig, 350)
        fig.update_layout(title='Calor: Puntajes por Grupo y Jurado')
        st.plotly_chart(fig, use_container_width=True)

# ============================================================
# LINEA BASE VS FINAL
# ============================================================
elif pagina == "📈 Linea Base vs Final":
    st.title("Comparacion: Linea Base vs Linea Final")
    st.markdown("Evolucion de conocimientos autopercibidos antes y despues del programa")
    st.markdown("---")

    df_lb = df_b.copy()
    df_lf_f = df_lf.copy()

    c1, c2, c3 = st.columns(3)
    with c1: st.metric("Linea Base", f"{len(df_lb)} becarios")
    with c2: st.metric("Linea Final", f"{len(df_lf_f)} respuestas")
    with c3: st.metric("Tasa Respuesta", f"{len(df_lf_f)/len(df_lb)*100:.0f}%")

    st.markdown("---")

    cn = ['Des. Agrario', 'Agroecologia', 'Enf. Genero', 'Interculturalidad',
          'Formalizacion', 'CANVA', 'Comercializacion', 'Form. Proyectos', 'Fondos']

    lb_cols = [c for c in df_lb.columns if c.startswith('Conoc_')]
    lb_m = [df_lb[c].mean() for c in lb_cols]

    m = {'Nada': 1, 'Basico': 2, 'Intermedio': 3, 'Avanzado': 4}
    lf_m = []
    for c in range(9, 18):
        v = df_lf.iloc[:, c].map(m).dropna()
        lf_m.append(v.mean() if len(v) > 0 else 0)
    lf_mn = [(v-1) for v in lf_m]

    fig = go.Figure()
    fig.add_trace(go.Bar(name='Linea Base (0-3)', x=cn, y=lb_m, marker_color=PALETTE[0],
                          text=[f'{v:.2f}' for v in lb_m], textposition='outside'))
    fig.add_trace(go.Bar(name='Linea Final (0-3)', x=cn, y=lf_mn, marker_color=PALETTE[1],
                          text=[f'{v:.2f}' for v in lf_mn], textposition='outside'))
    fig = template(fig, 480)
    fig.update_layout(title='Conocimientos: Antes vs Despues', barmode='group', yaxis_range=[0, 3.8])
    fig.add_hline(y=2, line_dash="dash", line_color="#aaa", annotation_text="Nivel Intermedio")
    fig.update_xaxes(tickangle=-25)
    st.plotly_chart(fig, use_container_width=True)

    diff = [lf - lb for lf, lb in zip(lf_mn, lb_m)]
    diff_c = [PALETTE[3] if d > 0 else PALETTE[1] for d in diff]
    fig = go.Figure(data=[go.Bar(x=cn, y=diff, marker_color=diff_c,
                                  text=[f'{d:+.2f}' for d in diff], textposition='outside')])
    fig = template(fig, 380)
    fig.update_layout(title='Cambio: Linea Final - Linea Base')
    fig.add_hline(y=0, line_dash="solid", line_color="#aaa")
    fig.update_xaxes(tickangle=-25)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("Mapas de Calor Individuales")

    # Preparar datos para heatmaps individuales
    lb_conoc_cols = [c for c in df_lb.columns if c.startswith('Conoc_')]
    cn_short = ['Des.Agrario', 'Agroecol.', 'Genero', 'Intercult.', 'Formaliz.',
                'CANVA', 'Comercial.', 'Form.Proy.', 'Fondos']

    # Linea Base: matriz becario x conocimiento (0-3)
    lb_matrix = df_lb[['Nombre'] + lb_conoc_cols].copy()
    lb_matrix.columns = ['Nombre'] + cn_short
    lb_matrix = lb_matrix.set_index('Nombre')

    # Linea Final: matriz becario x conocimiento (0-3 normalizado)
    lf_matrix_data = df_lf_f.iloc[:, 2].values  # nombres
    lf_conoc = df_lf_f.iloc[:, 9:18].replace(m)  # cols 9-17, mapear a 1-4
    lf_conoc = lf_conoc - 1  # normalizar a 0-3
    lf_matrix = pd.DataFrame(lf_conoc.values, index=lf_matrix_data, columns=cn_short)

    # Heatmap Linea Base
    fig = px.imshow(lb_matrix, text_auto='.0f', color_continuous_scale='RdYlGn',
                    zmin=0, zmax=3, aspect='auto',
                    labels=dict(x="Conocimiento", y="Becario", color="Nivel"))
    fig = template(fig, max(400, len(lb_matrix)*25))
    fig.update_layout(title='Linea Base: Nivel de Conocimiento por Becario (0-3)',
                     coloraxis_colorbar_title="Nivel")
    st.plotly_chart(fig, use_container_width=True)

    # Heatmap Linea Final
    fig = px.imshow(lf_matrix, text_auto='.0f', color_continuous_scale='RdYlGn',
                    zmin=0, zmax=3, aspect='auto',
                    labels=dict(x="Conocimiento", y="Becario", color="Nivel"))
    fig = template(fig, max(400, len(lf_matrix)*25))
    fig.update_layout(title='Linea Final: Nivel de Conocimiento por Becario (0-3)',
                     coloraxis_colorbar_title="Nivel")
    st.plotly_chart(fig, use_container_width=True)

    # Heatmap de Diferencia (solo becarios que aparecen en ambas)
    common_names = set(lb_matrix.index) & set(lf_matrix.index)
    if len(common_names) > 0:
        lb_common = lb_matrix.loc[sorted(common_names)]
        lf_common = lf_matrix.loc[sorted(common_names)]
        diff_matrix = lf_common - lb_common

        fig = px.imshow(diff_matrix, text_auto='+.0f', color_continuous_scale='RdBu',
                        zmin=-3, zmax=3, aspect='auto',
                        labels=dict(x="Conocimiento", y="Becario", color="Cambio"))
        fig = template(fig, max(400, len(diff_matrix)*25))
        fig.update_layout(title='Cambio Individual: Linea Final - Linea Base (verde=mejoro, rojo=bajo)',
                         coloraxis_colorbar_title="Cambio")
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Comparativa: Que esperaba aprender vs Que aprendio")

    # Normalizar categorías para comparar
    map_lb = {
        'Agroecología': 'Agroecologia',
        'Agroecolog�a': 'Agroecologia',
        'Emprendimiento rural': 'Emprendimiento',
        'Herramientas prácticas': 'Herramientas',
        'Herramientas pr�cticas': 'Herramientas',
        'General / Otros': 'Otros',
        'Investigación': 'Investigacion',
        'Investigaci�n': 'Investigacion',
        'Formulación de proyectos': 'Formulacion',
        'Formulaci�n de proyectos': 'Formulacion',
        'Liderazgo juvenil': 'Liderazgo',
    }
    map_lf = {
        'Agroecologia y Suelos': 'Agroecologia',
        'Emprendimiento Rural': 'Emprendimiento',
        'Conocimientos y Herramientas': 'Herramientas',
        'Realidad Rural y Politicas': 'Realidad Rural',
        'Formulacion de Proyectos': 'Formulacion',
        'Interculturalidad': 'Interculturalidad',
        'Liderazgo y Habilidades': 'Liderazgo',
        'Modelo CANVAS': 'CANVAS',
    }

    esperaba = df_lb['Cat_QueEsperaAprender'].map(map_lb).value_counts().reset_index()
    esperaba.columns = ['Categoria', 'Esperaba']

    aprendio = df_lf['Cat_Aprendido'].map(map_lf).value_counts().reset_index()
    aprendio.columns = ['Categoria', 'Aprendio']

    comp = pd.merge(esperaba, aprendio, on='Categoria', how='outer').fillna(0)
    comp['Esperaba'] = comp['Esperaba'].astype(int)
    comp['Aprendio'] = comp['Aprendio'].astype(int)
    comp = comp.sort_values('Esperaba', ascending=True)

    fig = go.Figure()
    fig.add_trace(go.Bar(name='Esperaba Aprender (Linea Base)', y=comp['Categoria'],
                          x=comp['Esperaba'], orientation='h',
                          marker_color=PALETTE[0], text=comp['Esperaba'], textposition='outside'))
    fig.add_trace(go.Bar(name='Aprendio (Linea Final)', y=comp['Categoria'],
                          x=comp['Aprendio'], orientation='h',
                          marker_color=PALETTE[1], text=comp['Aprendio'], textposition='outside'))
    fig = template(fig, max(350, len(comp)*45))
    fig.update_layout(title='Expectativas vs Resultados', barmode='group')
    st.plotly_chart(fig, use_container_width=True)

    # Diferencia
    comp['Diff'] = comp['Aprendio'] - comp['Esperaba']
    diff_colors = [PALETTE[3] if d > 0 else PALETTE[6] if d < 0 else '#888' for d in comp['Diff']]
    fig = go.Figure(data=[go.Bar(y=comp['Categoria'], x=comp['Diff'], orientation='h',
                                  marker_color=diff_colors,
                                  text=[f'{d:+d}' for d in comp['Diff']], textposition='outside')])
    fig = template(fig, max(300, len(comp)*40))
    fig.update_layout(title='Diferencia: Aprendio - Esperaba (verde=supero expectativas, rojo=por debajo)')
    fig.add_vline(x=0, line_dash="solid", line_color="#aaa")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Categorias - Linea Final")
    for col, nombre, color in [('Cat_Aprendido', 'Que Aprendieron', PALETTE[0]),
                                 ('Cat_TemasFinal', 'Temas de Interes', PALETTE[1]),
                                 ('Cat_Logrado', 'Que Lograron', PALETTE[2])]:
        cats = df_lf[col].value_counts().reset_index()
        cats.columns = ['Categoria', 'Cantidad']
        fig = px.bar(cats, x='Cantidad', y='Categoria', orientation='h', text='Cantidad',
                     color_discrete_sequence=[color])
        fig = template(fig, max(280, len(cats)*38))
        fig.update_layout(title=nombre, margin=dict(t=50))
        bar_text(fig)
        st.plotly_chart(fig, use_container_width=True)
