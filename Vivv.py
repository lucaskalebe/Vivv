

import streamlit as st
import sqlite3
import pandas as pd
import openai
import urllib.parse
from pathlib import Path
from datetime import datetime

# ================= 1. DESIGN ULTRA NEON (DEEP BLACK & COBALT BLUE) =================
st.set_page_config(page_title="Vivv Lab Master", layout="wide", page_icon="🧬")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    .stApp { background-color: #000205; color: #d1d1d1; font-family: 'Inter', sans-serif; }
    
    /* Cards de Métricas */
    .neon-card {
        background: linear-gradient(145deg, #000814, #001220);
        border: 1px solid #0056b3;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 0 20px rgba(0, 86, 179, 0.2);
        transition: all 0.4s ease;
        text-align: center;
    }
    .neon-card:hover { 
        border-color: #00d4ff; 
        box-shadow: 0 0 30px rgba(0, 212, 255, 0.4);
        transform: scale(1.03);
    }
    
    /* Botões Customizados */
    .stButton>button {
        background: #001d3d; color: #00d4ff; border: 1px solid #0056b3;
        border-radius: 8px; font-weight: bold; width: 100%; transition: 0.3s;
    }
    .stButton>button:hover { background: #003566; border-color: #00d4ff; color: white; box-shadow: 0 0 10px #00d4ff; }
    
    /* Tabelas e Dataframes */
    [data-testid="stDataFrame"] { border: 1px solid #0056b3; border-radius: 10px; background: #000814; }

    /* Estilo para abas e textos */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background: #000814; border: 1px solid #003566; color: #00d4ff; border-radius: 5px; padding: 5px 20px; }
    .stTabs [aria-selected="true"] { background: #003566; border-color: #00d4ff; }
    
    h1, h2, h3 { color: #00d4ff; text-shadow: 0 0 8px rgba(0, 212, 255, 0.5); }
</style>
""", unsafe_allow_html=True)

# ================= 2. CORE: BANCO DE DADOS E AUTH =================
CLIENTES_CONFIG = {
    "lucas": {"db": "lucas.db", "nome": "Vivv Lab Master", "senha": "123"},
    "barber_nunes": {"db": "nunes.db", "nome": "Barbearia do Nunes", "senha": "123"}
}

DBS_DIR = Path(__file__).parent / "dbs"
DBS_DIR.mkdir(exist_ok=True)

def get_connection():
    return sqlite3.connect(st.session_state.db_p, check_same_thread=False)

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
    st.markdown("<br><br><h1 style='text-align:center;'>🧬 LOGIN VIVV MASTER</h1>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 0.8, 1])
    with col:
        u = st.text_input("ID do Usuário")
        p = st.text_input("Senha", type="password")
        if st.button("ACESSAR"):
            if u in CLIENTES_CONFIG and CLIENTES_CONFIG[u]["senha"] == p:
                st.session_state.auth, st.session_state.u_id = True, u
                st.session_state.db_p = DBS_DIR / CLIENTES_CONFIG[u]['db']
                init_db(st.session_state.db_p)
                st.rerun()
    st.stop()

# ================= 3. DASHBOARD METRICS =================
conn = get_connection()
df_cx = pd.read_sql("SELECT valor, tipo FROM caixa", conn)
entradas = df_cx[df_cx.tipo=="Entrada"]["valor"].sum() if not df_cx.empty else 0
saidas = df_cx[df_cx.tipo=="Saída"]["valor"].sum() if not df_cx.empty else 0
clis_total = pd.read_sql("SELECT COUNT(*) FROM clientes", conn).iloc[0,0]
hoje = datetime.now().strftime('%Y-%m-%d')
ag_hoje = pd.read_sql(f"SELECT COUNT(*) FROM agenda WHERE data='{hoje}'", conn).iloc[0,0]

# UI Header
c1, c2 = st.columns([5, 1])
c1.title(f"💈 {CLIENTES_CONFIG[st.session_state.u_id]['nome']}")
if c2.button("LOGOUT"):
    st.session_state.clear()
    st.rerun()

m1, m2, m3, m4 = st.columns(4)
with m1: st.markdown(f'<div class="neon-card"><small>CLIENTES</small><h2>{clis_total}</h2></div>', unsafe_allow_html=True)
with m2: st.markdown(f'<div class="neon-card"><small>FATURAMENTO</small><h2 style="color:#00d4ff">R$ {entradas:,.2f}</h2></div>', unsafe_allow_html=True)
with m3: st.markdown(f'<div class="neon-card"><small>LUCRO LÍQUIDO</small><h2 style="color:#00ff88">R$ {(entradas - saidas):,.2f}</h2></div>', unsafe_allow_html=True)
with m4: st.markdown(f'<div class="neon-card"><small>AGENDADOS HOJE</small><h2 style="color:#ff007f">{ag_hoje}</h2></div>', unsafe_allow_html=True)

# ================= 4. OPERAÇÕES E AGENDAMENTO =================
st.markdown("<br>", unsafe_allow_html=True)
col_ops, col_list = st.columns([1.5, 2])

with col_ops:
    st.subheader("⚡ Painel Operacional")
    t1, t2, t3, t4 = st.tabs(["📅 Agenda", "👤 Cliente", "💰 Serviço", "📉 Caixa"])
    
    with t1:
        c_list = pd.read_sql("SELECT id, nome FROM clientes", conn)
        s_list = pd.read_sql("SELECT id, nome FROM servicos", conn)
        with st.form("new_ag"):
            cli = st.selectbox("Cliente", c_list['nome']) if not c_list.empty else None
            srv = st.selectbox("Serviço", s_list['nome']) if not s_list.empty else None
            dt = st.date_input("Data", format="DD/MM/YYYY")
            hr = st.time_input("Hora")
            if st.form_submit_button("CONFIRMAR AGENDAMENTO"):
                c_id = c_list[c_list.nome == cli].id.values[0]
                s_id = s_list[s_list.nome == srv].id.values[0]
                conn.execute("INSERT INTO agenda (cliente_id, servico_id, data, hora, status) VALUES (?,?,?,?, 'Pendente')", (int(c_id), int(s_id), str(dt), str(hr)))
                conn.commit(); st.rerun()

    with t2:
        with st.form("new_cli"):
            nome = st.text_input("Nome")
            zap = st.text_input("WhatsApp")
            if st.form_submit_button("SALVAR CLIENTE"):
                conn.execute("INSERT INTO clientes (nome, telefone) VALUES (?,?)", (nome, zap))
                conn.commit(); st.rerun()

    with t3:
        with st.form("new_srv"):
            nome_s = st.text_input("Serviço")
            preco = st.number_input("Preço R$", min_value=0.0)
            if st.form_submit_button("SALVAR SERVIÇO"):
                conn.execute("INSERT INTO servicos (nome, preco) VALUES (?,?)", (nome_s, preco))
                conn.commit(); st.rerun()

    with t4:
        with st.form("new_cx"):
            desc = st.text_input("Descrição")
            valor = st.number_input("Valor", min_value=0.0)
            tipo = st.selectbox("Tipo", ["Entrada", "Saída"])
            if st.form_submit_button("LANÇAR"):
                conn.execute("INSERT INTO caixa (descricao, valor, tipo, data) VALUES (?,?,?,?)", (desc, valor, tipo, hoje))
                conn.commit(); st.rerun()

with col_list:
    st.subheader("📋 Fila de Atendimento")
    q = "SELECT a.id, c.nome, c.telefone, s.nome as serv, s.preco, a.data, a.hora FROM agenda a JOIN clientes c ON c.id=a.cliente_id JOIN servicos s ON s.id=a.servico_id WHERE a.status='Pendente' ORDER BY a.data, a.hora"
    df_ag = pd.read_sql(q, conn)
    for _, r in df_ag.iterrows():
        with st.expander(f"📍 {datetime.strptime(r.data, '%Y-%m-%d').strftime('%d/%m/%Y')} - {r.hora[:5]} | {r.nome}"):
            c_inf, c_b1, c_b2 = st.columns([2, 1, 1])
            c_inf.write(f"**{r.serv}** (R$ {r.preco:.2f})")
            if c_b1.button("CONCLUIR", key=f"ok{r.id}"):
                conn.execute("UPDATE agenda SET status='Concluído' WHERE id=?", (r.id,))
                conn.execute("INSERT INTO caixa (descricao, valor, tipo, data) VALUES (?,?,?,?)", (f"Atend: {r.nome}", r.preco, "Entrada", hoje))
                conn.commit(); st.rerun()
            if c_b2.button("❌ CANCELAR", key=f"del{r.id}"):
                conn.execute("DELETE FROM agenda WHERE id=?", (r.id,))
                conn.commit(); st.rerun()

# ================= 5. CENTRAL DE DADOS (NOVO) =================
st.markdown("---")
st.subheader("🗄️ Central de Dados & Auditoria")
col_db1, col_db2 = st.columns(2)

with col_db1:
    with st.expander("👥 Banco de Dados de Clientes"):
        df_clientes = pd.read_sql("SELECT nome as Nome, telefone as WhatsApp FROM clientes", conn)
        st.dataframe(df_clientes, use_container_width=True)

with col_db2:
    with st.expander("📊 Extrato de Fluxo de Caixa"):
        df_fluxo = pd.read_sql("SELECT data as Data, descricao as Descricao, tipo as Tipo, valor as Valor FROM caixa ORDER BY id DESC", conn)
        st.dataframe(df_fluxo, use_container_width=True)

# ================= 6. IA CONSULTORA =================
st.markdown("---")
st.subheader("💬 Vivv AI: Estrategista")
if prompt := st.chat_input("Como posso otimizar meu lucro?"):
    with st.chat_message("user"): st.write(prompt)
    with st.chat_message("assistant"):
        ctx = f"Contexto: {entradas} faturamento, {saidas} despesas. Clientes: {clis_total}. Pergunta: {prompt}"
        try:
            client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
            res = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role":"user", "content": ctx}])
            st.write(res.choices[0].message.content)
        except: st.error("IA Offline - Verifique os Secrets.")
