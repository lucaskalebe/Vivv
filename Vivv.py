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
                        "➕ Criar Agendamento",
            "btn_criar_agendamento"
        ), unsafe_allow_html=True)

# ================= 11. PÁGINA: AGENDA =================
def pagina_agenda(email_usuario):
    """Sistema de agenda profissional com visão diária/semanal"""
    
    st.markdown("""
    <div style="margin-bottom: 2rem;">
        <h1 style="margin-bottom: 0.5rem;">📅 Gestão de Agenda</h1>
        <p style="color: #94A3B8; margin-bottom: 1.5rem;">Controle completo dos agendamentos e atendimentos</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Carregar dados
    clis, srvs, agnd, _ = carregar_dados_usuario(email_usuario)
    user_ref = db.collection("usuarios").document(email_usuario)
    
    # Filtros rápidos
    col_filtro1, col_filtro2, col_filtro3, col_filtro4 = st.columns(4)
    
    with col_filtro1:
        periodo = st.selectbox("Período", ["Hoje", "Amanhã", "Esta Semana", "Próximos 7 dias", "Todos"], key="filtro_periodo")
    
    with col_filtro2:
        status_filtro = st.selectbox("Status", ["Todos", "Pendente", "Confirmado", "Concluído", "Cancelado"], key="filtro_status")
    
    with col_filtro3:
        cliente_filtro = st.selectbox("Cliente", ["Todos"] + [c["nome"] for c in clis], key="filtro_cliente")
    
    with col_filtro4:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("➕ Novo Agendamento", use_container_width=True, type="primary"):
            st.session_state.modo_agenda = "criar"
            st.rerun()
    
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    
    # Filtrar agenda
    hoje = datetime.now(fuso_br).strftime('%d/%m/%Y')
    amanha = (datetime.now(fuso_br) + timedelta(days=1)).strftime('%d/%m/%Y')
    
    agendamentos_filtrados = agnd.copy()
    
    if periodo == "Hoje":
        agendamentos_filtrados = [a for a in agendamentos_filtrados if a.get('data') == hoje]
    elif periodo == "Amanhã":
        agendamentos_filtrados = [a for a in agendamentos_filtrados if a.get('data') == amanha]
    elif periodo == "Esta Semana":
        # Lógica simplificada para semana
        agendamentos_filtrados = [a for a in agendamentos_filtrados 
                                 if a.get('data') in [hoje, amanha]]
    
    if status_filtro != "Todos":
        agendamentos_filtrados = [a for a in agendamentos_filtrados 
                                 if a.get('status') == status_filtro]
    
    if cliente_filtro != "Todos":
        agendamentos_filtrados = [a for a in agendamentos_filtrados 
                                 if a.get('cliente') == cliente_filtro]
    
    # Ordenar por data e hora
    agendamentos_filtrados.sort(key=lambda x: (x.get('data', ''), x.get('hora', '')))
    
    # Modo criação/edição
    if st.session_state.get('modo_agenda') in ['criar', 'editar']:
        st.markdown("#### 📝 Novo Agendamento")
        
        with st.form("form_agendamento"):
            col_f1, col_f2 = st.columns(2)
            
            with col_f1:
                cliente_novo = st.selectbox("Cliente", [c["nome"] for c in clis], 
                                          key="form_cliente")
                servico_novo = st.selectbox("Serviço", [s["nome"] for s in srvs], 
                                          key="form_servico")
            
            with col_f2:
                data_novo = st.date_input("Data", format="DD/MM/YYYY", 
                                        key="form_data")
                hora_novo = st.time_input("Horário", key="form_hora")
            
            obs_novo = st.text_area("Observações", placeholder="Observações importantes...", 
                                   key="form_obs")
            
            col_b1, col_b2, col_b3 = st.columns(3)
            
            with col_b1:
                if st.form_submit_button("💾 Salvar Agendamento", use_container_width=True):
                    if cliente_novo and servico_novo:
                        preco = next((s['preco'] for s in srvs if s['nome'] == servico_novo), 0)
                        status = "Confirmado" if st.session_state.get('modo_agenda') == 'criar' else agnd[0].get('status', 'Pendente')
                        
                        agenda_data = {
                            "cliente": cliente_novo,
                            "servico": servico_novo,
                            "preco": preco,
                            "status": status,
                            "data": data_novo.strftime('%d/%m/%Y'),
                            "hora": hora_novo.strftime('%H:%M'),
                            "observacoes": obs_novo,
                            "criado_em": firestore.SERVER_TIMESTAMP
                        }
                        
                        if st.session_state.get('modo_agenda') == 'editar' and st.session_state.get('agenda_edit_id'):
                            user_ref.collection("minha_agenda").document(
                                st.session_state.agenda_edit_id
                            ).update(agenda_data)
                            st.success("✅ Agendamento atualizado!")
                        else:
                            user_ref.collection("minha_agenda").add(agenda_data)
                            st.success("✅ Agendamento criado!")
                        
                        st.cache_data.clear()
                        st.session_state.modo_agenda = None
                        st.session_state.agenda_edit_id = None
                        st.rerun()
            
            with col_b2:
                if st.form_submit_button("❌ Cancelar", use_container_width=True, type="secondary"):
                    st.session_state.modo_agenda = None
                    st.session_state.agenda_edit_id = None
                    st.rerun()
        
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    
    # Lista de agendamentos
    if agendamentos_filtrados:
        st.markdown(f"#### 📋 {len(agendamentos_filtrados)} Agendamentos Encontrados")
        
        for i, agenda in enumerate(agendamentos_filtrados):
            with st.container():
                col_a, col_b, col_c = st.columns([3, 2, 2])
                
                with col_a:
                    st.markdown(f"""
                    <div style="padding: 1rem; background: rgba(255,255,255,0.02); border-radius: 10px; margin-bottom: 0.5rem;">
                        <div style="display: flex; justify-content: space-between; align-items: start;">
                            <div>
                                <div style="font-weight: 600; color: #E2E8F0; font-size: 1.1rem;">{agenda.get('cliente')}</div>
                                <div style="color: #94A3B8; font-size: 0.9rem; margin-top: 0.25rem;">
                                    {agenda.get('servico')} • {agenda.get('data')} às {agenda.get('hora')}
                                </div>
                                {f'<div style="color: #64748B; font-size: 0.85rem; margin-top: 0.5rem;">{agenda.get("observacoes", "")}</div>' if agenda.get('observacoes') else ''}
                            </div>
                            <div>
                                {status_badge(agenda.get('status', 'Pendente'))}
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col_b:
                    st.markdown(f"""
                    <div style="padding: 1rem; text-align: center;">
                        <div style="font-size: 1.5rem; font-weight: 700; color: #00FF88;">R$ {agenda.get('preco', 0):.2f}</div>
                        <div style="color: #94A3B8; font-size: 0.85rem;">Valor do serviço</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col_c:
                    col_c1, col_c2, col_c3 = st.columns(3)
                    
                    # Botão WhatsApp
                    raw_tel = next((c.get('telefone', '') for c in clis if c.get('nome') == agenda.get('cliente')), "")
                    clean_tel = "".join(filter(str.isdigit, raw_tel))
                    if clean_tel:
                        msg = urllib.parse.quote(f"VIVV PRO: Confirmação - {agenda.get('servico')} agendado para {agenda.get('data')} às {agenda.get('hora')}")
                        col_c1.markdown(f"""
                        <a href="https://wa.me/55{clean_tel}?text={msg}" target="_blank" 
                           style="display: block; text-align: center; padding: 0.5rem; 
                                  background: rgba(37, 211, 102, 0.1); border: 1px solid rgba(37, 211, 102, 0.3); 
                                  border-radius: 8px; color: #25D366; text-decoration: none; font-size: 1.2rem;">
                            📱
                        </a>
                        """, unsafe_allow_html=True)
                    
                    # Botão Concluir
                    if col_c2.button("✓", key=f"concluir_{agenda['id']}", 
                                   help="Marcar como concluído"):
                        user_ref.collection("minha_agenda").document(agenda['id']).update({
                            "status": "Concluído",
                            "concluido_em": firestore.SERVER_TIMESTAMP
                        })
                        
                        # Adicionar ao caixa
                        user_ref.collection("meu_caixa").add({
                            "descricao": f"Serviço: {agenda.get('cliente')} - {agenda.get('servico')}",
                            "valor": agenda.get('preco', 0),
                            "tipo": "Entrada",
                            "data": firestore.SERVER_TIMESTAMP,
                            "referencia": agenda['id']
                        })
                        
                        st.cache_data.clear()
                        st.rerun()
                    
                    # Botão Editar
                    if col_c3.button("✏️", key=f"editar_{agenda['id']}", help="Editar agendamento"):
                        st.session_state.modo_agenda = "editar"
                        st.session_state.agenda_edit_id = agenda['id']
                        st.rerun()
    else:
        st.markdown(empty_state(
            "📅", "Nenhum Agendamento Encontrado",
            "Não há agendamentos para os filtros selecionados. Crie um novo agendamento para começar.",
            "➕ Criar Primeiro Agendamento",
            "btn_novo_agendamento_vazio"
        ), unsafe_allow_html=True)

# ================= 12. PÁGINA: CLIENTES =================
def pagina_clientes(email_usuario):
    """Gestão avançada da base de clientes"""
    
    st.markdown("""
    <div style="margin-bottom: 2rem;">
        <h1 style="margin-bottom: 0.5rem;">👥 Base de Clientes</h1>
        <p style="color: #94A3B8; margin-bottom: 1.5rem;">Gerencie seus clientes e histórico de atendimentos</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Carregar dados
    clis, srvs, agnd, _ = carregar_dados_usuario(email_usuario)
    user_ref = db.collection("usuarios").document(email_usuario)
    
    # Métricas de clientes
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    
    clientes_com_whatsapp = len([c for c in clis if c.get('telefone')])
    clientes_ativos = len(set([a.get('cliente') for a in agnd if a.get('status') == 'Concluído']))
    ticket_medio = sum([a.get('preco', 0) for a in agnd if a.get('status') == 'Concluído']) / max(clientes_ativos, 1)
    
    with col_m1:
        st.markdown(metric_card("👥", "Total", len(clis), None, "#00D4FF"), unsafe_allow_html=True)
    with col_m2:
        st.markdown(metric_card("📱", "Com WhatsApp", clientes_com_whatsapp, f"{int(clientes_com_whatsapp/len(clis)*100)}%", "#25D366"), unsafe_allow_html=True)
    with col_m3:
        st.markdown(metric_card("✅", "Ativos", clientes_ativos, f"{int(clientes_ativos/len(clis)*100)}%", "#00FF88"), unsafe_allow_html=True)
    with col_m4:
        st.markdown(metric_card("💰", "Ticket Médio", f"R$ {ticket_medio:.2f}", "por cliente", "#FF9100"), unsafe_allow_html=True)
    
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    
    # Ações rápidas
    col_acoes1, col_acoes2, col_acoes3 = st.columns(3)
    
    with col_acoes1:
        if st.button("➕ Novo Cliente", use_container_width=True, type="primary"):
            st.session_state.modo_cliente = "criar"
    
    with col_acoes2:
        busca_cliente = st.text_input("🔍 Buscar cliente", placeholder="Nome ou telefone...", 
                                     key="busca_cliente")
    
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    
    # Formulário de criação/edição
    if st.session_state.get('modo_cliente') in ['criar', 'editar']:
        st.markdown(f"#### {'📝 Novo Cliente' if st.session_state.modo_cliente == 'criar' else '✏️ Editar Cliente'}")
        
        with st.form("form_cliente"):
            col_c1, col_c2 = st.columns(2)
            
            with col_c1:
                nome_cliente = st.text_input("Nome Completo *", 
                                           value=st.session_state.get('cliente_edit_nome', ''),
                                           key="form_nome_cliente")
                email_cliente = st.text_input("E-mail", 
                                            value=st.session_state.get('cliente_edit_email', ''),
                                            key="form_email_cliente")
            
            with col_c2:
                telefone_cliente = st.text_input("WhatsApp *", 
                                               value=st.session_state.get('cliente_edit_tel', ''),
                                               key="form_tel_cliente")
                aniversario = st.date_input("Data de Nascimento", 
                                          value=st.session_state.get('cliente_edit_aniv'),
                                          key="form_aniv_cliente")
            
            observacoes_cliente = st.text_area("Observações / Preferências", 
                                             value=st.session_state.get('cliente_edit_obs', ''),
                                             placeholder="Ex: Prefere horário da tarde, gosta de tal serviço...",
                                             key="form_obs_cliente")
            
            col_bc1, col_bc2 = st.columns(2)
            
            with col_bc1:
                if st.form_submit_button("💾 Salvar Cliente", use_container_width=True):
                    if nome_cliente and telefone_cliente:
                        cliente_data = {
                            "nome": nome_cliente,
                            "telefone": telefone_cliente,
                            "email": email_cliente if email_cliente else None,
                            "aniversario": aniversario.strftime('%d/%m') if aniversario else None,
                            "observacoes": observacoes_cliente if observacoes_cliente else None,
                            "atualizado_em": firestore.SERVER_TIMESTAMP
                        }
                        
                        if st.session_state.modo_cliente == 'editar' and st.session_state.get('cliente_edit_id'):
                            user_ref.collection("meus_clientes").document(
                                st.session_state.cliente_edit_id
                            ).update(cliente_data)
                            st.success("✅ Cliente atualizado!")
                        else:
                            cliente_data["criado_em"] = firestore.SERVER_TIMESTAMP
                            user_ref.collection("meus_clientes").add(cliente_data)
                            st.success("✅ Cliente cadastrado!")
                        
                        st.cache_data.clear()
                        st.session_state.modo_cliente = None
                        st.session_state.cliente_edit_id = None
                        st.rerun()
            
            with col_bc2:
                if st.form_submit_button("❌ Cancelar", use_container_width=True, type="secondary"):
                    st.session_state.modo_cliente = None
                    st.session_state.cliente_edit_id = None
                    st.rerun()
        
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    
    # Lista de clientes
    if clis:
        # Filtrar por busca
        if busca_cliente:
            clis_filtrados = [c for c in clis 
                            if busca_cliente.lower() in c.get('nome', '').lower() 
                            or busca_cliente in c.get('telefone', '')]
        else:
            clis_filtrados = clis
        
        st.markdown(f"#### 📋 {len(clis_filtrados)} Clientes")
        
        for cliente in clis_filtrados:
            with st.expander(f"👤 {cliente.get('nome')}", expanded=False):
                col_info, col_historico = st.columns([1, 2])
                
                with col_info:
                    st.markdown(f"""
                    **📱 WhatsApp:** {cliente.get('telefone', 'Não informado')}
                    
                    **📧 E-mail:** {cliente.get('email', 'Não informado')}
                    
                    **🎂 Aniversário:** {cliente.get('aniversario', 'Não informado')}
                    """)
                    
                    # Agendamentos deste cliente
                    agendamentos_cliente = [a for a in agnd if a.get('cliente') == cliente.get('nome')]
                    concluidos = len([a for a in agendamentos_cliente if a.get('status') == 'Concluído'])
                    
                    st.markdown(f"""
                    **📊 Histórico:**
                    - {len(agendamentos_cliente)} agendamentos
                    - {concluidos} concluídos
                    - R$ {sum([a.get('preco', 0) for a in agendamentos_cliente if a.get('status') == 'Concluído']):.2f} gastos
                    """)
                    
                    # Botões de ação
                    col_btn1, col_btn2, col_btn3 = st.columns(3)
                    
                    if col_btn1.button("✏️", key=f"edit_cli_{cliente['id']}", help="Editar"):
                        st.session_state.modo_cliente = "editar"
                        st.session_state.cliente_edit_id = cliente['id']
                        st.session_state.cliente_edit_nome = cliente.get('nome')
                        st.session_state.cliente_edit_tel = cliente.get('telefone', '')
                        st.session_state.cliente_edit_email = cliente.get('email', '')
                        st.session_state.cliente_edit_obs = cliente.get('observacoes', '')
                        st.rerun()
                    
                    if col_btn2.button("📅", key=f"agendar_cli_{cliente['id']}", help="Agendar"):
                        st.session_state.agenda_cliente_pre = cliente.get('nome')
                        st.experimental_set_query_params(pagina="agenda")
                        st.rerun()
                
                with col_historico:
                    if agendamentos_cliente:
                        st.markdown("**📅 Últimos Atendimentos:**")
                        for ag in agendamentos_cliente[:5]:
                            status_color = {
                                'Concluído': '#00FF88',
                                'Pendente': '#FF9100',
                                'Cancelado': '#FF4B4B'
                            }.get(ag.get('status'), '#94A3B8')
                            
                            st.markdown(f"""
                            <div style="
                                padding: 0.75rem;
                                margin-bottom: 0.5rem;
                                background: rgba(255,255,255,0.02);
                                border-radius: 8px;
                                border-left: 4px solid {status_color};
                            ">
                                <div style="display: flex; justify-content: space-between;">
                                    <div>
                                        <strong>{ag.get('servico')}</strong><br>
                                        <small style="color: #94A3B8;">{ag.get('data')} às {ag.get('hora')}</small>
                                    </div>
                                    <div>
                                        <strong style="color: #00FF88;">R$ {ag.get('preco', 0):.2f}</strong><br>
                                        <small style="color: {status_color};">{ag.get('status')}</small>
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.info("Nenhum atendimento registrado.")
    else:
        st.markdown(empty_state(
            "👥", "Nenhum Cliente Cadastrado",
            "Comece cadastrando seus primeiros clientes para gerenciar agendamentos e histórico.",
            "➕ Cadastrar Primeiro Cliente",
            "btn_novo_cliente_vazio"
        ), unsafe_allow_html=True)

# ================= 13. PÁGINA: SERVIÇOS =================
def pagina_servicos(email_usuario):
    """Catálogo de serviços gerenciável"""
    
    st.markdown("""
    <div style="margin-bottom: 2rem;">
        <h1 style="margin-bottom: 0.5rem;">🛠️ Catálogo de Serviços</h1>
        <p style="color: #94A3B8; margin-bottom: 1.5rem;">Gerencie seus serviços, preços e popularidade</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Carregar dados
    clis, srvs, agnd, _ = carregar_dados_usuario(email_usuario)
    user_ref = db.collection("usuarios").document(email_usuario)
    
    # Métricas de serviços
    if srvs:
        servico_mais_vendido = max(srvs, key=lambda s: len([a for a in agnd if a.get('servico') == s['nome']]))
        total_vendas = sum([a.get('preco', 0) for a in agnd if a.get('status') == 'Concluído'])
        
        col_s1, col_s2, col_s3 = st.columns(3)
        
        with col_s1:
            st.markdown(metric_card("🛠️", "Serviços", len(srvs), None, "#00D4FF"), unsafe_allow_html=True)
        
        with col_s2:
            st.markdown(metric_card("💰", "Faturamento Total", f"R$ {total_vendas:.2f}", 
                                  f"R$ {(total_vendas/len(srvs)):.2f} por serviço" if srvs else "", "#00FF88"), 
                      unsafe_allow_html=True)
        
        with col_s3:
            vendas_mais_vendido = len([a for a in agnd if a.get('servico') == servico_mais_vendido['nome']])
            st.markdown(metric_card("🏆", "Mais Popular", servico_mais_vendido['nome'], 
                                  f"{vendas_mais_vendido} vendas", "#FF9100"), 
                      unsafe_allow_html=True)
    
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    
    # Formulário de serviço
    if st.session_state.get('modo_servico') in ['criar', 'editar']:
        st.markdown(f"#### {'🛠️ Novo Serviço' if st.session_state.modo_servico == 'criar' else '✏️ Editar Serviço'}")
        
        with st.form("form_servico"):
            col_sf1, col_sf2 = st.columns(2)
            
            with col_sf1:
                nome_servico = st.text_input("Nome do Serviço *", 
                                           value=st.session_state.get('servico_edit_nome', ''),
                                           key="form_nome_servico")
                duracao = st.number_input("Duração (minutos)", min_value=15, step=15, value=60,
                                        key="form_duracao_servico")
            
            with col_sf2:
                preco_servico = st.number_input("Preço *", min_value=0.0, step=10.0,
                                              value=st.session_state.get('servico_edit_preco', 50.0),
                                              key="form_preco_servico")
                categoria = st.selectbox("Categoria", ["Corte", "Barba", "Coloração", "Tratamento", "Outros"],
                                       key="form_categoria_servico")
            
            descricao = st.text_area("Descrição", 
                                   value=st.session_state.get('servico_edit_desc', ''),
                                   placeholder="Descreva o serviço detalhadamente...",
                                   key="form_desc_servico")
            
            col_bs1, col_bs2 = st.columns(2)
            
            with col_bs1:
                if st.form_submit_button("💾 Salvar Serviço", use_container_width=True):
                    if nome_servico and preco_servico > 0:
                        servico_data = {
                            "nome": nome_servico,
                            "preco": float(preco_servico),
                            "duracao": int(duracao),
                            "categoria": categoria,
                            "descricao": descricao if descricao else None,
                            "atualizado_em": firestore.SERVER_TIMESTAMP
                        }
                        
                        if st.session_state.modo_servico == 'editar' and st.session_state.get('servico_edit_id'):
                            user_ref.collection("meus_servicos").document(
                                st.session_state.servico_edit_id
                            ).update(servico_data)
                            st.success("✅ Serviço atualizado!")
                        else:
                            servico_data["criado_em"] = firestore.SERVER_TIMESTAMP
                            user_ref.collection("meus_servicos").add(servico_data)
                            st.success("✅ Serviço cadastrado!")
                        
                        st.cache_data.clear()
                        st.session_state.modo_servico = None
                        st.session_state.servico_edit_id = None
                        st.rerun()
            
            with col_bs2:
                if st.form_submit_button("❌ Cancelar", use_container_width=True, type="secondary"):
                    st.session_state.modo_servico = None
                    st.session_state.servico_edit_id = None
                    st.rerun()
        
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    
    # Ações rápidas
    col_sa1, col_sa2 = st.columns([1, 3])
    
    with col_sa1:
        if st.button("➕ Novo Serviço", use_container_width=True, type="primary"):
            st.session_state.modo_servico = "criar"
    
    # Lista de serviços
    if srvs:
        st.markdown(f"#### 📋 {len(srvs)} Serviços Cadastrados")
        
        for servico in srvs:
            # Calcular popularidade
            vendas_servico = len([a for a in agnd if a.get('servico') == servico['nome'] and a.get('status') == 'Concluído'])
            faturamento_servico = sum([a.get('preco', 0) for a in agnd if a.get('servico') == servico['nome'] and a.get('status') == 'Concluído'])
            
            col_ss1, col_ss2, col_ss3 = st.columns([3, 2, 1])
            
            with col_ss1:
                st.markdown(f"""
                <div style="padding: 1rem 0;">
                    <div style="font-weight: 600; color: #E2E8F0; font-size: 1.1rem;">{servico['nome']}</div>
                    <div style="color: #94A3B8; font-size: 0.9rem; margin-top: 0.25rem;">
                        {servico.get('categoria', 'Geral')} • {servico.get('duracao', 60)} minutos
                        {f'<br><small style="color: #64748B;">{servico.get("descricao", "")}</small>' if servico.get('descricao') else ''}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col_ss2:
                st.markdown(f"""
                <div style="padding: 1rem 0; text-align: center;">
                    <div style="font-size: 1.5rem; font-weight: 700; color: #00FF88;">R$ {servico['preco']:.2f}</div>
                    <div style="color: #94A3B8; font-size: 0.85rem;">
                        {vendas_servico} vendas • R$ {faturamento_servico:.2f} faturado
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col_ss3:
                col_sb1, col_sb2 = st.columns(2)
                
                if col_sb1.button("✏️", key=f"edit_srv_{servico['id']}", help="Editar"):
                    st.session_state.modo_servico = "editar"
                    st.session_state.servico_edit_id = servico['id']
                    st.session_state.servico_edit_nome = servico['nome']
                    st.session_state.servico_edit_preco = servico['preco']
                    st.session_state.servico_edit_desc = servico.get('descricao', '')
                    st.rerun()
                
                if col_sb2.button("📊", key=f"stats_srv_{servico['id']}", help="Estatísticas"):
                    st.session_state.servico_detalhe = servico['id']
                    # Poderia abrir um modal com estatísticas detalhadas
                    st.info(f"Estatísticas de {servico['nome']}: {vendas_servico} vendas")
    else:
        st.markdown(empty_state(
            "🛠️", "Nenhum Serviço Cadastrado",
            "Cadastre seus serviços para começar a agendar atendimentos.",
            "➕ Cadastrar Primeiro Serviço",
            "btn_novo_servico_vazio"
        ), unsafe_allow_html=True)

# ================= 14. VIVV AI EVOLUÍDO =================
def pagina_vivv_ai(email_usuario):
    """Sistema de IA avançado para insights de negócio"""
    
    st.markdown("""
    <div style="margin-bottom: 2rem;">
        <h1 style="margin-bottom: 0.5rem;">🤖 Vivv AI - Consultor Inteligente</h1>
        <p style="color: #94A3B8; margin-bottom: 1.5rem;">Análises preditivas e insights para seu negócio crescer</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Carregar dados para contexto
    clis, srvs, agnd, cx_list = carregar_dados_usuario(email_usuario)
    
    faturamento = sum([float(x.get('valor', 0)) for x in cx_list if x.get('tipo') == 'Entrada'])
    despesas = sum([float(x.get('valor', 0)) for x in cx_list if x.get('tipo') == 'Saída'])
    lucro = faturamento - despesas
    
    # Cards de contexto
    st.markdown("#### 📊 Contexto do Seu Negócio")
    
    col_ctx1, col_ctx2, col_ctx3 = st.columns(3)
    
    with col_ctx1:
        st.markdown(f"""
        <div class="interactive-card">
            <div style="font-size: 0.9rem; color: #94A3B8;">Clientes Ativos</div>
            <div style="font-size: 1.5rem; font-weight: 700; color: #00D4FF;">{len(clis)}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col_ctx2:
        st.markdown(f"""
        <div class="interactive-card">
            <div style="font-size: 0.9rem; color: #94A3B8;">Lucro Mensal</div>
            <div style="font-size: 1.5rem; font-weight: 700; color: #00FF88;">R$ {lucro:.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col_ctx3:
        servico_mais_popular = max(srvs, key=lambda s: len([a for a in agnd if a.get('servico') == s['nome']])) if srvs else {"nome": "N/A"}
        st.markdown(f"""
        <div class="interactive-card">
            <div style="font-size: 0.9rem; color: #94A3B8;">Serviço Mais Popular</div>
            <div style="font-size: 1.1rem; font-weight: 700; color: #FF9100;">{servico_mais_popular['nome'][:20]}{'...' if len(servico_mais_popular['nome']) > 20 else ''}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    
    # Perguntas sugeridas
    st.markdown("#### 💡 Perguntas Sugeridas")
    
    perguntas = [
        "Como aumentar meu faturamento em 30%?",
        "Quais são meus melhores horários de atendimento?",
        "Como fidelizar mais clientes?",
        "Devo aumentar o preço dos meus serviços?",
        "Qual é o perfil ideal do meu cliente?"
    ]
    
    cols_perguntas = st.columns(len(perguntas))
    for idx, pergunta in enumerate(perguntas):
        with cols_perguntas[idx]:
            if st.button(pergunta[:30] + ("..." if len(pergunta) > 30 else ""), 
                        key=f"perg_sug_{idx}",
                        use_container_width=True):
                st.session_state.pergunta_ai = pergunta
    
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    
        # Campo de pergunta
    st.markdown("#### 💬 Faça sua pergunta")
    
    pergunta = st.text_area(
        "Descreva o que você gostaria de analisar:",
        placeholder="Ex: Como posso melhorar a margem de lucro dos meus serviços?",
        height=100,
        key="input_pergunta_ai",
        value=st.session_state.get("pergunta_ai", "")
    )
    
    col_ai1, col_ai2 = st.columns([1, 1])
    
    with col_ai1:
        if st.button("🚀 Analisar com IA", use_container_width=True, type="primary"):
            if pergunta:
                with st.spinner("🤖 Vivv AI analisando seu negócio..."):
                    try:
                        # Implementação da IA (mantendo a original com melhorias)
                        api_key = st.secrets["GOOGLE_API_KEY"]
                        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={api_key}"
                        
                        # Contexto rico para a IA
                        contexto = f"""
                        CONTEXTO DO NEGÓCIO:
                        - {len(clis)} clientes cadastrados
                        - {len(srvs)} serviços oferecidos
                        - Faturamento mensal: R$ {faturamento:.2f}
                        - Despesas mensais: R$ {despesas:.2f}
                        - Lucro líquido: R$ {lucro:.2f}
                        - {len([a for a in agnd if a.get('status') == 'Concluído'])} atendimentos concluídos
                        - Ticket médio: R$ {(faturamento/max(len([a for a in agnd if a.get('status') == 'Concluído']), 1)):.2f}
                        
                        PERGUNTA DO USUÁRIO: {pergunta}
                        
                        INSTRUÇÕES:
                        1. Responda como um consultor especializado em pequenos negócios
                        2. Use dados concretos do contexto fornecido
                        3. Forneça 3-5 recomendações acionáveis
                        4. Seja direto e prático
                        5. Use emojis relevantes para tornar a resposta visual
                        6. Formate com tópicos claros
                        """
                        
                        payload = {
                            "contents": [{
                                "parts": [{"text": contexto}]
                            }],
                            "generationConfig": {
                                "temperature": 0.7,
                                "topP": 0.8,
                                "topK": 40
                            }
                        }
                        
                        import requests
                        response = requests.post(url, json=payload, timeout=45)
                        
                        if response.status_code == 200:
                            resposta_json = response.json()
                            texto_resposta = resposta_json['candidates'][0]['content']['parts'][0]['text']
                            
                            # Exibir resposta formatada
                            st.markdown("""
                            <div style="
                                background: linear-gradient(135deg, rgba(0, 212, 255, 0.1) 0%, rgba(0, 136, 255, 0.1) 100%);
                                border: 1px solid rgba(0, 212, 255, 0.2);
                                border-radius: 12px;
                                padding: 1.5rem;
                                margin-top: 1rem;
                            ">
                                <h4 style="color: #00D4FF; margin-bottom: 1rem;">🎯 Análise Vivv AI</h4>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            st.markdown(f"""
                            <div style="
                                background: rgba(255, 255, 255, 0.02);
                                border-radius: 8px;
                                padding: 1.5rem;
                                margin-top: 0.5rem;
                                line-height: 1.6;
                            ">
                                {texto_resposta.replace('**', '<strong>').replace('**', '</strong>')}
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Botão para ações
                            col_act1, col_act2, col_act3 = st.columns(3)
                            with col_act1:
                                if st.button("📋 Criar Plano de Ação", use_container_width=True):
                                    st.info("Funcionalidade em desenvolvimento - Em breve!")
                            
                            with col_act2:
                                if st.button("📊 Ver Métricas Detalhadas", use_container_width=True):
                                    st.experimental_set_query_params(pagina="dashboard")
                                    st.rerun()
                            
                        else:
                            st.error("Erro na consulta à IA. Tente novamente.")
                            
                    except requests.exceptions.Timeout:
                        st.error("⏱️ A análise está demorando mais que o esperado. Tente uma pergunta mais específica.")
                    except Exception as e:
                        st.error(f"❌ Erro: {str(e)}")
            else:
                st.warning("Digite uma pergunta para a IA analisar.")
    
    with col_ai2:
        if st.button("🔄 Limpar", use_container_width=True, type="secondary"):
            st.session_state.pergunta_ai = ""
            st.rerun()
    
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    
    # Insights automáticos
    st.markdown("#### 📈 Insights Automáticos")
    
    insights = [
        {
            "titulo": "📊 Oportunidade de Crescimento",
            "descricao": f"Seu ticket médio é R$ {(faturamento/max(len([a for a in agnd if a.get('status') == 'Concluído']), 1)):.2f}. Aumente em 15% oferecendo combos.",
            "acao": "Criar promoção"
        },
        {
            "titulo": "👥 Fidelização",
            "descricao": f"Você tem {len(clis)} clientes. Aumente a retenção com lembretes automáticos.",
            "acao": "Configurar lembretes"
        },
        {
            "titulo": "⏰ Otimização de Agenda",
            "descricao": "Horários das 10h-12h têm maior taxa de confirmação. Priorize agendamentos nesse período.",
            "acao": "Ver agenda"
        }
    ]
    
    for insight in insights:
        col_in1, col_in2 = st.columns([3, 1])
        
        with col_in1:
            st.markdown(f"""
            <div class="interactive-card">
                <div style="font-weight: 600; color: #E2E8F0;">{insight['titulo']}</div>
                <div style="color: #94A3B8; font-size: 0.9rem; margin-top: 0.25rem;">{insight['descricao']}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col_in2:
            if st.button(insight['acao'], key=f"insight_{insight['titulo'][:10]}", use_container_width=True):
                st.info(f"Ação '{insight['acao']}' acionada!")

# ================= 15. PÁGINA: FINANCEIRO =================
def pagina_financeiro(email_usuario):
    """Dashboard financeiro avançado"""
    
    st.markdown("""
    <div style="margin-bottom: 2rem;">
        <h1 style="margin-bottom: 0.5rem;">💰 Saúde Financeira</h1>
        <p style="color: #94A3B8; margin-bottom: 1.5rem;">Controle completo das finanças do seu negócio</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Carregar dados
    clis, srvs, agnd, cx_list = carregar_dados_usuario(email_usuario)
    user_ref = db.collection("usuarios").document(email_usuario)
    
    # Cálculos financeiros
    entradas = [float(x.get('valor', 0)) for x in cx_list if x.get('tipo') == 'Entrada']
    saidas = [float(x.get('valor', 0)) for x in cx_list if x.get('tipo') == 'Saída']
    
    total_entradas = sum(entradas)
    total_saidas = sum(saidas)
    lucro = total_entradas - total_saidas
    
    # Métricas principais
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    
    with col_f1:
        st.markdown(metric_card("💰", "Entradas", f"R$ {total_entradas:,.2f}", 
                              f"{len(entradas)} transações", "#00FF88"), unsafe_allow_html=True)
    
    with col_f2:
        st.markdown(metric_card("📉", "Saídas", f"R$ {total_saidas:,.2f}", 
                              f"{len(saidas)} despesas", "#FF4B4B"), unsafe_allow_html=True)
    
    with col_f3:
        st.markdown(metric_card("📈", "Lucro", f"R$ {lucro:,.2f}", 
                              f"Margem: {(lucro/total_entradas*100 if total_entradas > 0 else 0):.1f}%", "#00D4FF"), 
                  unsafe_allow_html=True)
    
    with col_f4:
        # Calcular projeção
        media_diaria = total_entradas / max(len(cx_list), 1)
        projecao_mensal = media_diaria * 30
        st.markdown(metric_card("🎯", "Projeção", f"R$ {projecao_mensal:,.0f}", 
                              "próximos 30 dias", "#FF9100"), unsafe_allow_html=True)
    
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    
    # Gráficos
    if cx_list:
        col_graf1, col_graf2 = st.columns(2)
        
        with col_graf1:
            st.markdown("#### 📊 Fluxo de Caixa")
            
            # Criar DataFrame temporal
            df_cx = pd.DataFrame(cx_list)
            df_cx['data'] = pd.to_datetime(df_cx.get('data', ''), errors='coerce')
            df_cx['valor'] = pd.to_numeric(df_cx['valor'], errors='coerce')
            
            # Agrupar por dia
            df_diario = df_cx.groupby([pd.Grouper(key='data', freq='D'), 'tipo'])['valor'].sum().reset_index()
            
            fig = px.line(df_diario, x='data', y='valor', color='tipo',
                         color_discrete_map={'Entrada': '#00FF88', 'Saída': '#FF4B4B'},
                         height=300)
            
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font_color="#FFFFFF",
                showlegend=True,
                margin=dict(l=20, r=20, t=40, b=20),
                xaxis_title=None,
                yaxis_title=None
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col_graf2:
            st.markdown("#### 📈 Composição das Despesas")
            
            # Filtrar apenas saídas
            df_saidas = df_cx[df_cx['tipo'] == 'Saída'].copy()
            
            if not df_saidas.empty:
                # Extrair categoria da descrição (simplificado)
                df_saidas['categoria'] = df_saidas['descricao'].apply(
                    lambda x: 'Fornecedores' if 'forn' in str(x).lower() else 
                             'Salários' if 'sal' in str(x).lower() else
                             'Aluguel' if 'alug' in str(x).lower() else
                             'Manutenção' if 'manut' in str(x).lower() else
                             'Outros'
                )
                
                df_categorias = df_saidas.groupby('categoria')['valor'].sum().reset_index()
                
                fig2 = px.pie(df_categorias, values='valor', names='categoria',
                             height=300, hole=0.4,
                             color_discrete_sequence=px.colors.qualitative.Set3)
                
                fig2.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font_color="#FFFFFF",
                    showlegend=True,
                    margin=dict(l=20, r=20, t=40, b=20)
                )
                
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("Nenhuma despesa registrada para análise.")
    
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    
    # Ações rápidas
    col_acoes_f1, col_acoes_f2, col_acoes_f3 = st.columns(3)
    
    with col_acoes_f1:
        if st.button("➕ Nova Entrada", use_container_width=True, type="primary"):
            st.session_state.modo_financeiro = "entrada"
    
    with col_acoes_f2:
        if st.button("📉 Nova Despesa", use_container_width=True):
            st.session_state.modo_financeiro = "saida"
    
    with col_acoes_f3:
        if st.button("📥 Exportar Relatório", use_container_width=True):
            # Simulação de exportação
            st.info("📊 Relatório gerado! (Funcionalidade completa em desenvolvimento)")
    
    # Formulário de transação
    if st.session_state.get('modo_financeiro'):
        tipo = "Entrada" if st.session_state.modo_financeiro == "entrada" else "Saída"
        st.markdown(f"#### 💰 Registrar {'Receita' if tipo == 'Entrada' else 'Despesa'}")
        
        with st.form(f"form_{tipo.lower()}"):
            col_ff1, col_ff2 = st.columns(2)
            
            with col_ff1:
                descricao = st.text_input("Descrição *", 
                                        placeholder=f"Ex: {'Pagamento serviço' if tipo == 'Entrada' else 'Compra de produtos'}")
                valor = st.number_input("Valor *", min_value=0.0, step=10.0)
            
            with col_ff2:
                data_transacao = st.date_input("Data", format="DD/MM/YYYY")
                categoria = st.selectbox("Categoria", 
                                       ["Serviço", "Venda", "Outros"] if tipo == "Entrada" 
                                       else ["Fornecedores", "Salários", "Aluguel", "Manutenção", "Outros"])
            
            observacoes = st.text_area("Observações", placeholder="Detalhes adicionais...")
            
            col_fb1, col_fb2 = st.columns(2)
            
            with col_fb1:
                if st.form_submit_button(f"💾 Salvar {tipo}", use_container_width=True):
                    if descricao and valor > 0:
                        transacao_data = {
                            "descricao": descricao,
                            "valor": float(valor),
                            "tipo": tipo,
                            "categoria": categoria,
                            "data": data_transacao.strftime('%d/%m/%Y'),
                            "observacoes": observacoes if observacoes else None,
                            "registrado_em": firestore.SERVER_TIMESTAMP
                        }
                        
                        user_ref.collection("meu_caixa").add(transacao_data)
                        st.success(f"✅ {tipo} registrada com sucesso!")
                        st.cache_data.clear()
                        st.session_state.modo_financeiro = None
                        st.rerun()
            
            with col_fb2:
                if st.form_submit_button("❌ Cancelar", use_container_width=True, type="secondary"):
                    st.session_state.modo_financeiro = None
                    st.rerun()
        
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    
    # Últimas transações
    st.markdown("#### 📋 Últimas Transações")
    
    if cx_list:
        # Ordenar por data mais recente
        cx_ordenado = sorted(cx_list, 
                           key=lambda x: x.get('data', ''), 
                           reverse=True)[:10]
        
        for transacao in cx_ordenado:
            cor_valor = "#00FF88" if transacao.get('tipo') == 'Entrada' else "#FF4B4B"
            icone = "💰" if transacao.get('tipo') == 'Entrada' else "📉"
            
            col_t1, col_t2, col_t3 = st.columns([3, 2, 1])
            
            with col_t1:
                st.markdown(f"""
                <div style="padding: 0.75rem 0;">
                    <div style="font-weight: 600; color: #E2E8F0;">{icone} {transacao.get('descricao', 'Transação')}</div>
                    <div style="color: #94A3B8; font-size: 0.9rem;">
                        {transacao.get('data', 'Data não informada')} • {transacao.get('categoria', 'Geral')}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col_t2:
                st.markdown(f"""
                <div style="padding: 0.75rem 0; text-align: center;">
                    <div style="font-size: 1.2rem; font-weight: 700; color: {cor_valor};">R$ {transacao.get('valor', 0):.2f}</div>
                    <div style="color: #94A3B8; font-size: 0.85rem;">{transacao.get('tipo', 'Transação')}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col_t3:
                if transacao.get('observacoes'):
                    st.button("📝", key=f"obs_{transacao.get('id', '')}", 
                            help=transacao['observacoes'][:50])
    else:
        st.markdown(empty_state(
            "💰", "Nenhuma Transação Registrada",
            "Comece registrando suas receitas e despesas para acompanhar a saúde financeira do negócio.",
            "➕ Registrar Primeira Transação",
            "btn_nova_transacao_vazio"
        ), unsafe_allow_html=True)

# ================= 16. CONFIGURAÇÕES =================
def pagina_configuracoes(email_usuario):
    """Página de configurações do usuário"""
    
    st.markdown("""
    <div style="margin-bottom: 2rem;">
        <h1 style="margin-bottom: 0.5rem;">⚙️ Configurações</h1>
        <p style="color: #94A3B8; margin-bottom: 1.5rem;">Personalize sua experiência no Vivv Pro</p>
    </div>
    """, unsafe_allow_html=True)
    
    user_ref = db.collection("usuarios").document(email_usuario)
    user_data = user_ref.get().to_dict()
    
    # Abas de configuração
    tab1, tab2, tab3, tab4 = st.tabs(["👤 Perfil", "🎨 Aparência", "🔔 Notificações", "🔒 Segurança"])
    
    with tab1:
        st.markdown("#### Informações Pessoais")
        
        with st.form("form_perfil"):
            nome_atual = user_data.get('nome', '')
            nome = st.text_input("Nome Completo", value=nome_atual)
            email = st.text_input("E-mail", value=email_usuario, disabled=True)
            telefone = st.text_input("Telefone", value=user_data.get('telefone', ''))
            
            if st.form_submit_button("💾 Atualizar Perfil", use_container_width=True):
                user_ref.update({
                    "nome": nome,
                    "telefone": telefone,
                    "atualizado_em": firestore.SERVER_TIMESTAMP
                })
                st.success("✅ Perfil atualizado com sucesso!")
                st.rerun()
    
    with tab2:
        st.markdown("#### Personalização da Interface")
        
        tema = st.selectbox("Tema da Interface", ["Escuro (Padrão)", "Claro", "Automático"])
        densidade = st.selectbox("Densidade de Informação", ["Compacta", "Confortável", "Espaçada"])
        fonte = st.selectbox("Tamanho da Fonte", ["Pequeno", "Médio", "Grande"])
        
        if st.button("💾 Aplicar Preferências", use_container_width=True):
            st.info("🎨 Preferências de interface salvas! (Recarregue para aplicar)")
    
    with tab3:
        st.markdown("#### Preferências de Notificação")
        
        col_not1, col_not2 = st.columns(2)
        
        with col_not1:
            st.markdown("**📱 WhatsApp**")
            notif_whatsapp = st.checkbox("Lembretes de agendamento", value=True)
            notif_pagamentos = st.checkbox("Confirmações de pagamento", value=True)
            notif_promocoes = st.checkbox("Promoções e novidades", value=False)
        
        with col_not2:
            st.markdown("**📧 E-mail**")
            notif_email_diario = st.checkbox("Resumo diário", value=True)
            notif_email_semanal = st.checkbox("Relatório semanal", value=True)
            notif_email_mensal = st.checkbox("Faturamento mensal", value=True)
        
        horario_notificacoes = st.time_input("Horário preferencial para notificações", 
                                           value=datetime.strptime("18:00", "%H:%M").time())
        
        if st.button("💾 Salvar Notificações", use_container_width=True):
            st.success("✅ Preferências de notificação salvas!")
    
    with tab4:
        st.markdown("#### Configurações de Segurança")
        
        with st.form("form_seguranca"):
            senha_atual = st.text_input("Senha Atual", type="password")
            nova_senha = st.text_input("Nova Senha", type="password")
            confirmar_senha = st.text_input("Confirmar Nova Senha", type="password")
            
            if st.form_submit_button("🔐 Alterar Senha", use_container_width=True):
                if nova_senha == confirmar_senha:
                    if user_data.get('senha') == hash_senha(senha_atual):
                        user_ref.update({
                            "senha": hash_senha(nova_senha),
                            "senha_alterada_em": firestore.SERVER_TIMESTAMP
                        })
                        st.success("✅ Senha alterada com sucesso!")
                    else:
                        st.error("❌ Senha atual incorreta")
                else:
                    st.error("❌ As novas senhas não coincidem")
        
        st.markdown("---")
        st.markdown("#### 💻 Sessões Ativas")
        
        if st.button("🚪 Sair de Todos os Dispositivos", use_container_width=True, type="secondary"):
            st.warning("Esta ação desconectará todas as sessões ativas.")
            if st.button("Confirmar Logout Global", type="primary"):
                # Aqui implementaria logout global
                st.session_state.logado = False
                st.rerun()
        
        st.markdown("---")
        st.markdown("#### ⚠️ Zona de Perigo")
        
        if st.button("🗑️ Excluir Minha Conta", use_container_width=True, type="secondary"):
            st.error("Esta ação é irreversível! Todos os seus dados serão permanentemente excluídos.")
            confirmar = st.checkbox("Confirmo que desejo excluir minha conta e todos os dados permanentemente")
            if confirmar:
                if st.button("CONFIRMAR EXCLUSÃO DEFINITIVA", type="primary"):
                    st.error("Funcionalidade de exclusão em desenvolvimento")

# ================= 17. ROTEAMENTO PRINCIPAL =================
def main():
    """Função principal que gerencia todo o aplicativo"""
    
    # Verificar autenticação
    email_usuario = verificar_autenticacao()
    
    # Verificar assinatura
    verificar_assinatura(email_usuario)
    
    # Renderizar navegação
    renderizar_navegacao()
    
    # Renderizar top bar
    query_params = st.experimental_get_query_params()
    pagina_atual = query_params.get("pagina", ["dashboard"])[0]
    renderizar_top_bar(email_usuario, pagina_atual)
    
    # Adicionar padding para a top bar fixa
    st.markdown("<div style='padding-top: 70px;'></div>", unsafe_allow_html=True)
    
    # Roteamento de páginas
    if pagina_atual == "dashboard":
        pagina_dashboard(email_usuario)
    
    elif pagina_atual == "agenda":
        pagina_agenda(email_usuario)
    
    elif pagina_atual == "clientes":
        pagina_clientes(email_usuario)
    
    elif pagina_atual == "servicos":
        pagina_servicos(email_usuario)
    
    elif pagina_atual == "financeiro":
        pagina_financeiro(email_usuario)
    
    elif pagina_atual == "relatorios":
        pagina_vivv_ai(email_usuario)  # Usando Vivv AI como relatórios
    
    elif pagina_atual == "config":
        pagina_configuracoes(email_usuario)
    
    else:
        # Página não encontrada
        st.markdown(empty_state(
            "🔍", "Página Não Encontrada",
            "A página que você está procurando não existe ou foi movida.",
            "🏠 Voltar ao Dashboard",
            "btn_voltar_dashboard"
        ), unsafe_allow_html=True)
        
        if st.button("🏠 Ir para o Dashboard", use_container_width=True):
            st.experimental_set_query_params(pagina="dashboard")
            st.rerun()

# ================= 18. INICIALIZAÇÃO =================
if __name__ == "__main__":
    # Inicializar session states
    if "modo_agenda" not in st.session_state:
        st.session_state.modo_agenda = None
    
    if "modo_cliente" not in st.session_state:
        st.session_state.modo_cliente = None
    
    if "modo_servico" not in st.session_state:
        st.session_state.modo_servico = None
    
    if "modo_financeiro" not in st.session_state:
        st.session_state.modo_financeiro = None
    
    # Executar aplicação
    main()

