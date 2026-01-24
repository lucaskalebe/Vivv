

import streamlit as st
import sqlite3
import pandas as pd
import openai
import urllib.parse
from pathlib import Path
from datetime import datetime

# ================= 1. CONFIGURAÇÃO E ESTILO NEON PREMIUM =================
st.set_page_config(page_title="Vivv Business AI", layout="wide", page_icon="🧬")

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
    
    .wa-btn {
        background: linear-gradient(45deg, #25D366, #128C7E);
        color: white !important; padding: 10px 20px; border-radius: 12px;
        text-align: center; font-weight: bold; text-decoration: none; display: inline-block;
        box-shadow: 0 4px 15px rgba(37, 211, 102, 0.3);
    }
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
        u = st.text_input("ID do Estabelecimento")
        p = st.text_input("Senha", type="password")
        if st.button("ACESSAR PAINEL"):
            if u in CLIENTES_CONFIG and CLIENTES_CONFIG[u]["senha"] == p:
                st.session_state.auth, st.session_state.u_id = True, u
                st.session_state.db_p = DBS_DIR / CLIENTES_CONFIG[u]['db']
                init_db(st.session_state.db_p)
                st.rerun()
            else: st.error("Acesso Negado")
    st.stop()

# ================= 3. LOGICA FINANCEIRA E DADOS =================
db_p = st.session_state.db_p
conn = sqlite3.connect(db_p, check_same_thread=False)

# Puxar métricas reais
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
c_h1.title(f"🧬 {CLIENTES_CONFIG[st.session_state.u_id]['nome']}")
if c_h2.button("SAIR / LOGOUT"):
    st.session_state.clear()
    st.rerun()

# MÉTRICAS TOTAIS (Dashboard Neon)
m1, m2, m3, m4 = st.columns(4)
with m1: st.markdown(f'<div class="neon-card"><div class="metric-label">Clientes</div><div class="metric-value">{clis_count}</div></div>', unsafe_allow_html=True)
with m2: st.markdown(f'<div class="neon-card"><div class="metric-label">Faturamento</div><div class="metric-value" style="color:#10B981">{format_rs(entradas)}</div></div>', unsafe_allow_html=True)
with m3: st.markdown(f'<div class="neon-card"><div class="metric-label">Lucro Líquido</div><div class="metric-value" style="color:#00f2ff">{format_rs(lucro_liquido)}</div></div>', unsafe_allow_html=True)
with m4: st.markdown(f'<div class="neon-card"><div class="metric-label">Agenda Hoje</div><div class="metric-value" style="color:#ff007f">{ag_hoje}</div></div>', unsafe_allow_html=True)

# ================= 4. ÁREA DE OPERAÇÕES (CADASTROS) =================
st.markdown("---")
col_operacao, col_visualizacao = st.columns([1.3, 2])

with col_operacao:
    st.subheader("⚡ Ações Rápidas")
    tab_ag, tab_cli, tab_srv, tab_fin = st.tabs(["📅 Agendar", "👤 Cliente", "💰 Serviço", "📉 Caixa"])
    
    with tab_ag:
        clis_df = pd.read_sql("SELECT id, nome FROM clientes", conn)
        svs_df = pd.read_sql("SELECT id, nome, preco FROM servicos", conn)
        with st.form("form_agendamento"):
            c_sel = st.selectbox("Selecionar Cliente", clis_df["nome"]) if not clis_df.empty else st.warning("Cadastre um cliente primeiro")
            s_sel = st.selectbox("Serviço", svs_df["nome"]) if not svs_df.empty else st.warning("Cadastre um serviço")
            data_ag = st.date_input("Data do Atendimento", format="DD/MM/YYYY")
            hora_ag = st.time_input("Horário")
            if st.form_submit_button("AGENDAR HORÁRIO"):
                if c_sel and s_sel:
                    c_id = clis_df[clis_df.nome == c_sel].id.values[0]
                    s_id = svs_df[svs_df.nome == s_sel].id.values[0]
                    conn.execute("INSERT INTO agenda (cliente_id, servico_id, data, hora, status) VALUES (?,?,?,?, 'Pendente')", (int(c_id), int(s_id), str(data_ag), str(hora_ag)))
                    conn.commit(); st.success("Agendado!"); st.rerun()

    with tab_cli:
        with st.form("form_cliente"):
            n_cli = st.text_input("Nome Completo")
            t_cli = st.text_input("WhatsApp (DDD + Número)")
            if st.form_submit_button("SALVAR CLIENTE"):
                conn.execute("INSERT INTO clientes (nome, telefone) VALUES (?,?)", (n_cli, t_cli))
                conn.commit(); st.success("Cadastrado!"); st.rerun()

    with tab_srv:
        with st.form("form_servico"):
            n_srv = st.text_input("Nome do Serviço (ex: Corte)")
            p_srv = st.number_input("Valor (R$)", min_value=0.0, step=5.0)
            if st.form_submit_button("SALVAR SERVIÇO"):
                conn.execute("INSERT INTO servicos (nome, preco) VALUES (?,?)", (n_srv, p_srv))
                conn.commit(); st.success("Serviço Salvo!"); st.rerun()

    with tab_fin:
        with st.form("form_caixa"):
            desc_cx = st.text_input("Descrição da Despesa/Entrada")
            val_cx = st.number_input("Valor R$", min_value=0.0)
            tipo_cx = st.selectbox("Tipo", ["Entrada", "Saída"])
            if st.form_submit_button("LANÇAR NO CAIXA"):
                conn.execute("INSERT INTO caixa (descricao, valor, tipo, data) VALUES (?,?,?,?)", (desc_cx, val_cx, tipo_cx, hoje_str))
                conn.commit(); st.success("Lançado!"); st.rerun()

# ================= 5. LISTA DE ATENDIMENTOS E IA =================
with col_visualizacao:
    st.subheader("📋 Próximos Atendimentos")
    q = """
        SELECT a.id, c.nome, c.telefone, s.nome as serv, s.preco, a.data, a.hora 
        FROM agenda a 
        JOIN clientes c ON c.id=a.cliente_id 
        JOIN servicos s ON s.id=a.servico_id 
        WHERE a.status='Pendente' ORDER BY a.data, a.hora
    """
    df_lista = pd.read_sql(q, conn)
    
    if df_lista.empty:
        st.info("Nenhum atendimento pendente para exibir.")
    else:
        for _, r in df_lista.iterrows():
            # Formatação de data brasileira na lista
            data_formatada = datetime.strptime(r.data, '%Y-%m-%d').strftime('%d/%m/%Y')
            with st.expander(f"📌 {data_formatada} às {r.hora[:5]} - {r.nome}"):
                col_info, col_btn = st.columns([2, 1])
                col_info.write(f"**Serviço:** {r.serv} | **Valor:** R$ {r.preco:.2f}")
                
                # Botão WhatsApp
                msg = urllib.parse.quote(f"Olá {r.nome}, confirmamos seu horário no {CLIENTES_CONFIG[st.session_state.u_id]['nome']} para dia {data_formatada} às {r.hora[:5]}.")
                col_info.markdown(f'<a href="https://wa.me/{r.telefone}?text={msg}" class="wa-btn">📱 Confirmar via WhatsApp</a>', unsafe_allow_html=True)
                
                if col_btn.button(f"Concluir ✅", key=f"btn_{r.id}"):
                    conn.execute("UPDATE agenda SET status='Concluído' WHERE id=?", (r.id,))
                    conn.execute("INSERT INTO caixa (descricao, valor, tipo, data) VALUES (?,?,?,?)", (f"Serviço: {r.serv} ({r.nome})", r.preco, "Entrada", hoje_str))
                    conn.commit(); st.rerun()

# ================= 6. CONSULTORIA IA VIVV =================
st.markdown("---")
st.subheader("💬 Vivv AI: Inteligência de Negócio")
if "chat_history" not in st.session_state: st.session_state.chat_history = []

for m in st.session_state.chat_history:
    with st.chat_message(m["role"]): st.write(m["content"])

if prompt_user := st.chat_input("Como posso melhorar meu lucro este mês?"):
    st.session_state.chat_history.append({"role": "user", "content": prompt_user})
    with st.chat_message("user"): st.write(prompt_user)
    
    with st.chat_message("assistant"):
        contexto = f"Empresa: {CLIENTES_CONFIG[st.session_state.u_id]['nome']}. Faturamento: {entradas}. Lucro: {lucro_liquido}. Clientes: {clis_count}. Pergunta: {prompt_user}"
        try:
            client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
            response = client.chat.completions.create(model="gpt-5-mini", messages=[{"role":"user", "content": contexto}])
            resp_texto = response.choices[0].message.content
        except:
            resp_texto = "🤖 IA Offline. Verifique sua OpenAI API Key nos Secrets do Streamlit."
        
        st.write(resp_texto)
        st.session_state.chat_history.append({"role": "assistant", "content": resp_texto})
