import streamlit as st
import sqlite3
import pandas as pd
import openai
import urllib.parse
from pathlib import Path
from datetime import datetime

# ================= 1. DESIGN PREMIUM ULTRA NEON =================
st.set_page_config(page_title="Vivv Lab Master", layout="wide", page_icon="🧬")

st.markdown("""
<style>

.orange-neon {
    color: #ff9100;
    text-shadow: 0 0 10px rgba(255, 145, 0, 0.5);
    font-size: 2rem;
    font-weight: 800;
}

button.header-anchor {
    display: none !important;
}

    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    /* Fundo Deep Black */
    .stApp { background-color: #000205; color: #d1d1d1; font-family: 'Inter', sans-serif; }
    
    /* Cards de Métricas com Glow Azul */
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
    .neon-card:hover { 
        border-color: #00d4ff; 
        box-shadow: 0 0 30px rgba(0, 212, 255, 0.4);
        transform: scale(1.02);
    }
    
    /* Botões do Sistema */
    .stButton>button {
        background: #001d3d; color: #00d4ff; border: 1px solid #0056b3;
        border-radius: 8px; font-weight: bold; width: 100%; transition: 0.3s;
    }
    .stButton>button:hover { background: #003566; border-color: #00d4ff; color: white; box-shadow: 0 0 10px #00d4ff; }
    
    /* Botão WhatsApp Estilizado */
    .wa-link {
        background: linear-gradient(45deg, #25D366, #128C7E);
        color: white !important; padding: 10px 15px; border-radius: 10px;
        text-align: center; font-weight: bold; text-decoration: none; display: block;
        box-shadow: 0 4px 15px rgba(37, 211, 102, 0.3); transition: 0.3s;
        margin-bottom: 5px;
    }
    .wa-link:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(37, 211, 102, 0.5); }

    /* Tabelas e Abas */
    [data-testid="stDataFrame"] { border: 1px solid #0056b3; border-radius: 10px; background: #000814; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { background: #000814; border: 1px solid #003566; color: #00d4ff; border-radius: 5px; }
    
    h1, h2, h3 { color: #00d4ff; text-shadow: 0 0 8px rgba(0, 212, 255, 0.5); }
</style>
""", unsafe_allow_html=True)

# ================= 2. CORE: GERENCIAMENTO DE DADOS =================
CLIENTES_CONFIG = {
    "lucas": {"db": "lucas.db", "nome": "Vivv Lab Master", "senha": "123"},
    "barber_nunes": {"db": "nunes.db", "nome": "Barbearia do Nunes", "senha": "123"}
}

DBS_DIR = Path(__file__).parent / "dbs"
DBS_DIR.mkdir(exist_ok=True)

def init_db(db_path):
    """Inicializa as tabelas do banco de dados caso não existam."""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS clientes (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, telefone TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS servicos (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, preco REAL)')
    c.execute('CREATE TABLE IF NOT EXISTS agenda (id INTEGER PRIMARY KEY AUTOINCREMENT, cliente_id INTEGER, servico_id INTEGER, data TEXT, hora TEXT, status TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS caixa (id INTEGER PRIMARY KEY AUTOINCREMENT, descricao TEXT, valor REAL, tipo TEXT, data TEXT)')
    conn.commit()
    conn.close()

# Controle de Sessão / Login
if "auth" not in st.session_state:
    st.markdown("<br><br><h1 style='text-align:center;'>🧬 VIVV SYSTEM LOGIN</h1>", unsafe_allow_html=True)
    _, col_login, _ = st.columns([1, 0.8, 1])
    with col_login:
        user_input = st.text_input("ID do Estabelecimento")
        pass_input = st.text_input("Chave de Acesso", type="password")
        if st.button("AUTENTICAR"):
            if user_input in CLIENTES_CONFIG and CLIENTES_CONFIG[user_input]["senha"] == pass_input:
                st.session_state.auth = True
                st.session_state.u_id = user_input
                st.session_state.db_p = DBS_DIR / CLIENTES_CONFIG[user_input]['db']
                init_db(st.session_state.db_p)
                st.rerun()
            else:
                st.error("Credenciais inválidas.")
    st.stop()

# Conexão Global
conn = sqlite3.connect(st.session_state.db_p, check_same_thread=False)

# ================= 3. LÓGICA FINANCEIRA E DASHBOARD =================
def get_metrics():
    df_c = pd.read_sql("SELECT valor, tipo FROM caixa", conn)
    ent = df_c[df_c.tipo=="Entrada"]["valor"].sum() if not df_c.empty else 0
    sai = df_c[df_c.tipo=="Saída"]["valor"].sum() if not df_c.empty else 0
    cli_count = pd.read_sql("SELECT COUNT(*) FROM clientes", conn).iloc[0,0]
    hoje_iso = datetime.now().strftime('%Y-%m-%d')
    ag_count = pd.read_sql(f"SELECT COUNT(*) FROM agenda WHERE data='{hoje_iso}'", conn).iloc[0,0]
    return ent, sai, cli_count, ag_count

faturamento, despesas, total_clientes, agendados_hoje = get_metrics()

# Header e Logout
c_head, c_exit = st.columns([5, 1])
c_head.title(f"🧬 {CLIENTES_CONFIG[st.session_state.u_id]['nome']}")
if c_exit.button("SAIR / LOGOUT"):
    st.session_state.clear()
    st.rerun()

# Cards de Impacto
m1, m2, m3, m4 = st.columns(4)
with m1: st.markdown(f'<div class="neon-card"><small>BASE DE CLIENTES</small><h2>{total_clientes}</h2></div>', unsafe_allow_html=True)
with m2: st.markdown(f'<div class="neon-card"><small>RECEITA BRUTA</small><h2 style="color:#00d4ff">R$ {faturamento:,.2f}</h2></div>', unsafe_allow_html=True)
with m3: st.markdown(f'<div class="neon-card"><small>LUCRO LÍQUIDO</small><h2 style="color:#00ff88">R$ {(faturamento - despesas):,.2f}</h2></div>', unsafe_allow_html=True)
with m4: 
    st.markdown(f'''
        <div class="neon-card">
            <small>AGENDA HOJE</small>
            <div class="orange-neon">{ag_hoje}</div>
        </div>
    ''', unsafe_allow_html=True)

# ================= 4. PAINEL OPERACIONAL (CADASTROS) =================
st.write("---")
col_forms, col_display = st.columns([1.5, 2])

with col_forms:
    st.subheader("⚡ Painel de Controle")
    aba_ag, aba_cli, aba_srv, aba_cx = st.tabs(["📅 Agenda", "👤 Cliente", "💰 Serviço", "📉 Caixa"])
    
    with aba_ag:
        df_clis = pd.read_sql("SELECT id, nome FROM clientes", conn)
        df_servs = pd.read_sql("SELECT id, nome, preco FROM servicos", conn)
        with st.form("form_ag"):
            sel_cli = st.selectbox("Cliente", df_clis['nome']) if not df_clis.empty else None
            sel_srv = st.selectbox("Serviço", df_servs['nome']) if not df_servs.empty else None
            data_val = st.date_input("Data", format="DD/MM/YYYY")
            hora_val = st.time_input("Hora")
            if st.form_submit_button("REGISTRAR NA AGENDA"):
                if sel_cli and sel_srv:
                    cid = df_clis[df_clis.nome == sel_cli].id.values[0]
                    sid = df_servs[df_servs.nome == sel_srv].id.values[0]
                    conn.execute("INSERT INTO agenda (cliente_id, servico_id, data, hora, status) VALUES (?,?,?,?, 'Pendente')", (int(cid), int(sid), str(data_val), str(hora_val)))
                    conn.commit()
                    st.rerun()

    with aba_cli:
        with st.form("form_cli"):
            nome_c = st.text_input("Nome do Cliente")
            zap_c = st.text_input("WhatsApp (ex: 55119...)")
            if st.form_submit_button("CADASTRAR CLIENTE"):
                conn.execute("INSERT INTO clientes (nome, telefone) VALUES (?,?)", (nome_c, zap_c))
                conn.commit(); st.rerun()

    with aba_srv:
        with st.form("form_srv"):
            nome_s = st.text_input("Nome do Serviço")
            preco_s = st.number_input("Preço R$", min_value=0.0, step=5.0)
            if st.form_submit_button("CADASTRAR SERVIÇO"):
                conn.execute("INSERT INTO servicos (nome, preco) VALUES (?,?)", (nome_s, preco_s))
                conn.commit(); st.rerun()

    with aba_cx:
        with st.form("form_cx"):
            d_cx = st.text_input("Descrição")
            v_cx = st.number_input("Valor", min_value=0.0)
            t_cx = st.selectbox("Tipo", ["Entrada", "Saída"])
            if st.form_submit_button("LANÇAR NO FLUXO"):
                conn.execute("INSERT INTO caixa (descricao, valor, tipo, data) VALUES (?,?,?,?)", (d_cx, v_cx, t_cx, datetime.now().strftime('%Y-%m-%d')))
                conn.commit(); st.rerun()

# ================= 5. FILA DE ATENDIMENTO E WHATSAPP =================
with col_display:
    st.subheader("📋 Próximos Atendimentos")
    query = """
        SELECT a.id, c.nome, c.telefone, s.nome as serv, s.preco, a.data, a.hora 
        FROM agenda a 
        JOIN clientes c ON c.id=a.cliente_id 
        JOIN servicos s ON s.id=a.servico_id 
        WHERE a.status='Pendente' ORDER BY a.data, a.hora
    """
    fila = pd.read_sql(query, conn)
    
    if fila.empty:
        st.info("Nenhum atendimento pendente.")
    else:
        for _, r in fila.iterrows():
            dt_br = datetime.strptime(r.data, '%Y-%m-%d').strftime('%d/%m/%Y')
            with st.expander(f"📍 {dt_br} | {r.hora[:5]} - {r.nome}"):
                c_txt, c_btn1, c_btn2 = st.columns([2, 1, 1])
                c_txt.write(f"**Serviço:** {r.serv} | **Valor:** R$ {r.preco:.2f}")
                
                # Botão WhatsApp Link
                msg = urllib.parse.quote(f"Olá {r.nome}, confirmamos seu horário para o dia {dt_br} às {r.hora[:5]}!")
                c_txt.markdown(f'<a href="https://wa.me/{r.telefone}?text={msg}" class="wa-link">📱 Confirmar via WhatsApp</a>', unsafe_allow_html=True)
                
                if c_btn1.button("CONCLUIR", key=f"ok_{r.id}"):
                    conn.execute("UPDATE agenda SET status='Concluído' WHERE id=?", (r.id,))
                    conn.execute("INSERT INTO caixa (descricao, valor, tipo, data) VALUES (?,?,?,?)", (f"Atend: {r.nome}", r.preco, "Entrada", r.data))
                    conn.commit(); st.rerun()
                
                if c_btn2.button("CANCELAR", key=f"del_{r.id}"):
                    conn.execute("DELETE FROM agenda WHERE id=?", (r.id,))
                    conn.commit(); st.rerun()

# ================= 6. CENTRAL DE AUDITORIA (VIP DESIGN) =================
# ================= 6. CENTRAL DE AUDITORIA (CARDS EXPANSÍVEIS) =================
st.write("---")
st.markdown("### 🗄️ Central de Auditoria e Controle de Dados")

# Criando o respiro lateral
_, col_audit, _ = st.columns([0.05, 0.9, 0.05])

with col_audit:
    # Gap amplo para separação visual
    c_db1, c_db2 = st.columns(2, gap="large")

    with c_db1:
        # Expander que funciona como o 'clique' para abrir a gestão
        with st.expander("👥 CLIQUE PARA: GESTÃO DE CLIENTES", expanded=False):
            st.markdown("""
                <div style='background: rgba(0, 86, 179, 0.1); padding: 10px; border-radius: 10px; border-left: 5px solid #00d4ff; margin-bottom: 15px;'>
                    <small style='color: #00d4ff;'>Edite nomes ou telefones diretamente na tabela abaixo e salve.</small>
                </div>
            """, unsafe_allow_html=True)
            
            df_edit_clis = pd.read_sql("SELECT id, nome, telefone FROM clientes", conn)
            edited_clis = st.data_editor(
                df_edit_clis, 
                hide_index=True, 
                use_container_width=True, 
                key="ed_cli_v3",
                height=350 
            )
            
            if st.button("💾 SALVAR ALTERAÇÕES DE CLIENTES", use_container_width=True):
                try:
                    conn.execute("DELETE FROM clientes")
                    edited_clis.to_sql("clientes", conn, if_exists="append", index=False)
                    conn.commit()
                    st.success("Base de clientes atualizada!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")

    with c_db2:
        # Expander para o histórico financeiro
        with st.expander("📊 CLIQUE PARA: HISTÓRICO DE CAIXA", expanded=False):
            st.markdown("""
                <div style='background: rgba(255, 0, 127, 0.1); padding: 10px; border-radius: 10px; border-left: 5px solid #ff007f; margin-bottom: 15px;'>
                    <small style='color: #ff007f;'>Corrija valores, datas ou descrições de lançamentos passados.</small>
                </div>
            """, unsafe_allow_html=True)
            
            df_edit_cx = pd.read_sql("SELECT id, data, descricao, tipo, valor FROM caixa", conn)
            edited_cx = st.data_editor(
                df_edit_cx, 
                hide_index=True, 
                use_container_width=True, 
                key="ed_cx_v3",
                height=350
            )
            
            if st.button("💾 SALVAR ALTERAÇÕES DE CAIXA", use_container_width=True):
                try:
                    conn.execute("DELETE FROM caixa")
                    edited_cx.to_sql("caixa", conn, if_exists="append", index=False)
                    conn.commit()
                    st.success("Fluxo de caixa sincronizado!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")
                
# ================= 7. IA CONSULTORA DE NEGÓCIOS =================
st.write("---")
st.subheader("💬 Vivv AI: Estrategista de Negócios")
if "chat_log" not in st.session_state: st.session_state.chat_log = []

for m in st.session_state.chat_log:
    with st.chat_message(m["role"]): st.write(m["content"])

if prompt_ia := st.chat_input("Pergunte à IA sobre seu faturamento ou estratégias..."):
    st.session_state.chat_log.append({"role": "user", "content": prompt_ia})
    with st.chat_message("user"): st.write(prompt_ia)
    
    with st.chat_message("assistant"):
        contexto_ia = f"Estabelecimento: {CLIENTES_CONFIG[st.session_state.u_id]['nome']}. Receita: R${faturamento}. Lucro: R${faturamento-despesas}. Clientes: {total_clientes}. Pergunta: {prompt_ia}"
        try:
            client_ai = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
            res_ia = client_ai.chat.completions.create(model="gpt-4o-mini", messages=[{"role":"user", "content": contexto_ia}])
            texto_ia = res_ia.choices[0].message.content
        except:
            texto_ia = "🤖 IA Offline. Verifique sua OpenAI API Key nos Secrets."
        
        st.write(texto_ia)
        st.session_state.chat_log.append({"role": "assistant", "content": texto_ia})

# FIM DO CÓDIGO - ESTRUTURA COMPLETA





