import streamlit as st
import pandas as pd
import io
import json
import hashlib
import requests
import plotly.express as px
from datetime import datetime, timezone, timedelta
from google.cloud import firestore
from google.oauth2 import service_account
import time

# ================= 1. CONFIGURAÇÕES TÉCNICAS E ESTILO MASTER =================

st.set_page_config(page_title="Vivv Pro v2", layout="wide", page_icon="🎯")
fuso_br = timezone(timedelta(hours=-3))

def hash_senha(senha):
    return hashlib.sha256(str.encode(senha)).hexdigest()

def format_brl(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# Interface de Alto Nível (CSS Customizado)
st.markdown("""
<style>
    header, [data-testid="stHeader"], .stAppDeployButton { display: none !important; }
    .stApp { background-color: #000205 !important; }
    .block-container { padding-top: 50px !important; max-width: 95% !important; }
    
    .vivv-logo {
        position: fixed; top: 15px; left: 25px; color: #ffffff;
        font-size: 32px; font-weight: 900; letter-spacing: -1px; z-index: 999999;
        text-shadow: 0 0 14px rgba(0, 212, 255, 0.65);
    }

    .metric-card {
        background: linear-gradient(145deg, #000814, #001a2c);
        border: 1px solid rgba(0, 86, 179, 0.4);
        border-radius: 16px; padding: 20px;
    }
    .metric-card h2 { margin: 0; font-size: 2.2rem !important; font-weight: 800; }
    .ia-box {
        background: linear-gradient(90deg, rgba(0,212,255,0.1) 0%, rgba(121,40,202,0.1) 100%);
        border-left: 4px solid #00d4ff; padding: 20px; border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="vivv-logo">Vivv<span style="color:#00d4ff">.</span></div>', unsafe_allow_html=True)

# ================= 2. BANCO DE DADOS =================
@st.cache_resource
def init_db():
    try:
        secrets_dict = json.loads(st.secrets["FIREBASE_DETAILS"])
        creds = service_account.Credentials.from_service_account_info(secrets_dict)
        return firestore.Client(credentials=creds)
    except Exception as e:
        st.error(f"Erro Firebase: {e}"); st.stop()

db = init_db()

# ================= 3. AUTENTICAÇÃO =================
if "logado" not in st.session_state: 
    st.session_state.logado = False

if not st.session_state.logado:
    tab_l, tab_c = st.tabs(["🔑 LOGIN", "📝 CRIAR CONTA"])
    with tab_l:
        le = st.text_input("E-mail").lower().strip()
        ls = st.text_input("Senha", type="password")
        if st.button("ACESSAR"):
            u = db.collection("usuarios").document(le).get()
            if u.exists and u.to_dict().get("senha") == hash_senha(ls):
                st.session_state.logado = True
                st.session_state.user_email = le
                st.rerun()
            else: st.error("Dados incorretos.")
    with tab_c:
        with st.form("reg_novo"):
            n = st.text_input("Nome")
            e = st.text_input("E-mail").lower().strip()
            s = st.text_input("Senha", type="password")
            if st.form_submit_button("CADASTRAR"):
                if e and s:
                    db.collection("usuarios").document(e).set({
                        "nome": n, "senha": hash_senha(s), "pago": True,
                        "criado_em": datetime.now()
                    })
                    st.success("Criado! Vá para Login.")
    st.stop()

# Referência do usuário logado
user_ref = db.collection("usuarios").document(st.session_state.user_email)

# ================= 4. CARREGAMENTO DE DADOS =================
@st.cache_data(ttl=60)
def load_vivv_data(email):
    u = db.collection("usuarios").document(email)
    c = [{"id": d.id, **d.to_dict()} for d in u.collection("meus_clientes").stream()]
    s = [{"id": d.id, **d.to_dict()} for d in u.collection("meus_servicos").stream()]
    a = [{"id": d.id, **d.to_dict()} for d in u.collection("minha_agenda").where("status", "==", "Pendente").stream()]
    a = sorted(a, key=lambda x: x.get('hora', '00:00'))
    cx = [d.to_dict() for d in u.collection("meu_caixa").stream()]
    return c, s, a, cx

clis, srvs, agnd, cx_list = load_vivv_data(st.session_state.user_email)

# Cálculos
faturamento = sum([float(x.get('valor', 0)) for x in cx_list if x.get('tipo') == 'Entrada'])
despesas = sum([float(x.get('valor', 0)) for x in cx_list if x.get('tipo') == 'Saída'])
lucro = faturamento - despesas
cor_lucro = "#00ff88" if lucro >= 0 else "#ff4b4b"

# ================= 5. DASHBOARD =================
c_top1, c_top2 = st.columns([5,1])
c_top1.markdown(f"##### Bem vindo(a), <span style='color:#00d4ff'>{st.session_state.user_email}</span>.", unsafe_allow_html=True)
if c_top2.button("LOGOUT", use_container_width=True):
    st.session_state.logado = False
    st.rerun()

m1, m2, m3, m4 = st.columns(4)
m1.markdown(f'<div class="metric-card"><small>👥 Clientes</small><h2>{len(clis)}</h2></div>', unsafe_allow_html=True)
m2.markdown(f'<div class="metric-card"><small>💰 Total</small><h2 style="color:#00d4ff">{format_brl(faturamento)}</h2></div>', unsafe_allow_html=True)
m3.markdown(f'<div class="metric-card"><small>📈 Lucro</small><h2 style="color:{cor_lucro}">{format_brl(lucro)}</h2></div>', unsafe_allow_html=True)
m4.markdown(f'<div class="metric-card"><small>⏳ Agenda</small><h2 style="color:#ff9100">{len(agnd)}</h2></div>', unsafe_allow_html=True)

# ================= 6. OPERACIONAL =================
st.write("---")
col_l, col_r = st.columns([1.3, 1])

with col_l:
    st.markdown("### ⚡ Gestão")
    t1, t2, t3, t4 = st.tabs(["📅 Agenda", "👤 Clientes", "🛠️ Serviços", "💸 Caixa"])
    
    with t1:
        with st.form("form_ag", clear_on_submit=True):
            c_n = st.selectbox("Cliente", [c['nome'] for c in clis]) if clis else st.warning("Cadastre um cliente primeiro.")
            s_n = st.selectbox("Serviço", [s['nome'] for s in srvs]) if srvs else st.warning("Cadastre um serviço primeiro.")
            d_v = st.date_input("Data", format="DD/MM/YYYY")
            h_v = st.time_input("Hora")
            if st.form_submit_button("AGENDAR", use_container_width=True):
                p_s = next((s['preco'] for s in srvs if s['nome'] == s_n), 0)
                user_ref.collection("minha_agenda").add({
                    "cliente": c_n, "servico": s_n, "preco": p_s, "status": "Pendente",
                    "data": d_v.strftime('%d/%m/%Y'), "hora": h_v.strftime('%H:%M'), "timestamp": datetime.now()
                })
                st.cache_data.clear(); st.rerun()

    with t2:
        with st.form("form_cli", clear_on_submit=True):
            nc = st.text_input("Nome")
            tc = st.text_input("WhatsApp")
            if st.form_submit_button("CADASTRAR"):
                user_ref.collection("meus_clientes").add({"nome": nc, "telefone": tc})
                st.cache_data.clear(); st.rerun()

# (Restante do seu código de Serviços e Caixa segue a mesma lógica...)

# ================= 8. VIVV AI =================
st.write("---")
st.subheader("💬 Vivv AI: Consultoria")
prompt_ia = st.text_input("Pergunta:", placeholder="Ex: Como crescer meu faturamento?", key="ia_input_master")

sucesso = False 

if st.button("ANALISAR COM IA", use_container_width=True) and prompt_ia:
    if "GOOGLE_API_KEY" not in st.secrets:
        st.error("Chave API ausente nos Secrets.")
    else:
        api_key = st.secrets["GOOGLE_API_KEY"]
        modelos = ["gemini-2.0-flash", "gemini-1.5-flash"]
        
        with st.spinner("Analisando..."):
            for modelo in modelos:
                if sucesso: break
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={api_key}"
                payload = {"contents": [{"parts": [{"text": f"Dê uma dica curta. Clientes: {len(clis)}. Fat: {faturamento}. Pergunta: {prompt_ia}"}]}]}
                
                try:
                    res = requests.post(url, json=payload, timeout=20)
                    if res.status_code == 200:
                        txt = res.json()["candidates"][0]["content"]["parts"][0]["text"]
                        st.markdown(f'<div class="ia-box"><b>AI ({modelo}):</b><br><br>{txt}</div>', unsafe_allow_html=True)
                        sucesso = True
                except: continue

        if not sucesso:
            st.error("IA temporariamente fora do ar.")

st.markdown("<br><p style='text-align:center; color:#555;'>Vivv Pro © 2026</p>", unsafe_allow_html=True)
