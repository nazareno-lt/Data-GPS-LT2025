import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. Configuración de página e idioma
st.set_page_config(page_title="Rugby Performance Dashboard", layout="wide")

st.markdown(
    """
    <html lang="es">
    <style>
        input[role="combobox"] { caret-color: transparent !important; }
    </style>
    <script> document.documentElement.lang = 'es'; </script>
    """,
    unsafe_allow_html=True
)

# --- CONFIGURACIÓN ---
VERDE_OSCURO = '#1b4d3e'
AMARILLO_OSCURO = '#b8860b'
NOMBRE_IMAGEN = "foto_rugby.jpg"

@st.cache_data
def load_data():
    df = pd.read_csv('DATOS_PARTIDOS.csv.csv')
    df.columns = df.columns.str.strip()
    
    # --- FILTRO CRÍTICO ---
    # Solo nos quedamos con las filas de la sesión completa para evitar duplicados
    df = df[df['Period Name'] == 'Session'].copy()
    
    def time_to_min(time_str):
        try:
            h, m, s = map(int, str(time_str).split(':'))
            return h * 60 + m + s / 60
        except: return 0
    df['Duration_Min'] = df['Total Duration'].apply(time_to_min)
    return df

df = load_data()

def limpiar_nombre_partido(nombre):
    nuevo = nombre.replace("PARTIDO", "").replace("PRIMERA", "").strip()
    return nuevo if nuevo.lower().startswith("vs") else f"vs {nuevo}"

if 'count' not in st.session_state: st.session_state.count = 0
def volver_inicio(): st.session_state.count += 1

# --- SIDEBAR ---
st.sidebar.header("Menú de Selección")
st.sidebar.button("🏠 Volver al Inicio", on_click=volver_inicio, use_container_width=True)

lista_jugadores = sorted(df['Player Name'].unique().tolist())
jugador_sel = st.sidebar.selectbox("Jugador:", ["- Seleccionar Jugador -"] + lista_jugadores, key=f"j_{st.session_state.count}")

# --- CABECERA ---
col_img1, col_img2, col_img3 = st.columns([1, 2, 1])
with col_img2:
    try: st.image(NOMBRE_IMAGEN)
    except: st.warning("Imagen no encontrada.")

if jugador_sel == "- Seleccionar Jugador -":
    st.info("🏉 **Bienvenido.** Selecciona un jugador para comenzar.")
else:
    st.title(f"Estadísticas: {jugador_sel}")
    partidos_raw = sorted(df[df['Player Name'] == jugador_sel]['Activity Name'].unique().tolist())
    mapa_partidos = {limpiar_nombre_partido(p): p for p in partidos_raw}
    partido_sel = st.sidebar.selectbox("Partido:", ["- Seleccionar Partido -"] + list(mapa_partidos.keys()), key=f"p_{st.session_state.count}")

    metricas_dict = {
        'Total Distance': 'Distancia Total (m)',
        'HSR': 'HSR (m)',
        'Acceleration B1-3 Total Efforts (Gen 2)': 'Aceleraciones',
        'Maximum Velocity': 'Velocidad Máxima',
        'Tackles Total (Band1-Band3)': 'Tackles Totales',
        'Duration_Min': 'Duración (min)'
    }

    tab1, tab2, tab3 = st.tabs(["📊 Rendimiento por Partido", "📈 Comparativa vs Equipo", "📋 Evolución Histórica"])

    with tab1:
        if partido_sel == "- Seleccionar Partido -":
            st.warning("👈 Selecciona un partido en el menú lateral.")
        else:
            data_match = df[(df['Player Name'] == jugador_sel) & (df['Activity Name'] == mapa_partidos[partido_sel])]
            
            if not data_match.empty:
                m_cols = st.columns(len(metricas_dict))
                for i, (col_id, label) in enumerate(metricas_dict.items()):
                    m_cols[i].metric(label, f"{data_match[col_id].iloc[0]:.1f}")
                
                st.markdown("---")
                for col_id, label in metricas_dict.items():
                    fig = go.Figure(go.Bar(x=[label], y=[data_match[col_id].iloc[0]], marker_color=VERDE_OSCURO, width=0.4))
                    fig.update_layout(title=f"{label} en {partido_sel}", height=250, margin=dict(l=20, r=20, t=40, b=20))
                    st.plotly_chart(fig, use_container_width=True)

    with tab2:
        met_comp = st.selectbox("Métrica:", list(metricas_dict.keys()), format_func=lambda x: metricas_dict[x], key=f"c_{st.session_state.count}")
        
        # Datos del jugador (Ya filtrados por Session en load_data)
        hist_j = df[df['Player Name'] == jugador_sel].copy()
        hist_j['Activity Name'] = hist_j['Activity Name'].apply(limpiar_nombre_partido)
        
        # Promedio del equipo (Solo de las filas Session)
        prom_e = df.groupby('Activity Name')[met_comp].mean().reset_index()
        prom_e['Activity Name'] = prom_e['Activity Name'].apply(limpiar_nombre_partido)

        fig_c = go.Figure()
        fig_c.add_trace(go.Bar(x=hist_j['Activity Name'], y=hist_j[met_comp], name="Jugador", marker_color=VERDE_OSCURO))
        fig_c.add_trace(go.Bar(x=prom_e['Activity Name'], y=prom_e[met_comp], name="Promedio Equipo", marker_color=AMARILLO_OSCURO))
        fig_c.update_layout(barmode='group', title=f"Comparativa: {metricas_dict[met_comp]} (Solo Session)")
        st.plotly_chart(fig_c, use_container_width=True)

    with tab3:
        hist_full = df[df['Player Name'] == jugador_sel].copy()
        hist_full['Activity Name'] = hist_full['Activity Name'].apply(limpiar_nombre_partido)
        for col_id, label in metricas_dict.items():
            fig_e = go.Figure(go.Bar(x=hist_full['Activity Name'], y=hist_full[col_id], marker_color=VERDE_OSCURO))
            fig_e.update_layout(title=f"Evolución: {label}", height=300)
            st.plotly_chart(fig_e, use_container_width=True)