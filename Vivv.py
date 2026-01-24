import streamlit as st
import sqlite3
import pandas as pd
import openai
import urllib.parse
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime

# ================= 1. CONFIGURAÇÃO DA PÁGINA & ESTILO NEON =================
st.set_page_config(page_title="Vivv Business AI", layout="wide", page_icon="💈")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700&display=swap');
    .stApp { background-color: #000505; color: #e0fbfc; font-family: 'Plus Jakarta Sans', sans-serif; }
    [data-testid="stSidebar"] { background-color: #000808; border-right: 1px solid #00f2ff; }
    
    /* Cards Neon Dinâmicos */
    .neon-card {
        background: rgba(0, 20, 20, 0.6);
        border: 1px solid #00f2ff;
        border-radius: 20px;
        padding: 25px;
        box-shadow: 0 0 15px rgba(0, 242, 255, 0.1);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    .neon-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 0 25px rgba(0, 242, 255, 0.3);
        border-color: #ff007f; /* Brilho muda ao passar o mouse */
    }
    
    .metric-label { color: #8E8E93; font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; }
    .metric-value { color: #FFFFFF; font-size: 32px; font-weight: 700; text-shadow: 0 0 10px rgba(255,255,255,0.2); }
    h1, h2, h3 { color: #00f2ff; text-shadow: 0 0 10px #00f2ff; }
    
    .wa-btn {
        background: linear-gradient(45deg, #25D366, #128C7E);
        color: white !important; padding: 12px; border-radius: 12px;
        text-align: center; font-weight: bold; text-decoration: none;
        display: block; margin-top: 10px; box-shadow: 0 4px 15px rgba(37, 211, 102, 0.3);
    }
</style>
""", unsafe_allow_html=True)

# ================= 2. CONTROLE DE ACESSOS E DB =================
CLIENTES_CONFIG = {
    "barber_nunes": {"db": "nunes.db", "nome": "Barbearia do Nunes", "senha": "123"},
    "lucas": {"db": "lucas.db", "nome": "Vivv Lab Master", "senha": "123"}
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

# ================= 3. INTEGRAÇÃO INTELIGÊNCIA ARTIFICIAL =================
def consultar_ia(contexto):
    try:
        client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        response = client.chat.completions.create(
            model="gpt-5-mini",
            messages=[
                {"role": "system", "content": "Você é o Vivv Business AI. Analise os dados financeiros e de agenda e dê conselhos estratégicos curtos e práticos para o dono do negócio."},
                {"role": "user", "content": contexto}
            ]
        )
        return response.choices[0].message.content
    except:
        return "🤖 IA Offline. Verifique sua API Key nos Secrets."

# ================= 4. COMPONENTES VISUAIS =================
def render_neon_metric(label, value, color="#00f2ff"):
    st.markdown(f"""
        <div class="neon-card">
            <div style="width: 40px; height: 4px; background: {color}; border-radius: 10px; margin-bottom: 15px;"></div>
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
        </div>
    """, unsafe_allow_html=True)

def format_moeda(v):
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# ================= 5. LÓGICA DO APP =================
def main():
    if "auth" not in st.session_state:
        # TELA DE LOGIN ESTILIZADA
        st.markdown("<br><br><div style='text-align:center;'><h1>🧬 VIVV BUSINESS AI</h1><p>Acesse seu Gêmeo Digital Corporativo</p></div>", unsafe_allow_html=True)
        _, col_login, _ = st.columns([1, 1, 1])
        with col_login:
            u = st.text_input("ID do Estabelecimento")
            p = st.text_input("Senha de Acesso", type="password")
            if st.button("AUTENTICAR SISTEMA"):
                if u in CLIENTES_CONFIG and CLIENTES_CONFIG[u]["senha"] == p:
                    st.session_state.auth, st.session_state.u_id = True, u
                    st.session_state.db_p = DBS_DIR / CLIENTES_CONFIG[u]['db']
                    init_db(st.session_state.db_p)
                    st.rerun()
                else: st.error("Acesso negado.")
    else:
        db_p = st.session_state.db_p
        info = CLIENTES_CONFIG[st.session_state.u_id]
        
        # HEADER
        c_h1, c_h2 = st.columns([4, 1])
        c_h1.title(f"💈 {info['nome']}")
        if c_h2.button("LOGOUT"):
            st.session_state.clear()
            st.rerun()

        # CÁLCULO DE MÉTRICAS REAIS
        conn = sqlite3.connect(db_p)
        clis = pd.read_sql("SELECT COUNT(*) FROM clientes", conn).iloc[0,0]
        df_cx = pd.read_sql("SELECT valor, tipo FROM caixa", conn)
        ent = df_cx[df_cx.tipo=="Entrada"]["valor"].sum() if not df_cx.empty else 0
        sai = df_cx[df_cx.tipo=="Saída"]["valor"].sum() if not df_cx.empty else 0
        lucro = ent - sai
        hoje = str(datetime.now().date())
        ag_hoje = pd.read_sql(f"SELECT COUNT(*) FROM agenda WHERE data='{hoje}'", conn).iloc[0,0]

        # DASHBOARD NEON
        m1, m2, m3, m4 = st.columns(4)
        with m1: render_neon_metric("Clientes", f"{clis}")
        with m2: render_neon_metric("Receita", format_moeda(ent), "#10B981")
        with m3: render_neon_metric("Lucro Líquido", format_moeda(lucro), "#00f2ff")
        with m4: render_neon_metric("Agenda Hoje", f"{ag_hoje}", "#ff007f")

        st.markdown("---")

        # OPERAÇÕES & AGENDA
        col_esq, col_dir = st.columns([1.3, 2])
        
        with col_esq:
            st.subheader("⚡ Ações Rápidas")
            t_ag, t_cli, t_srv = st.tabs(["Agendar", "+ Cliente", "+ Serviço"])
            
            with t_ag:
                clis_df = pd.read_sql("SELECT id, nome FROM clientes", conn)
                svs_df = pd.read_sql("SELECT id, nome, preco FROM servicos", conn)
                if not clis_df.empty and not svs_df.empty:
                    with st.form("add_ag"):
                        c_sel = st.selectbox("Quem?", clis_df["nome"])
                        s_sel = st.selectbox("O que?", svs_df["nome"])
                        d_in = st.date_input("Quando?")
                        h_in = st.time_input("Hora")
                        if st.form_submit_button("Confirmar"):
                            c_id = clis_df[clis_df.nome == c_sel].id.values[0]
                            s_id = svs_df[svs_df.nome == s_sel].id.values[0]
                            conn.execute("INSERT INTO agenda (cliente_id, servico_id, data, hora, status) VALUES (?,?,?,?, 'Pendente')", (int(c_id), int(s_id), str(d_in), str(h_in)))
                            conn.commit(); st.rerun()
                else: st.warning("Cadastre clientes e serviços primeiro.")

        with col_dir:
            st.subheader("📋 Próximos Atendimentos")
            df_lista = pd.read_sql("SELECT a.id, c.nome, c.telefone, s.nome as serv, s.preco, a.data, a.hora FROM agenda a JOIN clientes c ON c.id=a.cliente_id JOIN servicos s ON s.id=a.servico_id WHERE a.status='Pendente' ORDER BY a.data ASC LIMIT 5", conn)
            for _, r in df_lista.iterrows():
                with st.container():
                    st.markdown(f"""
                    <div class="neon-card" style="padding:15px; margin-bottom:10px; border-color: rgba(0,242,255,0.3)">
                        <b>{r.nome}</b> - {r.serv} <br>
                        <small>{r.data} às {r.hora[:5]}</small>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button(f"Concluir {r.nome}", key=f"btn_{r.id}"):
                        conn.execute("UPDATE agenda SET status='Concluído' WHERE id=?", (r.id,))
                        conn.execute("INSERT INTO caixa (descricao, valor, tipo, data) VALUES (?,?,?,?)", (f"Atend: {r.nome}", r.preco, "Entrada", hoje))
                        conn.commit(); st.rerun()

        # ================= 6. CHAT DE CONSULTORIA IA (O DIFERENCIAL) =================
        st.markdown("---")
        st.subheader("💬 Vivv AI: Consultor de Negócios")
        
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        for m in st.session_state.chat_history:
            with st.chat_message(m["role"]): st.write(m["content"])

        if p := st.chat_input("Pergunte: 'Como está meu faturamento?' ou 'Dê uma dica para atrair clientes'"):
            st.session_state.chat_history.append({"role": "user", "content": p})
            with st.chat_message("user"): st.write(p)
            
            with st.chat_message("assistant"):
                # Passa dados reais do banco para a IA analisar
                resumo = f"Dados atuais: Receita {ent}, Lucro {lucro}, Clientes {clis}, Agendamentos {ag_hoje}. Pergunta do dono: {p}"
                resp = consultar_ia(resumo)
                st.write(resp)
                st.session_state.chat_history.append({"role": "assistant", "content": resp})
        
        conn.close()

if __name__ == "__main__":
    main()
