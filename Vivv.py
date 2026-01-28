

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
    /* Reset e Fundo Deep Black */
    header, [data-testid="stHeader"], .stAppDeployButton { display: none !important; }
    .stApp { background-color: #000205 !important; }
    .block-container { padding-top: 50px !important; max-width: 95% !important; }

    /* Logo Vivv Flutuante */
    .vivv-logo {
        position: fixed; top: 15px; left: 25px;
        color: #ffffff; font-size: 32px; font-weight: 900;
        z-index: 999999; letter-spacing: -1px;
        text-shadow: 0 0 10px rgba(0, 212, 255, 0.5);
    }

    /* Cards de Métricas Neon */
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

    /* Cards de Agendamento Ultra Compactos */
    .compact-container {
        border-radius: 10px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        padding: 10px !important;
        margin-bottom: 8px !important;
        background: rgba(255, 255, 255, 0.02) !important;
    }

    /* Efeito de Brilho Branco ao clicar */
button[kind="secondary"]:active {
    border-color: #ffffff !important;
    color: #ffffff !important;
    box-shadow: 0 0 25px rgba(255, 255, 255, 0.8) !important;
    transition: 0.1s;
    transform: scale(0.95); /* Leve efeito de compressão ao clicar */
}

    /* Botões e Inputs Custom */
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

    /* Estilo Especial para IA */
    .ia-box {
        background: linear-gradient(90deg, rgba(0,212,255,0.1) 0%, rgba(121,40,202,0.1) 100%);
        border-left: 4px solid #00d4ff;
        padding: 20px; border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="vivv-logo">Vivv<span style="color:#00d4ff">.</span></div>', unsafe_allow_html=True)

# ================= 2. BANCO DE DADOS (FIRESTORE) =================


# O código deve ler o segredo como uma STRING e converter para JSON
if "FIREBASE_DETAILS" in st.secrets:
    firebase_raw = st.secrets["FIREBASE_DETAILS"]
    secrets_dict = json.loads(firebase_raw)
else:
    st.error("Erro: FIREBASE_DETAILS não encontrado nos Secrets!")

@st.cache_resource
def init_db():
    try:
        secrets_dict = json.loads(st.secrets["FIREBASE_DETAILS"])
        creds = service_account.Credentials.from_service_account_info(secrets_dict)
        return firestore.Client(credentials=creds)
    except Exception as e:
        st.error(f"Erro Crítico de Conexão: {e}")
        return None

db = init_db()
if not db: st.stop()

# ================= 3. AUTENTICAÇÃO E SEGURANÇA =================
if "logado" not in st.session_state: st.session_state.logado = False

if not st.session_state.logado:
    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        st.markdown("<br><br>", unsafe_allow_html=True)
        tab_l, tab_c = st.tabs(["🔑 LOGIN VIVV", "📝 CRIAR CONTA"])
        
        with tab_l:
            # .strip() remove espaços acidentais que o usuário digita no final
            le = st.text_input("E-mail", placeholder="seu@email.com").lower().strip()
            ls = st.text_input("Senha", type="password")
            
            if st.button("ACESSAR SISTEMA", use_container_width=True):
                if le and ls:
                    with st.spinner("Autenticando..."):
                        u = db.collection("usuarios").document(le).get()
                        
                        # Validação direta e segura
                        if u.exists:
                            dados_user = u.to_dict()
                            if dados_user.get("senha") == hash_senha(ls):
                                st.session_state.logado = True
                                st.session_state.user_email = le
                                st.success("Acesso autorizado!")
                                time.sleep(0.5) # Pequena pausa para o usuário ver o sucesso
                                st.rerun()
                            else:
                                st.error("Senha incorreta.")
                        else:
                            st.error("Usuário não encontrado.")
                else:
                    st.warning("Preencha todos os campos.")

        with tab_c:
            with st.form("reg_master"):
                n = st.text_input("Nome da Empresa/Profissional")
                e = st.text_input("E-mail de Acesso").lower().strip()
                s = st.text_input("Senha Master", type="password")
                if st.form_submit_button("FINALIZAR CADASTRO", use_container_width=True):
                    if e and s:
                        if db.collection("usuarios").document(e).get().exists: st.error("E-mail já em uso.")
                        else:
                            val = datetime.now(fuso_br) + timedelta(days=7)
                            db.collection("usuarios").document(e).set({
                                "nome": n, "senha": hash_senha(s), 
                                "pago": False, "validade": val, "criado_em": datetime.now()
                            })
                            st.success("Conta criada! Vá para aba Login.")
    st.stop()

# ================= 4. CORE ENGINE (DATA & ACCESS) =================
user_ref = db.collection("usuarios").document(st.session_state.user_email)

@st.cache_data(ttl=60)
def load_vivv_data(email):
    u = db.collection("usuarios").document(email)
    c = [{"id": d.id, **d.to_dict()} for d in u.collection("meus_clientes").stream()]
    s = [{"id": d.id, **d.to_dict()} for d in u.collection("meus_servicos").stream()]
    # Apenas pendentes para a lista de trabalho
    a = [{"id": d.id, **d.to_dict()} for d in u.collection("minha_agenda").where("status", "==", "Pendente").stream()]
    # Ordenar agenda por hora
    a = sorted(a, key=lambda x: x.get('hora', '00:00'))
    cx = [d.to_dict() for d in u.collection("meu_caixa").stream()]
    return c, s, a, cx

clis, srvs, agnd, cx_list = load_vivv_data(st.session_state.user_email)

hoje_str = datetime.now(fuso_br).strftime('%d/%m/%Y')
clis_hoje = [a for a in agnd if a.get('data') == hoje_str]

# Cálculos Rápidos
faturamento = sum([float(x.get('valor', 0)) for x in cx_list if x.get('tipo') == 'Entrada'])
despesas = sum([float(x.get('valor', 0)) for x in cx_list if x.get('tipo') == 'Saída'])

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

st.write("<br>", unsafe_allow_html=True)

# ================= 6, 7 e 8. PAINEL UNIFICADO (ANTI-ERRO) =================
st.write("---")
col_ops_l, col_ops_r = st.columns([1.3, 1])

# Filtro de hoje para a agenda
hoje_str = datetime.now(fuso_br).strftime('%d/%m/%Y')
clis_hoje = [a for a in agnd if a.get('data') == hoje_str]

with col_ops_l:
    st.markdown("### ⚡ Gestão Operacional")
    t1, t2, t3, t4 = st.tabs(["📅 Agendar", "👤 Clientes", "🛠️ Serviços", "💸 Caixa"])
    
    with t1:
        with st.form("form_ag_v10", clear_on_submit=True):
            cli_n = st.selectbox("Cliente", [c['nome'] for c in clis], key="cli_v10") if clis else None
            srv_n = st.selectbox("Serviço", [s['nome'] for s in srvs], key="srv_v10") if srvs else None
            c_d, c_h = st.columns(2)
            # AQUI ESTÁ A DATA FORMATADA DD/MM/YYYY
            d_val = c_d.date_input("Data", key="dat_v10", format="DD/MM/YYYY")
            h_val = c_h.time_input("Horário", key="hor_v10")
            
            # O BOTÃO DE SUBMIT (OBRIGATÓRIO DENTRO DO FORM)
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
            # Adicionado format="%.2f" para visual profissional
            valor_cx = st.number_input("Valor", min_value=0.0, format="%.2f", key="vlr_vF")
            tipo_cx = st.selectbox("Tipo", ["Entrada", "Saída"], key="tip_vF")
            
            if st.form_submit_button("LANÇAR", use_container_width=True):
                if valor_cx > 0:
                    user_ref.collection("meu_caixa").add({
                        "descricao": desc_cx, 
                        "valor": float(valor_cx), # Garante que salve como número
                        "tipo": tipo_cx, 
                        "data": hoje_str, 
                        "timestamp": datetime.now()
                    })
                    st.cache_data.clear(); st.rerun()
                
with col_ops_r:
    st.markdown("### 📋 Próximos Atendimentos")
    with st.expander(f"Agenda de Hoje ({len(clis_hoje)})", expanded=True):
        if not clis_hoje:
            st.info("Agenda limpa para hoje.")
        else:
            for ag in clis_hoje:
                id_a = ag.get('id')
                t_raw = next((c.get('telefone', '') for c in clis if c.get('nome') == ag['cliente']), "")
                t_clean = "".join(filter(str.isdigit, str(t_raw)))
                
                c1, c2, c3, c4 = st.columns([2.5, 1, 1, 1])
                with c1:
                    # No loop da agenda, dentro da c1:
                    # 1. Primeiro, criamos o texto do preço formatado (Padrão BR)
                    preco_formatado = f"{ag.get('preco', 0):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                    st.markdown(f"**{ag['hora']}** | {ag['cliente']}<br><small style='color:#888'>{ag['servico']} • R$ {preco_formatado}</small>", unsafe_allow_html=True)
                
                with c2:
                    # Estilização melhorada: Texto branco, fonte maior e centralizada
                    st.markdown(f'''
                        <a href="https://wa.me/55{t_clean}" target="_blank" style="text-decoration:none;">
                            <div style="
                                background-color: #25D366; 
                                color: white; 
                                text-align: center; 
                                padding: 8px 0px; 
                                border-radius: 8px; 
                                font-size: 12px; 
                                font-weight: bold; 
                                text-transform: uppercase;
                                letter-spacing: 1px;
                                margin-top: 5px;
                                border: 1px solid rgba(255,255,255,0.2);
                            ">
                                📱 WhatsApp
                            </div>
                        </a>
                    ''', unsafe_allow_html=True)
                with c3:
                    if st.button("✅", key=f"btn_ok_vF_{id_a}", use_container_width=True):
                        user_ref.collection("minha_agenda").document(id_a).update({"status": "Concluido"})
                        user_ref.collection("meu_caixa").add({
                            "data": hoje_str, 
                            "descricao": f"Serviço: {ag['cliente']}", 
                            "valor": float(ag.get('preco', 0)), # <--- Adicionado float() aqui
                            "tipo": "Entrada", 
                            "timestamp": datetime.now()})
                        
                        st.cache_data.clear(); st.rerun()
                        
    for ag in clis_hoje:
        id_a = ag.get("id")
        c1, c2, c3, c4 = st.columns([2.5, 1, 1, 1])

    with c1:
        # conteúdo do atendimento
        pass

    with c2:
        # botão whatsapp
        pass

    with c3:
        if st.button("✅", key=f"btn_ok_{id_a}", use_container_width=True):
            user_ref.collection("minha_agenda").document(id_a).update({"status": "Concluido"})
            user_ref.collection("meu_caixa").add({
                "data": hoje_str,
                "descricao": f"Serviço: {ag['cliente']}",
                "valor": float(ag.get("preco", 0)),
                "tipo": "Entrada",
                "timestamp": datetime.now()
            })
            st.cache_data.clear()
            st.rerun()

    # ✅ BLOCO CORRETO DO DELETE
    with c4:
        if st.button(
            "🗑️",
            key=f"btn_del_vF_{id_a}",
            use_container_width=True,
            help="Excluir agendamento"
        ):
            st.session_state[f"confirma_del_{id_a}"] = True

        if st.session_state.get(f"confirma_del_{id_a}", False):
            st.warning("Confirmar exclusão?")

            col_y, col_n = st.columns(2)

            with col_y:
                if st.button("SIM", key=f"yes_del_{id_a}", use_container_width=True):
                    user_ref.collection("minha_agenda").document(id_a).delete()
                    st.session_state[f"confirma_del_{id_a}"] = False
                    st.cache_data.clear()
                    st.success("Agendamento excluído com sucesso")
                    st.rerun()

            with col_n:
                if st.button("NÃO", key=f"no_del_{id_a}", use_container_width=True):
                    st.session_state[f"confirma_del_{id_a}"] = False


st.write("---")
col_perf_l, col_perf_r = st.columns([1, 1])

with col_perf_l:
    st.subheader("📊 Performance Financeira")
    if cx_list:
        df_cx = pd.DataFrame(cx_list)
        df_cx['valor'] = df_cx['valor'].astype(float)
        resumo = df_cx.groupby('tipo')['valor'].sum().reset_index()
        fig = px.pie(resumo, values='valor', names='tipo', hole=.6,
                     color='tipo', color_discrete_map={'Entrada': '#00d4ff', 'Saída': '#ff4b4b'})
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

    # Botão Excel Master
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine='xlsxwriter') as writer:
        if clis: pd.DataFrame(clis).astype(str).to_excel(writer, sheet_name='Clientes', index=False)
        if cx_list: pd.DataFrame(cx_list).astype(str).to_excel(writer, sheet_name='Caixa', index=False)
    
    st.download_button(
        label="📥 BAIXAR RELATÓRIO EXCEL COMPLETO",
        data=buf.getvalue(),
        file_name=f"VIVV_PRO_DATA_{datetime.now().strftime('%d_%m')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

# ================= 8. VIVV AI: RESILIÊNCIA TOTAL (ANTI-429) =================
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
st.write("---")
st.subheader("💬 Vivv AI: Consultoria Estratégica")
prompt_ia = st.text_input("Analise seu negócio ou peça dicas:", placeholder="Ex: Como posso atrair mais clientes?", key="ia_input_master")

if st.button("SOLICITAR ANÁLISE IA", use_container_width=True) and prompt_ia:
    if "GOOGLE_API_KEY" not in st.secrets:
        st.error("Chave API não configurada nos Secrets.")
    else:
        api_key = st.secrets["GOOGLE_API_KEY"]
        modelos = ["gemini-2.0-flash", "gemini-1.5-flash"]
        sucesso = False
        
        with st.spinner("Vivv AI analisando dados..."):
            for modelo in modelos:
                if sucesso:
                    break
                
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={api_key}"
        
                payload = {
    "contents": [{"parts": [{"text": f"Responda como consultor Vivv Pro. Dados: {len(clis)} clientes, R$ {faturamento:.2f}. Pergunta: {prompt_ia}"}]}]
}

# Tentativas para contornar o Erro 429
sucesso = False
for tentativa in range(2):
    try:
        response = requests.post(url, json=payload, timeout=25)

        # O código abaixo precisa estar recuado (dentro do try)
        if response.status_code == 200:
            res_json = response.json()
            texto_ia = (
                res_json.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "Resposta indisponível no momento.")
            )

            st.markdown(
                f'<div class="ia-box"><b>Vivv AI Insights ({modelo}):</b><br><br>{texto_ia}</div>',
                unsafe_allow_html=True
            )
            sucesso = True
            break

        elif response.status_code == 429:
            time.sleep(5)
        else:
            break

    except (requests.exceptions.RequestException, KeyError):
        continue

if not sucesso:
    st.error("⚠️ Instabilidade temporária detectada. Tente novamente em instantes.")
st.markdown("<br><p style='text-align:center; color:#555;'>Vivv Pro © 2026</p>", unsafe_allow_html=True)
st.markdown("<br><p style='text-align:center; color:#555;'>Contato Suporte 4002-8922</p>", unsafe_allow_html=True)












