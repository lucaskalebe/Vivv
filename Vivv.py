import streamlit as st
import pandas as pd
import io
import json
import hashlib
import plotly.express as px
from datetime import datetime, timezone, timedelta
from google.cloud import firestore
from google.oauth2 import service_account
import time

# ================= 1. CONFIGURAÇÕES TÉCNICAS E ESTILO =================

st.set_page_config(page_title="Vivv Pro v2", layout="wide", page_icon="🎯")
fuso_br = timezone(timedelta(hours=-3))

def hash_senha(senha):
    return hashlib.sha256(str.encode(senha)).hexdigest()

def format_brl(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

st.markdown("""
<style>
    header, [data-testid="stHeader"], .stAppDeployButton { display: none !important; }
    .stApp { background-color: #000205 !important; }
    .block-container { padding-top: 50px !important; max-width: 95% !important; }
    .vivv-logo {
        position: fixed; top: 15px; left: 25px;
        color: #ffffff; font-size: 32px; font-weight: 900;
        z-index: 999999; letter-spacing: -1px;
        text-shadow: 0 0 10px rgba(0, 212, 255, 0.5);
    }
    .metric-card {
        background: linear-gradient(145deg, #000814, #001a2c);
        border: 1px solid rgba(0, 86, 179, 0.4);
        border-radius: 16px; padding: 20px;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background-color: rgba(255,255,255,0.05);
        border-radius: 8px 8px 0 0;
        padding: 10px 20px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="vivv-logo">Vivv<span style="color:#00d4ff">.</span></div>', unsafe_allow_html=True)

# ================= 2. BANCO DE DADOS (FIRESTORE) =================
@st.cache_resource
def init_db():
    try:
        firebase_raw = st.secrets["FIREBASE_DETAILS"]
        secrets_dict = json.loads(firebase_raw)
        creds = service_account.Credentials.from_service_account_info(secrets_dict)
        return firestore.Client(credentials=creds)
    except Exception as e:
        st.error(f"Erro na conexão: {e}")
        return None

db = init_db()

# ================= 3. PAGAMENTO (STRIPE LINK) =================
STRIPE_CHECKOUT_URL = "https://buy.stripe.com/test_6oU4gB7Q4glM1JZ2Z06J200"

# ================= 4. AUTENTICAÇÃO E CADASTRO EM 2 ETAPAS =================
if "logado" not in st.session_state: st.session_state.logado = False

if not st.session_state.logado:
    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        st.markdown("<br><br>", unsafe_allow_html=True)
        tab_login, tab_cadastro = st.tabs(["🔑 LOGIN VIVV", "📝 CRIAR CONTA"])
        
        with tab_login:
            le = st.text_input("E-mail", key="l_email").lower().strip()
            ls = st.text_input("Senha", type="password", key="l_pass")
            if st.button("ACESSAR SISTEMA", use_container_width=True):
                u_doc = db.collection("usuarios").document(le).get()
                if u_doc.exists:
                    u_data = u_doc.to_dict()
                    if u_data.get("senha") == hash_senha(ls):
                        st.session_state.logado = True
                        st.session_state.user_email = le
                        st.rerun()
                    else: st.error("Senha incorreta.")
                else: st.error("Usuário não cadastrado.")

        with tab_cadastro:
            with st.form("form_reg"):
                st.subheader("Etapa 1: Dados do Negócio")
                u_id = st.text_input("Username (@exemplo)")
                n_emp = st.text_input("Nome da Empresa")
                e_cad = st.text_input("E-mail de Acesso").lower().strip()
                w_cad = st.text_input("WhatsApp")
                t_neg = st.selectbox("Tipo de Negócio", ["Barbearia", "Salão", "Estética", "Outro"])
                s_cad = st.text_input("Crie uma Senha Master", type="password")
                
                if st.form_submit_button("CADASTRAR E IR PARA PAGAMENTO 💳", use_container_width=True):
                    if e_cad and s_cad and u_id:
                        if db.collection("usuarios").document(e_cad).get().exists:
                            st.error("Este e-mail já possui cadastro.")
                        else:
                            # Salva Etapa 1
                            db.collection("usuarios").document(e_cad).set({
                                "username": u_id, "nome": n_emp, "whatsapp": w_cad,
                                "tipo_negocio": t_neg, "senha": hash_senha(s_cad),
                                "pago": False, "ativo": False, "plano": "pro",
                                "criado_em": datetime.now()
                            })
                            st.success("Cadastro realizado! Redirecionando para o Stripe...")
                            time.sleep(1)
                            # Redirecionamento automático
                            st.markdown(f'<a href="{STRIPE_CHECKOUT_URL}" target="_self" id="stripe_link"></a><script>document.getElementById("stripe_link").click();</script>', unsafe_allow_html=True)
                            st.stop()
    st.stop()

# ================= 5. MIDDLEWARE DE BLOQUEIO (GATEKEEPER) =================
user_ref = db.collection("usuarios").document(st.session_state.user_email)
user_data = user_ref.get().to_dict()

if not user_data.get("ativo", False):
    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.warning("### 💳 Conta Pendente de Ativação")
        st.info(f"Olá **{user_data.get('nome')}**, seu cadastro foi recebido! Para liberar o acesso total ao Vivv Pro, conclua o pagamento abaixo.")
        
        st.markdown(f"""
        **Resumo da Assinatura:**
        * Ativação Master: **R$ 300,00** (Taxa única)
        * Assinatura Pro: **R$ 49,90/mês**
        """)
        
        st.link_button("CONCLUIR PAGAMENTO NO STRIPE 🚀", STRIPE_CHECKOUT_URL, use_container_width=True)
        
        if st.button("Já paguei? Clique aqui para atualizar"):
            st.rerun()
            
        if st.button("Sair", type="secondary"):
            st.session_state.logado = False
            st.rerun()
    st.stop()

# ================= 6. CORE APP (SÓ RODA SE ATIVO == TRUE) =================
# ... [Seu código original do Dashboard continua aqui]
st.write(f"Bem-vindo ao Vivv Pro, {user_data.get('username')}!")
