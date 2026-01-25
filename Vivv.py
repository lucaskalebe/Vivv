import streamlit as st
import pandas as pd
import urllib.parse
from datetime import datetime, timezone, timedelta
import google.generativeai as genai
from google.cloud import firestore
from google.oauth2 import service_account
import json
import hashlib


fuso_br = timezone(timedelta(hours=-3))

# CSS Refinado para remover GitHub, Menu e Header de forma estável
# ================= 1. CONFIGURAÇÃO E DESIGN VIVV =================
st.set_page_config(page_title="Vivv Pro", layout="wide", page_icon="🚀")

def hash_senha(senha):
    return hashlib.sha256(str.encode(senha)).hexdigest()

# CSS Único e Corrigido (Sem duplicidade de tags)
st.markdown("""
<style>
    header, [data-testid="stHeader"], .stAppDeployButton { display: none !important; }

    .vivv-top-left {
        position: fixed; top: 20px; left: 25px;
        color: #ffffff !important; font-size: 28px;
        font-weight: 900; z-index: 999999;
    }

    .stApp { background-color: #000205 !important; }

    .block-container { padding-top: 60px !important; max-width: 95% !important; }

    .neon-card {
        background: linear-gradient(145deg, #000814, #001220);
        border: 1px solid #0056b3;
        border-radius: 12px;
        padding: 12px 20px;
        transition: all 0.3s ease-in-out;
        cursor: pointer;
    }

    .neon-card:hover {
        border: 1px solid #00d4ff;
        box-shadow: 0 0 20px rgba(0, 212, 255, 0.3);
        transform: translateY(-3px);
    }

    .neon-card h2 {
        margin: 5px 0 0 0 !important;
        font-size: 1.8rem !important;
    }

    .orange-neon { color: #ff9100 !important; text-shadow: 0 0 15px rgba(255,145,0,0.5); text-align: center; }

    /* ESTILO DO BOTÃO WHATSAPP */
    .whatsapp-button {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        background: rgba(0, 212, 255, 0.1);
        color: #00d4ff !important;
        border: 1px solid #00d4ff;
        padding: 6px 15px;
        border-radius: 8px;
        text-decoration: none !important;
        font-weight: bold;
        transition: all 0.3s ease;
    }

    .whatsapp-button:hover {
        background: #00d4ff;
        color: #000814 !important;
        box-shadow: 0 0 15px rgba(0, 212, 255, 0.6);
        transform: scale(1.05);
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="vivv-top-left">Vivv</div>', unsafe_allow_html=True)

# ================= 2. CONEXÃO FIREBASE =================
# ================= 2. CONEXÃO FIREBASE =================

@st.cache_resource
def init_db():
    try:
        # Pega a string do segredo que você colou no painel
        secrets_dict = json.loads(st.secrets["FIREBASE_DETAILS"])
        
        # Converte a string em objeto de credencial (SEM procurar arquivo no disco)
        creds = service_account.Credentials.from_service_account_info(secrets_dict)
        
        return firestore.Client(credentials=creds)

    except Exception as e:
        st.error(f"Erro ao conectar ao Banco: {e}")
        return None

db = init_db()
if db is None:
    st.stop()


# ================= 3. LOGIN / CADASTRO =================
if "logado" not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    aba_login, aba_cadastro = st.tabs(["🔑 Acesso", "📝 Novo Cadastro"])
    
    with aba_login:
        le = st.text_input("E-mail", key="l_email").lower().strip()
        ls = st.text_input("Senha", type="password", key="l_pass")
        if st.button("ENTRAR"):
            u = db.collection("usuarios").document(le).get()
            if u.exists and u.to_dict().get("senha") == hash_senha(ls):
                st.session_state.logado = True
                st.session_state.user_email = le
                st.rerun()
            else:
                st.error("Dados incorretos.")
    
    with aba_cadastro:
        with st.form("reg_form"):
            n = st.text_input("Nome Completo")
            e = st.text_input("E-mail (Login)").lower().strip()
            s = st.text_input("Senha", type="password")
            if st.form_submit_button("CRIAR CONTA"):
                if e and s:
                    if db.collection("usuarios").document(e).get().exists:
                        st.error("Este e-mail já está cadastrado.")
                    else:
                        val = datetime.now(fuso_br) + timedelta(days=7)
                        db.collection("usuarios").document(e).set({
                            "nome": n, "senha": hash_senha(s), 
                            "pago": False, "validade": val
                        })
                        st.success("Conta criada! Use a aba Acesso para entrar.")
                else:
                    st.warning("Preencha e-mail e senha.")
    
    st.stop() # Bloqueia o resto do app se não estiver logado

# ================= 4. VERIFICAÇÃO DE ASSINATURA =================
def verificar_acesso():
    u_ref = db.collection("usuarios").document(st.session_state.user_email).get()
    if u_ref.exists:
        d = u_ref.to_dict()
        if not d.get("pago", False):
            # Validação de Expiração
            validade = d.get("validade")
            if validade and datetime.now(fuso_br) > validade.replace(tzinfo=fuso_br):
                st.markdown('<h1 class="orange-neon">VIVV</h1>', unsafe_allow_html=True)
                st.warning("### 🔒 Assinatura Necessária")
                st.link_button("💳 ATIVAR ACESSO VIVV PRO", "https://buy.stripe.com/exemplo")
                if st.button("🔄 Já realizei o pagamento"): st.rerun()
                st.stop()

verificar_acesso()

# ================= 5. DASHBOARD =================
user_ref = db.collection("usuarios").document(st.session_state.user_email)

@st.cache_data(ttl=60)
def carregar_dados_usuario(email):
    # Use o email para garantir que o cache é único por usuário
    u_ref = db.collection("usuarios").document(email)
    c = [{"id": doc.id, **doc.to_dict()} for doc in u_ref.collection("meus_clientes").stream()]
    s = [{"id": doc.id, **doc.to_dict()} for doc in u_ref.collection("meus_servicos").stream()]
    a = [{"id": doc.id, **doc.to_dict()} for doc in u_ref.collection("minha_agenda").where("status", "==", "Pendente").stream()]
    cx = [doc.to_dict() for doc in u_ref.collection("meu_caixa").stream()]
    return c, s, a, cx

# Chamada da função
clis, srvs, agnd, cx_list = carregar_dados_usuario(st.session_state.user_email)

# 3. Cálculos (permanecem iguais, mas agora usam os dados do cache)
faturamento = sum([float(x.get('valor', 0)) for x in cx_list if x.get('tipo') == 'Entrada'])
despesas = sum([float(x.get('valor', 0)) for x in cx_list if x.get('tipo') == 'Saída'])

c_header1, c_header2 = st.columns([4,1])
with c_header1:
    st.markdown(f"##### 🚀 adm: <span style='color:#00d4ff'>{st.session_state.user_email}</span>", unsafe_allow_html=True)
with c_header2:
    if st.button("SAIR"):
        st.session_state.logado = False
        st.rerun()

m1, m2, m3, m4 = st.columns(4)
m1.markdown(f'<div class="neon-card"><small>👥 CLIENTES</small><h2>{len(clis)}</h2></div>', unsafe_allow_html=True)
m2.markdown(f'<div class="neon-card"><small>💰 RECEITA</small><h2 style="color:#00d4ff">R$ {faturamento:,.2f}</h2></div>', unsafe_allow_html=True)
m3.markdown(f'<div class="neon-card"><small>📈 LUCRO</small><h2 style="color:#00ff88">R$ {faturamento-despesas:,.2f}</h2></div>', unsafe_allow_html=True)
m4.markdown(f'<div class="neon-card"><small>📅 PENDENTES</small><h2 style="color:#ff9100">{len(agnd)}</h2></div>', unsafe_allow_html=True)


# ================= 7. OPERAÇÕES =================
st.write("---")
col_ops_l, col_ops_r = st.columns([1.5, 2])

with col_ops_l:
    st.subheader("⚡ Painel de Controle")
    t1, t2, t3, t4 = st.tabs(["📅 Agenda", "👤 Cliente", "🛠️ Serviço", "📉 Caixa"])
    
    with t1:
        with st.form("f_ag"):
            c_sel = st.selectbox("Cliente", [c['nome'] for c in clis]) if clis else None
            s_sel = st.selectbox("Serviço", [s['nome'] for s in srvs]) if srvs else None
            col_d, col_h = st.columns(2)
            d_ag = col_d.date_input("Data", format="DD/MM/YYYY")
            h_ag = col_h.time_input("Hora")
            if st.form_submit_button("AGENDAR"):
                if c_sel and s_sel:
                    st.cache_data.clear() # <--- ADICIONE ESTA LINHA
                    p_v = next((s['preco'] for s in srvs if s['nome'] == s_sel), 0)
                    user_ref.collection("minha_agenda").add({
                        "cliente": c_sel, "servico": s_sel, "preco": p_v,
                        "status": "Pendente", "data": d_ag.strftime('%d/%m/%Y'),
                        "hora": h_ag.strftime('%H:%M')
                    })
                    st.rerun()

    with t2:
        with st.form("f_cli"):
            nome = st.text_input("Nome")
            tel = st.text_input("WhatsApp")
            if st.form_submit_button("CADASTRAR"):
                user_ref.collection("meus_clientes").add({"nome": nome, "telefone": tel})
                st.cache_data.clear()  # <--- Adicione isso para limpar o cache e ler o novo cliente
                st.rerun()

    with t3:
        with st.form("f_srv"):
            serv = st.text_input("Nome do Serviço")
            prec = st.number_input("Preço", min_value=0.0)
            if st.form_submit_button("SALVAR"):
                user_ref.collection("meus_servicos").add({"nome": serv, "preco": prec})
                st.cache_data.clear() # <--- ADICIONE ESTA LINHA
                st.rerun()

    with t4:
        with st.form("f_cx"):
            ds = st.text_input("Descrição")
            vl = st.number_input("Valor", min_value=0.0)
            tp = st.selectbox("Tipo", ["Entrada", "Saída"])
            if st.form_submit_button("LANÇAR"):
                st.cache_data.clear() # <--- ADICIONE ESTA LINHA
                user_ref.collection("meu_caixa").add({
                    "descricao": ds, "valor": vl, "tipo": tp, "data": firestore.SERVER_TIMESTAMP
                })
                st.rerun()

with col_ops_r:
    st.subheader("📋 Agendamentos:")
    if not agnd:
        st.info("Agenda livre para hoje.")
    else:
        for i, a in enumerate(agnd):
            with st.expander(f"📍 {a.get('hora')} - {a.get('cliente')}"):
                st.write(f"**Serviço:** {a.get('servico')} | **R$ {a.get('preco',0):.2f}**")
                c1, c2, c3 = st.columns(3)
                
                # WhatsApp Link
                raw_tel = next((c.get('telefone', '') for c in clis if c.get('nome') == a.get('cliente')), "")
                clean_tel = "".join(filter(str.isdigit, raw_tel))
                msg = urllib.parse.quote(f"VIVV PRO: Confirmado {a.get('servico')} às {a.get('hora')}!")
                c1.markdown(f'<a href="https://wa.me/55{clean_tel}?text={msg}" target="_blank" class="whatsapp-button">📱 Whats</a>', unsafe_allow_html=True)

                
                if c2.button("✅", key=f"f_{a['id']}"):
                    st.cache_data.clear()
                    user_ref.collection("minha_agenda").document(a['id']).update({"status": "Concluído"})
                    user_ref.collection("meu_caixa").add({
                        "descricao": f"Serviço: {a.get('cliente')}", "valor": a.get('preco', 0),
                        "tipo": "Entrada", "data": firestore.SERVER_TIMESTAMP
                    })
                    st.rerun()
                
                if c3.button("❌", key=f"d_{a['id']}"):
                    st.cache_data.clear()
                    user_ref.collection("minha_agenda").document(a['id']).delete()
                    st.rerun()

        

        # ================= 7.5 GESTÃO DE CADASTROS (EDITÁVEL) =================
# ================= 7.5 GESTÃO DE CADASTROS (EDITÁVEL) =================
st.write("---")
st.subheader("⚙️ Gestão de Cadastros")
exp_gestao = st.expander("Visualizar e Gerenciar Dados", expanded=False)

with exp_gestao:
    tab_edit_cli, tab_edit_srv = st.tabs(["👥 Meus Clientes", "🛠️ Meus Serviços"])
    
    with tab_edit_cli:
        if clis:
            df_clis = pd.DataFrame(clis)
            # Layout com colunas para tabela + ação de excluir
            col_tbl, col_act = st.columns([3, 1])
            
            with col_tbl:
                # Mostramos apenas Nome e Telefone para edição
                # use_container_width=True garante o layout otimizado
                edited_df = st.data_editor(
                    df_clis[["nome", "telefone"]], 
                    key="edit_cli_tab", 
                    use_container_width=True,
                    num_rows="fixed"
                )
            
            with col_act:
                st.write("🗑️ **Excluir**")
                id_para_deletar = st.selectbox("Selecionar para remover", df_clis["nome"], key="del_cli_sel")
                if st.button("CONFIRMAR EXCLUSÃO", key="btn_del_cli"):
                    doc_id = df_clis[df_clis["nome"] == id_para_deletar]["id"].values[0]
                    user_ref.collection("meus_clientes").document(doc_id).delete()
                    st.cache_data.clear()
                    st.rerun()

            if st.button("💾 SALVAR ALTERAÇÕES NOS CLIENTES"):
                # Lógica para atualizar nomes/telefones editados
                for index, row in edited_df.iterrows():
                    original_id = df_clis.iloc[index]["id"]
                    user_ref.collection("meus_clientes").document(original_id).update({
                        "nome": row["nome"],
                        "telefone": row["telefone"]
                    })
                st.cache_data.clear()
                st.success("Dados atualizados!")
                st.rerun()
        else:
            st.info("Cadastre clientes no Painel de Controle.")

    with tab_edit_srv:
        if srvs:
            df_srvs = pd.DataFrame(srvs)
            col_tbl_s, col_act_s = st.columns([3, 1])
            
            with col_tbl_s:
                edited_srv_df = st.data_editor(
                    df_srvs[["nome", "preco"]], 
                    key="edit_srv_tab", 
                    use_container_width=True
                )
            
            with col_act_s:
                st.write("🗑️ **Excluir**")
                srv_para_deletar = st.selectbox("Serviço para remover", df_srvs["nome"], key="del_srv_sel")
                if st.button("CONFIRMAR EXCLUSÃO", key="btn_del_srv"):
                    s_id = df_srvs[df_srvs["nome"] == srv_para_deletar]["id"].values[0]
                    user_ref.collection("meus_servicos").document(s_id).delete()
                    st.cache_data.clear()
                    st.rerun()

            if st.button("💾 SALVAR ALTERAÇÕES NOS SERVIÇOS"):
                for index, row in edited_srv_df.iterrows():
                    s_orig_id = df_srvs.iloc[index]["id"]
                    user_ref.collection("meus_servicos").document(s_orig_id).update({
                        "nome": row["nome"],
                        "preco": row["preco"]
                    })
                st.cache_data.clear()
                st.success("Preços/Nomes atualizados!")
                st.rerun()


# ================= 8. VIVV AI (SOLUÇÃO DE INFRAESTRUTURA) =================
# ================= 8. VIVV AI (SOLUÇÃO DE BAIXO NÍVEL) =================
# ================= 8. VIVV AI (VERSÃO COMPATÍVEL) =================
model = genai.GenerativeModel('gemini-1.5-flash')
st.write("---")
st.subheader("💬 Vivv AI: Inteligência de Negócio")
prompt = st.text_input("O que deseja analisar hoje?", placeholder="Ex: Como dobrar meu faturamento este mês?")

if st.button("CONSULTAR IA") and prompt:
    try:
        # 1. Configuração de API
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        
        # 2. Inicialização Simples e Direta
        # Removido o RequestOptions para evitar erro de 'unexpected keyword'
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        ctx = f"""
        Você é o consultor estratégico Vivv Pro.
        Dados atuais:
        - Clientes: {len(clis)}
        - Lucro: R$ {faturamento-despesas:.2f}
        
        Pergunta do usuário: {prompt}
        """
        
        with st.spinner("Vivv AI analisando dados..."):
            # 3. Chamada de geração
            response = model.generate_content(ctx)
            
            if response.text:
                st.info(response.text)
            else:
                st.warning("IA não retornou texto. Tente reformular a pergunta.")
                
    except Exception as e:
        st.error(f"Erro na IA: {e}")
        st.info("💡 Se o erro 404 voltar, o problema é 100% no cache do Streamlit Cloud.")







