import streamlit as st
import pandas as pd
import io
import json
import hashlib
import plotly.express as px
from datetime import datetime, timezone, timedelta
from google.cloud import firestore
from google.oauth2 import service_account
import time

# ================= 1. CONFIGURAÇÕES TÉCNICAS E ESTILO MASTER =================

st.set_page_config(page_title="Vivv Pro v2", layout="wide", page_icon="🎯")
fuso_br = timezone(timedelta(hours=-3))

def hash_senha(senha):
    return hashlib.sha256(str.encode(senha)).hexdigest()

def format_brl(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# Interface de Alto Nível (CSS Customizado)
st.markdown("""
<style>
    header, [data-testid="stHeader"], .stAppDeployButton { display: none !important; }
    .stApp { background-color: #000205 !important; }
    .block-container { padding-top: 50px !important; max-width: 95% !important; }
    .vivv-logo {
        position: fixed; top: 15px; left: 25px;
        color: #ffffff; font-size: 32px; font-weight: 900;
        z-index: 999999; letter-spacing: -1px;
        text-shadow: 0 0 10px rgba(0, 212, 255, 0.5);
    }
    .metric-card {
        background: linear-gradient(145deg, #000814, #001a2c);
        border: 1px solid rgba(0, 86, 179, 0.4);
        border-radius: 16px; padding: 20px;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    }
    .metric-card:hover {
        border: 1px solid #00d4ff;
        box-shadow: 0 0 25px rgba(0, 212, 255, 0.2);
        transform: translateY(-5px);
    }
    .metric-card small { color: #8899A6; font-weight: 600; text-transform: uppercase; }
    .metric-card h2 { margin: 0; font-size: 2.2rem !important; font-weight: 800; }
    div.stButton > button {
        border-radius: 8px !important;
        font-weight: 700 !important;
        transition: all 0.3s !important;
    }
    [data-testid="stForm"] {
        background: rgba(255, 255, 255, 0.02) !important;
        border: 1px solid rgba(0, 212, 255, 0.1) !important;
        border-radius: 15px !important;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="vivv-logo">Vivv<span style="color:#00d4ff">.</span></div>', unsafe_allow_html=True)

# ================= 2. BANCO DE DADOS (FIRESTORE) =================
@st.cache_resource
def init_db():
    try:
        if "FIREBASE_DETAILS" not in st.secrets:
            st.error("Erro: FIREBASE_DETAILS não configurado.")
            return None
        firebase_raw = st.secrets["FIREBASE_DETAILS"]
        secrets_dict = json.loads(firebase_raw)
        creds = service_account.Credentials.from_service_account_info(secrets_dict)
        return firestore.Client(credentials=creds)
    except Exception as e:
        st.error(f"Erro Crítico Firebase: {e}")
        return None

db = init_db()
if not db: st.stop()

# ================= 3. AUTENTICAÇÃO E CADASTRO (ETAPA 1) =================
if "logado" not in st.session_state: st.session_state.logado = False

if not st.session_state.logado:
    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        st.markdown("<br><br>", unsafe_allow_html=True)
        tab_login, tab_create = st.tabs(["🔑 LOGIN VIVV", "📝 CRIAR CONTA"])
        
        with tab_login:
            le = st.text_input("E-mail", key="login_email").lower().strip()
            ls = st.text_input("Senha", type="password", key="login_pass")
            if st.button("ACESSAR SISTEMA", use_container_width=True):
                u_doc = db.collection("usuarios").document(le).get()
                if u_doc.exists:
                    u_data = u_doc.to_dict()
                    if u_data.get("senha") == hash_senha(ls):
                        st.session_state.logado = True
                        st.session_state.user_email = le
                        st.rerun()
                    else: st.error("Senha incorreta.")
                else: st.error("Usuário não encontrado.")

        with tab_create:
            with st.form("registro_pro"):
                st.subheader("🚀 Novo Cadastro Vivv Pro")
                u_id = st.text_input("Username único (@seu-id)")
                n_pes = st.text_input("Nome Completo")
                e_cad = st.text_input("E-mail de acesso").lower().strip()
                w_cad = st.text_input("WhatsApp (com DDD)")
                n_neg = st.text_input("Nome do Negócio")
                t_neg = st.selectbox("Tipo de Negócio", ["Barbearia", "Salão", "Estética", "Outro"])
                s_cad = st.text_input("Crie uma Senha", type="password")
                
                if st.form_submit_button("CADASTRAR E ATIVAR CONTA 💳", use_container_width=True):
                    if not all([u_id, n_pes, e_cad, w_cad, n_neg, s_cad]):
                        st.error("Preencha todos os campos.")
                    elif db.collection("usuarios").document(e_cad).get().exists:
                        st.error("E-mail já cadastrado.")
                    else:
                        db.collection("usuarios").document(e_cad).set({
                            "username": u_id, "nome": n_pes, "whatsapp": w_cad,
                            "nome_negocio": n_neg, "tipo_negocio": t_neg,
                            "senha": hash_senha(s_cad), "pago": False, "ativo": False,
                            "criado_em": datetime.now(fuso_br)
                        })
                        st.success("Cadastro salvo! Redirecionando para ativação...")
                        time.sleep(1.5)
                        st.session_state.logado = True
                        st.session_state.user_email = e_cad
                        st.rerun()
    st.stop()

# ================= 4. MIDDLEWARE DE BLOQUEIO (ETAPA 2 - PAGAMENTO) =================
user_ref = db.collection("usuarios").document(st.session_state.user_email)
user_data = user_ref.get().to_dict()

if not user_data.get("ativo", False):
    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown(f"""
        <div style="background: rgba(255,255,255,0.05); padding: 30px; border-radius: 20px; border: 1px solid #00d4ff; text-align: center;">
            <h2 style="color: #fff;">Quase pronto, {user_data.get('nome')}! 🎯</h2>
            <p style="color: #ccc;">Sua conta no <b>{user_data.get('nome_negocio')}</b> está aguardando ativação.</p>
            <hr style="border: 0.5px solid rgba(0,212,255,0.2);">
            <p style="font-size: 1.1rem;">💰 <b>R$ 300,00</b> (Taxa de Ativação)<br>
            📅 <b>R$ 49,90/mês</b> (Plano Pro)</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        st.link_button("IR PARA PAGAMENTO SEGURO 💳", "https://buy.stripe.com/test_6oU4gB7Q4glM1JZ2Z06J200", use_container_width=True)
        
        if st.button("Já paguei? Verificar Acesso", use_container_width=True):
            st.rerun()
        if st.button("Sair", type="secondary", use_container_width=True):
            st.session_state.logado = False
            st.rerun()
    st.stop()

# ================= 5. CARREGAMENTO DE DADOS (PÓS-BLOQUEIO) =================
@st.cache_data(ttl=60)
def load_vivv_data(email):
    u = db.collection("usuarios").document(email)
    c = [{"id": d.id, **d.to_dict()} for d in u.collection("meus_clientes").stream()]
    s = [{"id": d.id, **d.to_dict()} for d in u.collection("meus_servicos").stream()]
    a = [{"id": d.id, **d.to_dict()} for d in u.collection("minha_agenda").where("status", "==", "Pendente").stream()]
    a = sorted(a, key=lambda x: x.get('hora', '00:00'))
    cx = [d.to_dict() for d in u.collection("meu_caixa").stream()]
    return c, s, a, cx

clis, srvs, agnd, cx_list = load_vivv_data(st.session_state.user_email)
hoje_str = datetime.now(fuso_br).strftime('%d/%m/%Y')
clis_hoje = [a for a in agnd if a.get('data') == hoje_str]
faturamento = sum([float(x.get('valor', 0)) for x in cx_list if x.get('tipo') == 'Entrada'])
despesas = sum([float(x.get('valor', 0)) for x in cx_list if x.get('tipo') == 'Saída'])

# ================= 6. DASHBOARD ELITE =================
c_top1, c_top2 = st.columns([5,1])
with c_top1:
    st.markdown(f"##### Gestão: <span style='color:#00d4ff'>{user_data.get('nome_negocio')}</span>", unsafe_allow_html=True)
with c_top2:
    if st.button("LOGOUT", use_container_width=True):
        st.session_state.logado = False
        st.rerun()

m1, m2, m3, m4 = st.columns(4)
m1.markdown(f'<div class="metric-card"><small>👥 Clientes</small><h2>{len(clis)}</h2></div>', unsafe_allow_html=True)
m2.markdown(f'<div class="metric-card"><small>💰 Faturamento</small><h2 style="color:#00d4ff">{format_brl(faturamento)}</h2></div>', unsafe_allow_html=True)
m3.markdown(f'<div class="metric-card"><small>📈 Lucro Líquido</small><h2 style="color:#00ff88">{format_brl(faturamento-despesas)}</h2></div>', unsafe_allow_html=True)
m4.markdown(f'<div class="metric-card"><small>⏳ Pendentes Hoje</small><h2 style="color:#ff9100">{len(clis_hoje)}</h2></div>', unsafe_allow_html=True)

# ================= 7. PAINEL OPERACIONAL =================
st.write("---")
col_ops_l, col_ops_r = st.columns([1.3, 1])

with col_ops_l:
    st.markdown("### ⚡ Operações")
    t1, t2, t3, t4 = st.tabs(["📅 Agendar", "👤 Clientes", "🛠️ Serviços", "💸 Caixa"])
    
    with t1:
        with st.form("form_ag", clear_on_submit=True):
            cli_n = st.selectbox("Cliente", [c['nome'] for c in clis]) if clis else st.info("Cadastre um cliente primeiro.")
            srv_n = st.selectbox("Serviço", [s['nome'] for s in srvs]) if srvs else st.info("Cadastre um serviço primeiro.")
            c_d, c_h = st.columns(2)
            d_val = c_d.date_input("Data", format="DD/MM/YYYY")
            h_val = c_h.time_input("Horário")
            if st.form_submit_button("AGENDAR"):
                if clis and srvs:
                    p_s = next((s['preco'] for s in srvs if s['nome'] == srv_n), 0)
                    user_ref.collection("minha_agenda").add({
                        "cliente": cli_n, "servico": srv_n, "preco": p_s,
                        "status": "Pendente", "data": d_val.strftime('%d/%m/%Y'),
                        "hora": h_val.strftime('%H:%M'), "timestamp": datetime.now()
                    })
                    st.cache_data.clear(); st.rerun()

    with t2:
        with st.form("form_cli", clear_on_submit=True):
            nome_c = st.text_input("Nome do Cliente")
            tel_c = st.text_input("WhatsApp")
            if st.form_submit_button("SALVAR CLIENTE"):
                if nome_c:
                    user_ref.collection("meus_clientes").add({"nome": nome_c, "telefone": tel_c})
                    st.cache_data.clear(); st.rerun()

    with t3:
        with st.form("form_srv", clear_on_submit=True):
            nome_s = st.text_input("Nome do Serviço")
            preco_s = st.number_input("Preço", min_value=0.0)
            if st.form_submit_button("SALVAR SERVIÇO"):
                user_ref.collection("meus_servicos").add({"nome": nome_s, "preco": preco_s})
                st.cache_data.clear(); st.rerun()

    with t4:
        with st.form("form_cx", clear_on_submit=True):
            desc_cx = st.text_input("Descrição")
            valor_cx = st.number_input("Valor", min_value=0.0)
            tipo_cx = st.selectbox("Tipo", ["Entrada", "Saída"])
            if st.form_submit_button("LANÇAR"):
                user_ref.collection("meu_caixa").add({
                    "descricao": desc_cx, "valor": float(valor_cx), "tipo": tipo_cx, 
                    "data": hoje_str, "timestamp": datetime.now()
                })
                st.cache_data.clear(); st.rerun()

with col_ops_r:
    st.markdown("### 📋 Agenda do Dia")
    if not clis_hoje:
        st.info("Nenhum agendamento para hoje.")
    else:
        for ag in clis_hoje:
            id_a = ag.get('id')
            t_raw = next((c.get('telefone', '') for c in clis if c.get('nome') == ag['cliente']), "00")
            t_clean = "".join(filter(str.isdigit, str(t_raw)))
            exp = st.expander(f"📌 {ag['hora']} - {ag['cliente']}")
            c1, c2, c3 = exp.columns(3)
            c1.button("✅", key=f"ok_{id_a}", on_click=lambda id=id_a, ag=ag: (
                user_ref.collection("minha_agenda").document(id).update({"status": "Concluido"}),
                user_ref.collection("meu_caixa").add({"data": hoje_str, "descricao": f"Serviço: {ag['cliente']}", "valor": float(ag['preco']), "tipo": "Entrada", "timestamp": datetime.now()})
            ))
            c2.markdown(f"[Zap](https://wa.me/55{t_clean})")
            c3.button("🗑️", key=f"del_{id_a}", on_click=lambda id=id_a: user_ref.collection("minha_agenda").document(id).delete())

# ================= 8. EXPORTAÇÃO E RELATÓRIO =================
st.write("---")
if st.button("📥 BAIXAR RELATÓRIO EXCEL"):
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine='xlsxwriter') as writer:
        if clis: pd.DataFrame(clis).to_excel(writer, sheet_name='Clientes')
        if cx_list: pd.DataFrame(cx_list).to_excel(writer, sheet_name='Financeiro')
    st.download_button("Clique aqui para baixar", buf.getvalue(), f"Vivv_Pro_{hoje_str}.xlsx")
