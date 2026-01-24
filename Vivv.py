

import streamlit as st
import pandas as pd
import urllib.parse
from datetime import datetime, timezone, timedelta
import google.generativeai as genai
from google.cloud import firestore
from google.oauth2 import service_account
import json

# ================= 1. CONFIGURAÇÃO E DESIGN ULTRA NEON 300% =================
st.set_page_config(page_title="Vivv Pro", layout="wide", page_icon="🚀")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    .stApp { background-color: #000205; color: #d1d1d1; font-family: 'Inter', sans-serif; }
    
    /* CARDS COM GLOW DINÂMICO */
    .neon-card {
        background: linear-gradient(145deg, #000814, #001220);
        border: 1px solid #0056b3;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 0 15px rgba(0, 86, 179, 0.1);
        transition: all 0.3s ease-in-out;
        text-align: center;
    }
    .neon-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 0 30px rgba(0, 212, 255, 0.4);
        border-color: #00d4ff;
    }

    /* BOTÕES COM BRILHO AO CLICAR */
    div.stButton > button {
        background: linear-gradient(45deg, #003566, #000814);
        color: #00d4ff;
        border: 1px solid #00d4ff;
        border-radius: 10px;
        transition: 0.3s;
        width: 100%;
    }
    div.stButton > button:hover {
        box-shadow: 0 0 20px #00d4ff;
        background: #00d4ff;
        color: #000;
    }

    .orange-neon {
        color: #ff9100 !important;
        text-shadow: 0 0 15px rgba(255, 145, 0, 0.7);
        font-size: 2.5rem; font-weight: 800;
    }
    
    /* WHATSAPP LINK */
    .wa-link {
        background: #25D366; color: black !important; padding: 10px;
        border-radius: 8px; font-weight: bold; text-decoration: none;
        display: block; text-align: center; margin-top: 10px;
    }
</style>
""", unsafe_allow_html=True)

# ================= 2. BANCO DE DADOS (FIRESTORE) =================
@st.cache_resource
def init_db():
    key_dict = json.loads(st.secrets["FIREBASE_DETAILS"])
    creds = service_account.Credentials.from_service_account_info(key_dict)
    return firestore.Client(credentials=creds)

db = init_db()

# --- CONTROLE DE ACESSO ---
if "logado" not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    st.title("🚀 Vivv - Sistema SaaS Cloud")
    aba_login, aba_cadastro = st.tabs(["Entrar", "Solicitar Acesso"])
    
    with aba_cadastro:
        with st.form("reg"):
            n = st.text_input("Nome")
            e = st.text_input("E-mail")
            s = st.text_input("Senha", type="password")
            if st.form_submit_button("CADASTRAR"):
                validade = datetime.now(timezone.utc) + timedelta(days=7)
                db.collection("usuarios").document(e).set({
                    "nome": n, "senha": s, "pago": False, "teste": True, "validade": validade
                })
                st.success("Cadastrado! Use a aba Entrar.")

    with aba_login:
        le = st.text_input("E-mail", key="l_e")
        ls = st.text_input("Senha", type="password", key="l_s")
        if st.button("ACESSAR SISTEMA"):
            u = db.collection("usuarios").document(le).get()
            if u.exists and u.to_dict().get("senha") == ls:
                st.session_state.logado = True
                st.session_state.user_email = le
                st.rerun()
            else: st.error("Dados inválidos.")
    st.stop()

# ================= 3. BUSCA DE DADOS (AGORA 100% FIRESTORE) =================
user_ref = db.collection("usuarios").document(st.session_state.user_email)

# Puxando dados em tempo real
clis = [c.to_dict() for c in user_ref.collection("meus_clientes").stream()]
srvs = [s.to_dict() for s in user_ref.collection("meus_servicos").stream()]
agnd = []
for a in user_ref.collection("minha_agenda").where("status", "==", "Pendente").stream():
    d = a.to_dict()
    d['id'] = a.id
    agnd.append(d)
caixa = [x.to_dict() for x in user_ref.collection("meu_caixa").stream()]

# Métricas
total_clis = len(clis)
faturamento = sum([float(x['valor']) for x in caixa if x['tipo'] == 'Entrada'])
despesas = sum([float(x['valor']) for x in caixa if x['tipo'] == 'Saída'])
ag_hoje_count = len(agnd)

# ================= 4. DASHBOARD NEON =================
col_title, col_logout = st.columns([5, 1])
# Substitua col_title.title(f"Bem-vindo, {st.session_state.user_email}") por:

col_title.markdown(f"#### 👋 Bem-vindo, **{st.session_state.user_email}**")
if col_logout.button("SAIR"):
    st.session_state.logado = False
    st.rerun()

m1, m2, m3, m4 = st.columns(4)
m1.markdown(f'<div class="neon-card"><small>CLIENTES</small><h2>{total_clis}</h2></div>', unsafe_allow_html=True)
m2.markdown(f'<div class="neon-card"><small>RECEITA</small><h2 style="color:#00d4ff">R$ {faturamento:,.2f}</h2></div>', unsafe_allow_html=True)
m3.markdown(f'<div class="neon-card"><small>LUCRO</small><h2 style="color:#00ff88">R$ {faturamento-despesas:,.2f}</h2></div>', unsafe_allow_html=True)
m4.markdown(f'<div class="neon-card"><small>AGENDA</small><div class="orange-neon">{ag_hoje_count}</div></div>', unsafe_allow_html=True)

# ================= 5. OPERACIONAL =================
st.write("---")
c_left, c_right = st.columns([1.5, 2])

with c_left:
    st.subheader("⚡ Gestão")
    tab_ag, tab_cli, tab_srv, tab_cx = st.tabs(["📅 Agenda", "👤 Cliente", "💰 Serviço", "📉 Caixa"])
    
    with tab_cli:
        with st.form("f_cli"):
            nome = st.text_input("Nome do Cliente")
            tel = st.text_input("WhatsApp")
            if st.form_submit_button("CADASTRAR"):
                user_ref.collection("meus_clientes").add({"nome": nome, "telefone": tel})
                st.rerun()

    with tab_srv:
        with st.form("f_srv"):
            serv = st.text_input("Nome do Serviço")
            preco = st.number_input("Preço", min_value=0.0)
            if st.form_submit_button("SALVAR SERVIÇO"):
                user_ref.collection("meus_servicos").add({"nome": serv, "preco": preco})
                st.rerun()

    with tab_ag:
        with st.form("f_ag"):
            c_sel = st.selectbox("Cliente", [c['nome'] for c in clis]) if clis else st.info("Cadastre um cliente")
            s_sel = st.selectbox("Serviço", [s['nome'] for s in srvs]) if srvs else st.info("Cadastre um serviço")
            d_ag = st.date_input("Data")
            h_ag = st.time_input("Hora")
            if st.form_submit_button("AGENDAR"):
                p_val = next((s['preco'] for s in srvs if s['nome'] == s_sel), 0)
                user_ref.collection("minha_agenda").add({
                    "cliente": c_sel, "servico": s_sel, "preco": p_val, 
                    "data": str(d_ag), "hora": str(h_ag), "status": "Pendente"
                })
                st.rerun()

    with tab_cx:
        with st.form("f_cx"):
            desc = st.text_input("Descrição")
            valor = st.number_input("Valor")
            tipo = st.selectbox("Tipo", ["Entrada", "Saída"])
            if st.form_submit_button("REGISTRAR"):
                user_ref.collection("meu_caixa").add({"descricao": desc, "valor": valor, "tipo": tipo, "data": firestore.SERVER_TIMESTAMP})
                st.rerun()

# ================= 6. FILA DE ATENDIMENTOS =================
with c_right:
    st.subheader("📋 Fila Cloud")
    if not agnd:
        st.info("Nenhum agendamento pendente.")
    else:
        for a in agnd:
            with st.expander(f"📍 {a['data']} às {a['hora']} | {a['cliente']}"):
                col1, col2 = st.columns([2, 1])
                col1.write(f"**{a['servico']}** - R$ {a['preco']:.2f}")
                
                # Link WhatsApp
                msg = urllib.parse.quote(f"Confirmado: {a['servico']} às {a['hora']}. Vivv agradece!")
                # Busca telefone do cliente
                tel_c = next((c['telefone'] for c in clis if c['nome'] == a['cliente']), "")
                col1.markdown(f'<a href="https://wa.me/{tel_c}?text={msg}" class="wa-link">📱 WhatsApp</a>', unsafe_allow_html=True)
                
                if col2.button("CONCLUIR", key=a['id']):
                    user_ref.collection("minha_agenda").document(a['id']).update({"status": "Concluído"})
                    user_ref.collection("meu_caixa").add({
                        "descricao": f"Atend: {a['cliente']}", "valor": a['preco'], "tipo": "Entrada", "data": firestore.SERVER_TIMESTAMP
                    })
                    st.rerun()

# ================= 7. AUDITORIA E IA =================
st.write("---")
ca1, ca2 = st.columns(2)
with ca1:
    with st.expander("🗄️ Database Clientes/Serviços"):
        if clis: st.dataframe(pd.DataFrame(clis), use_container_width=True)
        if srvs: st.dataframe(pd.DataFrame(srvs), use_container_width=True)

with ca2:
    st.subheader("💬 Vivv Strategist AI")
    if prompt := st.chat_input("Dicas para meu negócio?"):
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        model = genai.GenerativeModel('gemini-1.5-flash')
        ctx = f"Dados: Clientes={total_clis}, Fat=R${faturamento}. Pergunta: {prompt}"
        st.write(model.generate_content(ctx).text)

# ================= 8. IA STRATEGIST (GOOGLE GEMINI) =================
st.write("---")
st.subheader("💬 Vivv AI: Consultor de Negócios")

if prompt := st.chat_input("Como posso melhorar meu lucro hoje?"):
    try:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        
        # Lista os modelos e escolhe o primeiro que suporta geração de conteúdo
        # Isso evita o erro 'NotFound' caso o nome do modelo mude
        modelos_disponiveis = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # Tenta usar o flash, se não existir, pega o primeiro da lista
        nome_modelo = 'models/gemini-1.5-flash' if 'models/gemini-1.5-flash' in modelos_disponiveis else modelos_disponiveis[0]
        
        model = genai.GenerativeModel(nome_modelo)
        
        lucro_atual = faturamento - despesas
        contexto = (
            f"Você é um consultor de negócios experiente. "
            f"Dados atuais: Clientes={total_clis}, Faturamento=R${faturamento}, Lucro=R${lucro_atual}. "
            f"O usuário perguntou: {prompt}"
        )
        
        with st.spinner("Analisando dados..."):
            response = model.generate_content(contexto)
            st.write(response.text)
            
    except Exception as e:
        st.error(f"Ocorreu um erro na IA: {e}")
        st.info("Verifique se sua GOOGLE_API_KEY está correta nos Secrets do Streamlit.")
