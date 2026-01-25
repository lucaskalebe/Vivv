

import streamlit as st
import pandas as pd
import urllib.parse
from datetime import datetime, timezone, timedelta
from google.cloud import firestore
from google.oauth2 import service_account
import json
import hashlib
import io
import requests
import plotly.express as px

# --- Configurações de Fuso ---
fuso_br = timezone(timedelta(hours=-3))

st.set_page_config(
    page_title="Vivv Pro | Ultra UX",
    layout="wide",
    page_icon="🚀",
    initial_sidebar_state="collapsed"
)

# ================= 1. ENGINE VISUAL VIVV 2026 (UI/UX 3000%) =================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;700;900&display=swap');

    /* Reset Geral */
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Inter', sans-serif;
        background: radial-gradient(circle at top right, #001220, #000205) !important;
    }
    header, [data-testid="stHeader"], .stAppDeployButton { display: none !important; }
    .block-container { padding-top: 5rem !important; }

    /* Logo Animado 3D */
    .vivv-logo-box {
        position: fixed; top: 20px; left: 30px; z-index: 9999;
        perspective: 1000px;
    }
    .vivv-logo {
        color: #ffffff; font-size: 34px; font-weight: 900;
        letter-spacing: -1.5px;
        text-shadow: 2px 2px 0px #00d4ff, 4px 4px 15px rgba(0, 212, 255, 0.4);
        animation: float 3s ease-in-out infinite;
    }
    @keyframes float { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-5px); } }

    /* Cartões Glassmorphism 3D */
    .stMarkdown div[data-testid="stMarkdownContainer"] p { margin-bottom: 0; }
    .neon-card {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(15px);
        border: 1px solid rgba(0, 212, 255, 0.2);
        border-radius: 20px;
        padding: 25px;
        text-align: center;
        transition: all 0.5s cubic-bezier(0.23, 1, 0.32, 1);
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }
    .neon-card:hover {
        transform: translateY(-12px) scale(1.02);
        border-color: #00d4ff;
        box-shadow: 0 20px 40px rgba(0, 212, 255, 0.2);
        background: rgba(255, 255, 255, 0.05);
    }
    .neon-card small { color: #8899a6; text-transform: uppercase; font-weight: 700; letter-spacing: 2px; }
    .neon-card h2 { font-size: 2.5rem !important; color: #fff; font-weight: 900; }

    /* Inputs e Forms Futuristas */
    .stTextInput input, .stNumberInput input, .stSelectbox select {
        background: rgba(255, 255, 255, 0.02) !important;
        border: 1px solid rgba(0, 212, 255, 0.3) !important;
        border-radius: 12px !important;
        color: white !important;
        padding: 12px !important;
    }
    
    /* Botões Glow */
    .stButton button {
        background: linear-gradient(135deg, #00d4ff 0%, #0056b3 100%) !important;
        border: none !important; color: white !important;
        font-weight: 700 !important; border-radius: 12px !important;
        padding: 15px 25px !important;
        transition: 0.4s !important;
        box-shadow: 0 4px 15px rgba(0, 212, 255, 0.3) !important;
    }
    .stButton button:hover {
        transform: scale(1.05) !important;
        box-shadow: 0 0 25px rgba(0, 212, 255, 0.6) !important;
    }

    /* Tabs Personalizadas */
    .stTabs [data-baseweb="tab-list"] { background-color: transparent; gap: 20px; }
    .stTabs [data-baseweb="tab"] {
        height: 50px; background: rgba(255,255,255,0.03);
        border-radius: 10px; color: #8899a6; border: none; padding: 0 20px;
    }
    .stTabs [aria-selected="true"] {
        background: #00d4ff !important; color: #000 !important; font-weight: 700 !important;
    }

    /* WhatsApp Button Micro-interaction */
    .whatsapp-button {
        background: rgba(0, 212, 255, 0.1); color: #00d4ff !important;
        border: 1px solid #00d4ff; padding: 10px 20px; border-radius: 12px;
        text-decoration: none; font-weight: 800; display: flex; align-items: center; justify-content: center;
        transition: 0.3s;
    }
    .whatsapp-button:hover { background: #00d4ff; color: #000 !important; transform: rotate(-2deg); }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="vivv-logo-box"><div class="vivv-logo">Vivv Pro</div></div>', unsafe_allow_html=True)

# ================= 2. CORE FUNCTIONS =================
def hash_senha(senha): return hashlib.sha256(str.encode(senha)).hexdigest()

@st.cache_resource
def init_db():
    try:
        info = json.loads(st.secrets["FIREBASE_DETAILS"])
        return firestore.Client(credentials=service_account.Credentials.from_service_account_info(info))
    except: return None

db = init_db()

# ================= 3. AUTH SYSTEM (DESIGN CLEAN) =================
if "logado" not in st.session_state: st.session_state.logado = False

if not st.session_state.logado:
    col_a, col_b, col_c = st.columns([1, 1.5, 1])
    with col_b:
        st.markdown("<br><br>", unsafe_allow_html=True)
        tab_l, tab_r = st.tabs(["🔒 ACESSAR", "✨ CRIAR CONTA"])
        with tab_l:
            le = st.text_input("E-mail").lower().strip()
            ls = st.text_input("Senha", type="password")
            if st.button("DESBLOQUEAR PAINEL", use_container_width=True):
                u = db.collection("usuarios").document(le).get()
                if u.exists and u.to_dict().get("senha") == hash_senha(ls):
                    st.session_state.logado, st.session_state.user_email = True, le
                    st.rerun()
                else: st.error("Acesso negado.")
        with tab_r:
            with st.form("reg"):
                n = st.text_input("Nome")
                e = st.text_input("E-mail").lower().strip()
                s = st.text_input("Senha", type="password")
                if st.form_submit_button("CRIAR AGORA"):
                    val = datetime.now(fuso_br) + timedelta(days=7)
                    db.collection("usuarios").document(e).set({"nome":n,"senha":hash_senha(s),"pago":False,"validade":val})
                    st.success("Pronto! Faça login.")
    st.stop()

# ================= 4. DATA ENGINE =================
user_ref = db.collection("usuarios").document(st.session_state.user_email)

@st.cache_data(ttl=60)
def get_data(email):
    u = db.collection("usuarios").document(email)
    cl = [{"id": d.id, **d.to_dict()} for d in u.collection("meus_clientes").stream()]
    sv = [{"id": d.id, **d.to_dict()} for d in u.collection("meus_servicos").stream()]
    ag = [{"id": d.id, **d.to_dict()} for d in u.collection("minha_agenda").where("status","==","Pendente").stream()]
    cx = [d.to_dict() for d in u.collection("meu_caixa").stream()]
    return cl, sv, ag, cx

clis, srvs, agnd, cx_list = get_data(st.session_state.user_email)
ent = sum(float(x.get('valor',0)) for x in cx_list if x.get('tipo')=='Entrada')
sai = sum(float(x.get('valor',0)) for x in cx_list if x.get('tipo')=='Saída')

# ================= 5. ULTRA DASHBOARD =================
# Cabeçalho de Resumo
m1, m2, m3, m4 = st.columns(4)
m1.markdown(f'<div class="neon-card"><small>Clientes Ativos</small><h2>{len(clis)}</h2></div>', unsafe_allow_html=True)
m2.markdown(f'<div class="neon-card"><small>Faturamento</small><h2 style="color:#00d4ff">R$ {ent:,.2s}</h2></div>', unsafe_allow_html=True)
m3.markdown(f'<div class="neon-card"><small>Saldo Líquido</small><h2 style="color:#00ff88">R$ {ent-sai:,.2f}</h2></div>', unsafe_allow_html=True)
m4.markdown(f'<div class="neon-card"><small>Agendamentos</small><h2 style="color:#ff9100">{len(agnd)}</h2></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Layout Principal: Operações à Esquerda, Agenda Dinâmica à Direita
c_left, c_right = st.columns([1.4, 2], gap="large")

with c_left:
    st.markdown("### ⚡ Central de Comando")
    t_ag, t_cl, t_sv, t_cx = st.tabs(["📅", "👤", "🛠️", "💰"])
    
    with t_ag:
        with st.form("ag_u"):
            c_n = st.selectbox("Cliente", [c['nome'] for c in clis]) if clis else None
            s_n = st.selectbox("Serviço", [s['nome'] for s in srvs]) if srvs else None
            d_u = st.date_input("Data")
            h_u = st.time_input("Hora")
            if st.form_submit_button("CONFIRMAR AGENDAMENTO"):
                pr = next(s['preco'] for s in srvs if s['nome']==s_n)
                user_ref.collection("minha_agenda").add({
                    "cliente":c_n, "servico":s_n, "preco":pr, "status":"Pendente", 
                    "data":d_u.strftime('%d/%m/%Y'), "hora":h_u.strftime('%H:%M')
                })
                st.cache_data.clear(); st.rerun()

    with t_cl:
        with st.form("cl_u"):
            nome = st.text_input("Nome do Cliente")
            tel = st.text_input("Telefone (DDD + Número)")
            if st.form_submit_button("CADASTRAR CLIENTE"):
                user_ref.collection("meus_clientes").add({"nome":nome, "telefone":tel})
                st.cache_data.clear(); st.rerun()

    with t_cx:
        with st.form("cx_u"):
            desc = st.text_input("Descrição do Lançamento")
            val = st.number_input("Valor R$", min_value=0.0)
            tipo = st.selectbox("Tipo", ["Entrada", "Saída"])
            if st.form_submit_button("EFETIVAR LANÇAMENTO"):
                user_ref.collection("meu_caixa").add({"descricao":desc, "valor":val, "tipo":tipo, "data":firestore.SERVER_TIMESTAMP})
                st.cache_data.clear(); st.rerun()

with c_right:
    st.markdown("### 📋 Agenda do Dia")
    if not agnd:
        st.info("Tudo limpo por aqui. Que tal prospectar novos clientes?")
    else:
        for a in agnd:
            with st.container():
                # Card de Agendamento Moderno
                st.markdown(f"""
                <div style="background: rgba(255,255,255,0.02); border-left: 4px solid #00d4ff; padding: 15px; border-radius: 0 15px 15px 0; margin-bottom: 15px;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <span style="color:#00d4ff; font-weight:900;">{a['hora']}</span> | 
                            <span style="font-size:18px; font-weight:700;">{a['cliente']}</span><br>
                            <small style="color:#8899a6;">{a['servico']} • R$ {a['preco']:.2f}</small>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                c1, c2, c3 = st.columns([1, 1, 1])
                # Whats
                tel_clean = "".join(filter(str.isdigit, next((c['telefone'] for c in clis if c['nome']==a['cliente']), "")))
                msg = urllib.parse.quote(f"Olá {a['cliente']}, confirmando seu horário de {a['servico']} às {a['hora']}!")
                c1.markdown(f'<a href="https://wa.me/55{tel_clean}?text={msg}" target="_blank" class="whatsapp-button">WHATSAPP</a>', unsafe_allow_html=True)
                
                if c2.button("CONCLUIR", key=f"ok_{a['id']}", use_container_width=True):
                    user_ref.collection("minha_agenda").document(a['id']).update({"status":"Concluído"})
                    user_ref.collection("meu_caixa").add({"descricao":f"Serviço: {a['cliente']}", "valor":a['preco'], "tipo":"Entrada", "data":firestore.SERVER_TIMESTAMP})
                    st.cache_data.clear(); st.rerun()
                
                if c3.button("EXCLUIR", key=f"del_{a['id']}", use_container_width=True):
                    user_ref.collection("minha_agenda").document(a['id']).delete()
                    st.cache_data.clear(); st.rerun()

# ================= 6. VIVV AI & GESTÃO =================
st.markdown("<br><hr>", unsafe_allow_html=True)
col_ai, col_mgt = st.columns([2, 1.5])

with col_ai:
    st.markdown("### 💬 Vivv AI Estrategista")
    prompt = st.text_input("Analise seu desempenho...", placeholder="Ex: Como posso aumentar meu faturamento com base nos meus clientes?")
    if st.button("OBTER INSIGHT DA IA") and prompt:
        try:
            api_key = st.secrets["GOOGLE_API_KEY"]
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
            payload = {"contents": [{"parts": [{"text": f"Dados: {len(clis)} clientes, R${ent} fat. Pergunta: {prompt}"}]}]}
            res = requests.post(url, json=payload, timeout=20).json()
            st.info(res['candidates'][0]['content']['parts'][0]['text'])
        except: st.error("A IA está processando muitos dados. Tente em instantes.")

with col_mgt:
    st.markdown("### ⚙️ Gestão de Dados")
    with st.expander("Editar Clientes / Serviços"):
        tab_c, tab_s = st.tabs(["👤", "🛠️"])
        with tab_c:
            if clis:
                df_c = pd.DataFrame(clis)
                new_clis = st.data_editor(df_c[["nome", "telefone"]], use_container_width=True)
                if st.button("SALVAR CLIENTES"):
                    for idx, r in new_clis.iterrows():
                        user_ref.collection("meus_clientes").document(df_clis.iloc[idx]['id']).update({"nome":r['nome'], "telefone":r['telefone']})
                    st.rerun()
