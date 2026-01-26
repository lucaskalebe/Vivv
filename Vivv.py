

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
st.set_page_config(page_title="Vivv Pro", layout="wide", page_icon="🎯")
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
c_h1.markdown(f"##### Bem-vindo ao Vivv, <span style='color:#00d4ff'>{st.session_state.user_email}</span>", unsafe_allow_html=True)
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
col_ops_l, col_ops_r = st.columns([1.2, 1]) 

with col_ops_l: 
    st.subheader("Painel de Controle")
    t1, t2, t3, t4 = st.tabs(["📅 Agenda", "👤 Cliente", "🛠️ Serviço", "💵 Caixa"])
    
    with t1:
        with st.form(key="form_agenda", clear_on_submit=True):
            st.markdown("### 📅 Novo Agendamento")
            # Seleção compacta
            c_sel = st.selectbox("Cliente", [c['nome'] for c in clis], key="at_cli") if clis else st.warning("Cadastre um cliente primeiro!")
            s_sel = st.selectbox("Serviço", [s['nome'] for s in srvs], key="at_srv") if srvs else st.warning("Cadastre um serviço!")
            
            col_d, col_h = st.columns(2)
            d_ag = col_d.date_input("Data", format="DD/MM/YYYY")
            h_ag = col_h.time_input("Horário")

            if st.form_submit_button("CONFIRMAR AGENDAMENTO", use_container_width=True):
                if c_sel and s_sel:
                    p_v = next((s['preco'] for s in srvs if s['nome'] == s_sel), 0)
                    user_ref.collection("minha_agenda").add({
                        "cliente": c_sel, "servico": s_sel, "preco": p_v,
                        "status": "Pendente", "data": d_ag.strftime('%d/%m/%Y'),
                        "hora": h_ag.strftime('%H:%M'), "timestamp": datetime.now()
                    })
                    st.cache_data.clear()
                    st.rerun()

    with t2:
        with st.form("form_cliente", clear_on_submit=True):
            st.markdown("### 👤 Novo Cliente")
            n_cli = st.text_input("Nome Completo")
            t_cli = st.text_input("WhatsApp (com DDD)")
            if st.form_submit_button("SALVAR CLIENTE", use_container_width=True):
                if n_cli:
                    user_ref.collection("meus_clientes").add({"nome": n_cli, "telefone": t_cli})
                    st.cache_data.clear()
                    st.rerun()

    with t3:
        with st.form("form_servico", clear_on_submit=True):
            st.markdown("### 🛠️ Novo Serviço")
            n_srv = st.text_input("Nome do Serviço")
            p_srv = st.number_input("Preço (R$)", min_value=0.0, step=10.0)
            if st.form_submit_button("SALVAR SERVIÇO", use_container_width=True):
                if n_srv:
                    user_ref.collection("meus_servicos").add({"nome": n_srv, "preco": p_srv})
                    st.cache_data.clear()
                    st.rerun()

    with t4:
        with st.form("form_caixa", clear_on_submit=True):
            st.markdown("### 💸 Lançamento Manual")
            desc_cx = st.text_input("Descrição")
            val_cx = st.number_input("Valor", min_value=0.0)
            tipo_cx = st.selectbox("Tipo", ["Entrada", "Saída"])
            if st.form_submit_button("LANÇAR", use_container_width=True):
                user_ref.collection("meu_caixa").add({
                    "descricao": desc_cx, "valor": val_cx, "tipo": tipo_cx, "data": datetime.now()
                })
                st.cache_data.clear()
                st.rerun()

# --- COLUNA DA DIREITA: LISTA ULTRA COMPACTA ---
with col_ops_r:
    st.subheader("📋 Próximos Atendimentos")
    if not agnd:
        st.info("Agenda livre hoje.")
    else:
        for item in agnd:
            with st.container(border=True):
                # Layout compacto: Info | Whats | Ações
                c1, c2, c3 = st.columns([2.5, 0.7, 1.2])
                
                with c1:
                    st.markdown(f"**{item['hora']}** | {item['cliente']}")
                    st.caption(f"{item['servico']} • {format_brl(item.get('preco',0))}")
                
                with c2:
                    t_raw = next((c.get('telefone', '') for c in clis if c.get('nome') == item['cliente']), "")
                    t_clean = "".join(filter(str.isdigit, t_raw))
                    msg = urllib.parse.quote(f"Opa, e aí, beleza? Passando aqui pra informar que está confirmado seu {item['servico']} às {item['hora']}! Agradecemos sua preferência. Até mais 🤝🚀")
                    st.markdown(f'[![Whats](https://img.shields.io/badge/-%20-25D366?style=flat&logo=whatsapp&logoColor=white)](https://wa.me/55{t_clean}?text={msg})')

                with c3:
                    b1, b2 = st.columns(2)
                    # Finalizar (Check)
                    if b1.button("✅", key=f"f_{item['id']}", help="Concluir"):
                        user_ref.collection("minha_agenda").document(item['id']).update({"status": "Concluido"})
                        user_ref.collection("meu_caixa").add({
                            "data": datetime.now().strftime('%d/%m/%Y'),
                            "descricao": f"Serviço: {item['cliente']}",
                            "valor": item.get('preco', 0), "tipo": "Entrada"
                        })
                        st.cache_data.clear()
                        st.rerun()
                    # Cancelar (X)
                    if b2.button("❌", key=f"c_{item['id']}", help="Excluir"):
                        user_ref.collection("minha_agenda").document(item['id']).delete()
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
# --- RELATÓRIO EXCEL (CORRIGIDO) ---
output = io.BytesIO()
try:
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        if clis:
            df_export_c = pd.DataFrame(clis).drop(columns=['id'], errors='ignore')
            # Converte qualquer coluna de data/objeto para texto para evitar o ValueError
            df_export_c = df_export_c.astype(str) 
            df_export_c.to_excel(writer, sheet_name='Clientes', index=False)
            
        if cx_list:
            df_export_cx = pd.DataFrame(cx_list)
            # Converte datas e objetos complexos para texto antes de salvar
            df_export_cx = df_export_cx.astype(str)
            df_export_cx.to_excel(writer, sheet_name='Caixa', index=False)

    st.download_button(
        label="📊 BAIXAR RELATÓRIO EXCEL",
        data=output.getvalue(),
        file_name=f"Relatorio_Vivv_{datetime.now().strftime('%d_%m_%Y')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
except Exception as e:
    st.error(f"Erro ao gerar Excel: {e}")


# ================= 9. PERFORMANCE E INTELIGÊNCIA =================
st.write("---")
st.subheader("📊 Performance Financeira")

if cx_list:
    df_cx = pd.DataFrame(cx_list)
    df_cx['valor'] = df_cx['valor'].astype(float)
    
    # Agrupa por Tipo para o Gráfico
    resumo_grafico = df_cx.groupby('tipo')['valor'].sum().reset_index()
    
    import plotly.express as px
    
    fig = px.bar(
        resumo_grafico, 
        x='tipo', 
        y='valor', 
        color='tipo',
        color_discrete_map={'Entrada': '#00d4ff', 'Saída': '#ff4b4b'},
        text_auto='.2s',
        title="Entradas vs Saídas Totais"
    )
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_color="white",
        showlegend=False,
        margin=dict(l=20, r=20, t=40, b=20),
        height=300
    )
    
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Lance dados no caixa para gerar os gráficos.")

# ================= 10. VIVV AI =================
st.write("---")
st.subheader("💬 Vivv AI: Inteligência de Negócio")
prompt = st.text_input("O que deseja analisar hoje?", placeholder="Ex: Como dobrar meu faturamento?")

if st.button("CONSULTAR IA") and prompt:
    try:
        api_key = st.secrets["GOOGLE_API_KEY"]
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={api_key}"
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": f"Atue como consultor Vivv Pro. Analise os dados: {len(clis)} clientes, faturamento R$ {faturamento:.2f}, despesas R$ {despesas:.2f}. Pergunta: {prompt}. Responda em tópicos curtos."
                }]
            }]
        }
        
        with st.spinner("Vivv AI analisando seu negócio..."):
            response = requests.post(url, json=payload, timeout=30)
            res_json = response.json()
            
            if response.status_code == 200:
                texto_ia = res_json['candidates'][0]['content']['parts'][0]['text']
                st.info(f"🚀 **Análise Vivv AI:**\n\n{texto_ia}")
            else:
                st.error("Erro na comunicação com a IA. Verifique sua chave API nos Secrets.")
                
    except Exception as e:
        st.error(f"Erro de conexão: {e}")










