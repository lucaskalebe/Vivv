

import streamlit as st
import sqlite3
import pandas as pd
import openai
import urllib.parse
from pathlib import Path
from datetime import datetime

# ================= 1. CONFIGURAÇÃO E DESIGN ULTRA NEON =================
st.set_page_config(page_title="Vivv", layout="wide", page_icon="🧬")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    /* REMOVE SÍMBOLOS DE ÂNCORA E LINKS DOS TÍTULOS */
    button.header-anchor, a.header-anchor, .header-anchor { display: none !important; }

    /* FUNDO DEEP BLACK */
    .stApp { background-color: #000205; color: #d1d1d1; font-family: 'Inter', sans-serif; }
    
    /* CARDS COM GLOW AZUL */
    .neon-card {
        background: linear-gradient(145deg, #000814, #001220);
        border: 1px solid #0056b3;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 0 20px rgba(0, 86, 179, 0.2);
        transition: all 0.4s ease;
        text-align: center;
        margin-bottom: 10px;
    }

    /* NÚMERO LARANJA NEON PARA AGENDA */
    .orange-neon {
        color: #ff9100 !important;
        text-shadow: 0 0 15px rgba(255, 145, 0, 0.7);
        font-size: 2.5rem;
        font-weight: 800;
        margin-top: 5px;
    }
    
    /* BOTÃO WHATSAPP */
    .wa-link {
        background: linear-gradient(45deg, #25D366, #128C7E);
        color: white !important; padding: 10px 15px; border-radius: 10px;
        text-align: center; font-weight: bold; text-decoration: none; display: block;
        box-shadow: 0 4px 15px rgba(37, 211, 102, 0.3); transition: 0.3s;
    }
    .wa-link:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(37, 211, 102, 0.5); }

    h1, h2, h3 { color: #00d4ff; text-shadow: 0 0 8px rgba(0, 212, 255, 0.5); }
    
    /* ESTILO DAS TABELAS E INPUTS */
    [data-testid="stDataFrame"] { border: 1px solid #0056b3; border-radius: 10px; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background: #000814; border: 1px solid #003566; color: #00d4ff; border-radius: 5px; padding: 10px; }
</style>
""", unsafe_allow_html=True)

# ================= 2. CORE: GERENCIAMENTO DE DADOS =================
DBS_DIR = Path(__file__).parent / "dbs"
DBS_DIR.mkdir(exist_ok=True)
db_path = DBS_DIR / "vivv.db"

def init_db():
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS clientes (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, telefone TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS servicos (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, preco REAL)')
    c.execute('CREATE TABLE IF NOT EXISTS agenda (id INTEGER PRIMARY KEY AUTOINCREMENT, cliente_id INTEGER, servico_id INTEGER, data TEXT, hora TEXT, status TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS caixa (id INTEGER PRIMARY KEY AUTOINCREMENT, descricao TEXT, valor REAL, tipo TEXT, data TEXT)')
    conn.commit()
    conn.close()

init_db()
conn = sqlite3.connect(db_path, check_same_thread=False)

# ================= 3. CÁLCULO DE MÉTRICAS (RESOLVENDO NAMEERROR) =================
# Definimos as variáveis antes de qualquer exibição visual
hoje_iso = datetime.now().strftime('%Y-%m-%d')

try:
    total_clientes = pd.read_sql("SELECT COUNT(*) FROM clientes", conn).iloc[0,0]
    faturamento = pd.read_sql("SELECT SUM(valor) FROM caixa WHERE tipo='Entrada'", conn).iloc[0,0] or 0.0
    despesas = pd.read_sql("SELECT SUM(valor) FROM caixa WHERE tipo='Saída'", conn).iloc[0,0] or 0.0
    
    # IMPORTANTE: Contamos apenas os PENDENTES para o número atualizar ao concluir
    ag_hoje = pd.read_sql(f"SELECT COUNT(*) FROM agenda WHERE data='{hoje_iso}' AND status='Pendente'", conn).iloc[0,0]
except:
    total_clientes, faturamento, despesas, ag_hoje = 0, 0.0, 0.0, 0.0

# ================= 4. HEADER E DASHBOARD =================
col_title, col_logout = st.columns([5, 1])
with col_title:
    st.title("Vivv")

if col_logout.button("SAIR / LOGOUT"):
    st.cache_data.clear()
    st.rerun()

# Layout dos Cards
m1, m2, m3, m4 = st.columns(4)

with m1:
    st.markdown(f'<div class="neon-card"><small>BASE DE CLIENTES</small><h2>{total_clientes}</h2></div>', unsafe_allow_html=True)

with m2:
    st.markdown(f'<div class="neon-card"><small>RECEITA BRUTA</small><h2 style="color:#00d4ff">R$ {faturamento:,.2f}</h2></div>', unsafe_allow_html=True)

with m3:
    st.markdown(f'<div class="neon-card"><small>LUCRO LÍQUIDO</small><h2 style="color:#00ff88">R$ {faturamento - despesas:,.2f}</h2></div>', unsafe_allow_html=True)

with m4:
    # Número Laranja Neon e Dinâmico
    st.markdown(f'''
        <div class="neon-card">
            <small>AGENDA HOJE</small>
            <div class="orange-neon">{ag_hoje}</div>
        </div>
    ''', unsafe_allow_html=True)

# ================= 5. PAINEL OPERACIONAL =================
st.write("---")
col_ops, col_fila = st.columns([1.5, 2])

with col_ops:
    st.subheader("⚡ Painel de Controle")
    aba_ag, aba_cli, aba_srv, aba_cx = st.tabs(["📅 Agenda", "👤 Cliente", "💰 Serviço", "📉 Caixa"])
    
    with aba_ag:
        df_clis = pd.read_sql("SELECT id, nome FROM clientes", conn)
        df_servs = pd.read_sql("SELECT id, nome, preco FROM servicos", conn)
        
        with st.form("add_agenda"):
            cli_sel = st.selectbox("Cliente", df_clis['nome']) if not df_clis.empty else None
            srv_sel = st.selectbox("Serviço", df_servs['nome']) if not df_servs.empty else None
            dt_ag = st.date_input("Data do Atendimento", format="DD/MM/YYYY")
            hr_ag = st.time_input("Hora")
            if st.form_submit_button("CONFIRMAR AGENDAMENTO"):
                if cli_sel and srv_sel:
                    cid = df_clis[df_clis.nome == cli_sel].id.values[0]
                    sid = df_servs[df_servs.nome == srv_sel].id.values[0]
                    conn.execute("INSERT INTO agenda (cliente_id, servico_id, data, hora, status) VALUES (?,?,?,?, 'Pendente')",
                                 (int(cid), int(sid), str(dt_ag), str(hr_ag)))
                    conn.commit()
                    st.rerun()

    with aba_cli:
        with st.form("add_cli"):
            n_cli = st.text_input("Nome Completo")
            t_cli = st.text_input("WhatsApp (ex: 55119...)")
            if st.form_submit_button("CADASTRAR CLIENTE"):
                conn.execute("INSERT INTO clientes (nome, telefone) VALUES (?,?)", (n_cli, t_cli))
                conn.commit()
                st.rerun()

    with aba_srv:
        with st.form("add_srv"):
            n_srv = st.text_input("Nome do Serviço")
            p_srv = st.number_input("Preço (R$)", min_value=0.0)
            if st.form_submit_button("CADASTRAR SERVIÇO"):
                conn.execute("INSERT INTO servicos (nome, preco) VALUES (?,?)", (n_srv, p_srv))
                conn.commit()
                st.rerun()

    with aba_cx:
        with st.form("add_caixa"):
            desc_cx = st.text_input("Descrição do Lançamento")
            val_cx = st.number_input("Valor", min_value=0.0)
            tipo_cx = st.selectbox("Tipo", ["Saída", "Entrada"])
            if st.form_submit_button("REGISTRAR NO CAIXA"):
                conn.execute("INSERT INTO caixa (descricao, valor, tipo, data) VALUES (?,?,?,?)",
                             (desc_cx, val_cx, tipo_cx, hoje_iso))
                conn.commit()
                st.rerun()

# ================= 6. FILA DE ATENDIMENTOS E WHATSAPP =================
with col_fila:
    st.subheader("📋 Próximos Atendimentos")
    query_fila = """
        SELECT a.id, c.nome, c.telefone, s.nome as serv, s.preco, a.data, a.hora 
        FROM agenda a 
        JOIN clientes c ON c.id=a.cliente_id 
        JOIN servicos s ON s.id=a.servico_id 
        WHERE a.status='Pendente' ORDER BY a.data, a.hora
    """
    fila_df = pd.read_sql(query_fila, conn)
    
    if fila_df.empty:
        st.info("Nenhum atendimento pendente para hoje.")
    else:
        for _, r in fila_df.iterrows():
            dt_br = datetime.strptime(r.data, '%Y-%m-%d').strftime('%d/%m/%Y')
            with st.expander(f"📍 {dt_br} às {r.hora[:5]} | {r.nome}"):
                c1, c2, c3 = st.columns([2, 1, 1])
                c1.write(f"**{r.serv}** - R$ {r.preco:.2f}")
                
                # Link WhatsApp com mensagem automática
                msg = urllib.parse.quote(f"Olá {r.nome}, confirmamos seu horário para o dia {dt_br} às {r.hora[:5]}. Até logo 🤝")
                c1.markdown(f'<a href="https://wa.me/{r.telefone}?text={msg}" class="wa-link">📱 Confirmar via WhatsApp</a>', unsafe_allow_html=True)
                
                # BOTÃO CONCLUIR (Atualiza o contador Agenda Hoje)
                if c2.button("CONCLUIR ✅", key=f"concluir_{r.id}"):
                    conn.execute("UPDATE agenda SET status='Concluído' WHERE id=?", (r.id,))
                    conn.execute("INSERT INTO caixa (descricao, valor, tipo, data) VALUES (?,?,?,?)", 
                                 (f"Atendimento: {r.nome}", r.preco, "Entrada", hoje_iso))
                    conn.commit()
                    st.rerun()
                
                # BOTÃO CANCELAR
                if c3.button("CANCELAR ❌", key=f"cancelar_{r.id}"):
                    conn.execute("DELETE FROM agenda WHERE id=?", (r.id,))
                    conn.commit()
                    st.rerun()

# ================= 7. CENTRAL DE AUDITORIA (EXPANSÍVEL) =================
st.write("---")
st.markdown("### 🗄️ Central de Auditoria e Controle de Dados")

_, col_central, _ = st.columns([0.05, 0.9, 0.05])

with col_central:
    ca1, ca2 = st.columns(2, gap="large")
    
    with ca1:
        with st.expander("👥 GESTÃO DE CLIENTES (Clique para editar)"):
            df_aud_cli = pd.read_sql("SELECT id, nome, telefone FROM clientes", conn)
            edit_cli = st.data_editor(df_aud_cli, hide_index=True, use_container_width=True, key="edit_cli_table")
            if st.button("💾 SALVAR ALTERAÇÕES CLIENTES"):
                conn.execute("DELETE FROM clientes")
                edit_cli.to_sql("clientes", conn, if_exists="append", index=False)
                conn.commit()
                st.rerun()

    with ca2:
        with st.expander("📊 HISTÓRICO DE CAIXA (Clique para editar)"):
            df_aud_cx = pd.read_sql("SELECT id, data, descricao, tipo, valor FROM caixa", conn)
            edit_cx = st.data_editor(df_aud_cx, hide_index=True, use_container_width=True, key="edit_cx_table")
            if st.button("💾 SALVAR ALTERAÇÕES CAIXA"):
                conn.execute("DELETE FROM caixa")
                edit_cx.to_sql("caixa", conn, if_exists="append", index=False)
                conn.commit()
                st.rerun()


# ================= 8. IA STRATEGIST (GOOGLE GEMINI) =================
# ================= 8. IA STRATEGIST (GOOGLE GEMINI) =================
import google.generativeai as genai

st.write("---")
st.subheader("💬 Vivv AI: Consultor de Negócios")

if "chat_history" not in st.session_state: 
    st.session_state.chat_history = []

for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]): 
        st.write(msg["content"])

if prompt := st.chat_input("Como posso melhorar meu lucro hoje?"):
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"): 
        st.write(prompt)
    
    with st.chat_message("assistant"):
        try:
            # Força a configuração limpa
            genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
            
            # Mudança crucial: usamos apenas o nome do modelo sem prefixos
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            # Dados do seu dashboard
            lucro_atual = faturamento - despesas
            contexto = (
                f"Analise como consultor: Clientes={total_clientes}, "
                f"Faturamento=R${faturamento}, Lucro=R${lucro_atual}. "
                f"Responda à pergunta: {prompt}"
            )
            
            # Chamada direta
            response = model.generate_content(contexto)
            resp_text = response.text
            
        except Exception as e:
            # Se o erro 404 persistir, vamos depurar o que a sua chave permite
            resp_text = f"❌ Erro de Versão: {str(e)}. Tente atualizar o requirements.txt para google-generativeai>=0.7.2"
            
        st.write(resp_text)
        st.session_state.chat_history.append({"role": "assistant", "content": resp_text})
