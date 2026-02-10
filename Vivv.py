import streamlit as st
import pandas as pd
import io
import json
import hashlib
import re
from datetime import datetime, timezone, timedelta
from google.cloud import firestore
from google.oauth2 import service_account
import plotly.express as px
import time

# ================= CONFIGURAÇÕES =================

st.set_page_config(page_title="Vivv Pro", layout="wide", page_icon="🎯")
fuso_br = timezone(timedelta(hours=-3))

# ================= SEGURANÇA =================

SALT = "vivv_secure_2026"

def hash_senha(senha):
    return hashlib.sha256((SALT + senha).encode()).hexdigest()

def email_valido(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def format_brl(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# ================= ESTILO =================

st.markdown("""
<style>
header, [data-testid="stHeader"], .stAppDeployButton { display: none !important; }
.stApp { background: linear-gradient(180deg, #020617, #000000); }
.block-container { padding-top: 40px !important; max-width: 95% !important; }

.card {
    background: #0f172a;
    padding: 20px;
    border-radius: 16px;
    box-shadow: 0px 4px 20px rgba(0,0,0,0.4);
}

.metric {
    font-size: 28px;
    font-weight: bold;
}

.small {
    color: #9ca3af;
    font-size: 13px;
}
</style>
""", unsafe_allow_html=True)

# ================= BANCO =================

@st.cache_resource
def init_db():
    firebase_raw = st.secrets["FIREBASE_DETAILS"]
    secrets_dict = json.loads(firebase_raw)
    creds = service_account.Credentials.from_service_account_info(secrets_dict)
    return firestore.Client(credentials=creds)

db = init_db()

def user_ref(email):
    return db.collection("usuarios").document(email)

def get_user(email):
    doc = user_ref(email).get()
    return doc.to_dict() if doc.exists else None

def criar_usuario(dados):
    user_ref(dados["email"]).set(dados)

# ================= SESSÃO =================

if "logado" not in st.session_state:
    st.session_state.logado = False

# ================= LOGIN =================

if not st.session_state.logado:
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        tab1, tab2 = st.tabs(["🔑 Login", "Criar conta"])

        with tab1:
            email = st.text_input("E-mail").lower().strip()
            senha = st.text_input("Senha", type="password")

            if st.button("Entrar"):
                user = get_user(email)
                if user and user["senha"] == hash_senha(senha):
                    st.session_state.logado = True
                    st.session_state.user_email = email
                    st.rerun()
                else:
                    st.error("Credenciais inválidas")

        with tab2:
            with st.form("cadastro"):
                username = st.text_input("Username")
                nome = st.text_input("Nome")
                email = st.text_input("Email").lower().strip()
                negocio = st.text_input("Negócio")
                senha = st.text_input("Senha", type="password")

                if st.form_submit_button("Criar conta"):
                    criar_usuario({
                        "email": email,
                        "username": username,
                        "nome": nome,
                        "nome_negocio": negocio,
                        "senha": hash_senha(senha),
                        "ativo": True,
                        "criado_em": datetime.now(fuso_br)
                    })
                    st.success("Conta criada!")
                    time.sleep(1)
                    st.session_state.logado = True
                    st.session_state.user_email = email
                    st.rerun()
    st.stop()

# ================= USUÁRIO =================

user_email = st.session_state.user_email
user_data = get_user(user_email)

# ================= DADOS =================

@st.cache_data(ttl=60)
def load_data(email):
    ref = user_ref(email)
    clientes = [d.to_dict() for d in ref.collection("meus_clientes").stream()]
    servicos = [d.to_dict() for d in ref.collection("meus_servicos").stream()]
    caixa = [d.to_dict() for d in ref.collection("meu_caixa").stream()]
    return clientes, servicos, caixa

clientes, servicos, caixa = load_data(user_email)

faturamento = sum(x.get("valor",0) for x in caixa if x.get("tipo")=="Entrada")
despesas = sum(x.get("valor",0) for x in caixa if x.get("tipo")=="Saída")
lucro = faturamento - despesas

# ================= HEADER =================

col1, col2 = st.columns([6,1])

with col1:
    st.title(user_data.get("nome_negocio","Vivv Pro"))

with col2:
    if st.button("Logout"):
        st.session_state.logado = False
        st.rerun()

# ================= MÉTRICAS =================

m1, m2, m3 = st.columns(3)

with m1:
    st.markdown(f"""
    <div class="card">
        <div class="small">Clientes</div>
        <div class="metric">{len(clientes)}</div>
    </div>
    """, unsafe_allow_html=True)

with m2:
    st.markdown(f"""
    <div class="card">
        <div class="small">Faturamento</div>
        <div class="metric">{format_brl(faturamento)}</div>
    </div>
    """, unsafe_allow_html=True)

with m3:
    st.markdown(f"""
    <div class="card">
        <div class="small">Lucro</div>
        <div class="metric">{format_brl(lucro)}</div>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# ================= GRÁFICO =================

if caixa:
    df = pd.DataFrame(caixa)
    df["data"] = pd.to_datetime(df["data"], errors="coerce")
    df_group = df.groupby("data")["valor"].sum().reset_index()

    fig = px.line(df_group, x="data", y="valor", title="Faturamento ao longo do tempo")
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ================= CLIENTES E SERVIÇOS =================

col1, col2 = st.columns(2)

with col1:
    st.subheader("Clientes")

    with st.form("novo_cliente", clear_on_submit=True):
        nome = st.text_input("Nome do cliente")
        tel = st.text_input("Telefone")
        if st.form_submit_button("Adicionar cliente"):
            if nome:
                user_ref(user_email).collection("meus_clientes").add({
                    "nome": nome,
                    "telefone": tel
                })
                st.cache_data.clear()
                st.rerun()

    for c in clientes[:5]:
        st.markdown(f"• {c.get('nome','Cliente')}")

with col2:
    st.subheader("Serviços")

    with st.form("novo_servico", clear_on_submit=True):
        nome = st.text_input("Nome do serviço")
        preco = st.number_input("Preço", min_value=0.0)
        if st.form_submit_button("Adicionar serviço"):
            user_ref(user_email).collection("meus_servicos").add({
                "nome": nome,
                "preco": preco
            })
            st.cache_data.clear()
            st.rerun()

    for s in servicos[:5]:
        st.markdown(f"• {s.get('nome')} — {format_brl(s.get('preco',0))}")

st.divider()

# ================= CAIXA =================

st.subheader("Caixa")

with st.form("novo_lancamento", clear_on_submit=True):
    desc = st.text_input("Descrição")
    valor = st.number_input("Valor", min_value=0.0)
    tipo = st.selectbox("Tipo", ["Entrada","Saída"])
    if st.form_submit_button("Lançar"):
        user_ref(user_email).collection("meu_caixa").add({
            "descricao": desc,
            "valor": valor,
            "tipo": tipo,
            "data": datetime.now(fuso_br).strftime("%Y-%m-%d")
        })
        st.cache_data.clear()
        st.rerun()

# ================= EXPORTAÇÃO =================

if st.button("Baixar relatório Excel"):
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine='xlsxwriter') as writer:
        if clientes:
            pd.DataFrame(clientes).to_excel(writer, sheet_name='Clientes')
        if caixa:
            pd.DataFrame(caixa).to_excel(writer, sheet_name='Financeiro')
    st.download_button("Clique para baixar", buf.getvalue(), "relatorio.xlsx")
