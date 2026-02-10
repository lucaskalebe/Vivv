

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import io
import json
import hashlib
import re
import time
from datetime import datetime, timezone, timedelta
from google.cloud import firestore
from google.oauth2 import service_account

# ================= CONFIGURAÇÃO =================
st.set_page_config(page_title="Vivv Pro Elite", layout="wide", page_icon="⚡", initial_sidebar_state="collapsed")
fuso_br = timezone(timedelta(hours=-3))

# ================= ESTILO PREMIUM ULTRA AVANÇADO =================
st.markdown("""
<style>
    /* Reset */
    header, [data-testid="stHeader"], .stAppDeployButton { display: none !important; }
    
    /* Fundo Gradiente Dinâmico */
    .stApp { 
        background: linear-gradient(135deg, #0a0a0f 0%, #0d1b2a 25%, #1b263b 50%, #0d1b2a 75%, #0a0a0f 100%) !important;
        background-size: 400% 400% !important;
        animation: gradientBG 15s ease infinite !important;
        min-height: 100vh;
    }
    @keyframes gradientBG {
        0% { background-position: 0% 50% }
        50% { background-position: 100% 50% }
        100% { background-position: 0% 50% }
    }
    
    /* Container Glass */
    .glass-card {
        background: rgba(255, 255, 255, 0.07);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-radius: 24px;
        border: 1px solid rgba(255, 255, 255, 0.15);
        padding: 25px;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
        transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    .glass-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent);
        transition: 0.7s;
    }
    .glass-card:hover::before { left: 100%; }
    .glass-card:hover {
        border: 1px solid rgba(0, 212, 255, 0.4);
        box-shadow: 0 30px 80px rgba(0, 212, 255, 0.2);
        transform: translateY(-8px);
    }
    
    /* Cards de Métrica Holográficos */
    .hologram-card {
        background: linear-gradient(145deg, rgba(0, 40, 85, 0.8), rgba(0, 20, 40, 0.9));
        border: 2px solid;
        border-image: linear-gradient(45deg, #00d4ff, #0066cc, #00d4ff) 1;
        border-radius: 20px;
        padding: 25px;
        position: relative;
        overflow: hidden;
        transition: all 0.5s ease;
    }
    .hologram-card::after {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: linear-gradient(45deg, transparent, rgba(0, 212, 255, 0.1), transparent);
        transform: rotate(30deg);
        animation: shine 3s infinite linear;
    }
    @keyframes shine {
        0% { transform: rotate(30deg) translateX(-100%); }
        100% { transform: rotate(30deg) translateX(100%); }
    }
    .hologram-card:hover {
        transform: translateY(-10px) scale(1.03);
        box-shadow: 0 25px 50px rgba(0, 212, 255, 0.3);
    }
    
    /* Botões Neomórficos com Efeito de Partículas */
    .stButton > button {
        background: linear-gradient(135deg, #0066cc 0%, #0099ff 50%, #00d4ff 100%);
        color: white !important;
        border: none;
        border-radius: 15px;
        padding: 14px 28px;
        font-weight: 700;
        font-size: 15px;
        letter-spacing: 0.5px;
        position: relative;
        overflow: hidden;
        transition: all 0.4s ease;
        box-shadow: 0 10px 30px rgba(0, 212, 255, 0.3);
    }
    .stButton > button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
        transition: 0.7s;
    }
    .stButton > button:hover::before { left: 100%; }
    .stButton > button:hover {
        transform: translateY(-5px);
        box-shadow: 0 20px 40px rgba(0, 212, 255, 0.5);
    }
    
    /* Inputs Futuristas */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div > select {
        background: rgba(255, 255, 255, 0.08) !important;
        border: 2px solid rgba(0, 212, 255, 0.2) !important;
        border-radius: 12px !important;
        color: white !important;
        padding: 14px !important;
        font-size: 15px;
        transition: all 0.3s ease !important;
        backdrop-filter: blur(10px);
    }
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus {
        border: 2px solid #00d4ff !important;
        box-shadow: 0 0 20px rgba(0, 212, 255, 0.4) !important;
        background: rgba(255, 255, 255, 0.12) !important;
    }
    
    /* Tabs Holográficas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 5px;
        background: rgba(255, 255, 255, 0.05);
        border-radius: 15px;
        padding: 5px;
        backdrop-filter: blur(10px);
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 12px !important;
        padding: 12px 24px !important;
        background: transparent !important;
        font-weight: 600;
        transition: all 0.3s ease !important;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #0066cc 0%, #00d4ff 100%) !important;
        box-shadow: 0 5px 20px rgba(0, 212, 255, 0.3);
    }
    
    /* Logo Holográfica */
    .vivv-logo {
        position: fixed;
        top: 20px;
        left: 30px;
        font-size: 42px;
        font-weight: 900;
        z-index: 999999;
        letter-spacing: -2px;
        background: linear-gradient(135deg, #00d4ff, #0066cc, #00d4ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-shadow: 0 0 30px rgba(0, 212, 255, 0.5);
        animation: glow 2s ease-in-out infinite alternate;
    }
    @keyframes glow {
        from { text-shadow: 0 0 20px rgba(0, 212, 255, 0.5); }
        to { text-shadow: 0 0 40px rgba(0, 212, 255, 0.8), 0 0 60px rgba(0, 212, 255, 0.6); }
    }
    
    /* Scrollbar Neon */
    ::-webkit-scrollbar { width: 10px; height: 10px; }
    ::-webkit-scrollbar-track { background: rgba(255, 255, 255, 0.05); border-radius: 5px; }
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, #00d4ff, #0066cc);
        border-radius: 5px;
        box-shadow: 0 0 10px rgba(0, 212, 255, 0.5);
    }
    
    /* Alertas Animados */
    .alert-pulse {
        animation: pulse 2s infinite;
        border: 2px solid;
        border-image: linear-gradient(45deg, #ff6b6b, #ffa726, #ff6b6b) 1;
        padding: 15px;
        border-radius: 12px;
        background: rgba(255, 107, 107, 0.1);
    }
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.02); }
        100% { transform: scale(1); }
    }
</style>

<div class="vivv-logo">VIVV<span style="color:#00d4ff">.</span>PRO</div>
""", unsafe_allow_html=True)

# ================= SEGURANÇA =================
class Security:
    SALT = "vivv_secure_2026_elite"
    
    @staticmethod
    def hash_senha(senha): return hashlib.sha256((Security.SALT + senha).encode()).hexdigest()
    @staticmethod
    def email_valido(email): return bool(re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email))
    @staticmethod
    def telefone_valido(tel): return len(''.join(filter(str.isdigit, tel))) in [10, 11]

# ================= FIREBASE =================
@st.cache_resource
def init_firebase():
    try:
        if "FIREBASE_DETAILS" not in st.secrets: return None
        creds = json.loads(st.secrets["FIREBASE_DETAILS"])
        db = firestore.Client(credentials=service_account.Credentials.from_service_account_info(creds))
        db.collection("test").document("test").set({"test": datetime.now(fuso_br)})
        return db
    except: return None

db = init_firebase()
if not db: st.error("❌ Erro ao conectar ao banco. Verifique as configurações."); st.stop()

# ================= FUNÇÕES BANCO =================
def buscar_usuario(email):
    try:
        doc = db.collection("usuarios").document(email).get()
        return doc.to_dict() if doc.exists else None
    except: return None

def criar_usuario(dados):
    try:
        if not dados.get("email") or not dados.get("senha"): return False
        if buscar_usuario(dados["email"]): st.error("❌ Email já cadastrado"); return False
        
        dados.update({
            "criado_em": datetime.now(fuso_br),
            "ativo": False,
            "plano": "pro",
            "senha": Security.hash_senha(dados["senha"])
        })
        db.collection("usuarios").document(dados["email"]).set(dados)
        return True
    except: st.error("❌ Erro ao criar conta"); return False

@st.cache_data(ttl=60)
def carregar_dados(email):
    try:
        ref = db.collection("usuarios").document(email)
        def carregar(col): return [{"id": d.id, **d.to_dict()} for d in ref.collection(col).stream()]
        return [carregar(c) for c in ["meus_clientes", "meus_servicos", "minha_agenda", "meu_caixa"]]
    except: return [[], [], [], []]

def log_auditoria(email, acao, detalhes=""):
    try: db.collection("logs_auditoria").add({"email": email, "acao": acao, "detalhes": detalhes, "timestamp": datetime.now(fuso_br)})
    except: pass

# ================= SESSÃO =================
if "logado" not in st.session_state:
    st.session_state.update({"logado": False, "user_email": None, "user_data": None})

# ================= LOGIN/CADASTRO =================
if not st.session_state.logado:
    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        
        login_tab, cadastro_tab = st.tabs(["🔐 LOGIN", "🚀 CADASTRO"])
        
        with login_tab:
            st.subheader("Acesso ao Sistema")
            with st.form("login_form"):
                email = st.text_input("Email").lower().strip()
                senha = st.text_input("Senha", type="password")
                if st.form_submit_button("⚡ ENTRAR", use_container_width=True):
                    if email and senha:
                        usuario = buscar_usuario(email)
                        if usuario and usuario["senha"] == Security.hash_senha(senha):
                            if usuario.get("ativo"):
                                st.session_state.update({"logado": True, "user_email": email, "user_data": usuario})
                                log_auditoria(email, "LOGIN")
                                st.success("✅ Login realizado!"); time.sleep(1); st.rerun()
                            else: st.error("❌ Conta aguardando pagamento")
                        else: st.error("❌ Credenciais inválidas")
        
        with cadastro_tab:
            st.subheader("Criar Conta Pro")
            with st.form("cadastro_form", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    username = st.text_input("Username")
                    nome = st.text_input("Nome Completo")
                    email = st.text_input("Email").lower().strip()
                with col2:
                    whatsapp = st.text_input("WhatsApp")
                    negocio = st.text_input("Nome do Negócio")
                    tipo = st.selectbox("Tipo", ["Barbearia", "Salão", "Estética", "Outro"])
                senha = st.text_input("Senha", type="password")
                senha_confirm = st.text_input("Confirmar Senha", type="password")
                
                if st.form_submit_button("🚀 CRIAR CONTA PRO", use_container_width=True):
                    if not all([username, nome, email, whatsapp, negocio, senha]):
                        st.error("❌ Preencha todos os campos")
                    elif senha != senha_confirm:
                        st.error("❌ Senhas não coincidem")
                    elif not Security.email_valido(email):
                        st.error("❌ Email inválido")
                    else:
                        dados = {
                            "username": username, "nome": nome, "email": email, "whatsapp": whatsapp,
                            "nome_negocio": negocio, "tipo_negocio": tipo, "senha": senha
                        }
                        if criar_usuario(dados):
                            st.success("✅ Conta criada! Finalize o pagamento.")
                            st.link_button("💳 PAGAR AGORA", "https://buy.stripe.com/test_6oU4gB7Q4glM1JZ2Z06J200")
        
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ================= VERIFICAÇÃO PAGAMENTO =================
if not st.session_state.user_data.get("ativo"):
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.warning("## 💳 Ativação Pendente")
        st.info(f"Olá **{st.session_state.user_data.get('nome')}**, complete o pagamento para ativar.")
        st.markdown("""
        **🎯 Plano Vivv Pro:**
        - Taxa de Ativação: R$ 300,00 (única)
        - Mensalidade: R$ 49,90/mês
        - Dashboard Inteligente
        - Agendamento Automático
        - Controle Financeiro
        - Relatórios Avançados
        """)
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            if st.button("💳 FINALIZAR PAGAMENTO", use_container_width=True):
                st.link_button("Pagar com Stripe", "https://buy.stripe.com/test_6oU4gB7Q4glM1JZ2Z06J200")
        with col_b2:
            if st.button("🔄 JÁ PAGUEI - VERIFICAR", type="secondary", use_container_width=True):
                time.sleep(2); st.rerun()
        if st.button("🚪 SAIR", type="secondary"): st.session_state.logado = False; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ================= DADOS DO USUÁRIO =================
clientes, servicos, agenda, caixa = carregar_dados(st.session_state.user_email)

# ================= DASHBOARD =================
col_h1, col_h2 = st.columns([5, 1])
with col_h1: st.markdown(f"# 🚀 {st.session_state.user_data.get('nome_negocio', 'Vivv Pro')}")
with col_h2: 
    if st.button("🚪 SAIR", use_container_width=True): 
        st.session_state.logado = False; st.rerun()

# Métricas
faturamento = sum(x.get("valor", 0) for x in caixa if x.get("tipo") == "Entrada")
despesas = sum(x.get("valor", 0) for x in caixa if x.get("tipo") == "Saída")
lucro = faturamento - despesas
agendamentos_hoje = len([a for a in agenda if a.get('data') == datetime.now(fuso_br).strftime('%d/%m/%Y')])

col_m1, col_m2, col_m3, col_m4 = st.columns(4)
with col_m1: st.markdown(f'<div class="hologram-card"><small>👥 CLIENTES</small><h2>{len(clientes)}</h2></div>', unsafe_allow_html=True)
with col_m2: st.markdown(f'<div class="hologram-card"><small>💰 FATURAMENTO</small><h2 style="color:#00d4ff">R$ {faturamento:,.2f}</h2></div>', unsafe_allow_html=True)
with col_m3: st.markdown(f'<div class="hologram-card"><small>📈 LUCRO</small><h2 style="color:#4CAF50">R$ {lucro:,.2f}</h2></div>', unsafe_allow_html=True)
with col_m4: st.markdown(f'<div class="hologram-card"><small>📅 AGENDA HOJE</small><h2 style="color:#FFA726">{agendamentos_hoje}</h2></div>', unsafe_allow_html=True)

# Alertas
if agendamentos_hoje > 15: st.markdown('<div class="alert-pulse">⚠️ AGENDA LOTADA! Mais de 15 atendimentos hoje</div>', unsafe_allow_html=True)

st.divider()

# ================= GRÁFICO FINANCEIRO =================
col_g1, col_g2 = st.columns([2, 1])
with col_g1:
    if caixa:
        try:
            df = pd.DataFrame(caixa)
            df['data'] = pd.to_datetime(df['data'], format='%d/%m/%Y', errors='coerce')
            df = df.dropna().sort_values('data')
            
            fig = go.Figure()
            entradas = df[df['tipo'] == 'Entrada'].groupby('data')['valor'].sum()
            saidas = df[df['tipo'] == 'Saída'].groupby('data')['valor'].sum()
            
            if not entradas.empty:
                fig.add_trace(go.Scatter(x=entradas.index, y=entradas.values, name='Faturamento',
                                       line=dict(color='#00d4ff', width=4), fill='tozeroy',
                                       fillcolor='rgba(0, 212, 255, 0.1)'))
            
            if not saidas.empty:
                fig.add_trace(go.Scatter(x=saidas.index, y=saidas.values, name='Despesas',
                                       line=dict(color='#ff4b4b', width=4)))
            
            fig.update_layout(title="📈 Performance Financeira", height=350,
                            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                            font_color="white", hovermode="x unified")
            st.plotly_chart(fig, use_container_width=True)
        except: st.info("📊 Gráfico em processamento...")

# ================= OPERAÇÕES =================
st.markdown("### ⚡ Gestão Operacional")
tab1, tab2, tab3, tab4 = st.tabs(["📅 Agendar", "👤 Clientes", "🛠️ Serviços", "💰 Caixa"])

with tab1:
    with st.form("agendar", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            cliente = st.selectbox("Cliente", [c['nome'] for c in clientes]) if clientes else st.info("Sem clientes")
            servico = st.selectbox("Serviço", [s['nome'] for s in servicos]) if servicos else st.info("Sem serviços")
        with col2:
            data = st.date_input("Data")
            hora = st.time_input("Horário")
        if st.form_submit_button("✅ AGENDAR", use_container_width=True):
            if cliente and servico:
                try:
                    preco = next((s['preco'] for s in servicos if s['nome'] == servico), 0)
                    db.collection("usuarios").document(st.session_state.user_email).collection("minha_agenda").add({
                        "cliente": cliente, "servico": servico, "preco": preco, "data": data.strftime('%d/%m/%Y'),
                        "hora": hora.strftime('%H:%M'), "status": "Pendente", "timestamp": datetime.now(fuso_br)
                    })
                    log_auditoria(st.session_state.user_email, "AGENDAMENTO_CRIADO")
                    st.success("✅ Agendado!"); st.cache_data.clear(); time.sleep(1); st.rerun()
                except: st.error("❌ Erro ao agendar")

with tab2:
    with st.form("cliente_form", clear_on_submit=True):
        nome = st.text_input("Nome *")
        telefone = st.text_input("WhatsApp *")
        email = st.text_input("Email")
        if st.form_submit_button("👤 CADASTRAR CLIENTE", use_container_width=True):
            if nome and telefone:
                db.collection("usuarios").document(st.session_state.user_email).collection("meus_clientes").add({
                    "nome": nome, "telefone": telefone, "email": email if email else None,
                    "data_cadastro": datetime.now(fuso_br).strftime('%d/%m/%Y'), "timestamp": datetime.now(fuso_br)
                })
                st.success("✅ Cliente cadastrado!"); st.cache_data.clear(); time.sleep(1); st.rerun()

with tab3:
    with st.form("servico_form", clear_on_submit=True):
        nome = st.text_input("Nome do Serviço *")
        preco = st.number_input("Preço *", min_value=0.0, step=10.0)
        categoria = st.selectbox("Categoria", ["Corte", "Coloração", "Tratamento", "Estética", "Outros"])
        if st.form_submit_button("🛠️ CADASTRAR SERVIÇO", use_container_width=True):
            if nome and preco > 0:
                db.collection("usuarios").document(st.session_state.user_email).collection("meus_servicos").add({
                    "nome": nome, "preco": preco, "categoria": categoria, "ativo": True,
                    "data_cadastro": datetime.now(fuso_br).strftime('%d/%m/%Y'), "timestamp": datetime.now(fuso_br)
                })
                st.success("✅ Serviço cadastrado!"); st.cache_data.clear(); time.sleep(1); st.rerun()

with tab4:
    with st.form("caixa_form", clear_on_submit=True):
        desc = st.text_input("Descrição *")
        valor = st.number_input("Valor *", min_value=0.0, step=10.0)
        tipo = st.selectbox("Tipo *", ["Entrada", "Saída"])
        categoria = st.selectbox("Categoria", ["Serviço", "Produto", "Salário", "Manutenção", "Outros"])
        if st.form_submit_button("💰 LANÇAR", use_container_width=True):
            if desc and valor > 0:
                db.collection("usuarios").document(st.session_state.user_email).collection("meu_caixa").add({
                    "descricao": desc, "valor": valor, "tipo": tipo, "categoria": categoria,
                    "data": datetime.now(fuso_br).strftime('%d/%m/%Y'), "timestamp": datetime.now(fuso_br)
                })
                st.success("✅ Lançado!"); st.cache_data.clear(); time.sleep(1); st.rerun()

# ================= RELATÓRIO =================
st.divider()
if st.button("📊 GERAR RELATÓRIO EXCEL", use_container_width=True):
    try:
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='xlsxwriter') as writer:
            if clientes: pd.DataFrame(clientes).to_excel(writer, sheet_name='Clientes', index=False)
            if caixa: pd.DataFrame(caixa).to_excel(writer, sheet_name='Financeiro', index=False)
        hoje = datetime.now(fuso_br).strftime('%Y-%m-%d')
        st.download_button("⬇️ BAIXAR EXCEL", buf.getvalue(), f"Vivv_Report_{hoje}.xlsx",
                          "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    except: st.error("❌ Erro ao gerar relatório")

# ================= RODAPÉ =================
st.divider()
st.markdown("""
<div style="text-align: center; color: #888; padding: 20px;">
    <small>Vivv Pro Elite © 2024 | Transformando negócios com tecnologia de ponta</small><br>
    <small>Versão 3.0 | Sistema de gestão premium para profissionais de beleza</small>
</div>
""", unsafe_allow_html=True)
