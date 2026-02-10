import streamlit as st
import pandas as pd
import urllib.parse
import io
import json
import hashlib
import requests
import plotly.express as px
from datetime import datetime, timezone, timedelta
from google.cloud import firestore
from google.oauth2 import service_account
import time
import google.generativeai as genai
import os

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
    button[kind="secondary"]:active {
        border-color: #ffffff !important;
        color: #ffffff !important;
        box-shadow: 0 0 25px rgba(255, 255, 255, 0.8) !important;
        transition: 0.1s;
        transform: scale(0.95);
    }
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
    .ia-box {
        background: linear-gradient(90deg, rgba(0,212,255,0.1) 0%, rgba(121,40,202,0.1) 100%);
        border-left: 4px solid #00d4ff;
        padding: 20px; border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="vivv-logo">Vivv<span style="color:#00d4ff">.</span></div>', unsafe_allow_html=True)

# ================= 2. BANCO DE DADOS (FIRESTORE) =================
@st.cache_resource
def init_db():
    try:
        firebase_raw = st.secrets["FIREBASE_DETAILS"]
        secrets_dict = json.loads(firebase_raw)
        creds = service_account.Credentials.from_service_account_info(secrets_dict)
        return firestore.Client(credentials=creds)
    except Exception as e:
        st.error(f"Erro na conexão: {e}")
        return None

db = init_db()

# ================= 3. LÓGICA DE PAGAMENTO (STRIPE) =================
def criar_checkout_stripe(email_usuario):
    """
    Simulação/Estrutura para o Stripe. 
    Aqui você geraria o link real via API do Stripe.
    """
    # Exemplo de URL de checkout (substitua pelo link gerado via stripe.checkout.Session.create)
    # Com R$ 300 setup + R$ 49,90/mês
    checkout_url = "https://buy.stripe.com/exemplo_seu_link" 
    return checkout_url

# ================= 3. AUTENTICAÇÃO E SEGURANÇA =================
if "logado" not in st.session_state: st.session_state.logado = False
if "user_data" not in st.session_state: st.session_state.user_data = None

if not st.session_state.logado:
    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        st.markdown("<br><br>", unsafe_allow_html=True)
        tab_l, tab_c = st.tabs(["🔑 LOGIN VIVV", "📝 CRIAR CONTA"])
        
        with tab_l:
            le = st.text_input("E-mail", key="login_email").lower().strip()
            ls = st.text_input("Senha", type="password", key="login_pass")
            if st.button("ACESSAR SISTEMA", use_container_width=True):
                u_doc = db.collection("usuarios").document(le).get()
                if u_doc.exists:
                    u_data = u_doc.to_dict()
                    if u_data.get("senha") == hash_senha(ls):
                        st.session_state.logado = True
                        st.session_state.user_email = le
                        st.session_state.user_data = u_data
                        st.rerun()
                    else: st.error("Senha incorreta.")
                else: st.error("Usuário não encontrado.")

        with tab_c:
            with st.form("reg_etapa_1"):
                st.subheader("🚀 Comece agora")
                col1, col2 = st.columns(2)
                user_id = col1.text_input("Username Único (@exemplo)")
                nome_p = col2.text_input("Seu Nome Completo")
                
                email_c = st.text_input("E-mail de Acesso").lower().strip()
                whatsapp = st.text_input("WhatsApp (com DDD)")
                
                empresa = st.text_input("Nome do seu Negócio")
                tipo_neg = st.selectbox("Tipo de Negócio", ["Barbearia", "Salão de Beleza", "Estética", "Outros"])
                
                senha_c = st.text_input("Crie uma Senha Master", type="password")
                
                if st.form_submit_button("IR PARA PAGAMENTO 💳", use_container_width=True):
                    if email_c and senha_c and user_id:
                        # Verifica se usuário já existe
                        if db.collection("usuarios").document(email_c).get().exists:
                            st.error("E-mail já cadastrado.")
                        else:
                            # SALVA ETAPA 1 NO FIRESTORE
                            novo_user = {
                                "username": user_id,
                                "nome": nome_p,
                                "whatsapp": whatsapp,
                                "empresa": empresa,
                                "tipo_negocio": tipo_neg,
                                "senha": hash_senha(senha_c),
                                "ativo": False, # Bloqueado até pagar
                                "pago": False,
                                "plano": "pro",
                                "criado_em": datetime.now(fuso_br)
                            }
                            db.collection("usuarios").document(email_c).set(novo_user)
                            st.success("Cadastro realizado! Redirecionando para o pagamento...")
                            time.sleep(1.5)
                            # Simula redirecionamento
                            st.markdown(f'<meta http-equiv="refresh" content="0;URL=\'{criar_checkout_stripe(email_c)}\'">', unsafe_allow_html=True)
                            st.stop()
    st.stop()

# ================= 4. CORE ENGINE (DATA & ACCESS) =================
user_ref = db.collection("usuarios").document(st.session_state.user_email)
# Refresh dos dados para garantir status real do Firestore (importante pós-pagamento)
user_data = user_ref.get().to_dict()

if not user_data.get("ativo", False):
    st.warning("### 💳 Aguardando confirmação de pagamento")
    st.info(f"Olá {user_data.get('nome')}, detectamos que sua conta ainda não foi ativada.")
    
    st.markdown(f"""
    **O que está incluso no Plano Pro:**
    * Taxa de Ativação: R$ 300,00 (única)
    * Mensalidade: R$ 49,90
    """)
    
    if st.button("FINALIZAR PAGAMENTO AGORA", use_container_width=True):
        st.markdown(f'<meta http-equiv="refresh" content="0;URL=\'{criar_checkout_stripe(st.session_state.user_email)}\'">', unsafe_allow_html=True)
    
    if st.button("Já paguei? Atualizar status", type="secondary"):
        st.rerun()
        
    st.stop() # Mata a execução aqui, não deixa ver o dashboard

# ================= 5. DASHBOARD ELITE =================
c_top1, c_top2 = st.columns([5,1])
with c_top1:
    st.markdown(f"##### Seja bem vindo, <span style='color:#00d4ff'>{st.session_state.user_email}</span>.", unsafe_allow_html=True)
with c_top2:
    if st.button("LOGOUT", use_container_width=True):
        st.session_state.logado = False
        st.rerun()

m1, m2, m3, m4 = st.columns(4)
m1.markdown(f'<div class="metric-card"><small>👥 Clientes Ativos</small><h2>{len(clis)}</h2></div>', unsafe_allow_html=True)
m2.markdown(f'<div class="metric-card"><small>💰 Faturamento</small><h2 style="color:#00d4ff">{format_brl(faturamento)}</h2></div>', unsafe_allow_html=True)
m3.markdown(f'<div class="metric-card"><small>📈 Lucro Líquido</small><h2 style="color:#00ff88">{format_brl(faturamento-despesas)}</h2></div>', unsafe_allow_html=True)
m4.markdown(f'<div class="metric-card"><small>⏳ Pendentes</small><h2 style="color:#ff9100">{len(agnd)}</h2></div>', unsafe_allow_html=True)

# ================= 6. PAINEL UNIFICADO =================
st.write("---")
col_ops_l, col_ops_r = st.columns([1.3, 1])

with col_ops_l:
    st.markdown("### ⚡ Gestão Operacional")
    t1, t2, t3, t4 = st.tabs(["📅 Agendar", "👤 Clientes", "🛠️ Serviços", "💸 Caixa"])
    
    with t1:
        with st.form("form_ag_v10", clear_on_submit=True):
            cli_n = st.selectbox("Cliente", [c['nome'] for c in clis], key="cli_v10") if clis else None
            srv_n = st.selectbox("Serviço", [s['nome'] for s in srvs], key="srv_v10") if srvs else None
            c_d, c_h = st.columns(2)
            d_val = c_d.date_input("Data", key="dat_v10", format="DD/MM/YYYY")
            h_val = c_h.time_input("Horário", key="hor_v10")
            if st.form_submit_button("CONFIRMAR AGENDAMENTO", use_container_width=True):
                if cli_n and srv_n:
                    p_s = next((s['preco'] for s in srvs if s['nome'] == srv_n), 0)
                    user_ref.collection("minha_agenda").add({
                        "cliente": cli_n, "servico": srv_n, "preco": p_s,
                        "status": "Pendente", "data": d_val.strftime('%d/%m/%Y'),
                        "hora": h_val.strftime('%H:%M'), "timestamp": datetime.now()
                    })
                    st.cache_data.clear(); st.rerun()

    with t2:
        with st.form("form_cli_vFINAL", clear_on_submit=True):
            nome_c = st.text_input("Nome", key="nom_vF")
            tel_c = st.text_input("WhatsApp", key="tel_vF")
            if st.form_submit_button("CADASTRAR CLIENTE", use_container_width=True):
                if nome_c:
                    user_ref.collection("meus_clientes").add({"nome": nome_c, "telefone": tel_c})
                    st.cache_data.clear(); st.rerun()

    with t3:
        with st.form("form_srv_vFINAL", clear_on_submit=True):
            nome_s = st.text_input("Serviço", key="nsr_vF")
            preco_s = st.number_input("Preço", min_value=0.0, key="pre_vF")
            if st.form_submit_button("SALVAR SERVIÇO", use_container_width=True):
                user_ref.collection("meus_servicos").add({"nome": nome_s, "preco": preco_s})
                st.cache_data.clear(); st.rerun()

    with t4:
        with st.form("form_cx_vFINAL", clear_on_submit=True):
            desc_cx = st.text_input("Descrição", key="dsc_vF")
            valor_cx = st.number_input("Valor", min_value=0.0, format="%.2f", key="vlr_vF")
            tipo_cx = st.selectbox("Tipo", ["Entrada", "Saída"], key="tip_vF")
            if st.form_submit_button("LANÇAR", use_container_width=True):
                if valor_cx > 0:
                    user_ref.collection("meu_caixa").add({
                        "descricao": desc_cx, "valor": float(valor_cx), "tipo": tipo_cx, 
                        "data": hoje_str, "timestamp": datetime.now()
                    })
                    st.cache_data.clear(); st.rerun()

# ================= 7. PRÓXIMOS ATENDIMENTOS =================
st.write("---")
st.markdown("### 📋 Próximos Atendimentos")

with st.expander(f"Agenda de Hoje ({len(clis_hoje)})", expanded=True):
    if not clis_hoje:
        st.info("Agenda limpa para hoje.")
    else:
        exibidos = set()
        for ag in clis_hoje:
            id_a = ag.get('id')
            if id_a in exibidos: continue
            exibidos.add(id_a)
            t_raw = next((c.get('telefone', '') for c in clis if c.get('nome') == ag['cliente']), "")
            t_clean = "".join(filter(str.isdigit, str(t_raw))) if t_raw else "00000000000"
            c1, c2, c3, c4 = st.columns([2.5, 1.2, 0.8, 0.8])
            with c1:
                preco_f = f"{ag.get('preco', 0):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                st.markdown(f"**{ag['hora']}** | {ag['cliente']}<br><small style='color:#888'>{ag['servico']} • R$ {preco_f}</small>", unsafe_allow_html=True)
            with c2:
                st.markdown(f'''<a href="https://wa.me/55{t_clean}" target="_blank" style="text-decoration:none;"><div style="background-color: #25D366; color: white; text-align: center; padding: 8px 0px; border-radius: 8px; font-size: 10px; font-weight: bold; border: 1px solid rgba(255,255,255,0.2);">🟢 WHATSAPP</div></a>''', unsafe_allow_html=True)
            with c3:
                if st.button("✅", key=f"ok_v_{id_a}", use_container_width=True):
                    user_ref.collection("minha_agenda").document(id_a).update({"status": "Concluido"})
                    user_ref.collection("meu_caixa").add({
                        "data": hoje_str, "descricao": f"Serviço: {ag['cliente']}", 
                        "valor": float(ag.get('preco', 0)), "tipo": "Entrada", "timestamp": datetime.now()})
                    st.cache_data.clear(); st.rerun()
            with c4:
                if st.button("🗑️", key=f"del_v_{id_a}", use_container_width=True):
                    user_ref.collection("minha_agenda").document(id_a).delete()
                    st.cache_data.clear(); st.rerun()

# ================= 8. PERFORMANCE E CONFIGS =================
st.write("---")
col_perf_l, col_perf_r = st.columns([1, 1])

with col_perf_l:
    st.subheader("📊 Performance Financeira")
    if cx_list:
        df_cx = pd.DataFrame(cx_list)
        df_cx['valor'] = df_cx['valor'].astype(float)
        resumo = df_cx.groupby('tipo')['valor'].sum().reset_index()
        fig = px.pie(resumo, values='valor', names='tipo', hole=.6, color='tipo', color_discrete_map={'Entrada': '#00d4ff', 'Saída': '#ff4b4b'})
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color="white", height=300, margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig, use_container_width=True)

with col_perf_r:
    st.subheader("⚙️ Configurações & Dados")
    with st.expander("📝 Gerenciar Cadastros (Edição)"):
        tab_c_ed, tab_s_ed = st.tabs(["Clientes", "Serviços"])
        with tab_c_ed:
            if clis:
                df_c = pd.DataFrame(clis)
                edt_c = st.data_editor(df_c[["nome", "telefone"]], use_container_width=True, key="ed_cli_master")
                if st.button("SALVAR ALTERAÇÕES CLIENTES"):
                    for i, r in edt_c.iterrows():
                        user_ref.collection("meus_clientes").document(df_c.iloc[i]["id"]).update({"nome": r["nome"], "telefone": r["telefone"]})
                    st.cache_data.clear(); st.rerun()
        with tab_s_ed:
            if srvs:
                df_s = pd.DataFrame(srvs)
                edt_s = st.data_editor(df_s[["nome", "preco"]], use_container_width=True, key="ed_srv_master")
                if st.button("SALVAR ALTERAÇÕES SERVIÇOS"):
                    for i, r in edt_s.iterrows():
                        user_ref.collection("meus_servicos").document(df_s.iloc[i]["id"]).update({"nome": r["nome"], "preco": r["preco"]})
                    st.cache_data.clear(); st.rerun()

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine='xlsxwriter') as writer:
        if clis: pd.DataFrame(clis).astype(str).to_excel(writer, sheet_name='Clientes', index=False)
        if cx_list: pd.DataFrame(cx_list).astype(str).to_excel(writer, sheet_name='Caixa', index=False)
    st.download_button(label="📥 BAIXAR RELATÓRIO EXCEL", data=buf.getvalue(), file_name=f"VIVV_PRO_{datetime.now().strftime('%d_%m')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)


