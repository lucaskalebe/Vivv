

import streamlit as st
import pandas as pd
import urllib.parse
import io
import json
import hashlib
import requests
from datetime import datetime, timezone, timedelta
from google.cloud import firestore
from google.oauth2 import service_account

# ================= 1. CONFIGURAÇÕES E ESTILO =================
st.set_page_config(page_title="Vivv Pro", layout="wide", page_icon="🚀")
fuso_br = timezone(timedelta(hours=-3))

def hash_senha(senha):
    return hashlib.sha256(str.encode(senha)).hexdigest()

def format_brl(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# CSS Customizado
st.markdown("""
<style>
    header, [data-testid="stHeader"], .stAppDeployButton { display: none !important; }
    .vivv-top-left { position: fixed; top: 20px; left: 25px; color: #ffffff !important; font-size: 28px; font-weight: 900; z-index: 999999; }
    .stApp { background-color: #000205 !important; }
    .block-container { padding-top: 60px !important; max-width: 95% !important; }
    .neon-card {
        background: linear-gradient(145deg, #000814, #001220);
        border: 1px solid #0056b3; border-radius: 12px; padding: 12px 20px;
        transition: all 0.3s ease-in-out;
    }
    .neon-card:hover { border: 1px solid #00d4ff; box-shadow: 0 0 20px rgba(0, 212, 255, 0.3); }
    .orange-neon { color: #ff9100 !important; text-shadow: 0 0 15px rgba(255,145,0,0.5); text-align: center; }
    [data-testid="stForm"] {
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(0, 212, 255, 0.2) !important;
        border-radius: 20px !important; padding: 25px !important;
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
        st.error(f"Erro ao conectar ao Banco: {e}")
        return None

db = init_db()
if not db: st.stop()

# ================= 3. LOGIN / ACESSO =================
if "logado" not in st.session_state: st.session_state.logado = False

if not st.session_state.logado:
    aba_l, aba_c = st.tabs(["🔑 Acesso", "📝 Novo Cadastro"])
    with aba_l:
        le = st.text_input("E-mail", key="l_email").lower().strip()
        ls = st.text_input("Senha", type="password", key="l_pass")
        if st.button("ENTRAR"):
            u = db.collection("usuarios").document(le).get()
            if u.exists and u.to_dict().get("senha") == hash_senha(ls):
                st.session_state.logado = True
                st.session_state.user_email = le
                st.rerun()
            else: st.error("Dados incorretos.")
    with aba_c:
        with st.form("reg_form"):
            n = st.text_input("Nome Completo")
            e = st.text_input("E-mail (Login)").lower().strip()
            s = st.text_input("Senha", type="password")
            if st.form_submit_button("CRIAR CONTA"):
                if e and s:
                    if db.collection("usuarios").document(e).get().exists: st.error("E-mail já cadastrado.")
                    else:
                        val = datetime.now(fuso_br) + timedelta(days=7)
                        db.collection("usuarios").document(e).set({"nome": n, "senha": hash_senha(s), "pago": False, "validade": val})
                        st.success("Conta criada! Entre pela aba Acesso.")
                else: st.warning("Preencha e-mail e senha.")
    st.stop()

# ================= 4. VERIFICAÇÃO DE ASSINATURA =================
user_ref = db.collection("usuarios").document(st.session_state.user_email)
u_data = user_ref.get().to_dict()
if not u_data.get("pago", False):
    validade = u_data.get("validade")
    if validade and datetime.now(fuso_br) > validade.replace(tzinfo=fuso_br):
        st.markdown('<h1 class="orange-neon">VIVV</h1>', unsafe_allow_html=True)
        st.warning("### 🔒 Assinatura Necessária")
        st.link_button("💳 ATIVAR ACESSO VIVV PRO", "https://buy.stripe.com/sua_url_aqui")
        if st.button("🔄 Já paguei"): st.rerun()
        st.stop()

# ================= 5. CARGA DE DADOS =================
@st.cache_data(ttl=60)
def load_data(email):
    u = db.collection("usuarios").document(email)
    c = [{"id": d.id, **d.to_dict()} for d in u.collection("meus_clientes").stream()]
    s = [{"id": d.id, **d.to_dict()} for d in u.collection("meus_servicos").stream()]
    a = [{"id": d.id, **d.to_dict()} for d in u.collection("minha_agenda").where("status", "==", "Pendente").stream()]
    cx = [d.to_dict() for d in u.collection("meu_caixa").stream()]
    return c, s, a, cx

clis, srvs, agnd, cx_list = load_data(st.session_state.user_email)
faturamento = sum([float(x.get('valor', 0)) for x in cx_list if x.get('tipo') == 'Entrada'])
despesas = sum([float(x.get('valor', 0)) for x in cx_list if x.get('tipo') == 'Saída'])

# ================= 6. DASHBOARD PRINCIPAL =================
c_h1, c_h2 = st.columns([4,1])
c_h1.markdown(f"##### 🚀 adm: <span style='color:#00d4ff'>{st.session_state.user_email}</span>", unsafe_allow_html=True)
if c_h2.button("SAIR"):
    st.session_state.logado = False
    st.rerun()

m1, m2, m3, m4 = st.columns(4)
m1.markdown(f'<div class="neon-card"><small>👥 CLIENTES</small><h2>{len(clis)}</h2></div>', unsafe_allow_html=True)
m2.markdown(f'<div class="neon-card"><small>💰 RECEITA</small><h2 style="color:#00d4ff">{format_brl(faturamento)}</h2></div>', unsafe_allow_html=True)
m3.markdown(f'<div class="neon-card"><small>📈 LUCRO</small><h2 style="color:#00ff88">{format_brl(faturamento-despesas)}</h2></div>', unsafe_allow_html=True)
m4.markdown(f'<div class="neon-card"><small>📅 PENDENTES</small><h2 style="color:#ff9100">{len(agnd)}</h2></div>', unsafe_allow_html=True)

st.write("---")

# ================= 7. PAINEL OPERACIONAL =================
col_l, col_r = st.columns([1.2, 1])

with col_l:
    st.subheader("⚡ Controle")
    t1, t2, t3, t4 = st.tabs(["📅 Agenda", "👤 Cliente", "🛠️ Serviço", "📉 Caixa"])
    
    with t1:
        with st.form(key="form_ag", clear_on_submit=True):
            st.markdown("### 📅 Novo Agendamento")
            with st.popover("👤 Selecionar Cliente e Serviço", use_container_width=True):
                c_sel = st.selectbox("Cliente", [c['nome'] for c in clis]) if clis else None
                s_sel = st.selectbox("Serviço", [s['nome'] for s in srvs]) if srvs else None
            cd, ch = st.columns(2)
            d_ag = cd.date_input("Data", format="DD/MM/YYYY")
            h_ag = ch.time_input("Horário")
            if st.form_submit_button("CONFIRMAR AGENDAMENTO", use_container_width=True):
                if c_sel and s_sel:
                    p = next((s['preco'] for s in srvs if s['nome'] == s_sel), 0)
                    user_ref.collection("minha_agenda").add({
                        "cliente": c_sel, "servico": s_sel, "preco": p,
                        "status": "Pendente", "data": d_ag.strftime('%d/%m/%Y'),
                        "hora": h_ag.strftime('%H:%M'), "timestamp": datetime.now()
                    })
                    st.cache_data.clear()
                    st.rerun()

    with t2:
        with st.form("f_cli"):
            nome = st.text_input("Nome")
            tel = st.text_input("WhatsApp")
            if st.form_submit_button("CADASTRAR CLIENTE"):
                user_ref.collection("meus_clientes").add({"nome": nome, "telefone": tel})
                st.cache_data.clear()
                st.rerun()

    with t3:
        with st.form("f_srv"):
            serv = st.text_input("Nome do Serviço")
            prec = st.number_input("Preço", min_value=0.0)
            if st.form_submit_button("SALVAR SERVIÇO"):
                user_ref.collection("meus_servicos").add({"nome": serv, "preco": prec})
                st.cache_data.clear()
                st.rerun()

    with t4:
        with st.form("f_cx"):
            ds = st.text_input("Descrição")
            vl = st.number_input("Valor", min_value=0.0)
            tp = st.selectbox("Tipo", ["Entrada", "Saída"])
            if st.form_submit_button("LANÇAR"):
                user_ref.collection("meu_caixa").add({"descricao": ds, "valor": vl, "tipo": tp, "data": datetime.now()})
                st.cache_data.clear()
                st.rerun()

with col_r:
    st.subheader("📋 Próximos Atendimentos")
    if not agnd: st.info("Sem pendências hoje.")
    else:
        for item in agnd:
            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.markdown(f"**{item['hora']} - {item['cliente']}**")
                    st.caption(f"🛠️ {item['servico']} | {format_brl(item.get('preco',0))}")
                with c2:
                    t_raw = next((c.get('telefone', '') for c in clis if c.get('nome') == item['cliente']), "")
                    t_clean = "".join(filter(str.isdigit, t_raw))
                    msg = urllib.parse.quote(f"Confirmado: {item['servico']} às {item['hora']}!")
                    st.markdown(f'[![Whats](https://img.shields.io/badge/Whats-25D366?style=flat&logo=whatsapp&logoColor=white)](https://wa.me/55{t_clean}?text={msg})')
                    if st.button("✅", key=f"f_{item['id']}"):
                        user_ref.collection("minha_agenda").document(item['id']).update({"status": "Concluido"})
                        user_ref.collection("meu_caixa").add({"data": datetime.now().strftime('%d/%m/%Y'), "descricao": f"Serviço: {item['cliente']}", "valor": item.get('preco', 0), "tipo": "Entrada"})
                        st.cache_data.clear()
                        st.rerun()

# ================= 8. GESTÃO E IA =================
st.write("---")
with st.expander("⚙️ Gerenciar Cadastros (Editar/Excluir)"):
    tc, ts = st.tabs(["👥 Clientes", "🛠️ Serviços"])
    with tc:
        if clis:
            df_c = pd.DataFrame(clis)
            edt_c = st.data_editor(df_c[["nome", "telefone"]], key="ed_c", use_container_width=True)
            if st.button("💾 Salvar Clientes"):
                for i, r in edt_c.iterrows():
                    user_ref.collection("meus_clientes").document(df_c.iloc[i]["id"]).update({"nome": r["nome"], "telefone": r["telefone"]})
                st.cache_data.clear(); st.rerun()
    with ts:
        if srvs:
            df_s = pd.DataFrame(srvs)
            edt_s = st.data_editor(df_s[["nome", "preco"]], key="ed_s", use_container_width=True)
            if st.button("💾 Salvar Serviços"):
                for i, r in edt_s.iterrows():
                    user_ref.collection("meus_servicos").document(df_s.iloc[i]["id"]).update({"nome": r["nome"], "preco": r["preco"]})
                st.cache_data.clear(); st.rerun()

# Relatório Excel
output = io.BytesIO()
with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
    if clis: pd.DataFrame(clis).drop(columns=['id'], errors='ignore').to_excel(writer, sheet_name='Clientes', index=False)
    if cx_list: pd.DataFrame(cx_list).to_excel(writer, sheet_name='Caixa', index=False)
st.download_button("📊 BAIXAR RELATÓRIO EXCEL", output.getvalue(), "Relatorio.xlsx", "application/vnd.ms-excel")

# Vivv AI
st.write("---")
st.subheader("💬 Vivv AI")
p_ai = st.text_input("Pergunta para a IA", placeholder="Ex: Como aumentar meu lucro?")
if st.button("CONSULTAR IA") and p_ai:
    try:
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={st.secrets['GOOGLE_API_KEY']}"
        payload = {"contents": [{"parts": [{"text": f"Analise: {len(clis)} clientes, R$ {faturamento} fat. Pergunta: {p_ai}"}]}]}
        res = requests.post(url, json=payload, timeout=30).json()
        st.info(res['candidates'][0]['content']['parts'][0]['text'])
    except: st.error("Erro na IA. Verifique a chave API.")
