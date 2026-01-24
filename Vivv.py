
import streamlit as st
import sqlite3
import pandas as pd
import openai
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Vivv AI | BioTwin",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILO NEON (CSS) ---
st.markdown("""
<style>
    .stApp { background-color: #000505; color: #e0fbfc; }
    [data-testid="stSidebar"] { background-color: #000808; border-right: 1px solid #00f2ff; }
    .neon-card {
        background: rgba(0, 20, 20, 0.6);
        border: 1px solid #00f2ff;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 0 15px rgba(0, 242, 255, 0.2);
        margin-bottom: 20px;
    }
    h1, h2, h3 { color: #00f2ff; text-shadow: 0 0 10px #00f2ff; }
    .stMetric { background: rgba(0,0,0,0); border: none; }
</style>
""", unsafe_allow_html=True)

# --- BANCO DE DADOS (SQLite) ---
def init_db():
    conn = sqlite3.connect('vivv_saude.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS perfil 
                 (id INTEGER PRIMARY KEY, nome TEXT, idade INT, peso REAL, altura REAL, meta REAL)''')
    conn.commit()
    conn.close()

init_db()

# --- INTEGRAÇÃO OPENAI (GPT-5-mini) ---
def gerar_insight(prompt_contexto):
    try:
        client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        response = client.chat.completions.create(
            model="gpt-5-mini",
            messages=[{"role": "system", "content": "Você é o Vivv, um Gêmeo Digital focado em longevidade. Seja curto e científico."},
                      {"role": "user", "content": prompt_contexto}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Conecte sua API Key para ativar a IA. (Erro: {str(e)})"

# --- SIDEBAR: CADASTRO REAL ---
st.sidebar.title("🧬 Perfil Bio-Identificado")
with st.sidebar.form("cadastro"):
    nome = st.text_input("Nome", value="Lucas")
    idade = st.number_input("Idade", value=29)
    peso = st.number_input("Peso Atual (kg)", value=80.0)
    altura = st.number_input("Altura (m)", value=1.75)
    meta = st.number_input("Meta de Peso (kg)", value=75.0)
    if st.form_submit_button("Atualizar Bio-Dados"):
        conn = sqlite3.connect('vivv_saude.db')
        c = conn.cursor()
        c.execute("DELETE FROM perfil")
        c.execute("INSERT INTO perfil (nome, idade, peso, altura, meta) VALUES (?, ?, ?, ?, ?)", 
                  (nome, idade, peso, altura, meta))
        conn.commit()
        conn.close()
        st.sidebar.success("Dados salvos no SQLite!")

# --- BUSCA DADOS DO BANCO ---
conn = sqlite3.connect('vivv_saude.db')
df_user = pd.read_sql_query("SELECT * FROM perfil", conn)
conn.close()

if not df_user.empty:
    u_nome, u_idade, u_peso, u_altura, u_meta = df_user.iloc[0,1:]
else:
    u_nome, u_idade, u_peso, u_altura, u_meta = "Usuário", 29, 80.0, 1.75, 75.0

# --- CABEÇALHO ---
st.title(f"🧬 IA BIOTWIN - {u_nome.upper()}")
st.markdown(f"**Interface de Monitoramento Preditivo v2.0.26** | Dados de {datetime.now().strftime('%d/%m/%Y')}")

# --- DASHBOARD (METAS REAIS) ---
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown('<div class="neon-card">', unsafe_allow_html=True)
    imc = u_peso / (u_altura ** 2)
    st.metric("IMC Atual", f"{imc:.1f}", delta_color="inverse")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="neon-card">', unsafe_allow_html=True)
    st.metric("Idade Biológica", f"{u_idade - 2} anos", "-2,1 anos")
    st.markdown('</div>', unsafe_allow_html=True)

with col3:
    st.markdown('<div class="neon-card">', unsafe_allow_html=True)
    diff = u_peso - u_meta
    st.metric("Peso vs Meta", f"{u_peso} kg", f"{diff:.1f} kg para meta")
    st.markdown('</div>', unsafe_allow_html=True)

with col4:
    st.markdown('<div class="neon-card">', unsafe_allow_html=True)
    st.metric("Score Longevidade", "88.4", "+1.2%")
    st.markdown('</div>', unsafe_allow_html=True)

# --- GRÁFICO DE TENDÊNCIAS (PROJETADO) ---
st.subheader("📊 Projeção de Biomarcadores")
chart_data = pd.DataFrame({
    'Dias': pd.date_range(start='2026-01-01', periods=10),
    'HRV': np.random.randint(60, 80, 10),
    'Glicose': np.random.randint(85, 105, 10)
})
fig = go.Figure()
fig.add_trace(go.Scatter(x=chart_data['Dias'], y=chart_data['HRV'], name="HRV (ms)", line=dict(color='#00f2ff', width=3)))
fig.add_trace(go.Scatter(x=chart_data['Dias'], y=chart_data['Glicose'], name="Glicose (mg/dL)", line=dict(color='#ff007f', dash='dot')))
fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="#e0fbfc")
st.plotly_chart(fig, use_container_width=True)

# --- CHAT DE PESQUISA (FUNCIONAL) ---
st.markdown("---")
st.subheader("💬 Consultoria Gêmeo Digital")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Pergunte algo (ex: Como reduzir meu IMC?)"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        contexto = f"O usuário {u_nome} tem {u_idade} anos, pesa {u_peso}kg e mede {u_altura}m. Meta: {u_meta}kg. Pergunta: {prompt}"
        resposta = gerar_insight(contexto)
        st.markdown(resposta)
        st.session_state.messages.append({"role": "assistant", "content": resposta})
