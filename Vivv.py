

import streamlit as st
import pandas as pd
import hashlib
import json
from datetime import datetime, timezone, timedelta
from google.cloud import firestore
from google.oauth2 import service_account
import plotly.express as px

# ================= 1. CONFIGURAÇÃO E DESIGN SYSTEM =================
st.set_page_config(page_title="Vivv Pro | Intelligence", layout="wide", page_icon="⚡")

def inject_custom_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
        
        html, body, [data-testid="stapp"] { font-family: 'Inter', sans-serif; background-color: #050508; }
        
        /* Glassmorphism Cards */
        .stMetric, .metric-card {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 16px;
            padding: 20px;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .metric-card:hover {
            transform: translateY(-5px);
            border-color: #00D4FF;
            background: rgba(0, 212, 255, 0.05);
        }
        
        /* Botões Estilizados */
        .stButton>button {
            border-radius: 10px;
            transition: 0.3s;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 600;
        }
        
        /* Sidebar customizada */
        [data-testid="stSidebar"] {
            background-color: #0A0B14;
            border-right: 1px solid rgba(255,255,255,0.05);
        }
        
        .status-pill {
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }
        
        .gradient-text {
            background: linear-gradient(90deg, #00D4FF, #0088FF);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
    </style>
    """, unsafe_allow_html=True)

# ================= 2. CORE & DATABASE =================
@st.cache_resource
def get_db():
    try:
        # Tenta carregar dos secrets, se falhar, avisa o usuário
        if "FIREBASE_DETAILS" not in st.secrets:
            st.error("Configuração Firebase ausente nos Secrets.")
            return None
        info = json.loads(st.secrets["FIREBASE_DETAILS"])
        creds = service_account.Credentials.from_service_account_info(info)
        return firestore.Client(credentials=creds)
    except Exception as e:
        st.error(f"Erro de Conexão: {e}")
        return None

db = get_db()
fuso_br = timezone(timedelta(hours=-3))

def secure_hash(text):
    return hashlib.sha256(text.encode()).hexdigest()

# ================= 3. COMPONENTES DE UI =================
def ui_metric_card(label, value, delta=None, icon="📈"):
    delta_html = f'<span style="color: #00FF88; font-size: 0.8em;">▲ {delta}%</span>' if delta else ""
    st.markdown(f"""
    <div class="metric-card">
        <div style="color: #94A3B8; font-size: 0.9rem; margin-bottom: 8px;">{icon} {label}</div>
        <div style="font-size: 1.8rem; font-weight: 700; color: white;">{value}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)

# ================= 4. LOGICA DE NAVEGAÇÃO =================
def main():
    inject_custom_css()
    
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        show_login_page()
    else:
        show_app_interface()

def show_login_page():
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<br><br><h1 style='text-align: center;' class='gradient-text'>Vivv Pro</h1>", unsafe_allow_html=True)
        tab_login, tab_reg = st.tabs(["Acessar", "Registrar"])
        
        with tab_login:
            with st.form("login"):
                email = st.text_input("Email").lower().strip()
                password = st.text_input("Senha", type="password")
                if st.form_submit_button("Entrar", use_container_width=True):
                    user_ref = db.collection("usuarios").document(email).get()
                    if user_ref.exists and user_ref.to_dict()["senha"] == secure_hash(password):
                        st.session_state.authenticated = True
                        st.session_state.user_email = email
                        st.rerun()
                    else:
                        st.error("Credenciais inválidas")

def show_app_interface():
    # Sidebar Superior
    with st.sidebar:
        st.markdown("<h2 class='gradient-text'>⚡ Vivv Pro</h2>", unsafe_allow_html=True)
        menu = st.radio("Navegação", 
                        ["Dashboard", "Agenda", "Clientes", "Financeiro", "Configurações"],
                        label_visibility="collapsed")
        
        st.divider()
        if st.button("Sair", use_container_width=True):
            st.session_state.authenticated = False
            st.rerun()

    # Top Bar Contextual
    st.markdown(f"### {menu}")
    
    if menu == "Dashboard":
        render_dashboard()
    elif menu == "Agenda":
        render_agenda()

# ================= 5. PÁGINAS DO SISTEMA =================
def render_dashboard():
    # Dados Simulados (Aqui entraria sua função carregar_dados_usuario)
    c1, c2, c3, c4 = st.columns(4)
    with c1: ui_metric_card("Faturamento", "R$ 12.450", 12, "💰")
    with c2: ui_metric_card("Novos Clientes", "24", 5, "👥")
    with c3: ui_metric_card("Agendamentos", "8", None, "📅")
    with c4: ui_metric_card("Taxa de Lucro", "42%", 2, "📈")

    st.divider()
    
    col_graph, col_list = st.columns([2, 1])
    
    with col_graph:
        st.markdown("#### Performance Mensal")
        # Exemplo de gráfico Plotly otimizado
        df = pd.DataFrame({"Mes": ["Jan", "Fev", "Mar"], "Valor": [4000, 5500, 8000]})
        fig = px.line(df, x="Mes", y="Valor", template="plotly_dark")
        fig.update_traces(line_color="#00D4FF", line_width=4)
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)

    with col_list:
        st.markdown("#### Próximos Atendimentos")
        st.markdown("""
        <div class='metric-card'>
            <b>14:00 - João Silva</b><br>
            <span style='font-size: 0.8em; color: #94A3B8;'>Corte de Cabelo + Barba</span>
        </div><br>
        <div class='metric-card'>
            <b>15:30 - Maria Oliveira</b><br>
            <span style='font-size: 0.8em; color: #94A3B8;'>Coloração Premium</span>
        </div>
        """, unsafe_allow_html=True)

def render_agenda():
    st.info("Interface de Agenda em Grade (Grid View) em desenvolvimento.")
    # Implementar lógica de calendário aqui...

if __name__ == "__main__":
    if db:
        main()
