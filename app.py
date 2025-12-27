import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Configuración de la página
st.set_page_config(page_title="Rugby Performance Dashboard", layout="wide")

# --- COLORES ---
VERDE_OSCURO = '#1b4d3e'
AMARILLO_OSCURO = '#b8860b'
NOMBRE_IMAGEN = "crlt.png"

@st.cache_data
def load_data():
    df = pd.read_csv('DATOS_PARTIDOS.csv.csv')
    df.columns = df.columns.str.strip()
    
    def time_to_min(time_str):
        try:
            h, m, s = map(int, str(time_str).split(':'))
            return h * 60 + m + s / 60
        except: return 0

    df['Duration_Min'] = df['Total Duration'].apply(time_to_min)
    return df

df = load_data()

# --- FUNCIÓN PARA LIMPIAR NOMBRES DE PARTIDOS ---
def limpiar_nombre_partido(nombre):
    nuevo_nombre = nombre.replace("PARTIDO", "").replace("PRIMERA", "").strip()
    if nuevo_nombre.lower().startswith("vs"):
        return nuevo_nombre
    else:
        return f"vs {nuevo_nombre}"

# --- LÓGICA DE RESETEO ---
if 'count' not in st.session_state:
    st.session_state.count = 0

def volver_inicio():
    st.session_state.count += 1

# --- SIDEBAR ---
st.sidebar.header("Menú de Selección")
st.sidebar.button("🏠 Volver al Inicio", on_click=volver_inicio, use_container_width=True)

lista_jugadores = sorted(df['Player Name'].unique().tolist())
opciones_jugador = ["- Seleccionar Jugador -"] + lista_jugadores

jugador_sel = st.sidebar.selectbox(
    "Jugador:", 
    opciones_jugador, 
    key=f"jugador_{st.session_state.count}"
)

# --- CABECERA: IMAGEN CENTRADA ---
col_img1, col_img2, col_img3 = st.columns([1, 2, 1])
with col_img2:
    try:
        st.image(NOMBRE_IMAGEN) 
    except:
        st.warning(f"Imagen '{NOMBRE_IMAGEN}' no encontrada.")

# --- CUERPO DE LA APP ---
if jugador_sel == "- Seleccionar Jugador -":
    st.markdown("<br>", unsafe_allow_html=True)
    st.info("🏉 **Bienvenido.** Selecciona un jugador en el menú lateral para ver el análisis de rendimiento.")
else:
    st.title(f"Estadísticas: {jugador_sel}")
    
    partidos_raw = sorted(df[df['Player Name'] == jugador_sel]['Activity Name'].unique().tolist())
    mapa_partidos = {limpiar_nombre_partido(p): p for p in partidos_raw}
    opciones_partido = ["- Seleccionar Partido -"] + list(mapa_partidos.keys())
    
    partido_limpio_sel = st.sidebar.selectbox(
        "Partido:", 
        opciones_partido, 
        key=f"partido_{st.session_state.count}"
    )

    metricas_dict = {
        'Total Distance': 'Distancia Total (m)',
        'HSR': 'HSR (m)',
        'Acceleration B1-3 Total Efforts (Gen 2)': 'Aceleraciones',
        'Maximum Velocity': 'Velocidad Máxima',
        'Tackles Total (Band1-Band3)': 'Tackles Totales',
        'Duration_Min': 'Duración (min)'
    }

    # PESTAÑAS
    tab1, tab2, tab3 = st.tabs(["📊 Rendimiento por Partido", "📈 Comparativa vs Equipo", "📋 Evolución de todas las métricas"])

    with tab1:
        if partido_limpio_sel == "- Seleccionar Partido -":
            st.info("👈 Selecciona un partido en el menú lateral.")
        else:
            nombre_original_partido = mapa_partidos[partido_limpio_sel]
            data_match = df[(df['Player Name'] == jugador_sel) & (df['Activity Name'] == nombre_original_partido)]
            
            if not data_match.empty:
                m_cols = st.columns(len(metricas_dict))
                for i, (col_id, label) in enumerate(metricas_dict.items()):
                    m_cols[i].metric(label, f"{data_match[col_id].iloc[0]:.1f}")

                fig_bar = go.Figure()
                fig_bar.add_trace(go.Bar(
                    x=[metricas_dict[k] for k in metricas_dict.keys()],
                    y=[data_match[c].iloc[0] for c in metricas_dict.keys()],
                    marker_color=VERDE_OSCURO,
                    name=jugador_sel
                ))
                fig_bar.update_layout(title=f"Desempeño en {partido_limpio_sel}", height=500)
                st.plotly_chart(fig_bar, use_container_width=True)

    with tab2:
        st.subheader("Comparativa vs Promedio del Plantel")
        met_comp = st.selectbox("Métrica para comparar:", list(metricas_dict.keys()), 
                                format_func=lambda x: metricas_dict[x],
                                key=f"comp_{st.session_state.count}")
        
        hist_jugador = df[df['Player Name'] == jugador_sel].copy()
        hist_jugador['Activity Name'] = hist_jugador['Activity Name'].apply(limpiar_nombre_partido)
        
        promedio_equipo = df.groupby('Activity Name')[met_comp].mean().reset_index()
        promedio_equipo['Activity Name'] = promedio_equipo['Activity Name'].apply(limpiar_nombre_partido)

        fig_comp = go.Figure()
        fig_comp.add_trace(go.Bar(
            x=hist_jugador['Activity Name'], y=hist_jugador[met_comp],
            name=f"Jugador: {jugador_sel}", marker_color=VERDE_OSCURO
        ))
        fig_comp.add_trace(go.Bar(
            x=promedio_equipo['Activity Name'], y=promedio_equipo[met_comp],
            name="Promedio Equipo", marker_color=AMARILLO_OSCURO
        ))
        fig_comp.update_layout(barmode='group', title=f"Evolución: {metricas_dict[met_comp]}")
        st.plotly_chart(fig_comp, use_container_width=True)

    with tab3:
        st.subheader(f"Evolución de Métricas - {jugador_sel}")
        hist_full = df[df['Player Name'] == jugador_sel].copy()
        hist_full['Activity Name'] = hist_full['Activity Name'].apply(limpiar_nombre_partido)
        
        # Generar un gráfico por cada métrica para ver la evolución completa
        for col_id, label in metricas_dict.items():
            fig_evol = go.Figure()
            fig_evol.add_trace(go.Bar(
                x=hist_full['Activity Name'],
                y=hist_full[col_id],
                marker_color=VERDE_OSCURO,
                name=label
            ))
            fig_evol.update_layout(
                title=f"Evolución: {label}",
                height=300,
                xaxis_title="Partidos",
                yaxis_title=label,
                margin=dict(l=20, r=20, t=40, b=20)
            )
            st.plotly_chart(fig_evol, use_container_width=True)