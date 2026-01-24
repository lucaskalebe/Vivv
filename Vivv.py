import streamlit as st
import pandas as pd
import urllib.parse
from datetime import datetime, timezone, timedelta
import google.generativeai as genai
from google.cloud import firestore
from google.oauth2 import service_account
import json

# ================= 1. CONFIGURAÇÃO E DESIGN ULTRA NEON =================
st.set_page_config(page_title="Vivv Pro", layout="wide", page_icon="🚀")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    .stApp { background-color: #000205; color: #d1d1d1; font-family: 'Inter', sans-serif; }
    .neon-card {
        background: linear-gradient(145deg, #000814, #001220);
        border: 1px solid #0056b3;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 0 15px rgba(0, 86, 179, 0.1);
        transition: all 0.3s ease-in-out;
        text-align: center;
    }
    .neon-card:hover { transform: translateY(-5px); box-shadow: 0 0 30px rgba(0, 212, 255, 0.4); border-color: #00d4ff; }
    div.stButton > button {
        background: linear-gradient(45deg, #003566, #000814);
        color: #00d4ff; border: 1px solid #00d4ff; border-radius: 10px; width: 100%;
    }
    .orange-neon { color: #ff9100 !important; text-shadow: 0 0 15px rgba(255, 145, 0, 0.7); font-size: 2.5rem; font-weight: 800; }
    .wa-link { background: #25D366; color: black !important; padding: 10px; border-radius: 8px; font-weight: bold; text-decoration: none; display: block; text-align: center; }
</style>
""", unsafe_allow_html=True)

# ================= 2. BANCO DE DADOS =================
@st.cache_resource
def init_db():
    key_dict = json.loads(st.secrets["FIREBASE_DETAILS"])
    creds = service_account.Credentials.from_service_account_info(key_dict)
    return firestore.Client(credentials=creds)

db = init_db()

if "logado" not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    st.title("🚀 Vivv - Acesso")
    aba_login, aba_cadastro = st.tabs(["Entrar", "Cadastrar"])
    with aba_cadastro:
        with st.form("reg"):
            n, e, s = st.text_input("Nome"), st.text_input("E-mail"), st.text_input("Senha", type="password")
            if st.form_submit_button("CADASTRAR"):
                val = datetime.now(timezone.utc) + timedelta(days=7)
                db.collection("usuarios").document(e).set({"nome": n, "senha": s, "pago": False, "teste": True, "validade": val})
                st.success("Sucesso! Faça login.")
    with aba_login:
        le, ls = st.text_input("E-mail"), st.text_input("Senha", type="password")
        if st.button("ACESSAR"):
            u = db.collection("usuarios").document(le).get()
            if u.exists and u.to_dict().get("senha") == ls:
                st.session_state.logado, st.session_state.user_email = True, le
                st.rerun()
    st.stop()

# ================= 3. BUSCA DE DADOS =================
user_ref = db.collection("usuarios").document(st.session_state.user_email)
clis = [c.to_dict() for c in user_ref.collection("meus_clientes").stream()]
srvs = [s.to_dict() for s in user_ref.collection("meus_servicos").stream()]
agnd = []
for a in user_ref.collection("minha_agenda").where("status", "==", "Pendente").stream():
    d = a.to_dict(); d['id'] = a.id; agnd.append(d)
caixa = [x.to_dict() for x in user_ref.collection("meu_caixa").stream()]

faturamento = sum([float(x['valor']) for x in caixa if x['tipo'] == 'Entrada'])
despesas = sum([float(x['valor']) for x in caixa if x['tipo'] == 'Saída'])

# ================= 4. DASHBOARD =================
col_title, col_logout = st.columns([5, 1])
# Saudação menor conforme pedido
col_title.markdown(f"##### 👋 Bem-vindo, <span style='color: #00d4ff;'>{st.session_state.user_email}</span>", unsafe_allow_html=True)
if col_logout.button("SAIR"):
    st.session_state.logado = False
    st.rerun()

m1, m2, m3, m4 = st.columns(4)
m1.markdown(f'<div class="neon-card"><small>CLIENTES</small><h2>{len(clis)}</h2></div>', unsafe_allow_html=True)
m2.markdown(f'<div class="neon-card"><small>RECEITA</small><h2 style="color:#00d4ff">R$ {faturamento:,.2f}</h2></div>', unsafe_allow_html=True)
m3.markdown(f'<div class="neon-card"><small>LUCRO</small><h2 style="color:#00ff88">R$ {faturamento-despesas:,.2f}</h2></div>', unsafe_allow_html=True)
m4.markdown(f'<div class="neon-card"><small>AGENDA</small><div class="orange-neon">{len(agnd)}</div></div>', unsafe_allow_html=True)

# ================= 5. GESTÃO OPERACIONAL =================
st.write("---")
c_left, c_right = st.columns([1.5, 2])

with c_left:
    st.subheader("⚡ Painel")
    t1, t2, t3, t4 = st.tabs(["📅 Agenda", "👤 Cliente", "💰 Serviço", "📉 Caixa"])
    with t1:
        with st.form("f1"):
            c_s = st.selectbox("Cliente", [c['nome'] for c in clis]) if clis else st.warning("Cadastre um cliente")
            s_s = st.selectbox("Serviço", [s['nome'] for s in srvs]) if srvs else st.warning("Cadastre um serviço")
            if st.form_submit_button("AGENDAR"):
                p_v = next((s['preco'] for s in srvs if s['nome'] == s_s), 0)
                user_ref.collection("minha_agenda").add({"cliente": c_s, "servico": s_s, "preco": p_v, "status": "Pendente", "data": str(datetime.now().date())})
                st.rerun()
    with t2:
        with st.form("f2"):
            nome, tel = st.text_input("Nome"), st.text_input("WhatsApp")
            if st.form_submit_button("SALVAR CLIENTE"):
                user_ref.collection("meus_clientes").add({"nome": nome, "telefone": tel})
                st.rerun()
    with t3:
        with st.form("f3"):
            serv, prec = st.text_input("Serviço"), st.number_input("Preço")
            if st.form_submit_button("SALVAR SERVIÇO"):
                user_ref.collection("meus_servicos").add({"nome": serv, "preco": prec})
                st.rerun()
    with t4:
        with st.form("f4"):
            ds, vl, tp = st.text_input("Desc"), st.number_input("Valor"), st.selectbox("Tipo", ["Entrada", "Saída"])
            if st.form_submit_button("LANÇAR"):
                user_ref.collection("meu_caixa").add({"descricao": ds, "valor": vl, "tipo": tp, "data": firestore.SERVER_TIMESTAMP})
                st.rerun()

with c_right:
    st.subheader("📋 Fila")
    for a in agnd:
        with st.expander(f"📍 {a['cliente']} | {a['servico']}"):
            col_a, col_b = st.columns([2, 1])
            tel_c = next((c['telefone'] for c in clis if c['nome'] == a['cliente']), "")
            col_a.markdown(f'<a href="https://wa.me/{tel_c}" class="wa-link">📱 WhatsApp</a>', unsafe_allow_html=True)
            if col_b.button("CONCLUIR", key=a['id']):
                user_ref.collection("minha_agenda").document(a['id']).update({"status": "Concluído"})
                user_ref.collection("meu_caixa").add({"descricao": f"Serv: {a['servico']}", "valor": a['preco'], "tipo": "Entrada", "data": firestore.SERVER_TIMESTAMP})
                st.rerun()

# ================= 6. IA CONSULTOR DE NEGÓCIOS =================
st.write("---")
st.subheader("💬 Vivv AI: Consultor de Negócios")
if prompt := st.chat_input("Como posso melhorar meu lucro hoje?"):
    try:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        model = genai.GenerativeModel('models/gemini-1.5-flash' if 'models/gemini-1.5-flash' in modelos else modelos[0])
        ctx = f"Dados: Clientes={len(clis)}, Receita=R${faturamento}. Pergunta: {prompt}"
        with st.spinner("Analisando..."):
            st.write(model.generate_content(ctx).text)
    except Exception as e:
        st.error(f"Erro: {e}")
