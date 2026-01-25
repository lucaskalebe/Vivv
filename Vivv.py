import streamlit as st
import pandas as pd
import urllib.parse
from datetime import datetime, timezone, timedelta
import google.generativeai as genai
from google.cloud import firestore
from google.oauth2 import service_account
import json
import hashlib

# ================= 1. CONFIGURAÇÃO E DESIGN ULTRA NEON =================
st.set_page_config(page_title="Vivv Pro", layout="wide", page_icon="🚀")

def hash_senha(senha):
    return hashlib.sha256(str.encode(senha)).hexdigest()

# CSS Refinado para remover GitHub, Menu e Header de forma estável
st.markdown("""
<style>

    .vivv-header {
        color: #ffffff !important;
        font-family: 'Inter', sans-serif;
        font-size: 26px;
        font-weight: 800;
        padding-top: 45px; /* Espaço do teto */
        padding-left: 25px; /* Espaço da esquerda */
        position: relative;
        z-index: 999;

        }

        .vivv-top-left {
        position: absolute;
        top: 25px; /* Espaço do teto */
        left: 20px; /* Espaço da esquerda */
        color: #ffffff !important;
        font-size: 22px;
        font-weight: 800;
        font-family: 'Inter', sans-serif;
        z-index: 9999;
    
    }

    /* 2. AJUSTE DE TELA PARA CELULAR */
    .stApp {
        background-color: #000205 !important;
        margin-top: -75px !important; /* Esconde a barra original */
    }

    .block-container {
        padding-top: 2rem !important; 
        max-width: 95% !important;
    }

    /* 3. TIPOGRAFIA E CORES NEON */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: #d1d1d1;
    }

    .orange-neon { 
        color: #ff9100 !important; 
        text-shadow: 0 0 15px rgba(255, 145, 0, 0.7), 0 0 30px rgba(255, 145, 0, 0.3); 
        font-size: 3rem; 
        font-weight: 900; 
        text-align: center;
        margin-bottom: 5px;
    }

    .neon-card {
        background: linear-gradient(145deg, #000814, #001220);
        border: 1px solid #0056b3;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 0 15px rgba(0, 86, 179, 0.15);
        margin-bottom: 10px;
    }

    /* Botões Personalizados */
    div.stButton > button {
        background: linear-gradient(45deg, #003566, #000814) !important;
        color: #00d4ff !important; 
        border: 1px solid #00d4ff !important; 
        border-radius: 12px; 
        font-weight: bold;
        width: 100%;
        transition: 0.3s;
    }
    
    div.stButton > button:hover {
        box-shadow: 0 0 20px rgba(0, 212, 255, 0.4);
        transform: scale(1.02);
    }
</style>
""", unsafe_allow_html=True)

# ================= 2. CONEXÃO FIREBASE =================
@st.cache_resource
def init_db():
    key_dict = json.loads(st.secrets["FIREBASE_DETAILS"])
    creds = service_account.Credentials.from_service_account_info(key_dict)
    return firestore.Client(credentials=creds)

db = init_db()

# ================= 3. SISTEMA DE LOGIN (VIVV ACCESS) =================
if "logado" not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    st.markdown('<div class="vivv-top-left">Vivv</div>', unsafe_allow_html=True) # <--- 4 ESPAÇOS AQUI
    
    aba_login, aba_cadastro = st.tabs(["🔑 Acesso", "📝 Novo Cadastro"])
    
    with aba_login:
        with st.container():
            le = st.text_input("E-mail para Acesso", placeholder="seu@email.com").lower().strip()
            ls = st.text_input("Senha", type="password", placeholder="******")
            if st.button("ENTRAR NO VIVV"):
                if le and ls:
                    u = db.collection("usuarios").document(le).get()
                    if u.exists and u.to_dict().get("senha") == hash_senha(ls):
                        st.session_state.logado = True
                        st.session_state.user_email = le
                        st.rerun()
                    else:
                        st.error("Dados incorretos.")
                else:
                    st.warning("Preencha os campos.")

    with aba_cadastro:
        with st.form("reg_form"):
            n = st.text_input("Nome Completo")
            e = st.text_input("E-mail").lower().strip()
            s = st.text_input("Crie uma Senha", type="password")
            if st.form_submit_button("CRIAR MINHA CONTA"):
                val = datetime.now(timezone.utc) + timedelta(days=7)
                db.collection("usuarios").document(e).set({
                    "nome": n, "senha": hash_senha(s), 
                    "pago": False, "teste": True, "validade": val
                })
                st.success("Conta criada! Use a aba de Acesso.")
    st.stop()

# ================= 4. VERIFICAÇÃO DE ASSINATURA =================
def verificar_acesso():
    u_ref = db.collection("usuarios").document(st.session_state.user_email).get()
    if u_ref.exists:
        d = u_ref.to_dict()
        if not d.get("pago", False):
            st.markdown('<h1 class="orange-neon">VIVV</h1>', unsafe_allow_html=True)
            st.warning("### 🔒 Assinatura Necessária")
            st.write("Sua conta de teste expirou ou não foi ativada.")
            st.link_button("💳 ATIVAR ACESSO VIVV PRO", "https://buy.stripe.com/exemplo")
            if st.button("🔄 Já realizei o pagamento"): st.rerun()
            st.stop()

verificar_acesso()

# ================= 5. COLETA DE DADOS =================
user_ref = db.collection("usuarios").document(st.session_state.user_email)

# Clientes e Serviços
clis = [{"id": c.id, **c.to_dict()} for c in user_ref.collection("meus_clientes").stream()]
srvs = [{"id": s.id, **s.to_dict()} for s in user_ref.collection("meus_servicos").stream()]

# Agenda e Caixa
agnd = [{"id": a.id, **a.to_dict()} for a in user_ref.collection("minha_agenda").where("status", "==", "Pendente").stream()]
cx_list = [x.to_dict() for x in user_ref.collection("meu_caixa").stream()]

faturamento = sum([float(x['valor']) for x in cx_list if x['tipo'] == 'Entrada'])
despesas = sum([float(x['valor']) for x in cx_list if x['tipo'] == 'Saída'])

# ================= 6. DASHBOARD VIVV =================
st.markdown('<h1 class="orange-neon">VIVV</h1>', unsafe_allow_html=True)

c_header1, c_header2 = st.columns([4,1])
with c_header1:
    st.markdown(f"##### 🚀 Dashboard: <span style='color:#00d4ff'>{st.session_state.user_email}</span>", unsafe_allow_html=True)
with c_header2:
    if st.button("SAIR"):
        st.session_state.logado = False
        st.rerun()

# Métricas Principais
m1, m2, m3, m4 = st.columns(4)
m1.markdown(f'<div class="neon-card"><small>👥 CLIENTES</small><h2>{len(clis)}</h2></div>', unsafe_allow_html=True)
m2.markdown(f'<div class="neon-card"><small>💰 RECEITA</small><h2 style="color:#00d4ff">R$ {faturamento:,.2f}</h2></div>', unsafe_allow_html=True)
m3.markdown(f'<div class="neon-card"><small>📈 LUCRO</small><h2 style="color:#00ff88">R$ {faturamento-despesas:,.2f}</h2></div>', unsafe_allow_html=True)
m4.markdown(f'<div class="neon-card"><small>📅 PENDENTES</small><h2 style="color:#ff9100">{len(agnd)}</h2></div>', unsafe_allow_html=True)

# ================= 7. OPERAÇÕES =================
st.write("---")
col_ops_l, col_ops_r = st.columns([1.5, 2])

with col_ops_l:
    st.subheader("⚡ Painel de Controle")
    t1, t2, t3, t4 = st.tabs(["📅 Agenda", "👤 Cliente", "🛠️ Serviço", "📉 Caixa"])
    
    with t1:
        with st.form("f_ag"):
            c_sel = st.selectbox("Cliente", [c['nome'] for c in clis]) if clis else None
            s_sel = st.selectbox("Serviço", [s['nome'] for s in srvs]) if srvs else None
            col_d, col_h = st.columns(2)
            d_ag = col_d.date_input("Data", format="DD/MM/YYYY")
            h_ag = col_h.time_input("Hora")
            if st.form_submit_button("AGENDAR"):
                if c_sel and s_sel:
                    p_v = next((s['preco'] for s in srvs if s['nome'] == s_sel), 0)
                    user_ref.collection("minha_agenda").add({
                        "cliente": c_sel, "servico": s_sel, "preco": p_v,
                        "status": "Pendente", "data": d_ag.strftime('%d/%m/%Y'),
                        "hora": h_ag.strftime('%H:%M')
                    })
                    st.rerun()

    with t2:
        with st.form("f_cli"):
            nome = st.text_input("Nome")
            tel = st.text_input("WhatsApp")
            if st.form_submit_button("CADASTRAR"):
                user_ref.collection("meus_clientes").add({"nome": nome, "telefone": tel})
                st.rerun()

    with t3:
        with st.form("f_srv"):
            serv = st.text_input("Nome do Serviço")
            prec = st.number_input("Preço", min_value=0.0)
            if st.form_submit_button("SALVAR"):
                user_ref.collection("meus_servicos").add({"nome": serv, "preco": prec})
                st.rerun()

    with t4:
        with st.form("f_cx"):
            ds = st.text_input("Descrição")
            vl = st.number_input("Valor", min_value=0.0)
            tp = st.selectbox("Tipo", ["Entrada", "Saída"])
            if st.form_submit_button("LANÇAR"):
                user_ref.collection("meu_caixa").add({
                    "descricao": ds, "valor": vl, "tipo": tp, "data": firestore.SERVER_TIMESTAMP
                })
                st.rerun()

with col_ops_r:
    st.subheader("📋 Fila Vivv")
    if not agnd:
        st.info("Agenda livre para hoje.")
    else:
        for i, a in enumerate(agnd):
            with st.expander(f"📍 {a.get('hora')} - {a.get('cliente')}"):
                st.write(f"**Serviço:** {a.get('servico')} | **R$ {a.get('preco',0):.2f}**")
                c1, c2, c3 = st.columns(3)
                
                # WhatsApp Link
                raw_tel = next((c.get('telefone', '') for c in clis if c.get('nome') == a.get('cliente')), "")
                clean_tel = "".join(filter(str.isdigit, raw_tel))
                msg = urllib.parse.quote(f"VIVV PRO: Confirmado {a.get('servico')} às {a.get('hora')}!")
                c1.markdown(f'[📱 Whats](https://wa.me/55{clean_tel}?text={msg})')
                
                if c2.button("✅", key=f"f_{a['id']}"):
                    user_ref.collection("minha_agenda").document(a['id']).update({"status": "Concluído"})
                    user_ref.collection("meu_caixa").add({
                        "descricao": f"Serviço: {a.get('cliente')}", "valor": a.get('preco', 0),
                        "tipo": "Entrada", "data": firestore.SERVER_TIMESTAMP
                    })
                    st.rerun()
                
                if c3.button("❌", key=f"d_{a['id']}"):
                    user_ref.collection("minha_agenda").document(a['id']).delete()
                    st.rerun()

# ================= 8. VIVV AI =================
st.write("---")
st.subheader("💬 Vivv AI: Inteligência de Negócio")
prompt = st.text_input("O que deseja analisar hoje?", placeholder="Ex: Como dobrar meu faturamento este mês?")
if st.button("CONSULTAR IA") and prompt:
    try:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        model = genai.GenerativeModel('gemini-1.5-flash')
        ctx = f"Contexto Vivv: Clientes:{len(clis)}, Lucro:R${faturamento-despesas}. Pergunta: {prompt}"
        res = model.generate_content(ctx)
        st.info(res.text)
    except Exception as e:
        st.error(f"IA Indisponível: {e}")



