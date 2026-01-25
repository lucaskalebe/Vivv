import streamlit as st
import pandas as pd
import urllib.parse
from datetime import datetime, timezone, timedelta
from google.cloud import firestore
from google.oauth2 import service_account
import json
import hashlib
import io
import requests
import plotly.express as px

# --- Configurações Iniciais ---
fuso_br = timezone(timedelta(hours=-3))

st.set_page_config(
    page_title="Vivv Pro", 
    layout="wide", 
    page_icon="🚀",
    initial_sidebar_state="collapsed"
)

def hash_senha(senha):
    return hashlib.sha256(str.encode(senha)).hexdigest()

# ================= 1. DESIGN VIVV PRO (NEON STYLE) =================
st.markdown("""
<style>
    header, [data-testid="stHeader"], .stAppDeployButton { display: none !important; }
    .stApp { background-color: #000205 !important; color: #e0e0e0 !important; }
    .block-container { padding-top: 60px !important; max-width: 95% !important; }

    .vivv-top-left {
        position: fixed; top: 20px; left: 25px;
        color: #ffffff !important; font-size: 28px;
        font-weight: 900; z-index: 999999;
        text-shadow: 0 0 15px rgba(0, 212, 255, 0.8);
    }

    .neon-card {
        background: linear-gradient(145deg, #000814, #001220);
        border: 1px solid #0056b3;
        border-radius: 12px;
        padding: 20px;
        transition: all 0.3s ease-in-out;
        text-align: center;
    }
    .neon-card:hover {
        border: 1px solid #00d4ff;
        box-shadow: 0 0 20px rgba(0, 212, 255, 0.3);
        transform: translateY(-5px);
    }
    .neon-card h2 { font-size: 2.2rem !important; margin: 10px 0 0 0 !important; font-weight: 800; }
    .orange-neon { color: #ff9100 !important; text-shadow: 0 0 15px rgba(255,145,0,0.5); text-align: center; }

    .whatsapp-button {
        display: inline-flex; align-items: center; justify-content: center;
        background: rgba(0, 212, 255, 0.1); color: #00d4ff !important;
        border: 1px solid #00d4ff; padding: 8px 15px; border-radius: 8px;
        text-decoration: none !important; font-weight: bold; transition: 0.3s;
    }
    .whatsapp-button:hover { background: #00d4ff; color: #000 !important; box-shadow: 0 0 15px rgba(0, 212, 255, 0.6); }

    .stDownloadButton button {
        background: linear-gradient(45deg, #00d4ff, #0056b3) !important;
        border: none !important; color: white !important; font-weight: 900 !important;
        border-radius: 10px !important; width: 100%;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="vivv-top-left">Vivv</div>', unsafe_allow_html=True)

# ================= 2. CONEXÃO FIREBASE =================
@st.cache_resource
def init_db():
    try:
        secrets_dict = json.loads(st.secrets["FIREBASE_DETAILS"])
        creds = service_account.Credentials.from_service_account_info(secrets_dict)
        return firestore.Client(credentials=creds)
    except Exception as e:
        st.error(f"Erro no Banco: {e}")
        return None

db = init_db()
if db is None: st.stop()

# ================= 3. FUNÇÕES AUXILIARES =================
def gerar_excel(dados):
    if not dados: return None
    df = pd.DataFrame(dados)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Fluxo_Vivv')
    return output.getvalue()

# ================= 4. ACESSO & CADASTRO =================
if "logado" not in st.session_state: st.session_state.logado = False

if not st.session_state.logado:
    aba_login, aba_cadastro = st.tabs(["🔑 Acesso", "📝 Novo Cadastro"])
    
    with aba_login:
        le = st.text_input("E-mail", key="l_email").lower().strip()
        ls = st.text_input("Senha", type="password", key="l_pass")
        if st.button("ENTRAR NO SISTEMA", use_container_width=True):
            u = db.collection("usuarios").document(le).get()
            if u.exists and u.to_dict().get("senha") == hash_senha(ls):
                st.session_state.logado, st.session_state.user_email = True, le
                st.rerun()
            else: st.error("E-mail ou senha incorretos.")
    
    with aba_cadastro:
        with st.form("reg_form"):
            n = st.text_input("Nome Completo")
            e = st.text_input("E-mail (Login)").lower().strip()
            s = st.text_input("Senha", type="password")
            if st.form_submit_button("CRIAR MINHA CONTA VIVV"):
                if e and s:
                    if db.collection("usuarios").document(e).get().exists:
                        st.error("E-mail já cadastrado.")
                    else:
                        val = datetime.now(fuso_br) + timedelta(days=7)
                        db.collection("usuarios").document(e).set({
                            "nome": n, "senha": hash_senha(s), 
                            "pago": False, "validade": val
                        })
                        st.success("Conta criada! Volte na aba 'Acesso' para entrar.")
                else: st.warning("Preencha todos os campos.")
    st.stop()

# ================= 5. VERIFICAÇÃO DE ASSINATURA (CORRIGIDA) =================
def verificar_acesso():
    u_ref = db.collection("usuarios").document(st.session_state.user_email).get()
    if u_ref.exists:
        d = u_ref.to_dict()
        if not d.get("pago", False):
            val = d.get("validade")
            # Converte timestamp do Firebase para datetime Python se necessário
            validade_dt = val.to_pydatetime() if hasattr(val, 'to_pydatetime') else val
            
            if validade_dt and datetime.now(fuso_br) > validade_dt.replace(tzinfo=fuso_br):
                st.markdown('<h1 class="orange-neon">VIVV PRO</h1>', unsafe_allow_html=True)
                st.warning("### 🔒 Período de Experiência Encerrado")
                st.info("Para continuar acessando seus dados e a IA, ative sua assinatura.")
                # Link com preenchimento automático do e-mail para facilitar
                link = f"https://buy.stripe.com/test_6oU4gB7Q4glM1JZ2Z06J200?prefilled_email={st.session_state.user_email}"
                st.link_button("💳 ATIVAR ACESSO AGORA", link, use_container_width=True)
                if st.button("🔄 Já paguei, atualizar acesso"): 
                    st.cache_data.clear()
                    st.rerun()
                st.stop()

verificar_acesso()

# ================= 6. CARREGAMENTO DE DADOS =================
user_ref = db.collection("usuarios").document(st.session_state.user_email)

@st.cache_data(ttl=60)
def load_vivv_data(email):
    u = db.collection("usuarios").document(email)
    c = [{"id": d.id, **d.to_dict()} for d in u.collection("meus_clientes").stream()]
    s = [{"id": d.id, **d.to_dict()} for d in u.collection("meus_servicos").stream()]
    a = [{"id": d.id, **d.to_dict()} for d in u.collection("minha_agenda").where("status", "==", "Pendente").stream()]
    cx = [d.to_dict() for d in u.collection("meu_caixa").stream()]
    return c, s, a, cx

clis, srvs, agnd, cx_list = load_vivv_data(st.session_state.user_email)
fat = sum(float(x.get('valor', 0)) for x in cx_list if x.get('tipo') == 'Entrada')
des = sum(float(x.get('valor', 0)) for x in cx_list if x.get('tipo') == 'Saída')

# Header
c_h1, c_h2 = st.columns([4,1])
c_h1.markdown(f"##### 🚀 Logado como: <span style='color:#00d4ff'>{st.session_state.user_email}</span>", unsafe_allow_html=True)
if c_h2.button("SAIR"): 
    st.session_state.logado = False
    st.rerun()

# KPIs
m1, m2, m3, m4 = st.columns(4)
m1.markdown(f'<div class="neon-card"><small>👥 Clientes</small><h2>{len(clis)}</h2></div>', unsafe_allow_html=True)
m2.markdown(f'<div class="neon-card"><small>💰 Receita</small><h2 style="color:#00d4ff">R$ {fat:,.2f}</h2></div>', unsafe_allow_html=True)
m3.markdown(f'<div class="neon-card"><small>📈 Lucro</small><h2 style="color:#00ff88">R$ {fat-des:,.2f}</h2></div>', unsafe_allow_html=True)
m4.markdown(f'<div class="neon-card"><small>📅 Agenda</small><h2 style="color:#ff9100">{len(agnd)}</h2></div>', unsafe_allow_html=True)

# ================= 7. OPERAÇÕES & AGENDA =================
st.write("---")
col_l, col_r = st.columns([1.5, 2])

with col_l:
    st.subheader("⚡ Painel de Controle")
    t1, t2, t3, t4 = st.tabs(["📅 Agenda", "👤 Cliente", "🛠️ Serviço", "📉 Caixa"])
    
    with t1:
        with st.form("f_ag"):
            c_s = st.selectbox("Cliente", [c['nome'] for c in clis]) if clis else None
            s_s = st.selectbox("Serviço", [s['nome'] for s in srvs]) if srvs else None
            d_ag = st.date_input("Data")
            h_ag = st.time_input("Hora")
            if st.form_submit_button("AGENDAR"):
                p_v = next((s['preco'] for s in srvs if s['nome'] == s_s), 0)
                user_ref.collection("minha_agenda").add({
                    "cliente": c_s, "servico": s_s, "preco": p_v, "status": "Pendente",
                    "data": d_ag.strftime('%d/%m/%Y'), "hora": h_ag.strftime('%H:%M')
                })
                st.cache_data.clear(); st.rerun()

    with t2:
        with st.form("f_cli"):
            nome = st.text_input("Nome")
            tel = st.text_input("WhatsApp")
            if st.form_submit_button("CADASTRAR"):
                user_ref.collection("meus_clientes").add({"nome": nome, "telefone": tel})
                st.cache_data.clear(); st.rerun()

    with t3:
        with st.form("f_srv"):
            serv = st.text_input("Serviço")
            prec = st.number_input("Preço", min_value=0.0)
            if st.form_submit_button("SALVAR"):
                user_ref.collection("meus_servicos").add({"nome": serv, "preco": prec})
                st.cache_data.clear(); st.rerun()

    with t4:
        with st.form("f_cx"):
            ds = st.text_input("Descrição")
            vl = st.number_input("Valor")
            tp = st.selectbox("Tipo", ["Entrada", "Saída"])
            if st.form_submit_button("LANÇAR"):
                user_ref.collection("meu_caixa").add({"descricao": ds, "valor": vl, "tipo": tp, "data": firestore.SERVER_TIMESTAMP})
                st.cache_data.clear(); st.rerun()
        if cx_list:
            st.download_button("📊 EXPORTAR FLUXO EXCEL", gerar_excel(cx_list), "vivv_pro.xlsx")

with col_r:
    st.subheader("📋 Compromissos")
    if not agnd: st.info("Sem pendências.")
    for a in agnd:
        with st.expander(f"📍 {a.get('hora')} - {a.get('cliente')}"):
            st.write(f"**{a.get('servico')}** | R$ {a.get('preco',0):.2f}")
            c1, c2, c3 = st.columns(3)
            # WhatsApp
            raw_t = next((c.get('telefone', '') for c in clis if c.get('nome') == a.get('cliente')), "")
            msg = urllib.parse.quote(f"Confirmado: {a.get('servico')} às {a.get('hora')}!")
            c1.markdown(f'<a href="https://wa.me/55{raw_t}?text={msg}" target="_blank" class="whatsapp-button">📱 Whats</a>', unsafe_allow_html=True)
            
            if c2.button("✅", key=f"f_{a['id']}"):
                user_ref.collection("minha_agenda").document(a['id']).update({"status": "Concluído"})
                user_ref.collection("meu_caixa").add({"descricao": f"Serviço: {a.get('cliente')}", "valor": a.get('preco', 0), "tipo": "Entrada", "data": firestore.SERVER_TIMESTAMP})
                st.cache_data.clear(); st.rerun()
            if c3.button("❌", key=f"d_{a['id']}"):
                user_ref.collection("minha_agenda").document(a['id']).delete()
                st.cache_data.clear(); st.rerun()

# ================= 8. GESTÃO & ANALYTICS =================
st.write("---")
with st.expander("⚙️ Gerenciar Clientes e Serviços"):
    t_c, t_s = st.tabs(["Clientes", "Serviços"])
    with t_c:
        if clis:
            df_clis = pd.DataFrame(clis)
            ed_c = st.data_editor(df_clis[["nome", "telefone"]], use_container_width=True, key="ed_cli")
            if st.button("SALVAR ALTERAÇÕES CLIENTES"):
                for i, r in ed_c.iterrows():
                    user_ref.collection("meus_clientes").document(df_clis.iloc[i]["id"]).update({"nome": r["nome"], "telefone": r["telefone"]})
                st.cache_data.clear(); st.success("Ok!"); st.rerun()

st.subheader("📊 Performance & Vivv AI")
if cx_list:
    fig = px.pie(pd.DataFrame(cx_list), values='valor', names='tipo', hole=.4, color='tipo', color_discrete_map={'Entrada':'#00d4ff', 'Saída':'#ff4b4b'})
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
    st.plotly_chart(fig, use_container_width=True)

prompt = st.text_input("O que deseja analisar hoje?", placeholder="Ex: Como aumentar meu lucro?")
if st.button("CONSULTAR ESTRATEGISTA IA") and prompt:
    try:
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={st.secrets['GOOGLE_API_KEY']}"
        ctx = f"Consultor Vivv Pro. Dados: {len(clis)} clientes, R$ {fat} faturado. Pergunta: {prompt}"
        res = requests.post(url, json={"contents": [{"parts": [{"text": ctx}]}]}, timeout=30)
        st.info(f"🚀 **Análise Vivv AI:**\n\n{res.json()['candidates'][0]['content']['parts'][0]['text']}")
    except: st.error("IA temporariamente offline.")
