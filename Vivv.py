

import streamlit as st
import pandas as pd
import urllib.parse
from datetime import datetime, timezone, timedelta
import google.generativeai as genai
from google.cloud import firestore
from google.oauth2 import service_account
import json
import hashlib
import io
import requests
import plotly.express as px

fuso_br = timezone(timedelta(hours=-3))

# ================= 1. CONFIGURAÇÃO E DESIGN VIVV =================
st.set_page_config(page_title="Vivv Pro", layout="wide", page_icon="🚀")

# Função para processar o Excel
def gerar_excel(dados):
    if not dados: return None
    df_export = pd.DataFrame(dados)
    if 'data' in df_export.columns:
        df_export['data'] = pd.to_datetime(df_export['data']).dt.tz_localize(None)
    
    cols = {'descricao': 'Cliente/Descrição', 'valor': 'Valor', 'tipo': 'Tipo', 'servico': 'Serviço', 'data': 'Data'}
    df_export = df_export.rename(columns=cols).drop(columns=['id'], errors='ignore')
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_export.to_excel(writer, index=False, sheet_name='Fluxo de Caixa')
    return output.getvalue()

# CSS Consolidado
st.markdown("""
<style>
    header, [data-testid="stHeader"], .stAppDeployButton { display: none !important; }
    .stApp { background-color: #000205 !important; }
    .vivv-top-left { position: fixed; top: 20px; left: 25px; color: #ffffff !important; font-size: 28px; font-weight: 900; z-index: 999999; }
    .stDownloadButton button {
        background: linear-gradient(45deg, #00d4ff, #0056b3) !important;
        border: 1px solid #00d4ff !important; color: white !important;
        box-shadow: 0 0 15px rgba(0, 212, 255, 0.4); transition: 0.3s; width: 100%; font-weight: bold;
    }
    .neon-card {
        background: linear-gradient(145deg, #000814, #001220);
        border: 1px solid #0056b3; border-radius: 12px; padding: 12px 20px;
    }
    .whatsapp-button {
        display: inline-flex; align-items: center; justify-content: center;
        background: rgba(0, 212, 255, 0.1); color: #00d4ff !important;
        border: 1px solid #00d4ff; padding: 6px 15px; border-radius: 8px;
        text-decoration: none !important; font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="vivv-top-left">Vivv</div>', unsafe_allow_html=True)

def hash_senha(senha):
    return hashlib.sha256(str.encode(senha)).hexdigest()

# ================= 2. CONEXÃO FIREBASE =================
@st.cache_resource
def init_db():
    try:
        secrets_dict = json.loads(st.secrets["FIREBASE_DETAILS"])
        creds = service_account.Credentials.from_service_account_info(secrets_dict)
        return firestore.Client(credentials=creds)
    except Exception as e:
        st.error(f"Erro ao conectar ao Banco: {e}")
        return None

db = init_db()
if db is None: st.stop()

# ================= 3. LOGIN / CADASTRO =================
if "logado" not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    aba_login, aba_cadastro = st.tabs(["🔑 Acesso", "📝 Novo Cadastro"])
    with aba_login:
        le = st.text_input("E-mail", key="l_email").lower().strip()
        ls = st.text_input("Senha", type="password", key="l_pass")
        if st.button("ENTRAR"):
            u = db.collection("usuarios").document(le).get()
            if u.exists and u.to_dict().get("senha") == hash_senha(ls):
                st.session_state.logado = True
                st.session_state.user_email = le
                st.rerun()
            else: st.error("Dados incorretos.")
    # (Omitido aba_cadastro simplificada por espaço, mas mantida no seu fluxo)
    st.stop()

# ================= 4. DASHBOARD E LOGICA =================
user_ref = db.collection("usuarios").document(st.session_state.user_email)

@st.cache_data(ttl=60)
def carregar_dados_usuario(email):
    u_ref = db.collection("usuarios").document(email)
    c = [{"id": doc.id, **doc.to_dict()} for doc in u_ref.collection("meus_clientes").stream()]
    s = [{"id": doc.id, **doc.to_dict()} for doc in u_ref.collection("meus_servicos").stream()]
    a = [{"id": doc.id, **doc.to_dict()} for doc in u_ref.collection("minha_agenda").where("status", "==", "Pendente").stream()]
    cx = [doc.to_dict() for doc in u_ref.collection("meu_caixa").stream()]
    return c, s, a, cx

clis, srvs, agnd, cx_list = carregar_dados_usuario(st.session_state.user_email)
faturamento = sum([float(x.get('valor', 0)) for x in cx_list if x.get('tipo') == 'Entrada'])
despesas = sum([float(x.get('valor', 0)) for x in cx_list if x.get('tipo') == 'Saída'])

# --- Interface Métrica ---
m1, m2, m3, m4 = st.columns(4)
m1.markdown(f'<div class="neon-card"><small>👥 CLIENTES</small><h2>{len(clis)}</h2></div>', unsafe_allow_html=True)
m2.markdown(f'<div class="neon-card"><small>💰 RECEITA</small><h2 style="color:#00d4ff">R$ {faturamento:,.2f}</h2></div>', unsafe_allow_html=True)
m3.markdown(f'<div class="neon-card"><small>📈 LUCRO</small><h2 style="color:#00ff88">R$ {faturamento-despesas:,.2f}</h2></div>', unsafe_allow_html=True)
m4.markdown(f'<div class="neon-card"><small>📅 PENDENTES</small><h2 style="color:#ff9100">{len(agnd)}</h2></div>', unsafe_allow_html=True)

st.write("---")

# ================= 5. PAINEL DE OPERAÇÕES =================
col_ops_l, col_btn_mid, col_ops_r = st.columns([1.5, 0.8, 2])

with col_ops_l:
    st.subheader("⚡ Painel de Controle")
    t1, t2, t3, t4 = st.tabs(["📅 Agenda", "👤 Cliente", "🛠️ Serviço", "📉 Caixa"])
    
    with t1: # Agenda
        with st.form("f_ag"):
            c_sel = st.selectbox("Cliente", [c['nome'] for c in clis]) if clis else None
            s_sel = st.selectbox("Serviço", [s['nome'] for s in srvs]) if srvs else None
            d_ag = st.date_input("Data")
            if st.form_submit_button("AGENDAR"):
                p_v = next((s['preco'] for s in srvs if s['nome'] == s_sel), 0)
                user_ref.collection("minha_agenda").add({
                    "cliente": c_sel, "servico": s_sel, "preco": p_v, "status": "Pendente", "data": d_ag.strftime('%d/%m/%Y')
                })
                st.cache_data.clear()
                st.rerun()
    
    with t4: # Caixa
        with st.form("f_cx"):
            ds = st.text_input("Descrição")
            vl = st.number_input("Valor", min_value=0.0)
            tp = st.selectbox("Tipo", ["Entrada", "Saída"])
            if st.form_submit_button("LANÇAR"):
                user_ref.collection("meu_caixa").add({"descricao": ds, "valor": vl, "tipo": tp, "data": firestore.SERVER_TIMESTAMP})
                st.cache_data.clear()
                st.rerun()

with col_btn_mid:
    st.write("<br><br><br>", unsafe_allow_html=True)
    if cx_list:
        data_xlsx = gerar_excel(cx_list)
        st.download_button(label="📊 EXCEL", data=data_xlsx, file_name="fluxo_caixa_vivv.xlsx")

with col_ops_r:
    st.subheader("📋 Próximos Agendamentos")
    for a in agnd:
        with st.expander(f"📍 {a.get('cliente')}"):
            st.write(f"Serviço: {a.get('servico')}")
            if st.button("CONCLUIR", key=a['id']):
                user_ref.collection("minha_agenda").document(a['id']).update({"status": "Concluído"})
                user_ref.collection("meu_caixa").add({"descricao": f"Serviço: {a['cliente']}", "valor": a['preco'], "tipo": "Entrada", "data": firestore.SERVER_TIMESTAMP})
                st.cache_data.clear()
                st.rerun()

# ================= 6. GESTÃO DE DADOS (RECUPERADO) =================
st.write("---")
with st.expander("⚙️ Gerenciar Clientes e Serviços"):
    tab_c, tab_s = st.tabs(["Clientes", "Serviços"])
    with tab_c:
        if clis:
            df_clis = pd.DataFrame(clis)
            st.data_editor(df_clis.set_index("id")[["nome", "telefone"]], use_container_width=True)
            if st.button("Excluir Cliente"): # Logica de exclusão simplificada
                st.warning("Selecione no banco para deletar.")
    with tab_s:
        if srvs:
            df_srvs = pd.DataFrame(srvs)
            st.data_editor(df_srvs.set_index("id")[["nome", "preco"]], use_container_width=True)

# ================= 7. PERFORMANCE E IA =================
st.write("---")
if cx_list:
    df_cx = pd.DataFrame(cx_list)
    fig = px.bar(df_cx.groupby('tipo')['valor'].sum().reset_index(), x='tipo', y='valor', color='tipo', title="Performance Financeira")
    st.plotly_chart(fig, use_container_width=True)

st.subheader("💬 Vivv AI")
prompt = st.text_input("Pergunta para a IA:")
if st.button("ANALISAR") and prompt:
    api_key = st.secrets["GOOGLE_API_KEY"]
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    payload = {"contents": [{"parts": [{"text": f"Contexto: R$ {faturamento} receita. Pergunta: {prompt}"}]}]}
    res = requests.post(url, json=payload)
    if res.status_code == 200:
        st.info(res.json()['candidates'][0]['content']['parts'][0]['text'])
