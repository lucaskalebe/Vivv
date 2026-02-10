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
    return hashlib.sha256((SALT + senha).encode()).hexdigest()

def email_valido(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def format_brl(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# ================= ESTILO =================

st.markdown("""
<style>
header, [data-testid="stHeader"], .stAppDeployButton { display: none !important; }
.stApp { background-color: #000205 !important; }
.block-container { padding-top: 40px !important; max-width: 95% !important; }
</style>
""", unsafe_allow_html=True)

# ================= BANCO DE DADOS =================

@st.cache_resource
def init_db():
    firebase_raw = st.secrets["FIREBASE_DETAILS"]
    secrets_dict = json.loads(firebase_raw)
    creds = service_account.Credentials.from_service_account_info(secrets_dict)
    return firestore.Client(credentials=creds)

db = init_db()

# ================= FUNÇÕES DE DADOS =================

def get_user(email):
    doc = db.collection("usuarios").document(email).get()
    return doc.to_dict() if doc.exists else None

def criar_usuario(dados):
    db.collection("usuarios").document(dados["email"]).set(dados)

def user_ref(email):
    return db.collection("usuarios").document(email)

# ================= SESSÃO =================

if "logado" not in st.session_state:
    st.session_state.logado = False

# ================= LOGIN / CADASTRO =================

if not st.session_state.logado:
    col_l, col_c, col_r = st.columns([1, 2, 1])

    with col_c:
        tab_login, tab_create = st.tabs(["🔑 LOGIN", "📝 CRIAR CONTA"])

        # LOGIN
        with tab_login:
            email = st.text_input("E-mail").lower().strip()
            senha = st.text_input("Senha", type="password")

            if st.button("Entrar"):
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
user_data = user_ref(user_email).get().to_dict()

if not user_data.get("ativo", False):
    st.warning("Conta aguardando pagamento.")
    st.link_button("Pagar agora", "LINK_DO_STRIPE_AQUI")
    if st.button("Sair"):
        st.session_state.logado = False
        st.rerun()
    st.stop()

# ================= CARREGAMENTO DE DADOS =================

@st.cache_data(ttl=60)
def load_data(email):
    ref = user_ref(email)
    clientes = [d.to_dict() for d in ref.collection("meus_clientes").stream()]
    servicos = [d.to_dict() for d in ref.collection("meus_servicos").stream()]
    agenda = [d.to_dict() for d in ref.collection("minha_agenda").stream()]
    caixa = [d.to_dict() for d in ref.collection("meu_caixa").stream()]
    return clientes, servicos, agenda, caixa

clientes, servicos, agenda, caixa = load_data(user_email)

# ================= MÉTRICAS =================

faturamento = sum(x.get("valor", 0) for x in caixa if x.get("tipo") == "Entrada")
despesas = sum(x.get("valor", 0) for x in caixa if x.get("tipo") == "Saída")

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
    if st.form_submit_button("Adicionar"):
        if nome:
            user_ref(user_email).collection("meus_clientes").add({
                "nome": nome,
                "telefone": tel
            })
            st.cache_data.clear()
            st.rerun()

# ================= SERVIÇOS =================

st.subheader("Serviços")
with st.form("novo_servico", clear_on_submit=True):
    nome = st.text_input("Nome")
    preco = st.number_input("Preço", min_value=0.0)
    if st.form_submit_button("Adicionar"):
        user_ref(user_email).collection("meus_servicos").add({
            "nome": nome,
            "preco": preco
        })
        st.cache_data.clear()
        st.rerun()
