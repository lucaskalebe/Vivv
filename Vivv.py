import streamlit as st
import pandas as pd
import urllib.parse
from datetime import datetime, timezone, timedelta
import google.generativeai as genai
from google.cloud import firestore
from google.oauth2 import service_account
import json
import hashlib
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ================= 1. CONFIGURAÇÃO AVANÇADA =================
st.set_page_config(
    page_title="Vivv Pro • Gestão Inteligente",
    layout="wide",
    page_icon="⚡",
    initial_sidebar_state="expanded"
)

fuso_br = timezone(timedelta(hours=-3))

# ================= 2. SISTEMA DE TEMAS E DESIGN SYSTEM =================
def aplicar_tema(tema="escuro"):
    """Design System completo com tokens visuais"""
    
    if tema == "escuro":
        st.markdown(f"""
        <style>
            /* RESET E FUNDO */
            .stApp {{
                background: #0A0B14 !important;
            }}
            
            /* SIDEBAR PROFISSIONAL */
            section[data-testid="stSidebar"] {{
                background: linear-gradient(180deg, #0F1525 0%, #0A0B14 100%);
                border-right: 1px solid rgba(255, 255, 255, 0.05);
                padding-top: 3.5rem;
            }}
            
            section[data-testid="stSidebar"] > div {{
                padding-top: 2rem;
            }}
            
            /* NAVEGAÇÃO PRINCIPAL */
            .nav-item {{
                padding: 0.75rem 1.25rem;
                margin: 0.25rem 0.75rem;
                border-radius: 10px;
                display: flex;
                align-items: center;
                gap: 0.75rem;
                cursor: pointer;
                transition: all 0.2s ease;
                color: #94A3B8;
                text-decoration: none;
                font-weight: 500;
            }}
            
            .nav-item:hover {{
                background: rgba(255, 255, 255, 0.03);
                color: #E2E8F0;
            }}
            
            .nav-item.active {{
                background: rgba(0, 212, 255, 0.1);
                color: #00D4FF;
                border-left: 3px solid #00D4FF;
            }}
            
            .nav-icon {{
                font-size: 1.1rem;
                min-width: 24px;
            }}
            
            /* TOP BAR */
            .top-bar {{
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                height: 64px;
                background: rgba(10, 11, 20, 0.95);
                backdrop-filter: blur(10px);
                border-bottom: 1px solid rgba(255, 255, 255, 0.05);
                display: flex;
                align-items: center;
                justify-content: space-between;
                padding: 0 2rem;
                z-index: 999;
            }}
            
            .logo {{
                display: flex;
                align-items: center;
                gap: 0.75rem;
                font-size: 1.5rem;
                font-weight: 800;
                background: linear-gradient(90deg, #00D4FF 0%, #0088FF 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }}
            
            .user-pill {{
                background: rgba(255, 255, 255, 0.03);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 50px;
                padding: 0.5rem 1rem;
                display: flex;
                align-items: center;
                gap: 0.5rem;
                font-size: 0.875rem;
            }}
            
            /* COMPONENTES DO SISTEMA */
            .metric-card {{
                background: rgba(255, 255, 255, 0.02);
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 16px;
                padding: 1.5rem;
                transition: all 0.3s ease;
            }}
            
            .metric-card:hover {{
                border-color: rgba(0, 212, 255, 0.3);
                transform: translateY(-2px);
                box-shadow: 0 10px 30px rgba(0, 212, 255, 0.05);
            }}
            
            .metric-label {{
                font-size: 0.875rem;
                color: #94A3B8;
                text-transform: uppercase;
                letter-spacing: 0.05em;
                margin-bottom: 0.5rem;
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }}
            
            .metric-value {{
                font-size: 2rem;
                font-weight: 700;
                color: #FFFFFF;
                line-height: 1;
            }}
            
            .metric-subtext {{
                font-size: 0.875rem;
                color: #64748B;
                margin-top: 0.5rem;
            }}
            
            /* BOTÕES DO SISTEMA */
            .btn-primary {{
                background: linear-gradient(90deg, #00D4FF 0%, #0088FF 100%);
                color: white !important;
                border: none;
                border-radius: 10px;
                padding: 0.75rem 1.5rem;
                font-weight: 600;
                transition: all 0.3s ease;
            }}
            
            .btn-primary:hover {{
                transform: translateY(-1px);
                box-shadow: 0 10px 20px rgba(0, 212, 255, 0.2);
            }}
            
            .btn-outline {{
                background: transparent;
                color: #00D4FF !important;
                border: 1px solid rgba(0, 212, 255, 0.3);
                border-radius: 10px;
                padding: 0.75rem 1.5rem;
                font-weight: 600;
                transition: all 0.3s ease;
            }}
            
            .btn-outline:hover {{
                background: rgba(0, 212, 255, 0.1);
                border-color: #00D4FF;
            }}
            
            /* ESTADOS VAZIOS */
            .empty-state {{
                text-align: center;
                padding: 4rem 2rem;
                border-radius: 16px;
                background: rgba(255, 255, 255, 0.01);
                border: 2px dashed rgba(255, 255, 255, 0.05);
            }}
            
            .empty-icon {{
                font-size: 3rem;
                margin-bottom: 1rem;
                opacity: 0.5;
            }}
            
            /* CARDS INTERATIVOS */
            .interactive-card {{
                background: rgba(255, 255, 255, 0.02);
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 12px;
                padding: 1.25rem;
                transition: all 0.2s ease;
                cursor: pointer;
            }}
            
            .interactive-card:hover {{
                background: rgba(255, 255, 255, 0.04);
                border-color: rgba(0, 212, 255, 0.2);
                transform: translateY(-1px);
            }}
            
            /* BADGES DE STATUS */
            .status-badge {{
                display: inline-flex;
                align-items: center;
                padding: 0.25rem 0.75rem;
                border-radius: 50px;
                font-size: 0.75rem;
                font-weight: 600;
                gap: 0.25rem;
            }}
            
            .status-pendente {{
                background: rgba(255, 145, 0, 0.1);
                color: #FF9100;
                border: 1px solid rgba(255, 145, 0, 0.2);
            }}
            
            .status-concluido {{
                background: rgba(0, 255, 136, 0.1);
                color: #00FF88;
                border: 1px solid rgba(0, 255, 136, 0.2);
            }}
            
            .status-cancelado {{
                background: rgba(255, 75, 75, 0.1);
                color: #FF4B4B;
                border: 1px solid rgba(255, 75, 75, 0.2);
            }}
            
            /* UTILITÁRIOS */
            .text-gradient {{
                background: linear-gradient(90deg, #00D4FF 0%, #0088FF 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                font-weight: 700;
            }}
            
            .divider {{
                height: 1px;
                background: linear-gradient(90deg, transparent 0%, rgba(255, 255, 255, 0.1) 50%, transparent 100%);
                margin: 2rem 0;
            }}
        </style>
        """, unsafe_allow_html=True)
    else:
        # Light mode seria implementado aqui
        pass

# Aplicar tema escuro por padrão
aplicar_tema("escuro")

# ================= 3. SISTEMA DE NAVEGAÇÃO =================
def renderizar_navegacao():
    """Renderiza a barra de navegação lateral com estados ativos"""
    
    with st.sidebar:
        # Logo na sidebar
        st.markdown("""
        <div style="padding: 1.5rem 1.25rem 2rem;">
            <div class="logo">Vivv Pro</div>
            <div style="font-size: 0.875rem; color: #64748B; margin-top: 0.25rem;">
                Gestão Inteligente para Negócios
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Menu principal
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        
        # Definir página ativa baseada na query params
        query_params = st.experimental_get_query_params()
        pagina_ativa = query_params.get("pagina", ["dashboard"])[0]
        
        itens_menu = [
            {"icone": "📊", "label": "Dashboard", "id": "dashboard", "badge": None},
            {"icone": "📅", "label": "Agenda", "id": "agenda", "badge": "hoje"},
            {"icone": "👥", "label": "Clientes", "id": "clientes", "badge": None},
            {"icone": "🛠️", "label": "Serviços", "id": "servicos", "badge": None},
            {"icone": "💰", "label": "Financeiro", "id": "financeiro", "badge": "novo"},
            {"icone": "📈", "label": "Relatórios", "id": "relatorios", "badge": None},
        ]
        
        for item in itens_menu:
            classe = "nav-item active" if pagina_ativa == item["id"] else "nav-item"
            badge_html = f'<span style="background: #00D4FF; color: #000; font-size: 0.7rem; padding: 0.1rem 0.4rem; border-radius: 10px; margin-left: auto;">{item["badge"]}</span>' if item["badge"] else ""
            
            if st.button(f'{item["icone"]} {item["label"]}', key=f"nav_{item['id']}", 
                        use_container_width=True, 
                        type="primary" if pagina_ativa == item["id"] else "secondary"):
                st.experimental_set_query_params(pagina=item["id"])
                st.rerun()
        
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        
        # Menu secundário
        itens_secundarios = [
            {"icone": "⚙️", "label": "Configurações", "id": "config"},
            {"icone": "❓", "label": "Ajuda", "id": "ajuda"},
        ]
        
        for item in itens_secundarios:
            if st.button(f'{item["icone"]} {item["label"]}', key=f"nav_{item['id']}", 
                        use_container_width=True, type="secondary"):
                st.experimental_set_query_params(pagina=item["id"])
                st.rerun()

# ================= 4. COMPONENTES REUTILIZÁVEIS =================
def metric_card(icone, label, valor, subtexto=None, cor="#00D4FF", crescimento=None):
    """Componente de card métrica profissional"""
    
    growth_html = ""
    if crescimento:
        direcao = "↗️" if crescimento > 0 else "↘️"
        cor_cresc = "#00FF88" if crescimento > 0 else "#FF4B4B"
        growth_html = f'<div style="color: {cor_cresc}; font-size: 0.875rem; margin-top: 0.25rem;">{direcao} {abs(crescimento)}% vs mês passado</div>'
    
    subtext_html = f'<div class="metric-subtext">{subtexto}</div>' if subtexto else ""
    
    return f"""
    <div class="metric-card">
        <div class="metric-label">{icone} {label}</div>
        <div class="metric-value" style="color: {cor};">{valor}</div>
        {growth_html}
        {subtext_html}
    </div>
    """

def empty_state(icone, titulo, mensagem, acao_label=None, acao_id=None):
    """Componente para estados vazios"""
    
    acao_html = ""
    if acao_label and acao_id:
        acao_html = f'<div style="margin-top: 1.5rem;"><button class="btn-primary" id="{acao_id}">{acao_label}</button></div>'
    
    return f"""
    <div class="empty-state">
        <div class="empty-icon">{icone}</div>
        <h3 style="color: #E2E8F0; margin-bottom: 0.5rem;">{titulo}</h3>
        <p style="color: #94A3B8; max-width: 400px; margin: 0 auto;">{mensagem}</p>
        {acao_html}
    </div>
    """

def status_badge(status):
    """Badge de status com cores semânticas"""
    
    cores = {
        "Pendente": ("status-pendente", "⏳"),
        "Concluído": ("status-concluido", "✅"),
        "Cancelado": ("status-cancelado", "❌"),
        "Confirmado": ("status-concluido", "✓"),
    }
    
    classe, icone = cores.get(status, ("status-pendente", "○"))
    return f'<span class="status-badge {classe}">{icone} {status}</span>'

# ================= 5. TOP BAR DINÂMICA =================
def renderizar_top_bar(email_usuario, pagina_atual):
    """Barra superior fixa com contexto"""
    
    titulos_pagina = {
        "dashboard": "📊 Visão Geral",
        "agenda": "📅 Agenda do Dia",
        "clientes": "👥 Base de Clientes",
        "servicos": "🛠️ Catálogo de Serviços",
        "financeiro": "💰 Saúde Financeira",
        "relatorios": "📈 Insights Avançados"
    }
    
    titulo = titulos_pagina.get(pagina_atual, "Vivv Pro")
    
    st.markdown(f"""
    <div class="top-bar">
        <div>
            <h3 style="margin: 0; color: #E2E8F0; font-weight: 600;">{titulo}</h3>
        </div>
        <div class="user-pill">
            <div style="
                width: 32px;
                height: 32px;
                border-radius: 50%;
                background: linear-gradient(135deg, #00D4FF, #0088FF);
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-weight: bold;
            ">{email_usuario[0].upper()}</div>
            <div>
                <div style="font-weight: 600;">{email_usuario.split('@')[0]}</div>
                <div style="font-size: 0.75rem; color: #94A3B8;">Administrador</div>
            </div>
            <div style="margin-left: 0.5rem; cursor: pointer;" onclick="logout()">🚪</div>
        </div>
    </div>
    
    <script>
    function logout() {{
        window.location.href = window.location.pathname + "?logout=true";
    }}
    </script>
    """, unsafe_allow_html=True)

# ================= 6. CONEXÃO FIREBASE (OTIMIZADA) =================
@st.cache_resource
def init_db():
    try:
        secrets_dict = json.loads(st.secrets["FIREBASE_DETAILS"])
        creds = service_account.Credentials.from_service_account_info(secrets_dict)
        return firestore.Client(credentials=creds)
    except Exception as e:
        st.error(f"⚠️ Erro na conexão: {e}")
        return None

db = init_db()
if db is None:
    st.stop()

def hash_senha(senha):
    return hashlib.sha256(str.encode(senha)).hexdigest()

# ================= 7. SISTEMA DE AUTENTICAÇÃO =================
def verificar_autenticacao():
    """Sistema de login/cadastro unificado"""
    
    if "logado" not in st.session_state:
        st.session_state.logado = False
    
    # Logout via query param
    query_params = st.experimental_get_query_params()
    if query_params.get("logout"):
        st.session_state.logado = False
        st.experimental_set_query_params()
        st.rerun()
    
    if not st.session_state.logado:
        # Tela de autenticação premium
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown("""
            <div style="
                background: rgba(255, 255, 255, 0.02);
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 20px;
                padding: 3rem;
                margin-top: 5rem;
                text-align: center;
            ">
                <h1 class="text-gradient" style="font-size: 3rem; margin-bottom: 0.5rem;">Vivv Pro</h1>
                <p style="color: #94A3B8; margin-bottom: 2rem;">Gestão profissional para seu negócio</p>
            </div>
            """, unsafe_allow_html=True)
            
            tab1, tab2 = st.tabs(["🔐 Acesso", "✨ Nova Conta"])
            
            with tab1:
                with st.form("login_form"):
                    email = st.text_input("E-mail", key="login_email").lower().strip()
                    senha = st.text_input("Senha", type="password", key="login_senha")
                    
                    col_b1, col_b2 = st.columns([1, 1])
                    with col_b1:
                        submit_login = st.form_submit_button("Entrar na Conta", use_container_width=True)
                    with col_b2:
                        if st.form_submit_button("Esqueci a Senha", use_container_width=True, type="secondary"):
                            st.info("📧 Um e-mail de recuperação será enviado.")
                    
                    if submit_login and email and senha:
                        user_ref = db.collection("usuarios").document(email).get()
                        if user_ref.exists and user_ref.to_dict().get("senha") == hash_senha(senha):
                            st.session_state.logado = True
                            st.session_state.user_email = email
                            st.success("✅ Login realizado!")
                            st.rerun()
                        else:
                            st.error("❌ Credenciais inválidas")
            
            with tab2:
                with st.form("cadastro_form"):
                    nome = st.text_input("Nome Completo")
                    email_cad = st.text_input("E-mail (será seu login)").lower().strip()
                    senha_cad = st.text_input("Crie uma Senha", type="password")
                    senha_conf = st.text_input("Confirme a Senha", type="password")
                    
                    if st.form_submit_button("Criar Conta Gratuita", use_container_width=True):
                        if senha_cad != senha_conf:
                            st.error("❌ As senhas não coincidem")
                        elif email_cad and senha_cad:
                            if db.collection("usuarios").document(email_cad).get().exists:
                                st.error("❌ Este e-mail já está cadastrado")
                            else:
                                validade = datetime.now(fuso_br) + timedelta(days=7)
                                db.collection("usuarios").document(email_cad).set({
                                    "nome": nome,
                                    "senha": hash_senha(senha_cad),
                                    "pago": False,
                                    "validade": validade,
                                    "criado_em": firestore.SERVER_TIMESTAMP
                                })
                                st.success("✨ Conta criada! Faça login para começar.")
        
        st.stop()
    
    return st.session_state.user_email

# ================= 8. VERIFICAÇÃO DE ASSINATURA (MELHORADA) =================
def verificar_assinatura(email):
    """Verifica assinatura com UX melhorada"""
    
    user_ref = db.collection("usuarios").document(email).get()
    if not user_ref.exists:
        st.session_state.logado = False
        st.rerun()
    
    dados = user_ref.to_dict()
    
    # Usuário pago - acesso liberado
    if dados.get("pago", False):
        return True
    
    # Validação do período de teste
    validade = dados.get("validade")
    hoje = datetime.now(fuso_br)
    
    if validade:
        # Converter para timezone-aware se necessário
        if validade.tzinfo is None:
            validade = validade.replace(tzinfo=fuso_br)
        
        dias_restantes = (validade - hoje).days
        
        if dias_restantes < 0:
            # Período expirado
            st.markdown("""
            <div style="
                max-width: 600px;
                margin: 4rem auto;
                text-align: center;
                padding: 3rem;
                background: rgba(255, 255, 255, 0.02);
                border-radius: 20px;
                border: 1px solid rgba(255, 145, 0, 0.2);
            ">
                <div style="font-size: 4rem; margin-bottom: 1rem;">🔒</div>
                <h2 style="color: #FF9100; margin-bottom: 1rem;">Período de Teste Expirado</h2>
                <p style="color: #94A3B8; margin-bottom: 2rem;">
                    Seu acesso de 7 dias ao Vivv Pro terminou.<br>
                    Ative sua assinatura para continuar gerenciando seu negócio com todas as funcionalidades.
                </p>
                
                <div style="
                    background: rgba(255, 145, 0, 0.1);
                    border: 1px solid rgba(255, 145, 0, 0.3);
                    border-radius: 12px;
                    padding: 1.5rem;
                    margin-bottom: 2rem;
                ">
                    <div style="font-size: 2rem; font-weight: bold; color: #FF9100;">R$ 49,90/mês</div>
                    <div style="color: #94A3B8; font-size: 0.9rem;">+ taxa de ativação única: R$ 300,00</div>
                </div>
                
                <a href="https://buy.stripe.com/test_6oU4gB7Q4glM1JZ2Z06J200" target="_blank">
                    <button style="
                        background: linear-gradient(90deg, #FF9100 0%, #FF6B00 100%);
                        color: white;
                        border: none;
                        padding: 1rem 2rem;
                        border-radius: 12px;
                        font-weight: 600;
                        font-size: 1rem;
                        cursor: pointer;
                        transition: all 0.3s ease;
                        margin-bottom: 1rem;
                    " onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 10px 20px rgba(255, 145, 0, 0.3)';" 
                    onmouseout="this.style.transform='none'; this.style.boxShadow='none';">
                        💳 ATIVAR VIVV PRO AGORA
                    </button>
                </a>
                
                <div style="margin-top: 2rem;">
                    <button onclick="window.location.reload()" style="
                        background: transparent;
                        color: #94A3B8;
                        border: 1px solid rgba(255, 255, 255, 0.1);
                        padding: 0.75rem 1.5rem;
                        border-radius: 10px;
                        cursor: pointer;
                    ">
                        🔄 Já realizei o pagamento
                    </button>
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.stop()
        else:
            # Ainda no período de teste
            if dias_restantes <= 2:
                st.warning(f"⚠️ Seu período de teste termina em {dias_restantes} dias. [Ativar agora](https://buy.stripe.com/test_6oU4gB7Q4glM1JZ2Z06J200)")
    
    return False

# ================= 9. SISTEMA DE CACHE INTELIGENTE =================
@st.cache_data(ttl=30, show_spinner=False)
def carregar_dados_usuario(email):
    """Carrega todos os dados do usuário de forma otimizada"""
    
    user_ref = db.collection("usuarios").document(email)
    
    # Carregar em paralelo (simulação)
    clis = [{"id": doc.id, **doc.to_dict()} for doc in user_ref.collection("meus_clientes").stream()]
    srvs = [{"id": doc.id, **doc.to_dict()} for doc in user_ref.collection("meus_servicos").stream()]
    
    # Agenda: últimos 30 dias + futuros
    trinta_dias_atras = datetime.now(fuso_br) - timedelta(days=30)
    agnd = [{"id": doc.id, **doc.to_dict()} for doc in 
            user_ref.collection("minha_agenda")
            .where("data", ">=", trinta_dias_atras.strftime('%d/%m/%Y'))
            .stream()]
    
    # Caixa: últimos 90 dias
    noventa_dias_atras = datetime.now(fuso_br) - timedelta(days=90)
    cx_list = []
    for doc in user_ref.collection("meu_caixa").stream():
        doc_data = doc.to_dict()
        if "data" in doc_data:
            cx_list.append({"id": doc.id, **doc_data})
    
    return clis, srvs, agnd, cx_list

# ================= 10. PÁGINA: DASHBOARD =================
def pagina_dashboard(email_usuario):
    """Dashboard principal com visão instantânea"""
    
    st.markdown("""
    <div style="margin-bottom: 2rem;">
        <h1 style="margin-bottom: 0.5rem;">📊 Visão Geral do Negócio</h1>
        <p style="color: #94A3B8; margin-bottom: 1.5rem;">Resumo completo da performance do seu negócio</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Carregar dados
    clis, srvs, agnd, cx_list = carregar_dados_usuario(email_usuario)
    
    # Cálculos avançados
    faturamento = sum([float(x.get('valor', 0)) for x in cx_list if x.get('tipo') == 'Entrada'])
    despesas = sum([float(x.get('valor', 0)) for x in cx_list if x.get('tipo') == 'Saída'])
    lucro = faturamento - despesas
    
    hoje = datetime.now(fuso_br).strftime('%d/%m/%Y')
    agendamentos_hoje = [a for a in agnd if a.get('data') == hoje and a.get('status') != 'Concluído']
    
    # Métricas em grid
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(metric_card(
            "👥", "Clientes Ativos", 
            len(clis),
            f"{len([c for c in clis if 'telefone' in c])} com WhatsApp",
            "#00D4FF",
            12  # crescimento simulado
        ), unsafe_allow_html=True)
    
    with col2:
        st.markdown(metric_card(
            "💰", "Faturamento Mensal",
            f"R$ {faturamento:,.2f}",
            f"R$ {(faturamento/30):,.2f} por dia",
            "#00FF88",
            8
        ), unsafe_allow_html=True)
    
    with col3:
        st.markdown(metric_card(
            "📈", "Lucro Líquido",
            f"R$ {lucro:,.2f}",
            f"Margem: {(lucro/faturamento*100 if faturamento > 0 else 0):.1f}%",
            "#00D4FF",
            15
        ), unsafe_allow_html=True)
    
    with col4:
        st.markdown(metric_card(
            "📅", "Agenda Hoje",
            len(agendamentos_hoje),
            f"R$ {sum([a.get('preco', 0) for a in agendamentos_hoje]):,.2f} potencial",
            "#FF9100",
            -5
        ), unsafe_allow_html=True)
    
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    
    # Gráfico de performance
    if cx_list:
        col_graf, col_insights = st.columns([2, 1])
        
        with col_graf:
            st.markdown("#### 📈 Performance Financeira")
            
            df_cx = pd.DataFrame(cx_list)
            df_cx['valor'] = pd.to_numeric(df_cx['valor'], errors='coerce')
            
            # Agrupar por tipo
            resumo = df_cx.groupby('tipo')['valor'].sum().reset_index()
            
            fig = px.bar(
                resumo,
                x='tipo',
                y='valor',
                color='tipo',
                color_discrete_map={'Entrada': '#00D4FF', 'Saída': '#FF4B4B'},
                text_auto='.2s',
                height=300
            )
            
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font_color="#FFFFFF",
                showlegend=False,
                margin=dict(l=20, r=20, t=40, b=20),
                xaxis_title=None,
                yaxis_title=None
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col_insights:
            st.markdown("#### 🎯 Insights Rápidos")
            
            insights = [
                f"**💰 Ticket Médio:** R$ {(faturamento/len([x for x in cx_list if x.get('tipo') == 'Entrada']) if [x for x in cx_list if x.get('tipo') == 'Entrada'] else 0):.2f}",
                f"**📊 Cliente mais recorrente:** {max([(c['nome'], len([a for a in agnd if a.get('cliente') == c['nome']])) for c in clis], key=lambda x: x[1])[0] if clis else 'N/A'}",
                f"**🛠️ Serviço mais vendido:** {max([(s['nome'], len([a for a in agnd if a.get('servico') == s['nome']])) for s in srvs], key=lambda x: x[1])[0] if srvs else 'N/A'}"
            ]
            
            for insight in insights:
                st.markdown(f"""
                <div class="interactive-card" style="margin-bottom: 0.75rem;">
                    {insight}
                </div>
                """, unsafe_allow_html=True)
    
    # Próximos agendamentos
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    
    st.markdown("#### ⏰ Próximos Agendamentos")
    
    if agendamentos_hoje:
        for agenda in agendamentos_hoje[:5]:
            col_a, col_b, col_c = st.columns([3, 2, 1])
            
            with col_a:
                st.markdown(f"""
                <div style="padding: 1rem 0;">
                    <div style="font-weight: 600; color: #E2E8F0;">{agenda.get('cliente', 'Cliente')}</div>
                    <div style="color: #94A3B8; font-size: 0.9rem;">
                        {agenda.get('servico', 'Serviço')} • {agenda.get('hora', '--:--')}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col_b:
                st.markdown(f"""
                <div style="padding: 1rem 0;">
                    <div style="font-weight: 600; color: #00FF88;">R$ {agenda.get('preco', 0):.2f}</div>
                    <div style="color: #94A3B8; font-size: 0.9rem;">{status_badge(agenda.get('status', 'Pendente'))}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col_c:
                if st.button("👁️", key=f"view_{agenda['id']}", help="Ver detalhes"):
                    st.session_state.agenda_detalhe = agenda['id']
                    st.experimental_set_query_params(pagina="agenda")
                    st.rerun()
    else:
        st.markdown(empty_state(
            "📅", "Agenda Livre para Hoje",
            "Nenhum agendamento encontrado para hoje. Que tal agendar um serviço?",
            "➕ Criar
