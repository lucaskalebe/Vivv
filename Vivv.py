import streamlit as st
import pandas as pd
import urllib.parse
from datetime import datetime, timezone, timedelta
import google.generativeai as genai
from google.cloud import firestore
from google.oauth2 import service_account
import json
import hashlib

def hash_senha(senha):
    return hashlib.sha256(str.encode(senha)).hexdigest()

# ================= 1. CONFIGURAÇÃO E DESIGN ULTRA NEON =================
st.set_page_config(page_title="Vivv Pro", layout="wide", page_icon="🚀")
st.markdown("<div id='top'></div>", unsafe_allow_html=True)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    .stApp { background-color: #000205; color: #d1d1d1; font-family: 'Inter', sans-serif; }
    .neon-card {
        background: linear-gradient(145deg, #000814, #001220);
        border: 1px solid #0056b3;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 0 15px rgba(0, 86, 179, 0.1);
        transition: all 0.3s ease-in-out;
        text-align: center;
    }
    .neon-card:hover { transform: translateY(-5px); box-shadow: 0 0 30px rgba(0, 212, 255, 0.4); border-color: #00d4ff; }
    div.stButton > button {
        background: linear-gradient(45deg, #003566, #000814);
        color: #00d4ff; border: 1px solid #00d4ff; border-radius: 10px; width: 100%;
    }
    .orange-neon { color: #ff9100 !important; text-shadow: 0 0 15px rgba(255, 145, 0, 0.7); font-size: 2.5rem; font-weight: 800; }
    .wa-link { background: #25D366; color: black !important; padding: 10px; border-radius: 8px; font-weight: bold; text-decoration: none; display: block; text-align: center; }
</style>
""", unsafe_allow_html=True)



# ================= 2. BANCO DE DADOS =================
@st.cache_resource
def init_db():
    key_dict = json.loads(st.secrets["FIREBASE_DETAILS"])
    creds = service_account.Credentials.from_service_account_info(key_dict)
    return firestore.Client(credentials=creds)

db = init_db()

if "logado" not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    st.title("🚀 Vivv - Acesso")
    aba_login, aba_cadastro = st.tabs(["Entrar", "Cadastrar"])
    with aba_cadastro:
        with st.form("reg"):
            n, e, s = st.text_input("Nome"), st.text_input("E-mail"), st.text_input("Senha", type="password")
            if st.form_submit_button("CADASTRAR"):
                val = datetime.now(timezone.utc) + timedelta(days=7)
                db.collection("usuarios").document(e).set({"nome": n, "senha": hash_senha(s), "pago": False, "teste": True, "validade": val})
                st.success("Sucesso! Faça login.")

    
    with aba_login:
        le, ls = st.text_input("E-mail"), st.text_input("Senha", type="password")
        if st.button("ACESSAR"):
            u = db.collection("usuarios").document(le).get()
            if u.exists and u.to_dict().get("senha") == hash_senha(ls):
                st.session_state.logado, st.session_state.user_email = True, le
                st.rerun()
    st.stop() # O app para aqui se não estiver logado

# ESTA FUNÇÃO PRECISA ESTAR EXATAMENTE ASSIM:
def verificar_acesso():
    # As linhas abaixo têm 4 espaços de recuo (1 TAB)
    u_ref = db.collection("usuarios").document(st.session_state.user_email).get()
    if u_ref.exists:
        d = u_ref.to_dict()
        if not d.get("pago", False):
            st.warning("### 🔒 Acesso Restrito")
            st.write("Sua assinatura ainda não foi ativada. Conclua a ativação para liberar o sistema.")
            st.link_button("💳 ATIVAR MINHA CONTA", "https://buy.stripe.com/test_6oU4gB7Q4glM1JZ2Z06J200")
            if st.button("🔄 Já paguei, atualizar"): 
                st.rerun()
            st.stop() # Trava aqui se não houver pagamento confirmado

# Chamada da função encostada na esquerda
verificar_acesso()

# ================= 3. BUSCA DE DADOS =================
user_ref = db.collection("usuarios").document(st.session_state.user_email)

# Modifique a Seção 3 para incluir o ID
clis = []
for c in user_ref.collection("meus_clientes").stream():
    d = c.to_dict()
    d['id'] = c.id  # Guardamos o ID único do Firestore aqui
    clis.append(d)

srvs = []
for s in user_ref.collection("meus_servicos").stream():
    d = s.to_dict()
    d['id'] = s.id  # Guardamos o ID único do Firestore aqui
    srvs.append(d)


agnd = []
for a in user_ref.collection("minha_agenda").where("status", "==", "Pendente").stream():
    d = a.to_dict(); d['id'] = a.id; agnd.append(d)
caixa = [x.to_dict() for x in user_ref.collection("meu_caixa").stream()]

faturamento = sum([float(x['valor']) for x in caixa if x['tipo'] == 'Entrada'])
despesas = sum([float(x['valor']) for x in caixa if x['tipo'] == 'Saída'])

# ================= 4. DASHBOARD =================
col_title, col_logout = st.columns([5, 1])
# Saudação menor conforme pedido
col_title.markdown(f"##### 👋 Bem-vindo, <span style='color: #00d4ff;'>{st.session_state.user_email}</span>", unsafe_allow_html=True)
if col_logout.button("SAIR"):
    st.session_state.logado = False
    st.rerun()

m1, m2, m3, m4 = st.columns(4)
m1.markdown(f'<div class="neon-card"><small>CLIENTES</small><h2>{len(clis)}</h2></div>', unsafe_allow_html=True)
m2.markdown(f'<div class="neon-card"><small>RECEITA</small><h2 style="color:#00d4ff">R$ {faturamento:,.2f}</h2></div>', unsafe_allow_html=True)
m3.markdown(f'<div class="neon-card"><small>LUCRO</small><h2 style="color:#00ff88">R$ {faturamento-despesas:,.2f}</h2></div>', unsafe_allow_html=True)
m4.markdown(f'<div class="neon-card"><small>AGENDA</small><div class="orange-neon">{len(agnd)}</div></div>', unsafe_allow_html=True)

# ================= 5. GESTÃO OPERACIONAL (REFINADA) =================
st.write("---")
c_left, c_right = st.columns([1.5, 2])

with c_left:
    st.subheader("⚡ Painel de Controle")
    t1, t2, t3, t4 = st.tabs(["📅 Agenda", "👤 Cliente", "💰 Serviço", "📉 Caixa"])
    
    with t1:
        with st.form("f_agenda"):
            # Seleção de Cliente e Serviço
            c_s = st.selectbox("Selecione o Cliente", [c['nome'] for c in clis]) if clis else st.warning("Cadastre um cliente primeiro")
            s_s = st.selectbox("Selecione o Serviço", [s['nome'] for s in srvs]) if srvs else st.warning("Cadastre um serviço primeiro")
            
            # Novos campos: Data (BR) e Hora
            col_d, col_h = st.columns(2)
            # Adicionado format="DD/MM/YYYY" para o padrão brasileiro
            d_ag = col_d.date_input("Data do Agendamento", format="DD/MM/YYYY")
            h_ag = col_h.time_input("Horário")
            
            if st.form_submit_button("CONFIRMAR AGENDAMENTO"):
                if clis and srvs:
                    p_v = next((s['preco'] for s in srvs if s['nome'] == s_s), 0)
                    user_ref.collection("minha_agenda").add({
                        "cliente": c_s, 
                        "servico": s_s, 
                        "preco": p_v, 
                        "status": "Pendente", 
                        "data": d_ag.strftime('%d/%m/%Y'), # Salva no banco já formatado BR
                        "hora": h_ag.strftime('%H:%M')     # Salva apenas HH:MM
                    })
                    st.success("Agendado com sucesso!")
                    st.rerun()
                else:
                    st.error("Certifique-se de ter clientes e serviços cadastrados.")

    with t2:
        with st.form("f_cli"):
            nome, tel = st.text_input("Nome"), st.text_input("WhatsApp (com DDD)")
            if st.form_submit_button("CADASTRAR CLIENTE"):
                user_ref.collection("meus_clientes").add({"nome": nome, "telefone": tel})
                st.rerun()
    with t3:
        with st.form("f_srv"):
            serv = st.text_input("Nome do Serviço")
            prec = st.number_input("Preço", min_value=0.0)
            if st.form_submit_button("SALVAR SERVIÇO"):
                user_ref.collection("meus_servicos").add({"nome": serv, "preco": prec})
                st.rerun()

    with t4:
        # Este bloco precisa de 8 espaços (ou 2 TABs) de recuo da margem esquerda
        with st.form("f_cx"):
            ds = st.text_input("Descrição")
            vl = st.number_input("Valor", min_value=0.0)
            tp = st.selectbox("Tipo", ["Entrada", "Saída"])
            if st.form_submit_button("LANÇAR NO CAIXA"):
                user_ref.collection("meu_caixa").add({
                    "descricao": ds, 
                    "valor": vl, 
                    "tipo": tp, 
                    "data": firestore.SERVER_TIMESTAMP
                })
                st.rerun()




with c_right:
    st.subheader("📋 Fila de Atendimentos")
    if not agnd:
        st.info("Nenhum agendamento para hoje.")
    else:
        # Usamos enumerate para criar o índice 'i', garantindo chaves únicas
        for i, a in enumerate(agnd):
            with st.expander(f"📍 {a.get('data', '---')} às {a.get('hora', '---')} | {a.get('cliente', 'Cliente')}"):
                st.write(f"**Serviço:** {a.get('servico', '---')} — **Valor:** R$ {a.get('preco', 0.0):.2f}")                
                c1, c2, c3 = st.columns([1.5, 1, 1])
                
                # --- LÓGICA DO WHATSAPP ---
                raw_tel = next((c.get('telefone', '') for c in clis if c.get('nome') == a.get('cliente')), "")
                clean_tel = "".join(filter(str.isdigit, raw_tel))
                if clean_tel and not clean_tel.startswith("55"): 
                    clean_tel = "55" + clean_tel
                
                msg = urllib.parse.quote(f"Olá {a.get('cliente', 'Cliente')}, seu horário para {a.get('servico', 'serviço')} está confirmado para {a.get('data', '--/--')} às {a.get('hora', '--:--')}!")
                c1.markdown(f'<a href="https://wa.me/{clean_tel}?text={msg}" target="_blank" class="wa-link">📱 Confirmar</a>', unsafe_allow_html=True)
                
                # --- BOTÃO CONCLUIR (CHAVE ÚNICA) ---
                if c2.button("✅ Fechar", key=f"fechar_{a['id']}_{i}"):
                    user_ref.collection("minha_agenda").document(a['id']).update({"status": "Concluído"})
                    user_ref.collection("meu_caixa").add({
                        "descricao": f"Atend: {a.get('cliente', 'Cliente')}", 
                        "valor": a.get('preco', 0), 
                        "tipo": "Entrada", 
                        "data": firestore.SERVER_TIMESTAMP
                    })
                    st.rerun()

                # --- BOTÃO SAIR/CANCELAR (CHAVE ÚNICA) ---
                if c3.button("❌ Sair", key=f"cancelar_{a['id']}_{i}"):
                    user_ref.collection("minha_agenda").document(a['id']).delete()
                    st.rerun()


# ================= 6. BANCO DE DADOS EDITÁVEL (LIMPO E SEGURO) =================
st.write("---")
st.subheader("🗄️ Gestão de Dados (Editável)")
exp_db = st.expander("Clique para abrir a edição de Clientes e Serviços")

with exp_db:
    col_db1, col_db2 = st.columns(2)
    
    with col_db1:
        st.write("👤 **Clientes**")
        if clis:
            df_clis = pd.DataFrame(clis)
            # Ocultamos a coluna 'id' para o usuário não editar o que não deve
            edição_cli = st.data_editor(
                df_clis, 
                column_config={"id": None}, 
                use_container_width=True, 
                key="editor_clis_final"
            )
            
            if st.button("Salvar Alterações de Clientes", key="btn_save_clis"):
                for i, row in edição_cli.iterrows():
                    user_ref.collection("meus_clientes").document(row['id']).update({
                        "nome": row['nome'], 
                        "telefone": row['telefone']
                    })
                st.success("Clientes atualizados!")
                st.rerun()
        else:
            st.info("Sem clientes cadastrados.")

    with col_db2:
        st.write("💰 **Serviços**")
        if srvs:
            df_srvs = pd.DataFrame(srvs)
            # Ocultamos a coluna 'id' aqui também
            edição_srv = st.data_editor(
                df_srvs, 
                column_config={"id": None}, 
                use_container_width=True, 
                key="editor_srvs_final"
            )
            
            if st.button("Salvar Alterações de Serviços", key="btn_save_srvs"):
                for i, row in edição_srv.iterrows():
                    user_ref.collection("meus_servicos").document(row['id']).update({
                        "nome": row['nome'], 
                        "preco": row['preco']
                    })
                st.success("Serviços atualizados!")
                st.rerun()
        else:
            st.info("Sem serviços cadastrados.")
# ================= 7. IA CONSULTOR DE NEGÓCIOS (AJUSTADA PARA TOPO) =================
st.write("---")
st.subheader("💬 Vivv AI: Consultor de Negócios")

# Usamos colunas para o botão ficar ao lado do campo e economizar espaço
c_ia1, c_ia2 = st.columns([4, 1])
prompt = c_ia1.text_input("Como posso melhorar meu lucro hoje?", placeholder="Ex: Como atrair mais clientes?", label_visibility="collapsed")
btn_ia = c_ia2.button("PERGUNTAR")

if btn_ia and prompt:
    try:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        nome_modelo = 'models/gemini-1.5-flash' if 'models/gemini-1.5-flash' in modelos else modelos[0]
        model = genai.GenerativeModel(nome_modelo)
        
        ctx = f"Dados: Clientes={len(clis)}, Lucro=R${faturamento-despesas}. Pergunta: {prompt}"
        
        with st.spinner("Analisando..."):
            resposta = model.generate_content(ctx)
            st.info(resposta.text) # Exibe em um quadro azul para destaque
    except Exception as e:
        st.error(f"Erro na IA: {e}")






















