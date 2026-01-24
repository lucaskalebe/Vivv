

import streamlit as st
import sqlite3
import pandas as pd
import openai
import urllib.parse
from pathlib import Path
from datetime import datetime
import google.generativeai as genai
from google.cloud import firestore
from google.oauth2 import service_account
import json


# --- 1. INICIALIZAÇÃO DO BANCO ---
@st.cache_resource
def init_db():
    key_dict = json.loads(st.secrets["FIREBASE_DETAILS"])
    creds = service_account.Credentials.from_service_account_info(key_dict)
    return firestore.Client(credentials=creds)

db = init_db()

#________________________________________________________________________________________

# --- 2. CONTROLE DE ACESSO E SESSÃO ---
if "logado" not in st.session_state:
    st.session_state.logado = False

# --- 3. TELA DE LOGIN / CADASTRO ---
if not st.session_state.logado:
    st.title("Vivv - Acesso")
    
    # CRIAÇÃO DAS ABAS (Isso resolve o NameError da linha 33)
    aba_login, aba_cadastro = st.tabs(["Entrar", "Solicitar Acesso"])
    
    with aba_cadastro:
        novo_nome = st.text_input("Nome Completo", key="reg_nome")
        novo_email = st.text_input("E-mail para cadastro", key="reg_email")
        nova_senha = st.text_input("Escolha uma Senha", type="password", key="reg_senha")
        
        if st.button("Enviar Solicitação"):
            if novo_nome and novo_email and nova_senha:
                validade_teste = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7)
                db.collection("usuarios").document(novo_email).set({
                    "nome": novo_nome,
                    "senha": nova_senha,
                    "pago": False,
                    "teste": True,
                    "validade": validade_teste,
                    "data_solicitacao": firestore.SERVER_TIMESTAMP
                })
                st.success("Solicitação enviada! Tente logar agora.")
            else:
                st.error("Preencha todos os campos.")

    with aba_login:
        email_input = st.text_input("E-mail", key="login_email")
        senha_input = st.text_input("Senha", type="password", key="login_senha")
        
        if st.button("Acessar"):
            user_doc = db.collection("usuarios").document(email_input).get()
            if user_doc.exists:
                dados = user_doc.to_dict()
                if dados.get("senha") == senha_input:
                    # CORREÇÃO AQUI: Usamos apenas datetime.now() 
                    # porque você já importou a classe no topo do arquivo
                    from datetime import timezone
                    agora = datetime.now(timezone.utc)
                    
                    if dados.get("pago") == True or (dados.get("teste") == True and agora < dados.get("validade")):
                        st.session_state.logado = True
                        st.session_state.user_email = email_input
                        st.rerun()
                    else:
                        st.error("Acesso expirado ou pendente de pagamento.")
                else:
                    st.error("Senha incorreta.")
            else:
                st.error("Usuário não encontrado.")
    
    # ISSO É O QUE LIMPA O FUNDO: Impede que o painel apareça sem login
    st.stop()

# --- 4. PAINEL VIVV (SÓ APARECE SE LOGADO) ---

# Botão de sair com KEY ÚNICA para evitar o DuplicateElementId
if st.sidebar.button("SAIR / LOGOUT", key="btn_logout_final"):
    st.session_state.logado = False
    st.rerun()

# --- 3. BUSCA DE DADOS (AGORA NO FIRESTORE) ---
# --- AJUSTE 1: BUSCA DE DADOS NA NUVEM ---
user_ref = db.collection("usuarios").document(st.session_state.user_email)

# Puxa as coleções da nuvem
clientes_cloud = list(user_ref.collection("meus_clientes").stream())
servicos_cloud = list(user_ref.collection("meus_servicos").stream())
agenda_cloud = list(user_ref.collection("minha_agenda").where("status", "==", "Pendente").stream())
caixa_cloud = list(user_ref.collection("meu_caixa").stream())

# Transforma em números para os Cards Neon
total_clientes = len(clientes_cloud)
ag_hoje = len(agenda_cloud)
faturamento = sum([float(doc.to_dict().get('valor', 0)) for doc in caixa_cloud if doc.to_dict().get('tipo') == 'Entrada'])
despesas = sum([float(doc.to_dict().get('valor', 0)) for doc in caixa_cloud if doc.to_dict().get('tipo') == 'Saída'])

# Tenta buscar os dados salvos. Se não existirem, usa os valores padrão
doc = user_ref.get()
if doc.exists:
    dados = doc.to_dict()
    base_clientes = dados.get("base_clientes", 0)
    receita_bruta = dados.get("receita_bruta", 0)
    lucro_liquido = dados.get("lucro_liquido", 0)
    agenda_hoje = dados.get("agenda_hoje", 0)
else:
    base_clientes, receita_bruta, lucro_liquido, agenda_hoje = 0, 0, 0, 0
    user_ref.set({
        "base_clientes": base_clientes,
        "receita_bruta": receita_bruta,
        "lucro_liquido": lucro_liquido,
        "agenda_hoje": agenda_hoje
    })

# --- 4. VISUAL (INTERFACE VIVV) ---

# Botão de Sair no menu lateral
if st.sidebar.button("SAIR / LOGOUT"):
    st.info("Sessão encerrada.")


# ================= 1. CONFIGURAÇÃO E DESIGN ULTRA NEON =================
st.set_page_config(page_title="Vivv", layout="centered", page_icon="🚀")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    /* REMOVE SÍMBOLOS DE ÂNCORA E LINKS DOS TÍTULOS */
    button.header-anchor, a.header-anchor, .header-anchor { display: none !important; }

    /* FUNDO DEEP BLACK */
    .stApp { background-color: #000205; color: #d1d1d1; font-family: 'Inter', sans-serif; }
    
    /* CARDS COM GLOW AZUL */
    .neon-card {
        background: linear-gradient(145deg, #000814, #001220);
        border: 1px solid #0056b3;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 0 20px rgba(0, 86, 179, 0.2);
        transition: all 0.4s ease;
        text-align: center;
        margin-bottom: 10px;
    }

    /* NÚMERO LARANJA NEON PARA AGENDA */
    .orange-neon {
        color: #ff9100 !important;
        text-shadow: 0 0 15px rgba(255, 145, 0, 0.7);
        font-size: 2.5rem;
        font-weight: 800;
        margin-top: 5px;
    }
    
    /* BOTÃO WHATSAPP */
    .wa-link {
        background: linear-gradient(45deg, #25D366, #128C7E);
        color: white !important; padding: 10px 15px; border-radius: 10px;
        text-align: center; font-weight: bold; text-decoration: none; display: block;
        box-shadow: 0 4px 15px rgba(37, 211, 102, 0.3); transition: 0.3s;
    }
    .wa-link:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(37, 211, 102, 0.5); }

    h1, h2, h3 { color: #00d4ff; text-shadow: 0 0 8px rgba(0, 212, 255, 0.5); }
    
    /* ESTILO DAS TABELAS E INPUTS */
    [data-testid="stDataFrame"] { border: 1px solid #0056b3; border-radius: 10px; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background: #000814; border: 1px solid #003566; color: #00d4ff; border-radius: 5px; padding: 10px; }
</style>
""", unsafe_allow_html=True)

# ================= 2. CORE: GERENCIAMENTO DE DADOS =================
DBS_DIR = Path(__file__).parent / "dbs"
DBS_DIR.mkdir(exist_ok=True)
db_path = DBS_DIR / "vivv.db"

def init_db():
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS clientes (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, telefone TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS servicos (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, preco REAL)')
    c.execute('CREATE TABLE IF NOT EXISTS agenda (id INTEGER PRIMARY KEY AUTOINCREMENT, cliente_id INTEGER, servico_id INTEGER, data TEXT, hora TEXT, status TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS caixa (id INTEGER PRIMARY KEY AUTOINCREMENT, descricao TEXT, valor REAL, tipo TEXT, data TEXT)')
    conn.commit()
    conn.close()

init_db()
conn = sqlite3.connect(db_path, check_same_thread=False)

# ================= 3. CÁLCULO DE MÉTRICAS (RESOLVENDO NAMEERROR) =================
# Definimos as variáveis antes de qualquer exibição visual
hoje_iso = datetime.now().strftime('%Y-%m-%d')

try:
    total_clientes = pd.read_sql("SELECT COUNT(*) FROM clientes", conn).iloc[0,0]
    faturamento = pd.read_sql("SELECT SUM(valor) FROM caixa WHERE tipo='Entrada'", conn).iloc[0,0] or 0.0
    despesas = pd.read_sql("SELECT SUM(valor) FROM caixa WHERE tipo='Saída'", conn).iloc[0,0] or 0.0
    
    # IMPORTANTE: Contamos apenas os PENDENTES para o número atualizar ao concluir
    ag_hoje = pd.read_sql(f"SELECT COUNT(*) FROM agenda WHERE data='{hoje_iso}' AND status='Pendente'", conn).iloc[0,0]
except:
    total_clientes, faturamento, despesas, ag_hoje = 0, 0.0, 0.0, 0.0

# ================= 4. HEADER E DASHBOARD =================
col_title, col_logout = st.columns([5, 1])
with col_title:
    st.title("Vivv")

if col_logout.button("SAIR / LOGOUT"):
    st.cache_data.clear()
    st.rerun()

# Layout dos Cards
m1, m2, m3, m4 = st.columns(4)

with m1:
    st.markdown(f'<div class="neon-card"><small>BASE DE CLIENTES</small><h2>{total_clientes}</h2></div>', unsafe_allow_html=True)

with m2:
    st.markdown(f'<div class="neon-card"><small>RECEITA BRUTA</small><h2 style="color:#00d4ff">R$ {faturamento:,.2f}</h2></div>', unsafe_allow_html=True)

with m3:
    st.markdown(f'<div class="neon-card"><small>LUCRO LÍQUIDO</small><h2 style="color:#00ff88">R$ {faturamento - despesas:,.2f}</h2></div>', unsafe_allow_html=True)

with m4:
    # Número Laranja Neon e Dinâmico
    st.markdown(f'''
        <div class="neon-card">
            <small>AGENDA HOJE</small>
            <div class="orange-neon">{ag_hoje}</div>
        </div>
    ''', unsafe_allow_html=True)

# ================= 5. PAINEL OPERACIONAL (100% CLOUD / FIRESTORE) =================
st.write("---")
col_ops, col_fila = st.columns([1.5, 2])

with col_ops:
    st.subheader("⚡ Painel de Controle")
    aba_ag, aba_cli, aba_srv, aba_cx = st.tabs(["📅 Agenda", "👤 Cliente", "💰 Serviço", "📉 Caixa"])
    
    with aba_cli:
        with st.form("add_cli_fire"):
            n_cli = st.text_input("Nome do Cliente")
            t_cli = st.text_input("WhatsApp (ex: 5511...)")
            if st.form_submit_button("CADASTRAR CLIENTE NA NUVEM"):
                if n_cli and t_cli:
                    user_ref.collection("meus_clientes").add({
                        "nome": n_cli, 
                        "telefone": t_cli,
                        "data_cadastro": firestore.SERVER_TIMESTAMP
                    })
                    st.success(f"Cliente {n_cli} salvo!")
                    st.rerun()

    with aba_ag:
        # Busca lista de clientes para o agendamento
        clientes_cloud = list(user_ref.collection("meus_clientes").stream())
        nomes_clientes = [c.to_dict()['nome'] for c in clientes_cloud]
        
        with st.form("add_ag_fire"):
            cli_sel = st.selectbox("Selecione o Cliente", nomes_clientes) if nomes_clientes else st.warning("Cadastre um cliente primeiro!")
            serv_nome = st.text_input("Nome do Serviço")
            preco_serv = st.number_input("Preço (R$)", min_value=0.0)
            if st.form_submit_button("CONFIRMAR AGENDAMENTO"):
                if cli_sel and serv_nome:
                    user_ref.collection("minha_agenda").add({
                        "cliente": cli_sel, 
                        "servico": serv_nome, 
                        "preco": preco_serv, 
                        "status": "Pendente",
                        "data_criacao": firestore.SERVER_TIMESTAMP
                    })
                    st.success("Agendado com sucesso!")
                    st.rerun()

    with aba_srv:
        st.info("Os serviços agora são integrados diretamente no agendamento para maior velocidade.")

    with aba_cx:
        with st.form("add_cx_fire"):
            desc_cx = st.text_input("Descrição")
            val_cx = st.number_input("Valor (R$)", min_value=0.0)
            tipo_cx = st.selectbox("Tipo", ["Entrada", "Saída"])
            if st.form_submit_button("REGISTRAR NO CAIXA"):
                user_ref.collection("meu_caixa").add({
                    "descricao": desc_cx,
                    "valor": val_cx,
                    "tipo": tipo_cx,
                    "data": firestore.SERVER_TIMESTAMP
                })
                st.success("Lançamento registrado!")
                st.rerun()

# ================= 6. FILA DE ATENDIMENTOS (FIRESTORE) =================
with col_fila:
    st.subheader("📋 Próximos Atendimentos")
    # Busca a agenda pendente no Firebase
    agenda_ref = user_ref.collection("minha_agenda").where("status", "==", "Pendente").stream()
    
    atendimentos = []
    for doc in agenda_ref:
        item = doc.to_dict()
        item['id_fire'] = doc.id
        atendimentos.append(item)

    if not atendimentos:
        st.info("Nenhum atendimento pendente na nuvem.")
    else:
        for a in atendimentos:
            with st.expander(f"📍 {a.get('cliente')} | {a.get('servico')}"):
                c1, c2 = st.columns([2, 1])
                c1.write(f"**Valor:** R$ {a.get('preco', 0):.2f}")
                
                # Botão Concluir no Firebase
                if c2.button("CONCLUIR ✅", key=f"fin_{a['id_fire']}"):
                    # 1. Marca como concluído
                    user_ref.collection("minha_agenda").document(a['id_fire']).update({"status": "Concluído"})
                    # 2. Lança no caixa automaticamente
                    user_ref.collection("meu_caixa").add({
                        "descricao": f"Serviço: {a.get('servico')}",
                        "valor": a.get('preco'),
                        "tipo": "Entrada",
                        "data": firestore.SERVER_TIMESTAMP
                    })
                    st.rerun()
# ================= 7. CENTRAL DE AUDITORIA (CORREÇÃO NameError) =================
st.write("---")
st.markdown("### 🗄️ Central de Auditoria")

# ESSA LINHA É A QUE FALTAVA: Criar as colunas antes de usá-las
ca1, ca2 = st.columns(2)

with ca1:
    with st.expander("👥 CLIENTES NA NUVEM"):
        clientes_stream = user_ref.collection("meus_clientes").stream()
        lista = [c.to_dict() for c in clientes_stream]
        if lista:
            st.dataframe(pd.DataFrame(lista)[['nome', 'telefone']], use_container_width=True)
        else:
            st.info("Nenhum cliente na nuvem.")

with ca2:
    with st.expander("📊 AGENDA ATIVA"):
        agenda_stream = user_ref.collection("minha_agenda").where("status", "==", "Pendente").stream()
        lista_ag = [a.to_dict() for a in agenda_stream]
        if lista_ag:
            st.dataframe(pd.DataFrame(lista_ag), use_container_width=True)
        else:
            st.info("Agenda vazia.")

# ================= 8. IA STRATEGIST (GOOGLE GEMINI) =================
import google.generativeai as genai

st.write("---")
st.subheader("💬 Vivv AI: Consultor de Negócios")

if "chat_history" not in st.session_state: 
    st.session_state.chat_history = []

for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]): 
        st.write(msg["content"])

if prompt := st.chat_input("Como posso melhorar meu lucro hoje?"):
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"): 
        st.write(prompt)
    
    with st.chat_message("assistant"):
        try:
            genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
            
            # Detecta automaticamente um modelo disponível na sua conta
            model_list = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            
            # Tenta o flash primeiro, se não, pega o primeiro disponível
            chosen_model = 'models/gemini-1.5-flash' if 'models/gemini-1.5-flash' in model_list else model_list[0]
            
            model = genai.GenerativeModel(chosen_model)
            
            lucro_atual = faturamento - despesas
            contexto = (
                f"Analise como consultor: Clientes={total_clientes}, "
                f"Faturamento=R${faturamento}, Lucro=R${lucro_atual}. "
                f"Pergunta: {prompt}"
            )
            
            response = model.generate_content(contexto)
            resp_text = response.text
            
        except Exception as e:
            resp_text = f"❌ Erro de Sistema: {str(e)}. Verifique se a biblioteca google-generativeai está no requirements.txt"
            
        st.write(resp_text)
        st.session_state.chat_history.append({"role": "assistant", "content": resp_text})





















