

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="BioTwin AI | Human Longevity",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- DESIGN NEON UX (CSS CUSTOMIZADO) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Inter:wght@300;400;600&display=swap');

    /* Fundo e Containers */
    .stApp {
        background: radial-gradient(circle at top right, #070b14, #000000);
        color: #e0e0e0;
        font-family: 'Inter', sans-serif;
    }

    /* Cards Neon */
    .neon-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(0, 255, 255, 0.2);
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 4px 15px rgba(0, 255, 255, 0.05);
        transition: all 0.3s ease;
    }
    .neon-card:hover {
        border: 1px solid rgba(0, 255, 255, 0.6);
        box-shadow: 0 0 20px rgba(0, 255, 255, 0.2);
    }

    /* Títulos e Métricas */
    h1, h2, h3 {
        font-family: 'Orbitron', sans-serif;
        letter-spacing: 2px;
        color: #00f2ff !important;
        text-shadow: 0 0 10px rgba(0, 242, 255, 0.5);
    }
    
    [data-testid="stMetricValue"] {
        font-family: 'Orbitron', sans-serif;
        color: #00f2ff !important;
        font-size: 1.8rem !important;
    }

    /* Custom Scrollbar */
    ::-webkit-scrollbar { width: 5px; }
    ::-webkit-scrollbar-track { background: #070b14; }
    ::-webkit-scrollbar-thumb { background: #00f2ff; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

# --- GERADOR DE DADOS SINTÉTICOS (COERENTES) ---
@st.cache_data
def get_health_data():
    dates = [datetime.now() - timedelta(days=x) for x in range(30, 0, -1)]
    hrv = np.random.normal(65, 5, 30)
    glucose = np.random.normal(95, 10, 30)
    sleep_score = np.random.randint(60, 95, 30)
    return pd.DataFrame({'Data': dates, 'HRV': hrv, 'Glicose': glucose, 'Sono': sleep_score})

df = get_health_data()

# --- HEADER ---
st.markdown("<h1 style='text-align: center;'>🧬 BIOTWIN <span style='color:white'>AI</span></h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #888;'>Interface de Monitoramento Preditivo v2.0.27</p>", unsafe_allow_html=True)
st.write("---")

# --- LINHA 1: KPIs NEON ---
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown('<div class="neon-card">', unsafe_allow_html=True)
    st.metric("Score de Longevidade", "84.2", "+1.2%")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="neon-card">', unsafe_allow_html=True)
    st.metric("Idade Biológica", "29.4y", "-0.3y", delta_color="normal")
    st.markdown('</div>', unsafe_allow_html=True)

with col3:
    st.markdown('<div class="neon-card">', unsafe_allow_html=True)
    st.metric("Variabilidade Cardíaca", "72ms", "Estável")
    st.markdown('</div>', unsafe_allow_html=True)

with col4:
    st.markdown('<div class="neon-card">', unsafe_allow_html=True)
    st.metric("Recuperação CNS", "92%", "+5%")
    st.markdown('</div>', unsafe_allow_html=True)

st.write("")

# --- LINHA 2: GRÁFICOS AVANÇADOS ---
c1, c2 = st.columns([2, 1])

with c1:
    st.markdown("### 📊 Tendências de Biomarcadores")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['Data'], y=df['HRV'], name="HRV (ms)",
                             line=dict(color='#00f2ff', width=3), fill='tozeroy',
                             fillcolor='rgba(0, 242, 255, 0.1)'))
    fig.add_trace(go.Scatter(x=df['Data'], y=df['Glicose'], name="Glicose (mg/dL)",
                             line=dict(color='#ff007f', width=3, dash='dot')))
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=20, b=0), height=400,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        font=dict(color="#888"),
        xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)')
    )
    st.plotly_chart(fig, use_container_width=True)

with c2:
    st.markdown("### 🧠 Insights da IA")
    st.info("Sua Variabilidade Cardíaca (HRV) sugere uma janela de treino de alta intensidade hoje.")
    
    # Gráfico de Radar para Equilíbrio Sistêmico
    categories = ['Sono', 'Nutrição', 'Atividade', 'Stress', 'Hidratação']
    values = [85, 70, 90, 65, 80]
    
    fig_radar = go.Figure(data=go.Scatterpolar(
        r=values, theta=categories, fill='toself',
        fillcolor='rgba(0, 242, 255, 0.3)', line=dict(color='#00f2ff')
    ))
    fig_radar.update_layout(
        polar=dict(radialaxis=dict(visible=False), bgcolor='rgba(0,0,0,0)'),
        showlegend=False, paper_bgcolor='rgba(0,0,0,0)', height=300,
        margin=dict(l=40, r=40, t=20, b=20)
    )
    st.plotly_chart(fig_radar, use_container_width=True)

# --- LINHA 3: SIMULADOR DE GÊMEO DIGITAL (A "MAGIA") ---
st.write("---")
st.markdown("### 🤖 Simulador do Gêmeo Digital")
col_sim1, col_sim2 = st.columns([1, 2])

with col_sim1:
    st.write("Ajuste variáveis futuras:")
    s_dieta = st.select_slider("Aporte de Carboidratos", options=["Baixo", "Moderado", "Alto"])
    s_treino = st.slider("Intensidade do Treino (RPE)", 1, 10, 5)
    s_suplemento = st.checkbox("Incluir Protocolo de Magnésio/Omega3")
    
    if st.button("🚀 RODAR SIMULAÇÃO"):
        st.toast("Processando dados no Gêmeo Digital...", icon="⏳")

with col_sim2:
    # Simulação visual de impacto
    sim_data = np.random.normal(70, 2, 10) + (10 if s_suplemento else 0)
    fig_sim = go.Figure()
    fig_sim.add_trace(go.Bar(y=sim_data, marker_color='#00f2ff', opacity=0.6, name="Projeção Saúde"))
    fig_sim.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=250, margin=dict(t=0))
    st.plotly_chart(fig_sim, use_container_width=True)
    st.success(f"Projeção: Com treino nível {s_treino} e suplementação, sua idade biológica pode reduzir 0.2y em 15 dias.")

# --- FOOTER ---
st.markdown("<br><p style='text-align: center; color: #444;'>Propriedade do Usuário | Dados Criptografados End-to-End</p>", unsafe_allow_html=True)