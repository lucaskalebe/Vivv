

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

# --- Configurações de Fuso e Sistema ---
fuso_br = timezone(timedelta(hours=-3))

st.set_page_config(
    page_title="Vivv Pro | Dashboard", 
    layout="wide", 
    page_icon="🚀",
    initial_sidebar_state="collapsed"
)

# ================= 1. ESTILO VISUAL VIVV (NEON & GLOW) =================
st.markdown("""
<style>
    /* Reset e Fundo */
    header, [data-testid="stHeader"], .stAppDeployButton { display: none !important; }
    .stApp { background-color: #00040a !important; color: #e0e0e0 !important; }
    .block-container { padding-top: 2rem !important; }

    /* Logo Vivv */
    .vivv-logo {
        position: fixed; top: 20px; left: 30px;
        color: #ffffff; font-size: 32px; font-weight: 900;
        letter-spacing: -1px; z-index: 9999;
        text-shadow: 0 0 10px rgba(0, 212, 255, 0.8);
    }

    /* Cartões Neon com Efeito de Brilho ao Passar o Mouse */
    .neon-card {
        background: linear-gradient(145deg, #000d1a, #001a33);
        border: 1px solid #0056b3;
        border-radius: 15px;
        padding: 20px;
        text-align: center;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        box-shadow: 0 4px 15px rgba(0,0,0,0.5);
    }
    .neon-card:hover {
        transform: translateY(-8px) scale(1.02);
        border-color: #00d4ff;
        box-shadow: 0 0 30px rgba(0, 212, 255, 0.4);
    }
    .neon-card h2 { font-size: 2.2rem !important; margin: 10px 0 0 0 !important; font-weight: 800; }
    .neon-card small { color: #8899a6; text-transform: uppercase; letter-spacing: 1px; }

    /* Botão WhatsApp Fluido */
    .whatsapp-button {
        display: inline-flex; align-items: center; justify-content: center;
        background: rgba(0, 212, 255, 0.05); color: #00d4ff !important;
        border: 1px solid #00d4ff; padding: 8px 18px; border-radius: 10px;
        text-decoration: none !important; font-weight: bold;
        transition: 0.3s ease; width: 100%;
    }
    .whatsapp-button:hover {
        background: #00d4ff; color: #000 !important;
        box-shadow: 0 0 20px rgba(0, 212, 255, 0.6);
    }

    /* Botão Excel com Gradiente Animado */
    .stDownloadButton button {
        background: linear-gradient(45deg, #00d4ff, #0056b3, #00d4ff) !important;
        background-size: 200% auto !important;
        border: none !important; color: white !important;
        font-weight: 900 !important; border-radius: 12px !important;
        transition: 0.5s !important; box-shadow: 0 0 15px rgba(0, 212, 255, 0.3) !important;
    }
    .stDownloadButton button:hover {
        background-position: right center !important;
        box-shadow: 0 0 25px rgba(0, 212, 255, 0.7) !important;
        transform: scale(1.03);
    }

    /* Tabs Customizadas */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; background-color: transparent; }
    .stTabs [data-baseweb="tab"] {
        background-color: #001220; border-radius: 8px 8px 0 0;
        padding: 10px 20px; color: #8899a6; border: 1px solid #002d5a;
    }
    .stTabs [aria-selected="true"] { background-color: #0056b3 !important; color: white !important; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="vivv-logo">Vivv</div>', unsafe_allow_html=True)

# ================= 2. FUNÇÕES CORE (DB & EXCEL) =================
@st.cache_resource
def init_db():
    try:
        info = json.loads(st.secrets["FIREBASE_DETAILS"])
        return firestore.Client(credentials=service_account.Credentials.from_service_account_info(info))
    except: return None

db = init_db()

def gerar_excel(dados):
    if not dados: return None
    df = pd.DataFrame(dados)
    if 'data' in df.columns:
        df['data'] = pd.to_datetime(df['data']).dt.tz_localize(None)
    
    df = df.rename(columns={'descricao':'Descrição','valor':'Valor','tipo':'Tipo','servico':'Serviço','data':'Data'})
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Vivv_Fluxo')
    return output.getvalue()

# ================= 3. LOGICA DE ACESSO =================
if "logado" not in st.session_state: st.session_state.logado = False

if not st.session_state.logado:
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        st.markdown("<h2 style='text-align:center; color:#00d4ff;'>Acesso Vivv Pro</h2>", unsafe_allow_html=True)
        le = st.text_input("E-mail").lower().strip()
        ls = st.text_input("Senha", type="password")
        if st.button("ENTRAR COM BRILHO", use_container_width=True):
            u = db.collection("usuarios").document(le).get()
            if u.exists and u.to_dict().get("senha") == hashlib.sha256(ls.encode()).hexdigest():
                st.session_state.logado, st.session_state.user_email = True, le
                st.rerun()
            else: st.error("Incorreto.")
    st.stop()

# ================= 4. CARREGAMENTO DE DADOS =================
user_ref = db.collection("usuarios").document(st.session_state.user_email)

@st.cache_data(ttl=60)
def fetch_data(email):
    u = db.collection("usuarios").document(email)
    cl = [{"id": d.id, **d.to_dict()} for d in u.collection("meus_clientes").stream()]
    sv = [{"id": d.id, **d.to_dict()} for d in u.collection("meus_servicos").stream()]
    ag = [{"id": d.id, **d.to_dict()} for d in u.collection("minha_agenda").where("status","==","Pendente").stream()]
    cx = [d.to_dict() for d in u.collection("meu_caixa").stream()]
    return cl, sv, ag, cx

clis, srvs, agnd, cx_list = fetch_data(st.session_state.user_email)
ent = sum(float(x.get('valor',0)) for x in cx_list if x.get('tipo')=='Entrada')
sai = sum(float(x.get('valor',0)) for x in cx_list if x.get('tipo')=='Saída')

# ================= 5. DASHBOARD INTERATIVO =================
m1, m2, m3, m4 = st.columns(4)
m1.markdown(f'<div class="neon-card"><small>Clientes</small><h2>{len(clis)}</h2></div>', unsafe_allow_html=True)
m2.markdown(f'<div class="neon-card"><small>Receita</small><h2 style="color:#00d4ff">R$ {ent:,.2f}</h2></div>', unsafe_allow_html=True)
m3.markdown(f'<div class="neon-card"><small>Lucro Líquido</small><h2 style="color:#00ff88">R$ {ent-sai:,.2f}</h2></div>', unsafe_allow_html=True)
m4.markdown(f'<div class="neon-card"><small>Agenda</small><h2 style="color:#ff9100">{len(agnd)}</h2></div>', unsafe_allow_html=True)

st.write("---")

col_left, col_mid, col_right = st.columns([1.6, 0.8, 2])

with col_left:
    st.subheader("⚡ Ações Rápidas")
    t_ag, t_cl, t_sv, t_cx = st.tabs(["📅 Agenda", "👤 Cliente", "🛠️ Serviço", "📉 Caixa"])
    
    with t_ag:
        with st.form("ag_f"):
            c_nm = st.selectbox("Quem?", [c['nome'] for c in clis]) if clis else None
            s_nm = st.selectbox("O que?", [s['nome'] for s in srvs]) if srvs else None
            dt = st.date_input("Quando?")
            if st.form_submit_button("CONFIRMAR AGENDAMENTO"):
                pr = next(s['preco'] for s in srvs if s['nome']==s_nm)
                user_ref.collection("minha_agenda").add({
                    "cliente":c_nm, "servico":s_nm, "preco":pr, "status":"Pendente", "data":dt.strftime('%d/%m/%Y')
                })
                st.cache_data.clear(); st.rerun()
    
    with t_cx:
        with st.form("cx_f"):
            d_cx = st.text_input("Descrição")
            v_cx = st.number_input("Valor", min_value=0.0)
            t_cx_sel = st.selectbox("Tipo", ["Entrada", "Saída"])
            if st.form_submit_button("LANÇAR NO FLUXO"):
                user_ref.collection("meu_caixa").add({"descricao":d_cx, "valor":v_cx, "tipo":t_cx_sel, "data":firestore.SERVER_TIMESTAMP})
                st.cache_data.clear(); st.rerun()

with col_mid:
    st.write("<br><br><br>", unsafe_allow_html=True)
    if cx_list:
        st.download_button("📊 EXPORTAR EXCEL", gerar_excel(cx_list), "vivv_pro_caixa.xlsx", use_container_width=True)

with col_right:
    st.subheader("📋 Compromissos Pendentes")
    if not agnd: st.info("Nada agendado.")
    for a in agnd:
        with st.expander(f"📌 {a['cliente']} | {a['data']}"):
            st.write(f"**Serviço:** {a['servico']} - **R$ {a['preco']:.2f}**")
            c1, c2 = st.columns(2)
            if c1.button("✅ CONCLUIR", key=f"ok_{a['id']}", use_container_width=True):
                user_ref.collection("minha_agenda").document(a['id']).update({"status":"Concluído"})
                user_ref.collection("meu_caixa").add({"descricao":f"Serviço: {a['cliente']}", "valor":a['preco'], "tipo":"Entrada", "data":firestore.SERVER_TIMESTAMP})
                st.cache_data.clear(); st.rerun()
            if c2.button("🗑️ CANCELAR", key=f"del_{a['id']}", use_container_width=True):
                user_ref.collection("minha_agenda").document(a['id']).delete()
                st.cache_data.clear(); st.rerun()

# ================= 6. GESTÃO DE DADOS (AVANÇADO) =================
st.write("---")
with st.expander("⚙️ Gestão Administrativa (Clientes & Serviços)"):
    tab_cl, tab_sv = st.tabs(["👤 Meus Clientes", "🛠️ Meus Serviços"])
    with tab_cl:
        if clis:
            df_c = pd.DataFrame(clis).set_index("id")
            new_df_c = st.data_editor(df_c[["nome", "telefone"]], use_container_width=True)
            if st.button("💾 SALVAR ALTERAÇÕES CLIENTES"):
                for idx, row in new_df_c.iterrows():
                    user_ref.collection("meus_clientes").document(idx).update({"nome":row["nome"], "telefone":row["telefone"]})
                st.cache_data.clear(); st.success("Atualizado!"); st.rerun()

# ================= 7. ANALYTICS & IA =================
st.write("---")
st.subheader("📊 Performance & IA")
if cx_list:
    df_g = pd.DataFrame(cx_list)
    fig = px.pie(df_g, values='valor', names='tipo', hole=.4, color='tipo',
                 color_discrete_map={'Entrada':'#00d4ff', 'Saída':'#ff4b4b'})
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
    st.plotly_chart(fig, use_container_width=True)

st.write("### 💬 Vivv AI: Sua Estrategista")
prompt = st.text_input("Analise seu negócio aqui...")
if st.button("CONSULTAR IA") and prompt:
    api_key = st.secrets["GOOGLE_API_KEY"]
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    ctx = f"Financeiro: R${ent} entrada, R${sai} saída. {len(clis)} clientes. Pergunta: {prompt}"
    try:
        res = requests.post(url, json={"contents": [{"parts": [{"text": ctx}]}]}, timeout=10)
        st.info(res.json()['candidates'][0]['content']['parts'][0]['text'])
    except: st.error("Erro na IA.")
