

import streamlit as st
import sqlite3
import pandas as pd
import openai
import urllib.parse
from pathlib import Path
from datetime import datetime

# ================= 1. CONFIGURAÇÃO E ESTILO NEON (CALENDÁRIO PT-BR) =================
st.set_page_config(page_title="Vivv Business AI", layout="wide", page_icon="💈")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700&display=swap');
    .stApp { background-color: #000505; color: #e0fbfc; font-family: 'Plus Jakarta Sans', sans-serif; }
    
    /* Efeito de Brilho e Movimento nos Cards */
    .neon-card {
        background: rgba(0, 20, 20, 0.6);
        border: 1px solid #00f2ff;
        border-radius: 20px;
        padding: 25px;
        box-shadow: 0 0 15px rgba(0, 242, 255, 0.1);
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
        margin-bottom: 15px;
    }
    .neon-card:hover { 
        transform: translateY(-8px) scale(1.02); 
        box-shadow: 0 0 30px rgba(0, 242, 255, 0.4); 
        border-color: #ff007f; 
    }
    
    .metric-label { color: #8E8E93; font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; }
    .metric-value { color: #FFFFFF; font-size: 28px; font-weight: 700; text-shadow: 0 0 5px rgba(255,255,255,0.2); }
    h1, h2, h3 { color: #00f2ff; text-shadow: 0 0 10px #00f2ff; }
</style>
""", unsafe_allow_html=True)

# ================= 2. BANCO DE DADOS E ACESSOS =================
CLIENTES_CONFIG = {
    "lucas": {"db": "lucas.db", "nome": "Vivv Lab Master", "senha": "123"},
    "barber_nunes": {"db": "nunes.db", "nome": "Barbearia do Nunes", "senha": "123"}
}

BASE_DIR = Path(__file__).parent
DBS_DIR = BASE_DIR / "dbs"
DBS_DIR.mkdir(exist_ok=True)

def init_db(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS clientes (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, telefone TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS servicos (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, preco REAL)')
    c.execute('CREATE TABLE IF NOT EXISTS agenda (id INTEGER PRIMARY KEY AUTOINCREMENT, cliente_id INTEGER, servico_id INTEGER, data TEXT, hora TEXT, status TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS caixa (id INTEGER PRIMARY KEY AUTOINCREMENT, descricao TEXT, valor REAL, tipo TEXT, data TEXT)')
    conn.commit()
    conn.close()

if "auth" not in st.session_state:
    st.markdown("<br><br><div style='text-align:center;'><h1>🧬 VIVV BUSINESS AI</h1></div>", unsafe_allow_html=True)
    _, col_login, _ = st.columns([1, 1, 1])
    with col_login:
        u = st.text_input("ID")
        p = st.text_input("Senha", type="password")
        if st.button("ACESSAR"):
            if u in CLIENTES_CONFIG and CLIENTES_CONFIG[u]["senha"] == p:
                st.session_state.auth, st.session_state.u_id = True, u
                st.session_state.db_p = DBS_DIR / CLIENTES_CONFIG[u]['db']
                init_db(st.session_state.db_p)
                st.rerun()
    st.stop()

# ================= 3. LOGICA FINANCEIRA E DASHBOARD =================
db_p = st.session_state.db_p
conn = sqlite3.connect(db_p, check_same_thread=False)

# Dados para os cards
clis_count = pd.read_sql("SELECT COUNT(*) FROM clientes", conn).iloc[0,0]
df_cx = pd.read_sql("SELECT valor, tipo FROM caixa", conn)
entradas = df_cx[df_cx.tipo=="Entrada"]["valor"].sum() if not df_cx.empty else 0
saidas = df_cx[df_cx.tipo=="Saída"]["valor"].sum() if not df_cx.empty else 0
lucro_liquido = entradas - saidas
hoje_str = str(datetime.now().date())
ag_hoje = pd.read_sql(f"SELECT COUNT(*) FROM agenda WHERE data='{hoje_str}'", conn).iloc[0,0]

def format_rs(v): return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# HEADER
c_h1, c_h2 = st.columns([4, 1])
c_h1.title(f"💈 {CLIENTES_CONFIG[st.session_state.u_id]['nome']}")
if c_h2.button("SAIR"):
    st.session_state.clear()
    st.rerun()

# CARDS COM MÉTRICAS ORIGINAIS (Fluidez e Brilho mantidos)
m1, m2, m3, m4 = st.columns(4)
with m1: st.markdown(f'<div class="neon-card"><div class="metric-label">Clientes</div><div class="metric-value">{clis_count}</div></div>', unsafe_allow_html=True)
with m2: st.markdown(f'<div class="neon-card"><div class="metric-label">Faturamento</div><div class="metric-value" style="color:#10B981">{format_rs(entradas)}</div></div>', unsafe_allow_html=True)
with m3: st.markdown(f'<div class="neon-card"><div class="metric-label">Lucro Líquido</div><div class="metric-value" style="color:#00f2ff">{format_rs(lucro_liquido)}</div></div>', unsafe_allow_html=True)
with m4: st.markdown(f'<div class="neon-card"><div class="metric-label">Agendados Hoje</div><div class="metric-value" style="color:#ff007f">{ag_hoje}</div></div>', unsafe_allow_html=True)

# ================= 4. GESTÃO E AGENDAMENTO (CALENDÁRIO PT-BR) =================
st.markdown("---")
col_c, col_l = st.columns([1.2, 2])

with col_c:
    st.subheader("⚡ Ações")
    aba1, aba2, aba3 = st.tabs(["📅 Agendar", "👤 Cliente", "💰 Serviço"])
    
    with aba1:
        clis_df = pd.read_sql("SELECT id, nome FROM clientes", conn)
        svs_df = pd.read_sql("SELECT id, nome, preco FROM servicos", conn)
        with st.form("ag"):
            c_sel = st.selectbox("Cliente", clis_df["nome"]) if not clis_df.empty else None
            s_sel = st.selectbox("Serviço", svs_df["nome"]) if not svs_df.empty else None
            # Ajuste de Calendário para PT-BR
            data_ag = st.date_input("Data", format="DD/MM/YYYY") 
            hora_ag = st.time_input("Hora")
            if st.form_submit_button("Confirmar"):
                if c_sel and s_sel:
                    c_id = clis_df[clis_df.nome == c_sel].id.values[0]
                    s_id = svs_df[svs_df.nome == s_sel].id.values[0]
                    conn.execute("INSERT INTO agenda (cliente_id, servico_id, data, hora, status) VALUES (?,?,?,?, 'Pendente')", (int(c_id), int(s_id), str(data_ag), str(hora_ag)))
                    conn.commit(); st.rerun()

with col_l:
    st.subheader("📋 Lista de Espera")
    df_lista = pd.read_sql("SELECT a.id, c.nome, c.telefone, s.nome as serv, s.preco, a.data, a.hora FROM agenda a JOIN clientes c ON c.id=a.cliente_id JOIN servicos s ON s.id=a.servico_id WHERE a.status='Pendente' ORDER BY a.data, a.hora", conn)
    for _, r in df_lista.iterrows():
        # Converte data para exibir em PT-BR na lista
        dt_br = datetime.strptime(r.data, '%Y-%m-%d').strftime('%d/%m/%Y')
        with st.expander(f"📌 {dt_br} - {r.hora[:5]} | {r.nome}"):
            st.write(f"Serviço: {r.serv} (R$ {r.preco:.2f})")
            if st.button(f"Concluir Atendimento", key=f"f_{r.id}"):
                conn.execute("UPDATE agenda SET status='Concluído' WHERE id=?", (r.id,))
                conn.execute("INSERT INTO caixa (descricao, valor, tipo, data) VALUES (?,?,?,?)", (f"Atend: {r.nome}", r.preco, "Entrada", hoje_str))
                conn.commit(); st.rerun()

# ================= 5. CHAT IA VIVV =================
st.markdown("---")
st.subheader("💬 Vivv AI: Consultor")
if p := st.chat_input("Pergunte sobre seu lucro ou faturamento..."):
    with st.chat_message("user"): st.write(p)
    with st.chat_message("assistant"):
        prompt = f"O negócio tem R$ {entradas} de receita e R$ {lucro_liquido} de lucro. {clis_count} clientes. Pergunta: {p}"
        try:
            client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
            res = client.chat.completions.create(model="gpt-5-mini", messages=[{"role":"user", "content": prompt}])
            st.write(res.choices[0].message.content)
        except: st.write("IA Offline. Verifique sua API Key.")
