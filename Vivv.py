import streamlit as st
import pandas as pd
import io
import json
import hashlib
import re
from datetime import datetime, timezone, timedelta
from google.cloud import firestore
from google.oauth2 import service_account
import time

# ================= CONFIGURAÇÕES =================

st.set_page_config(page_title="Vivv Pro", layout="wide", page_icon="🎯")
fuso_br = timezone(timedelta(hours=-3))

# ================= SEGURANÇA =================

SALT = "vivv_secure_2026"

def hash_senha(senha):
    senha = SALT + senha
    return hashlib.sha256(senha.encode()).hexdigest()

def email_valido(email):
    padrao = r"[^@]+@[^@]+\.[^@]+"
    return re.match(padrao, email)

def format_brl(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# ================= ESTILO PREMIUM =================

st.markdown("""
<style>
header, [data-testid="stHeader"], .stAppDeployButton {
    display: none !important;
}

.stApp {
    background: linear-gradient(180deg, #000205 0%, #000814 100%);
}

.block-container {
    padding-top: 60px !important;
    max-width: 95% !important;
}

.vivv-logo {
    position: fixed;
    top: 15px;
    left: 25px;
    color: #ffffff;
    font-size: 30px;
    font-weight: 900;
    z-index: 999999;
    letter-spacing: -1px;
    text-shadow: 0 0 12px rgba(0, 212, 255, 0.6);
}

.metric-card {
    background: linear-gradient(145deg, #000814, #001a2c);
    border: 1px solid rgba(0, 86, 179, 0.4);
    border-radius: 16px;
    padding: 20px;
    transition: all 0.3s ease;
}

.metric-card:hover {
    border: 1px solid #00d4ff;
    box-shadow: 0 0 20px rgba(0, 212, 255, 0.2);
    transform: translateY(-3px);
}

.metric-card small {
    color: #8899A6;
    font-weight: 600;
    text-transform: uppercase;
}

.metric-card h2 {
    margin: 0;
    font-size: 2rem !important;
    font-weight: 800;
}

div.stButton > button {
    border-radius: 10px !important;
    font-weight: 700 !important;
    background: linear-gradient(90deg, #00d4ff, #0099ff) !important;
    color: white !important;
    border: none !important;
}

[data-testid="stForm"] {
    background: rgba(255, 255, 255, 0.03) !important;
    border: 1px solid rgba(0, 212, 255, 0.15) !important;
    border-radius: 15px !important;
    padding: 15px !important;
}
</style>
""", unsafe_allow_html=True)

st.markdown(
    '<div class="vivv-logo">Vivv<span style="color:#00d4ff">.</span></div>',
    unsafe_allow_html=True
)


# ================= BANCO DE DADOS =================

@st.cache_resource
def init_db():
    try:
        firebase_raw = st.secrets["FIREBASE_DETAILS"]
        secrets_dict = json.loads(firebase_raw)
        creds = service_account.Credentials.from_service_account_info(secrets_dict)
        return firestore.Client(credentials=creds)
    except Exception as e:
        st.error(f"Erro ao conectar no banco: {e}")
        return None

db = init_db()
if not db:
    st.stop()

# ================= FUNÇÕES DE DADOS =================

def get_user(email):
    doc = db.collection("usuarios").document(email).get()
    return doc.to_dict() if doc.exists else None

def criar_usuario(dados):
    db.collection("usuarios").document(dados["email"]).set(dados)

# ================= SESSÃO =================

if "logado" not in st.session_state:
    st.session_state.logado = False

# ================= LOGIN E CADASTRO =================

if not st.session_state.logado:
    col_l, col_c, col_r = st.columns([1, 2, 1])

    with col_c:
        tab_login, tab_create = st.tabs(["🔑 LOGIN", "📝 CRIAR CONTA"])

        # LOGIN
        with tab_login:
            email = st.text_input("E-mail").lower().strip()
            senha = st.text_input("Senha", type="password")

            if st.button("Entrar"):
                if not email or not senha:
                    st.error("Preencha todos os campos.")
                else:
                    user = get_user(email)
                    if user and user["senha"] == hash_senha(senha):
                        st.session_state.logado = True
                        st.session_state.user_email = email
                        st.rerun()
                    else:
                        st.error("Credenciais inválidas.")

        # CADASTRO
        with tab_create:
            with st.form("cadastro"):
                st.subheader("Criar conta")

                username = st.text_input("Username")
                nome = st.text_input("Nome completo")
                email = st.text_input("E-mail").lower().strip()
                whatsapp = st.text_input("WhatsApp")
                negocio = st.text_input("Nome do negócio")
                tipo = st.selectbox("Tipo", ["Barbearia", "Salão", "Estética", "Outro"])
                senha = st.text_input("Senha", type="password")

                if st.form_submit_button("Cadastrar"):
                    if not all([username, nome, email, whatsapp, negocio, senha]):
                        st.error("Preencha todos os campos.")
                    elif not email_valido(email):
                        st.error("E-mail inválido.")
                    elif get_user(email):
                        st.error("E-mail já cadastrado.")
                    else:
                        criar_usuario({
                            "email": email,
                            "username": username,
                            "nome": nome,
                            "whatsapp": whatsapp,
                            "nome_negocio": negocio,
                            "tipo_negocio": tipo,
                            "senha": hash_senha(senha),
                            "ativo": False,
                            "criado_em": datetime.now(fuso_br)
                        })

                        st.success("Conta criada!")
                        time.sleep(1)
                        st.session_state.logado = True
                        st.session_state.user_email = email
                        st.rerun()

    st.stop()

# ================= USUÁRIO LOGADO =================

user_email = st.session_state.user_email
user_ref = db.collection("usuarios").document(user_email)
user_data = user_ref.get().to_dict()

if not user_data.get("ativo", False):
    st.warning("Conta aguardando pagamento.")
    st.link_button("Pagar agora", "https://buy.stripe.com/test_6oU4gB7Q4glM1JZ2Z06J200")
    if st.button("Sair"):
        st.session_state.logado = False
        st.rerun()
    st.stop()

# ================= CARREGAMENTO DE DADOS =================

@st.cache_data(ttl=60)
def load_data(email):
    ref = db.collection("usuarios").document(email)
    clientes = [{"id": d.id, **d.to_dict()} for d in ref.collection("meus_clientes").stream()]
    servicos = [{"id": d.id, **d.to_dict()} for d in ref.collection("meus_servicos").stream()]
    agenda = [{"id": d.id, **d.to_dict()} for d in ref.collection("minha_agenda").stream()]
    caixa = [d.to_dict() for d in ref.collection("meu_caixa").stream()]
    return clientes, servicos, agenda, caixa

clientes, servicos, agenda, caixa = load_data(user_email)

hoje_str = datetime.now(fuso_br).strftime('%d/%m/%Y')

faturamento = sum(x.get("valor", 0) for x in caixa if x.get("tipo") == "Entrada")
despesas = sum(x.get("valor", 0) for x in caixa if x.get("tipo") == "Saída")

# ================= DASHBOARD =================

col1, col2 = st.columns([5,1])

with col1:
    st.title(user_data.get("nome_negocio", "Vivv"))

with col2:
    if st.button("Logout"):
        st.session_state.logado = False
        st.rerun()

m1, m2, m3 = st.columns(3)

m1.metric("Clientes", len(clientes))
m2.metric("Faturamento", format_brl(faturamento))
m3.metric("Lucro", format_brl(faturamento - despesas))

st.divider()

# ================= CLIENTES =================

st.subheader("Clientes")

with st.form("novo_cliente", clear_on_submit=True):
    nome = st.text_input("Nome")
    tel = st.text_input("Telefone")
    if st.form_submit_button("Adicionar cliente"):
        if nome:
            user_ref.collection("meus_clientes").add({
                "nome": nome,
                "telefone": tel
            })
            st.cache_data.clear()
            st.rerun()

# ================= SERVIÇOS =================

st.subheader("Serviços")

with st.form("novo_servico", clear_on_submit=True):
    nome = st.text_input("Nome do serviço")
    preco = st.number_input("Preço", min_value=0.0)
    if st.form_submit_button("Adicionar serviço"):
        if nome:
            user_ref.collection("meus_servicos").add({
                "nome": nome,
                "preco": preco
            })
            st.cache_data.clear()
            st.rerun()

# ================= CAIXA =================

st.subheader("Caixa")

with st.form("novo_lancamento", clear_on_submit=True):
    desc = st.text_input("Descrição")
    valor = st.number_input("Valor", min_value=0.0)
    tipo = st.selectbox("Tipo", ["Entrada", "Saída"])
    if st.form_submit_button("Lançar"):
        user_ref.collection("meu_caixa").add({
            "descricao": desc,
            "valor": valor,
            "tipo": tipo,
            "data": hoje_str,
            "timestamp": datetime.now()
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
    st.download_button("Clique para baixar", buf.getvalue(), f"Vivv_{hoje_str}.xlsx")

