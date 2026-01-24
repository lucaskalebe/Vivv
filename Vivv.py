import streamlit as st
import sqlite3
import pandas as pd
import openai
import urllib.parse
from pathlib import Path
from datetime import datetime

# ================= 1. CONFIGURAÇÃO E ESTILO NEON =================
st.set_page_config(page_title="Vivv Business AI", layout="wide", page_icon="💈")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700&display=swap');
    .stApp { background-color: #000505; color: #e0fbfc; font-family: 'Plus Jakarta Sans', sans-serif; }
    [data-testid="stSidebar"] { background-color: #000808; border-right: 1px solid #00f2ff; }
    
    .neon-card {
        background: rgba(0, 20, 20, 0.6);
        border: 1px solid #00f2ff;
        border-radius: 20px;
        padding: 25px;
        box-shadow: 0 0 15px rgba(0, 242, 255, 0.1);
        transition: all 0.3s ease;
        margin-bottom: 15px;
    }
    .neon-card:hover { transform: translateY(-5px); box-shadow: 0 0 25px rgba(0, 242, 255, 0.3); border-color: #ff007f; }
    
    .metric-label { color: #8E8E93; font-size: 13px; font-weight: 600; text-transform: uppercase; }
    .metric-value { color: #FFFFFF; font-size: 32px; font-weight: 700; }
    h1, h2, h3 { color: #00f2ff; text-shadow: 0 0 10px #00f2ff; }
    
    .wa-btn {
        background: linear-gradient(45deg, #25D366, #128C7E);
        color: white !important; padding: 8px 15px; border-radius: 10px;
        text-align: center; font-weight: bold; text-decoration: none; display: inline-block;
    }
</style>
""", unsafe_allow_html=True)

# ================= 2. ACESSOS E BANCO DE DADOS =================
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

# ================= 3. LÓGICA DE LOGIN =================
if "auth" not in st.session_state:
    st.markdown("<br><br><div style='text-align:center;'><h1>🧬 VIVV BUSINESS AI</h1></div>", unsafe_allow_html=True)
    _, col_login, _ = st.columns([1, 1, 1])
    with col_login:
        u = st.text_input("ID do Estabelecimento")
        p = st.text_input("Senha", type="password")
        if st.button("ACESSAR PAINEL"):
            if u in CLIENTES_CONFIG and CLIENTES_CONFIG[u]["senha"] == p:
                st.session_state.auth, st.session_state.u_id = True, u
                st.session_state.db_p = DBS_DIR / CLIENTES_CONFIG[u]['db']
                init_db(st.session_state.db_p)
                st.rerun()
            else: st.error("Login Inválido")
    st.stop()

# ================= 4. APP PRINCIPAL =================
db_p = st.session_state.db_p
info = CLIENTES_CONFIG[st.session_state.u_id]
conn = sqlite3.connect(db_p, check_same_thread=False)

# HEADER
c_h1, c_h2 = st.columns([4, 1])
c_h1.title(f"💈 {info['nome']}")
if c_h2.button("SAIR"):
    st.session_state.clear()
    st.rerun()

# MÉTRICAS TOTAIS
clis_count = pd.read_sql("SELECT COUNT(*) FROM clientes", conn).iloc[0,0]
df_cx = pd.read_sql("SELECT valor, tipo FROM caixa", conn)
receita = df_cx[df_cx.tipo=="Entrada"]["valor"].sum() if not df_cx.empty else 0
hoje = str(datetime.now().date())
ag_hoje = pd.read_sql(f"SELECT COUNT(*) FROM agenda WHERE data='{hoje}'", conn).iloc[0,0]

m1, m2, m3, m4 = st.columns(4)
with m1: st.markdown(f'<div class="neon-card"><div class="metric-label">Clientes</div><div class="metric-value">{clis_count}</div></div>', unsafe_allow_html=True)
with m2: st.markdown(f'<div class="neon-card"><div class="metric-label">Receita</div><div class="metric-value">R$ {receita:.2f}</div></div>', unsafe_allow_html=True)
with m3: st.markdown(f'<div class="neon-card"><div class="metric-label">Agenda Hoje</div><div class="metric-value">{ag_hoje}</div></div>', unsafe_allow_html=True)
with m4: st.markdown(f'<div class="neon-card"><div class="metric-label">Status</div><div class="metric-value" style="color:#00f2ff">ONLINE</div></div>', unsafe_allow_html=True)

# SEÇÃO DE CADASTROS (O QUE HAVIA SUMIDO)
st.markdown("---")
col_cad, col_list = st.columns([1.2, 2])

with col_cad:
    st.subheader("⚡ Gestão de Dados")
    aba_ag, aba_cli, aba_srv = st.tabs(["📅 Agendar", "👤 Cliente", "💰 Serviço"])
    
    with aba_ag:
        clis_df = pd.read_sql("SELECT id, nome FROM clientes", conn)
        svs_df = pd.read_sql("SELECT id, nome, preco FROM servicos", conn)
        with st.form("form_ag"):
            c_sel = st.selectbox("Cliente", clis_df["nome"]) if not clis_df.empty else None
            s_sel = st.selectbox("Serviço", svs_df["nome"]) if not svs_df.empty else None
            data_ag = st.date_input("Data")
            hora_ag = st.time_input("Hora")
            if st.form_submit_button("Confirmar Agendamento"):
                if c_sel and s_sel:
                    c_id = clis_df[clis_df.nome == c_sel].id.values[0]
                    s_id = svs_df[svs_df.nome == s_sel].id.values[0]
                    conn.execute("INSERT INTO agenda (cliente_id, servico_id, data, hora, status) VALUES (?,?,?,?, 'Pendente')", (int(c_id), int(s_id), str(data_ag), str(hora_ag)))
                    conn.commit(); st.rerun()

    with aba_cli:
        with st.form("form_cli"):
            n_cli = st.text_input("Nome do Cliente")
            t_cli = st.text_input("WhatsApp (Ex: 11999999999)")
            if st.form_submit_button("Salvar Cliente"):
                conn.execute("INSERT INTO clientes (nome, telefone) VALUES (?,?)", (n_cli, t_cli))
                conn.commit(); st.rerun()

    with aba_srv:
        with st.form("form_srv"):
            n_srv = st.text_input("Nome do Serviço")
            p_srv = st.number_input("Preço (R$)", min_value=0.0)
            if st.form_submit_button("Salvar Serviço"):
                conn.execute("INSERT INTO servicos (nome, preco) VALUES (?,?)", (n_srv, p_srv))
                conn.commit(); st.rerun()

with col_list:
    st.subheader("📋 Lista de Espera")
    query = """
        SELECT a.id, c.nome, c.telefone, s.nome as serv, s.preco, a.data, a.hora 
        FROM agenda a 
        JOIN clientes c ON c.id=a.cliente_id 
        JOIN servicos s ON s.id=a.servico_id 
        WHERE a.status='Pendente' ORDER BY a.data, a.hora
    """
    df_agenda = pd.read_sql(query, conn)
    if df_agenda.empty: st.info("Nenhum agendamento pendente.")
    for _, r in df_agenda.iterrows():
        with st.expander(f"📌 {r.hora[:5]} - {r.nome}"):
            st.write(f"**Serviço:** {r.serv} | **Valor:** R$ {r.preco:.2f}")
            msg = urllib.parse.quote(f"Olá {r.nome}, confirmado seu horário para {r.data} às {r.hora[:5]}!")
            st.markdown(f'<a href="https://wa.me/{r.telefone}?text={msg}" class="wa-btn">📱 Enviar WhatsApp</a>', unsafe_allow_html=True)
            if st.button(f"Concluir Atendimento", key=f"f_{r.id}"):
                conn.execute("UPDATE agenda SET status='Concluído' WHERE id=?", (r.id,))
                conn.execute("INSERT INTO caixa (descricao, valor, tipo, data) VALUES (?,?,?,?)", (f"Serviço: {r.serv} ({r.nome})", r.preco, "Entrada", hoje))
                conn.commit(); st.rerun()

# ================= 5. CONSULTORIA IA VIVV =================
st.markdown("---")
st.subheader("💬 Vivv AI: Inteligência de Negócio")
if "mensagens" not in st.session_state: st.session_state.mensagens = []

for m in st.session_state.mensagens:
    with st.chat_message(m["role"]): st.write(m["content"])

if p := st.chat_input("Perquise sobre seu faturamento ou dicas de gestão..."):
    st.session_state.mensagens.append({"role": "user", "content": p})
    with st.chat_message("user"): st.write(p)
    
    with st.chat_message("assistant"):
        # Contexto real enviado para a OpenAI (GPT-5-mini)
        prompt = f"O negócio {info['nome']} tem {clis_count} clientes e R$ {receita:.2f} em receita. Pergunta: {p}"
        try:
            client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
            res = client.chat.completions.create(model="gpt-5-mini", messages=[{"role":"user", "content": prompt}])
            resp_ia = res.choices[0].message.content
        except: resp_ia = "⚠️ Erro de API Key. Verifique os Secrets do Streamlit."
        
        st.write(resp_ia)
        st.session_state.mensagens.append({"role": "assistant", "content": resp_ia})
