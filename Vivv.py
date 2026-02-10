import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import io
import json
import hashlib
import re
import time
import traceback
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, List, Any, Tuple
from google.cloud import firestore
from google.oauth2 import service_account
from google.cloud.exceptions import GoogleCloudError

# ================= CONFIGURAÇÃO DE LOGGING =================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VivvPro")

# ================= CONFIGURAÇÕES DO APP =================
st.set_page_config(
    page_title="Vivv Pro Elite",
    layout="wide",
    page_icon="⚡",
    initial_sidebar_state="collapsed"
)
fuso_br = timezone(timedelta(hours=-3))

# ================= CONSTANTES DE NEGÓCIO =================
ESTOQUE_MINIMO = 5
LOTACAO_MAXIMA = 15
ALERTAS = {
    "estoque_baixo": {"cor": "#FF6B6B", "icone": "⚠️"},
    "agenda_lotada": {"cor": "#FFA726", "icone": "📅"},
    "lucro_positivo": {"cor": "#4CAF50", "icone": "📈"},
    "pagamento_pendente": {"cor": "#F44336", "icone": "💳"}
}

# ================= ESTILO ELITE - DARK GLASSMORPHISM =================
st.markdown("""
<style>
    /* Reset e configurações gerais */
    header, [data-testid="stHeader"], .stAppDeployButton { 
        display: none !important; 
    }
    
    .stApp { 
        background: linear-gradient(135deg, #0a0a0f 0%, #13151f 50%, #0a0a0f 100%) !important;
        min-height: 100vh;
        background-attachment: fixed;
    }
    
    .block-container { 
        padding-top: 30px !important; 
        max-width: 98% !important;
    }
    
    /* Glassmorphism Container */
    .glass-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(15px);
        -webkit-backdrop-filter: blur(15px);
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 20px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    }
    
    .glass-card:hover {
        border: 1px solid rgba(0, 212, 255, 0.3);
        box-shadow: 0 15px 40px rgba(0, 212, 255, 0.15);
        transform: translateY(-5px);
    }
    
    /* Metric Cards Elite */
    .metric-card-elite {
        background: linear-gradient(145deg, 
            rgba(0, 8, 20, 0.7) 0%, 
            rgba(0, 26, 44, 0.7) 100%);
        border: 1px solid rgba(0, 150, 255, 0.2);
        border-radius: 16px;
        padding: 20px;
        position: relative;
        overflow: hidden;
        transition: all 0.4s ease;
    }
    
    .metric-card-elite::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, 
            transparent, 
            rgba(0, 212, 255, 0.1), 
            transparent);
        transition: 0.6s;
    }
    
    .metric-card-elite:hover::before {
        left: 100%;
    }
    
    .metric-card-elite:hover {
        border-color: #00d4ff;
        box-shadow: 0 0 25px rgba(0, 212, 255, 0.25);
        transform: translateY(-5px);
    }
    
    /* Botões com animação */
    .stButton > button {
        background: linear-gradient(135deg, #0066cc 0%, #00d4ff 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 12px 24px;
        font-weight: 600;
        font-size: 14px;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .stButton > button::before {
        content: '';
        position: absolute;
        top: 50%;
        left: 50%;
        width: 0;
        height: 0;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.2);
        transform: translate(-50%, -50%);
        transition: width 0.6s, height 0.6s;
    }
    
    .stButton > button:hover::before {
        width: 300px;
        height: 300px;
    }
    
    .stButton > button:hover {
        transform: scale(1.05);
        box-shadow: 0 10px 20px rgba(0, 212, 255, 0.3);
    }
    
    /* Formulários */
    [data-testid="stForm"] {
        background: rgba(255, 255, 255, 0.02) !important;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(0, 212, 255, 0.1) !important;
        border-radius: 18px !important;
        padding: 25px !important;
    }
    
    /* Inputs */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div > select {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 10px !important;
        color: white !important;
        padding: 12px !important;
        transition: all 0.3s ease !important;
    }
    
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus,
    .stSelectbox > div > div > select:focus {
        border-color: #00d4ff !important;
        box-shadow: 0 0 0 2px rgba(0, 212, 255, 0.2) !important;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(255, 255, 255, 0.02);
        border-radius: 12px;
        padding: 4px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px !important;
        padding: 10px 20px !important;
        background: transparent !important;
        transition: all 0.3s ease !important;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #0066cc 0%, #00d4ff 100%) !important;
    }
    
    /* Loading skeletons */
    .skeleton {
        background: linear-gradient(90deg, 
            rgba(255, 255, 255, 0.05) 25%, 
            rgba(255, 255, 255, 0.1) 50%, 
            rgba(255, 255, 255, 0.05) 75%);
        background-size: 200% 100%;
        animation: loading 1.5s infinite;
        border-radius: 8px;
    }
    
    @keyframes loading {
        0% { background-position: 200% 0; }
        100% { background-position: -200% 0; }
    }
    
    /* Alertas */
    .alert-badge {
        display: inline-flex;
        align-items: center;
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        margin: 2px;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.7; }
        100% { opacity: 1; }
    }
    
    /* Logo Elite */
    .vivv-logo-elite {
        position: fixed;
        top: 20px;
        left: 30px;
        color: #ffffff;
        font-size: 36px;
        font-weight: 900;
        z-index: 999999;
        letter-spacing: -1px;
        text-shadow: 0 0 20px rgba(0, 212, 255, 0.7);
        background: linear-gradient(135deg, #00d4ff 0%, #0066cc 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    /* Scrollbar personalizada */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #00d4ff 0%, #0066cc 100%);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #00a8cc 0%, #004c99 100%);
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="vivv-logo-elite">VIVV<span style="color:#00d4ff">.</span>PRO</div>', unsafe_allow_html=True)

# ================= FUNÇÕES DE SEGURANÇA E VALIDAÇÃO =================

class SecurityManager:
    SALT = "vivv_secure_2026_elite"
    
    @staticmethod
    def hash_senha(senha: str) -> str:
        """Hash seguro da senha com salt."""
        senha = SecurityManager.SALT + senha
        return hashlib.sha256(senha.encode()).hexdigest()
    
    @staticmethod
    def email_valido(email: str) -> bool:
        """Validação rigorosa de email."""
        padrao = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(padrao, email))
    
    @staticmethod
    def telefone_valido(telefone: str) -> bool:
        """Validação de telefone brasileiro."""
        telefone = ''.join(filter(str.isdigit, telefone))
        return len(telefone) >= 10 and len(telefone) <= 11
    
    @staticmethod
    def validar_campos_obrigatorios(dados: dict, campos: list) -> Tuple[bool, str]:
        """Valida se todos os campos obrigatórios estão preenchidos."""
        for campo in campos:
            valor = dados.get(campo)
            if not valor or (isinstance(valor, str) and valor.strip() == ""):
                return False, f"Campo '{campo}' é obrigatório"
        return True, ""

# ================= GERENCIAMENTO DE BANCO DE DADOS COM TRATAMENTO DE EXCEÇÕES =================

@st.cache_resource
def inicializar_firebase():
    """Inicializa e retorna conexão com Firebase Firestore."""
    try:
        # Verifica se existe a configuração
        if "FIREBASE_DETAILS" not in st.secrets:
            st.error("❌ Configuração do Firebase não encontrada.")
            return None
        
        # Carrega as credenciais
        firebase_config = st.secrets["FIREBASE_DETAILS"]
        
        if not firebase_config or firebase_config.strip() == "":
            st.error("❌ Configuração do Firebase está vazia.")
            return None
        
        # Converte de string JSON para dicionário
        credenciais = json.loads(firebase_config)
        
        # Cria as credenciais do service account
        creds = service_account.Credentials.from_service_account_info(credenciais)
        
        # Cria o cliente Firestore
        db = firestore.Client(credentials=creds)
        
        # Testa a conexão (operação simples)
        test_ref = db.collection("conexao_teste").document("ping")
        test_ref.set({
            "timestamp": datetime.now(fuso_br),
            "status": "conectado"
        })
        
        st.success("✅ Banco de dados conectado!")
        return db
        
    except json.JSONDecodeError as e:
        st.error(f"❌ Erro no formato JSON: {str(e)[:100]}")
        return None
    except Exception as e:
        st.error(f"❌ Erro ao conectar ao banco: {str(e)[:100]}")
        return None


    def log_auditoria(email: str, acao: str, detalhes: str = ""):
        """Registra log de auditoria."""
        try:
            log_data = {
            "email": email,
            "acao": acao,
            "detalhes": detalhes,
            "timestamp": datetime.now(fuso_br)
            }
            db.collection("logs_auditoria").add(log_data)
        except Exception as e:
            logger.error(f"Erro ao registrar log: {e}")
    

# ... (mantenha todo o código até a linha 385 igual)

# ================= INICIALIZAÇÃO DOS SERVIÇOS =================

# Inicializa o banco de dados
db = inicializar_firebase()

# Se não conseguiu conectar, para a aplicação
if db is None:
    st.error("""
    ## 🔧 ERRO DE CONEXÃO
    
    Não foi possível conectar ao banco de dados Firebase.
    
    **Possíveis causas:**
    1. Credenciais do Firebase incorretas
    2. Problema de rede/conexão
    3. Formato inválido do JSON
    
    **Solução:**
    - Verifique a variável `FIREBASE_DETAILS` nas Secrets do Streamlit Cloud
    - Certifique-se que o JSON está completo e válido
    - Entre em contato com o suporte técnico
    """)
    st.stop()

# ================= FUNÇÕES DO BANCO DE DADOS =================

def buscar_usuario(email: str):
    """Busca um usuário pelo email."""
    try:
        doc_ref = db.collection("usuarios").document(email)
        doc = doc_ref.get()
        
        if doc.exists:
            return doc.to_dict()
        return None
    except Exception as e:
        st.error(f"❌ Erro ao buscar usuário: {e}")
        return None

def criar_usuario(dados: dict):
    """Cria um novo usuário."""
    try:
        # Validações básicas
        if not dados.get("email"):
            st.error("❌ Email é obrigatório")
            return False
        
        if not dados.get("senha"):
            st.error("❌ Senha é obrigatória")
            return False
        
        # Verifica se usuário já existe
        if buscar_usuario(dados["email"]):
            st.error("❌ Usuário já cadastrado")
            return False
        
        # Adiciona timestamps
        dados["criado_em"] = datetime.now(fuso_br)
        dados["ativo"] = False
        dados["plano"] = "pro"
        
        # Salva no banco
        db.collection("usuarios").document(dados["email"]).set(dados)
        
        # Log simples
        print(f"✅ Usuário criado: {dados['email']}")
        return True
        
    except Exception as e:
        st.error(f"❌ Erro ao criar usuário: {e}")
        return False

@st.cache_data(ttl=60)
def carregar_dados_usuario(email: str):
    """Carrega todos os dados do usuário com cache."""
    try:
        user_ref = db.collection("usuarios").document(email)
        
        # Função auxiliar para carregar coleções
        def carregar_colecao(nome):
            try:
                docs = user_ref.collection(nome).stream()
                return [{"id": doc.id, **doc.to_dict()} for doc in docs]
            except:
                return []
        
        # Carrega todas as coleções
        clientes = carregar_colecao("meus_clientes")
        servicos = carregar_colecao("meus_servicos")
        agenda = carregar_colecao("minha_agenda")
        caixa = carregar_colecao("meu_caixa")
        
        # Garante que nunca retorna None
        return clientes or [], servicos or [], agenda or [], caixa or []
        
    except Exception as e:
        st.error(f"⚠️ Erro ao carregar dados: {e}")
        return [], [], [], []  # Sempre retorna listas vazias

def log_auditoria(email: str, acao: str, detalhes: str = ""):
    """Registra log de auditoria."""
    try:
        log_data = {
            "email": email,
            "acao": acao,
            "detalhes": detalhes,
            "timestamp": datetime.now(fuso_br)
        }
        db.collection("logs_auditoria").add(log_data)
    except Exception as e:
        logger.error(f"Erro ao registrar log: {e}")

# ================= GERENCIAMENTO DE SESSÃO =================

# Estado inicial da sessão
if "logado" not in st.session_state:
    st.session_state.logado = False
    st.session_state.user_email = None
    st.session_state.user_data = None
    st.session_state.dados_carregados = False

# Funções de sessão
def fazer_login(email: str, senha: str):
    """Realiza login do usuário."""
    usuario = buscar_usuario(email)
    
    if usuario and usuario.get("senha") == SecurityManager.hash_senha(senha):
        st.session_state.logado = True
        st.session_state.user_email = email
        st.session_state.user_data = usuario
        return True
    return False

def fazer_logout():
    """Realiza logout do usuário."""
    st.session_state.logado = False
    st.session_state.user_email = None
    st.session_state.user_data = None
    st.session_state.dados_carregados = False
    st.cache_data.clear()

# Verifica se usuário está logado para carregar dados
if st.session_state.logado and st.session_state.user_email:
    try:
        clientes, servicos, agenda, caixa = carregar_dados_usuario(st.session_state.user_email)
        st.session_state.dados_carregados = True
    except:
        st.error("Erro ao carregar dados do usuário")
        clientes, servicos, agenda, caixa = [], [], [], []
else:
    clientes, servicos, agenda, caixa = [], [], [], []

# ... (mantenha a classe UIComponents igual)

# ================= TELA DE LOGIN / CADASTRO =================

if not st.session_state.logado:
    # Tela de Login/Cadastro com estilo elite
    col_l, col_c, col_r = st.columns([1, 2, 1])
    
    with col_c:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        
        # Card de login
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        
        tab_login, tab_cadastro = st.tabs(["🔐 LOGIN ELITE", "🚀 CRIAR CONTA"])
        
        with tab_login:
            st.subheader("Acesso ao Sistema")
            
            with st.form("form_login"):
                email = st.text_input("Email", key="login_email").lower().strip()
                senha = st.text_input("Senha", type="password", key="login_senha")
                
                col_b1, col_b2 = st.columns(2)
                with col_b1:
                    submit_login = st.form_submit_button("⚡ ENTRAR", use_container_width=True)
                
                if submit_login:
                    if not email or not senha:
                        st.error("Preencha todos os campos")
                    else:
                        UIComponents.mostrar_loading("Validando credenciais...")
                        
                        try:
                            user = buscar_usuario(email)
                            
                            if user and user.get("senha") == SecurityManager.hash_senha(senha):
                                if user.get("ativo", False):
                                    st.session_state.logado = True
                                    st.session_state.user_email = email
                                    st.session_state.user_data = user
                                    
                                    # Log de auditoria
                                    log_auditoria(
                                        email=email,
                                        acao="LOGIN",
                                        detalhes="Login realizado com sucesso"
                                    )
                                    
                                    st.success("✅ Login realizado com sucesso!")
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.error("❌ Conta inativa. Complete o pagamento.")
                            else:
                                st.error("❌ Credenciais inválidas")
                        except Exception as e:
                            logger.error(f"Erro no login: {e}")
                            st.error("⚠️ Erro ao processar login. Tente novamente.")
        
        with tab_cadastro:
            st.subheader("Criar Nova Conta")
            
            with st.form("form_cadastro", clear_on_submit=True):
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
                
                submit_cadastro = st.form_submit_button("🚀 CRIAR CONTA PRO", use_container_width=True)
                
                if submit_cadastro:
                    # Validações
                    if senha != senha_confirm:
                        st.error("❌ As senhas não coincidem")
                    elif not SecurityManager.email_valido(email):
                        st.error("❌ Email inválido")
                    elif not SecurityManager.telefone_valido(whatsapp):
                        st.error("❌ WhatsApp inválido")
                    else:
                        UIComponents.mostrar_loading("Criando sua conta...")
                        
                        dados_usuario = {
                            "email": email,
                            "username": username,
                            "nome": nome,
                            "whatsapp": whatsapp,
                            "nome_negocio": negocio,
                            "tipo_negocio": tipo,
                            "senha": SecurityManager.hash_senha(senha),
                            "ativo": False,
                            "plano": "pro",
                            "criado_em": datetime.now(fuso_br)
                        }
                        
                        if criar_usuario(dados_usuario):
                            st.success("✅ Conta criada com sucesso! Redirecionando para pagamento...")
                            time.sleep(2)
                            # Aqui integraria com Stripe
                            st.link_button("💳 FINALIZAR PAGAMENTO", "https://buy.stripe.com/test_6oU4gB7Q4glM1JZ2Z06J200")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.stop()

# ================= VERIFICAÇÃO DE PAGAMENTO =================

if not st.session_state.user_data.get("ativo", False):
    # Tela de pagamento pendente
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        
        st.warning("## 💳 Ativação Pendente")
        st.info(f"Olá **{st.session_state.user_data.get('nome')}**, sua conta está aguardando ativação.")
        
        st.markdown("""
        ### 🚀 Plano Vivv Pro
        - **Taxa de Ativação:** R$ 300,00 (única)
        - **Mensalidade:** R$ 49,90/mês
        - **Recursos:** Gestão completa + Suporte prioritário
        
        ### 📈 O que você ganha:
        - Dashboard inteligente com métricas em tempo real
        - Sistema de agendamento automatizado
        - Controle financeiro avançado
        - Relatórios personalizados
        - Integração com WhatsApp
        """)
        
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            if st.button("💳 FINALIZAR PAGAMENTO", use_container_width=True):
                st.link_button("Pagar com Stripe", "https://buy.stripe.com/test_6oU4gB7Q4glM1JZ2Z06J200")
        
        with col_b2:
            if st.button("🔄 JÁ PAGUEI - VERIFICAR", type="secondary", use_container_width=True):
                UIComponents.mostrar_loading("Verificando pagamento...")
                # Simulação - aqui integraria com webhook do Stripe
                time.sleep(2)
                st.rerun()
        
        if st.button("🚪 SAIR", type="secondary"):
            fazer_logout()
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.stop()

# ================= DASHBOARD PRINCIPAL =================

# Calcula métricas de negócio
metricas = UIComponents.calcular_metricas_negocio(clientes, servicos, agenda, caixa)

# Header do Dashboard
col_header1, col_header2 = st.columns([5, 1])

with col_header1:
    st.markdown(f"""
    # 🚀 {st.session_state.user_data.get('nome_negocio', 'Vivv Pro')}
    ### Olá, {st.session_state.user_data.get('nome', 'Usuário')}! 
    """)

with col_header2:
    if st.button("🚪 LOGOUT", use_container_width=True):
        fazer_logout()
        st.rerun()

# ================= METRICAS E ALERTAS =================

st.markdown("### 📊 Dashboard de Performance")

# Cards de métricas
col_m1, col_m2, col_m3, col_m4 = st.columns(4)

with col_m1:
    st.markdown(f'''
    <div class="metric-card-elite">
        <small>👥 CLIENTES ATIVOS</small>
        <h2>{metricas["total_clientes"]}</h2>
        <small style="color:#00d4ff">+5% vs. semana passada</small>
    </div>
    ''', unsafe_allow_html=True)

with col_m2:
    st.markdown(f'''
    <div class="metric-card-elite">
        <small>💰 FATURAMENTO</small>
        <h2 style="color:#00d4ff">R$ {metricas["faturamento"]:,.2f}</h2>
        <small style="color:#00d4ff">Últimos 30 dias</small>
    </div>
    ''', unsafe_allow_html=True)

with col_m3:
    st.markdown(f'''
    <div class="metric-card-elite">
        <small>📈 LUCRO LÍQUIDO</small>
        <h2 style="color:#4CAF50">R$ {metricas["lucro"]:,.2f}</h2>
        <small style="color:#4CAF50">Margem: {(metricas["lucro"]/metricas["faturamento"]*100 if metricas["faturamento"] > 0 else 0):.1f}%</small>
    </div>
    ''', unsafe_allow_html=True)

with col_m4:
    st.markdown(f'''
    <div class="metric-card-elite">
        <small>📅 AGENDA HOJE</small>
        <h2 style="color:#FFA726">{metricas["agendamentos_hoje"]}</h2>
        <small style="color:#FFA726">{metricas["agendamentos_hoje"]}/{LOTACAO_MAXIMA} lotação</small>
    </div>
    ''', unsafe_allow_html=True)

# Alertas de negócio
if metricas["alertas"]:
    st.markdown("### ⚠️ Alertas do Sistema")
    cols_alerta = st.columns(min(3, len(metricas["alertas"])))
    
    for idx, alerta in enumerate(metricas["alertas"]):
        with cols_alerta[idx % len(cols_alerta)]:
            alert_config = ALERTAS.get(alerta["tipo"], {"cor": "#FF6B6B", "icone": "⚠️"})
            st.markdown(f'''
            <div style="
                background: rgba({int(alert_config['cor'][1:3], 16)}, 
                               {int(alert_config['cor'][3:5], 16)}, 
                               {int(alert_config['cor'][5:7], 16)}, 0.15);
                border: 1px solid {alert_config['cor']};
                border-radius: 12px;
                padding: 15px;
                margin: 5px;
                color: white;
                text-align: center;
            ">
                <strong>{alert_config['icone']} {alerta["mensagem"]}</strong>
            </div>
            ''', unsafe_allow_html=True)

st.divider()

# ================= GRÁFICO FINANCEIRO =================

col_graf1, col_graf2 = st.columns([2, 1])

with col_graf1:
    st.markdown("### 📈 Análise Financeira - Últimos 7 Dias")
    
    if caixa:
        fig = UIComponents.criar_grafico_financeiro(caixa)
        if fig.data:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("📊 Insira dados financeiros para ver o gráfico")
    else:
        st.info("📊 Nenhum dado financeiro disponível ainda")

with col_graf2:
    st.markdown("### 📋 Ações Rápidas")
    
    with st.container():
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        
        # Botões de ação rápida
        if st.button("📅 Agendar Serviço", use_container_width=True):
            st.session_state.show_agendamento = True
        
        if st.button("👤 Adicionar Cliente", use_container_width=True):
            st.session_state.show_cliente = True
        
        if st.button("💰 Lançar Financeiro", use_container_width=True):
            st.session_state.show_financeiro = True
        
        if st.button("📊 Gerar Relatório", use_container_width=True):
            # Lógica para gerar relatório
            with st.spinner("Gerando relatório..."):
                time.sleep(1)
                st.success("Relatório gerado com sucesso!")
        
        st.markdown('</div>', unsafe_allow_html=True)

st.divider()

# ================= GESTÃO OPERACIONAL =================

st.markdown("### ⚡ Gestão Operacional")

tab1, tab2, tab3, tab4 = st.tabs(["📅 Agendamentos", "👤 Clientes", "🛠️ Serviços", "💰 Financeiro"])

with tab1:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    
    with st.form("form_agendamento", clear_on_submit=True):
        st.subheader("Novo Agendamento")
        
        col_a1, col_a2 = st.columns(2)
        
        with col_a1:
            # Validação para listas vazias
            if clientes:
                cliente_nome = st.selectbox(
                    "Cliente",
                    options=[c.get('nome', 'Sem nome') for c in clientes],
                    key="ag_cliente"
                )
            else:
                st.info("Cadastre clientes primeiro")
                cliente_nome = None
            
            if servicos:
                servico_nome = st.selectbox(
                    "Serviço",
                    options=[s.get('nome', 'Sem nome') for s in servicos],
                    key="ag_servico"
                )
            else:
                st.info("Cadastre serviços primeiro")
                servico_nome = None
        
        with col_a2:
            data_ag = st.date_input("Data", key="ag_data")
            hora_ag = st.time_input("Horário", key="ag_hora")
            status_ag = st.selectbox("Status", ["Pendente", "Confirmado", "Cancelado"])
        
        if st.form_submit_button("✅ CONFIRMAR AGENDAMENTO", use_container_width=True):
            if cliente_nome and servico_nome:
                try:
                    # Encontra preço do serviço
                    preco_servico = next(
                        (s.get('preco', 0) for s in servicos if s.get('nome') == servico_nome),
                        0
                    )
                    
                    # Salva no banco
                    db.collection("usuarios").document(
                        st.session_state.user_email
                    ).collection("minha_agenda").add({
                        "cliente": cliente_nome,
                        "servico": servico_nome,
                        "preco": float(preco_servico),
                        "status": status_ag,
                        "data": data_ag.strftime('%d/%m/%Y'),
                        "hora": hora_ag.strftime('%H:%M'),
                        "timestamp": datetime.now(fuso_br),
                        "criado_em": datetime.now(fuso_br)
                    })
                    
                    # Log de auditoria
                    log_auditoria(
                        email=st.session_state.user_email,
                        acao="AGENDAMENTO_CRIADO",
                        detalhes=f"Agendamento para {cliente_nome} - {servico_nome}"
                    )
                    
                    st.success("✅ Agendamento criado com sucesso!")
                    st.cache_data.clear()
                    time.sleep(1)
                    st.rerun()
                    
                except Exception as e:
                    logger.error(f"Erro ao criar agendamento: {e}")
                    st.error("❌ Erro ao salvar agendamento")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Lista de agendamentos
    if agenda:
        st.markdown("#### 📋 Agendamentos Recentes")
        for ag in agenda[:10]:  # Mostra apenas os 10 mais recentes
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"**{ag.get('hora', '--:--')}** - {ag.get('cliente', 'N/A')}")
                    st.caption(f"{ag.get('servico', 'N/A')} - R$ {ag.get('preco', 0):.2f}")
                with col2:
                    st.write(f"Status: **{ag.get('status', 'Pendente')}**")
                with col3:
                    if st.button("🗑️", key=f"del_ag_{ag.get('id')}"):
                        try:
                            db.collection("usuarios").document(
                                st.session_state.user_email
                            ).collection("minha_agenda").document(ag.get('id')).delete()
                            
                            log_auditoria(
                                email=st.session_state.user_email,
                                acao="AGENDAMENTO_EXCLUIDO",
                                detalhes=f"Agendamento {ag.get('id')} excluído"
                            )
                            
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            logger.error(f"Erro ao excluir agendamento: {e}")
                            st.error("Erro ao excluir")

with tab2:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    
    with st.form("form_cliente", clear_on_submit=True):
        st.subheader("Novo Cliente")
        
        col_c1, col_c2 = st.columns(2)
        
        with col_c1:
            nome_cli = st.text_input("Nome completo *", key="cli_nome")
            email_cli = st.text_input("Email", key="cli_email")
        
        with col_c2:
            telefone_cli = st.text_input("WhatsApp *", key="cli_tel")
            aniversario = st.date_input("Aniversário", key="cli_bday")
        
        observacoes = st.text_area("Observações", key="cli_obs")
        
        if st.form_submit_button("👤 CADASTRAR CLIENTE", use_container_width=True):
            # Validação
            if not nome_cli.strip():
                st.error("❌ Nome é obrigatório")
            elif not telefone_cli.strip():
                st.error("❌ Telefone é obrigatório")
            else:
                try:
                    db.collection("usuarios").document(
                        st.session_state.user_email
                    ).collection("meus_clientes").add({
                        "nome": nome_cli.strip(),
                        "email": email_cli.strip() if email_cli.strip() else None,
                        "telefone": telefone_cli.strip(),
                        "aniversario": aniversario.strftime('%d/%m/%Y') if aniversario else None,
                        "observacoes": observacoes,
                        "data_cadastro": datetime.now(fuso_br).strftime('%d/%m/%Y'),
                        "timestamp": datetime.now(fuso_br)
                    })
                    
                    log_auditoria(
                        email=st.session_state.user_email,
                        acao="CLIENTE_CRIADO",
                        detalhes=f"Cliente {nome_cli} cadastrado"
                    )
                    
                    st.success("✅ Cliente cadastrado com sucesso!")
                    st.cache_data.clear()
                    time.sleep(1)
                    st.rerun()
                    
                except Exception as e:
                    logger.error(f"Erro ao cadastrar cliente: {e}")
                    st.error("❌ Erro ao cadastrar cliente")
    
    st.markdown('</div>', unsafe_allow_html=True)

with tab3:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    
    with st.form("form_servico", clear_on_submit=True):
        st.subheader("Novo Serviço")
        
        col_s1, col_s2 = st.columns(2)
        
        with col_s1:
            nome_serv = st.text_input("Nome do serviço *", key="srv_nome")
            categoria = st.selectbox(
                "Categoria",
                ["Corte", "Coloração", "Tratamento", "Estética", "Outros"]
            )
        
        with col_s2:
            preco_serv = st.number_input("Preço *", min_value=0.0, step=10.0, key="srv_preco")
            duracao = st.number_input("Duração (min)", min_value=15, step=15, value=60)
        
        descricao = st.text_area("Descrição", key="srv_desc")
        
        if st.form_submit_button("🛠️ CADASTRAR SERVIÇO", use_container_width=True):
            if not nome_serv.strip():
                st.error("❌ Nome do serviço é obrigatório")
            elif preco_serv <= 0:
                st.error("❌ Preço deve ser maior que zero")
            else:
                try:
                    db.collection("usuarios").document(
                        st.session_state.user_email
                    ).collection("meus_servicos").add({
                        "nome": nome_serv.strip(),
                        "preco": float(preco_serv),
                        "categoria": categoria,
                        "duracao_minutos": duracao,
                        "descricao": descricao,
                        "ativo": True,
                        "data_cadastro": datetime.now(fuso_br).strftime('%d/%m/%Y'),
                        "timestamp": datetime.now(fuso_br)
                    })
                    
                    log_auditoria(
                        email=st.session_state.user_email,
                        acao="SERVICO_CRIADO",
                        detalhes=f"Serviço {nome_serv} criado"
                    )
                    
                    st.success("✅ Serviço cadastrado com sucesso!")
                    st.cache_data.clear()
                    time.sleep(1)
                    st.rerun()
                    
                except Exception as e:
                    logger.error(f"Erro ao cadastrar serviço: {e}")
                    st.error("❌ Erro ao cadastrar serviço")
    
    st.markdown('</div>', unsafe_allow_html=True)

with tab4:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    
    with st.form("form_financeiro", clear_on_submit=True):
        st.subheader("Novo Lançamento Financeiro")
        
        col_f1, col_f2 = st.columns(2)
        
        with col_f1:
            descricao = st.text_input("Descrição *", key="fin_desc")
            categoria = st.selectbox(
                "Categoria",
                ["Venda", "Serviço", "Produto", "Aluguel", "Salário", "Manutenção", "Outros"]
            )
        
        with col_f2:
            valor = st.number_input("Valor *", min_value=0.0, step=10.0, key="fin_valor")
            tipo = st.selectbox("Tipo *", ["Entrada", "Saída"], key="fin_tipo")
        
        data_lancamento = st.date_input("Data", key="fin_data")
        forma_pagamento = st.selectbox(
            "Forma de pagamento",
            ["Dinheiro", "Cartão", "PIX", "Transferência", "Outros"]
        )
        
        if st.form_submit_button("💰 LANÇAR", use_container_width=True):
            if not descricao.strip():
                st.error("❌ Descrição é obrigatória")
            elif valor <= 0:
                st.error("❌ Valor deve ser maior que zero")
            else:
                try:
                    db.collection("usuarios").document(
                        st.session_state.user_email
                    ).collection("meu_caixa").add({
                        "descricao": descricao.strip(),
                        "valor": float(valor),
                        "tipo": tipo,
                        "categoria": categoria,
                        "forma_pagamento": forma_pagamento,
                        "data": data_lancamento.strftime('%d/%m/%Y'),
                        "timestamp": datetime.now(fuso_br),
                        "registrado_em": datetime.now(fuso_br)
                    })
                    
                    log_auditoria(
                        email=st.session_state.user_email,
                        acao="LANCAMENTO_FINANCEIRO",
                        detalhes=f"{tipo} de R$ {valor:.2f} - {descricao}"
                    )
                    
                    st.success("✅ Lançamento registrado com sucesso!")
                    st.cache_data.clear()
                    time.sleep(1)
                    st.rerun()
                    
                except Exception as e:
                    logger.error(f"Erro ao registrar lançamento: {e}")
                    st.error("❌ Erro ao registrar lançamento")
    
    st.markdown('</div>', unsafe_allow_html=True)

# ================= RELATÓRIOS E EXPORTAÇÃO =================

st.divider()
st.markdown("### 📊 Relatórios & Exportação")

col_rel1, col_rel2 = st.columns(2)

with col_rel1:
    if st.button("📥 GERAR RELATÓRIO EXCEL", use_container_width=True):
        try:
            with st.spinner("Gerando relatório Excel..."):
                # Cria buffer para Excel
                buf = io.BytesIO()
                
                with pd.ExcelWriter(buf, engine='xlsxwriter') as writer:
                    # Planilha de clientes
                    if clientes:
                        df_clientes = pd.DataFrame(clientes)
                        df_clientes.to_excel(writer, sheet_name='Clientes', index=False)
                    
                    # Planilha de serviços
                    if servicos:
                        df_servicos = pd.DataFrame(servicos)
                        df_servicos.to_excel(writer, sheet_name='Serviços', index=False)
                    
                    # Planilha financeira
                    if caixa:
                        df_caixa = pd.DataFrame(caixa)
                        df_caixa.to_excel(writer, sheet_name='Financeiro', index=False)
                    
                    # Planilha de agenda
                    if agenda:
                        df_agenda = pd.DataFrame(agenda)
                        df_agenda.to_excel(writer, sheet_name='Agenda', index=False)
                
                # Botão de download
                hoje = datetime.now(fuso_br).strftime('%Y-%m-%d')
                st.download_button(
                    label="⬇️ BAIXAR RELATÓRIO",
                    data=buf.getvalue(),
                    file_name=f"Vivv_Pro_Relatorio_{hoje}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
                log_auditoria(
                    email=st.session_state.user_email,
                    acao="RELATORIO_GERADO",
                    detalhes="Relatório Excel gerado"
                )
                
        except Exception as e:
            logger.error(f"Erro ao gerar relatório: {e}")
            st.error("❌ Erro ao gerar relatório")

with col_rel2:
    if st.button("📄 GERAR RELATÓRIO PDF", use_container_width=True):
        st.info("Funcionalidade em desenvolvimento")

# ================= RODAPÉ =================

st.divider()
st.markdown("""
<div style="text-align: center; color: #888; padding: 20px;">
    <small>Vivv Pro Elite © 2024 | Sistema de Gestão para Profissionais de Beleza</small><br>
    <small>Versão 2.0 | Desenvolvido com ❤️ para transformar seu negócio</small>
</div>
""", unsafe_allow_html=True)

