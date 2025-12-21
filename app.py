import streamlit as st
import pandas as pd
from datetime import date
from sqlmodel import select, desc
import time
import streamlit.components.v1 as components

# --- CONFIGURAÇÕES DO PROJETO ---
VERSAO_SISTEMA = "1.0.7" # Versão atualizada com melhoria de contraste
ANO_COPYRIGHT = "2025"
NOME_INSTITUICAO = "Guriatã Tecnologia Educacional"

# --- Importações Internas ---
try:
    from src.database import (
        create_db_and_tables, populate_initial_data, get_session, salvar_lancamento, 
        limpar_todos_lancamentos, deletar_usuario_por_id, limpar_lancamentos_por_usuario,
        excluir_lancamento_individual, alterar_senha_usuario
    )
    from src.models.account_model import ContaContabil
    from src.models.lancamento_model import Lancamento
    from src.models.usuario_model import Usuario
    from src.controllers.balancete_controller import gerar_balancete
    from src.controllers.dre_controller import gerar_relatorio_dre
    from src.controllers.balanco_controller import gerar_dados_balanco
    from src.controllers.razonete_controller import obter_dados_razonetes
except ImportError:
    # Fallback para caso a estrutura de pastas seja diferente localmente
    from database import (
        create_db_and_tables, populate_initial_data, get_session, salvar_lancamento, 
        limpar_todos_lancamentos, deletar_usuario_por_id, limpar_lancamentos_por_usuario,
        excluir_lancamento_individual, alterar_senha_usuario
    )
    from models.account_model import ContaContabil
    from models.lancamento_model import Lancamento
    from models.usuario_model import Usuario
    from controllers.balancete_controller import gerar_balancete
    from controllers.dre_controller import gerar_relatorio_dre
    from controllers.balanco_controller import gerar_dados_balanco
    from controllers.razonete_controller import obter_dados_razonetes

# --- Configuração Inicial ---
st.set_page_config(page_title="Guriatã - Gestão Contábil", layout="wide", page_icon="assets/logo.png")
create_db_and_tables()
populate_initial_data()

# --- CSS GLOBAL (AJUSTADO PARA CONTRASTE E ESPAÇAMENTO) ---
st.markdown(f"""
<style>
    /* 1. Ajustes de Layout (Espaçamento) */
    .block-container {{
        padding-top: 1.5rem; 
        padding-bottom: 2rem; 
        max-width: 100%;
    }}
    
    div[data-testid="stVerticalBlock"] > div {{
        gap: 0.5rem;
    }}

    /* 2. MELHORIA DE CONTRASTE DOS CAMPOS (INPUTS) */
    /* Afeta: Texto, Número, Data */
    .stTextInput > div > div, 
    .stNumberInput > div > div, 
    .stDateInput > div > div {{
        background-color: #ffffff !important; /* Fundo Branco */
        border: 1px solid #a0a0a0 !important; /* Borda Cinza Visível */
        color: #000000 !important;
        border-radius: 5px;
    }}
    
    /* Afeta: Caixas de Seleção (Selectbox) */
    div[data-baseweb="select"] > div {{
        background-color: #ffffff !important;
        border: 1px solid #a0a0a0 !important;
        color: #000000 !important;
        border-radius: 5px;
    }}

    /* 3. Estilos da Logo e Sidebar */
    div[data-testid="stImage"] {{display: flex; justify-content: flex-end; align-items: center; padding-right: 20px;}}
    [data-testid="stSidebar"] div[data-testid="stImage"] {{justify-content: center; padding-right: 0px;}}

    /* 4. Estilos dos Razonetes */
    .razonete-container {{border: 1px solid #ddd; border-radius: 5px; padding: 10px; background-color: #ffffff; margin-bottom: 20px; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); page-break-inside: avoid;}}
    .razonete-header {{text-align: center; font-weight: bold; border-bottom: 2px solid #333; padding-bottom: 5px; margin-bottom: 5px; color: #333; font-size: 1.1em;}}
    .razonete-body {{display: flex; min-height: 100px;}}
    .col-debito {{width: 50%; border-right: 2px solid #333; text-align: right; padding-right: 10px; color: #d63031;}}
    .col-credito {{width: 50%; text-align: left; padding-left: 10px; color: #0984e3;}}
    .razonete-footer {{border-top: 1px solid #aaa; margin-top: 5px; padding-top: 5px; display: flex; font-weight: bold; font-size: 0.9em;}}
    
    .footer-text {{font-size: 0.8em; color: gray; text-align: center; margin-top: 20px;}}

    /* 5. Modo Impressão */
    @media print {{
        [data-testid="stSidebar"], header, footer, .stButton, .stTextInput, .stSelectbox, .stDateInput, .stNumberInput, button[title="View fullscreen"], .stDeployButton, [data-testid="stExpander"] {{
            display: none !important;
        }}
        .block-container, [data-testid="stAppViewContainer"] {{
            background-color: white !important; padding: 0 !important; margin: 0 !important;
        }}
        body, h1, h2, h3, h4, p, div {{
            color: black !important; -webkit-print-color-adjust: exact;
        }}
        .razonete-container {{
            break-inside: avoid; border: 1px solid #000 !important;
        }}
    }}
</style>
""", unsafe_allow_html=True)

# --- FUNÇÕES AUXILIARES ---
def botao_imprimir():
    components.html(
        """<script>function printPage(){window.parent.print();}</script>
        <div style="display: flex; justify-content: center; margin-top: 20px;">
            <button onclick="printPage()" style="background-color: #004b8d; color: white; border: none; padding: 10px 24px; border-radius: 5px; font-size: 16px; font-weight: bold; cursor: pointer; display: flex; align-items: center; gap: 8px;">🖨️ Imprimir Relatório</button>
        </div>""", height=70
    )

def rodape_institucional():
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"""<div class='footer-text'><b>{NOME_INSTITUICAO}</b><br>Versão {VERSAO_SISTEMA}<br>© {ANO_COPYRIGHT} Todos os direitos reservados.</div>""", unsafe_allow_html=True)

# --- LOGIN ---
if "usuario_logado" not in st.session_state: st.session_state["usuario_logado"] = None

def verificar_credenciais():
    session = get_session()
    usuario_input = st.session_state.get("login_user")
    senha_input = st.session_state.get("login_pass")
    statement = select(Usuario).where(Usuario.username == usuario_input).where(Usuario.senha == senha_input)
    result = session.exec(statement).first()
    if result:
        st.session_state["usuario_logado"] = result
        st.success(f"Bem-vindo(a), {result.nome}!")
        time.sleep(0.5)
        st.rerun()
    else: st.error("Usuário ou senha incorretos.")

def realizar_logout(): st.session_state["usuario_logado"] = None; st.rerun()

# --- FUNÇÕES DE CADASTRO COM LIMPEZA DE CAMPOS ---
def callback_criar_usuario():
    u = st.session_state.get("k_new_user", "")
    p = st.session_state.get("k_new_pass", "")
    n = st.session_state.get("k_new_name", "")
    perf = st.session_state.get("k_new_perf", "aluno")

    if n and u and p:
        session = get_session()
        if session.exec(select(Usuario).where(Usuario.username == u)).first():
             st.toast("⚠️ Usuário já existe!", icon="⚠️")
        else:
            session.add(Usuario(username=u, senha=p, nome=n, perfil=perf))
            session.commit()
            st.toast(f"✅ Usuário {n} criado com sucesso!", icon="✅")
            st.session_state["k_new_user"] = ""
            st.session_state["k_new_pass"] = ""
            st.session_state["k_new_name"] = ""
    else:
        st.toast("⚠️ Preencha todos os campos.", icon="⚠️")

if not st.session_state["usuario_logado"]:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col_logo, col_form = st.columns([1, 1], gap="small", vertical_alignment="center")
    with col_logo: st.image("assets/logo.png", width=350)
    with col_form:
        st.markdown("### Acesso ao Sistema")
        with st.form("form_login"):
            st.text_input("Usuário", key="login_user")
            st.text_input("Senha", type="password", key="login_pass")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.form_submit_button("Entrar", type="primary", use_container_width=True): verificar_credenciais()
        st.markdown(f"<div style='text-align:center; margin-top:20px; color:gray; font-size:0.8em;'>© {ANO_COPYRIGHT} {NOME_INSTITUICAO}</div>", unsafe_allow_html=True)
    st.stop()

# --- SISTEMA LOGADO ---
usuario_atual = st.session_state["usuario_logado"]
session = get_session()
perfil = usuario_atual.perfil

if perfil == 'admin': filtro_id = None; aviso_modo = "👁️ Modo Visão Geral (Todos os Lançamentos)"
else: filtro_id = usuario_atual.id; aviso_modo = "🔒 Modo Individual (Seus Lançamentos)"

with st.sidebar:
    st.image("assets/logo.png", width=180)
    st.divider()
    st.write(f"👤 **{usuario_atual.nome}**")
    st.caption(f"Perfil: {perfil.upper()}")
    if st.button("Sair (Logout)"): realizar_logout()
    st.divider()
    opcoes_menu = ["Plano de Contas", "Novo Lançamento", "Diário (Extrato)", "Razonetes (T)", "Balancete", "DRE (Resultado)", "Balanço Patrimonial"]
    if perfil in ['admin', 'professor']: opcoes_menu.append("Gestão de Usuários"); opcoes_menu.append("Configurações")
    menu = st.radio("Navegação", opcoes_menu)
    rodape_institucional()

def carregar_contas_analiticas():
    results = session.exec(select(ContaContabil).where(ContaContabil.tipo == "Analítica")).all()
    results.sort(key=lambda x: x.codigo)
    return [f"{c.codigo} - {c.nome}" for c in results]

def widget_filtro_data():
    with st.expander("📅 Filtrar Período de Análise", expanded=True):
        st.markdown("<small style='color:grey'>Selecione o intervalo de datas para visualizar os lançamentos.</small>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        inicio_padrao = date(date.today().year, 1, 1) 
        d_inicio = c1.date_input("Data Inicial", value=inicio_padrao)
        d_fim = c2.date_input("Data Final", value=date.today())
    return d_inicio, d_fim

# --- CALLBACK PARA LANÇAMENTOS ---
def callback_salvar_lancamento():
    dt = st.session_state.get("k_data", date.today())
    val = st.session_state.get("k_valor", 0.0)
    hist = st.session_state.get("k_hist", "")
    deb = st.session_state.get("k_debito")
    cred = st.session_state.get("k_credito")

    if deb and cred and val > 0 and deb != cred:
        novo_lancamento = Lancamento(
            data_lancamento=dt, 
            historico=hist, 
            valor=val, 
            conta_debito=deb.split(" - ")[0], 
            conta_credito=cred.split(" - ")[0], 
            usuario_id=usuario_atual.id
        )
        salvar_lancamento(novo_lancamento)
        st.toast("✅ Lançamento salvo com sucesso!", icon="💾")
        st.session_state["k_valor"] = 0.0
        st.session_state["k_hist"] = ""
        st.session_state["k_debito"] = None
        st.session_state["k_credito"] = None
    else:
        st.toast("❌ Erro: Verifique contas (não podem ser iguais) e valor.", icon="❌")

# --- PÁGINAS ---
if menu == "Plano de Contas":
    st.header("Plano de Contas")
    contas = session.exec(select(ContaContabil).order_by(ContaContabil.codigo)).all()
    df_pc = pd.DataFrame([c.model_dump() for c in contas])
    def indent_name(row):
        padding = (row['nivel'] - 1) * 20
        return [f'padding-left: {padding}px;' if col == 'nome' else '' for col in row.index]
    styled_df = df_pc.style.apply(indent_name, axis=1)
    st.dataframe(styled_df, hide_index=True, use_container_width=True, column_order=["codigo", "nome", "tipo", "natureza"], column_config={"codigo": st.column_config.TextColumn("Código"), "nome": st.column_config.TextColumn("Nome da Conta"), "tipo": st.column_config.TextColumn("Tipo"), "natureza": st.column_config.TextColumn("Natureza")})
    botao_imprimir()

elif menu == "Novo Lançamento":
    st.header("📝 Escrituração")
    st.caption(aviso_modo)
    
    col1, col2 = st.columns(2)
    with col1:
        st.date_input("Data do Fato", value=date.today(), max_value=date.today(), key="k_data")
        st.number_input("Valor (R$)", min_value=0.00, step=10.00, key="k_valor")
    with col2:
        st.text_input("Histórico", help="Breve descrição", key="k_hist")
    
    st.divider()
    lista = carregar_contas_analiticas()
    c_deb, c_cred = st.columns(2)
    with c_deb: 
        st.selectbox("Débito (Destino/Aplicação)", lista, index=None, placeholder="Selecione...", key="k_debito")
    with c_cred: 
        st.selectbox("Crédito (Origem/Fonte)", lista, index=None, placeholder="Selecione...", key="k_credito")
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.button("💾 Salvar Lançamento", type="primary", on_click=callback_salvar_lancamento)

elif menu == "Diário (Extrato)":
    st.header("📖 Diário Contábil")
    d_ini, d_fim = widget_filtro_data()
    query = select(Lancamento).where(Lancamento.data_lancamento >= d_ini).where(Lancamento.data_lancamento <= d_fim).order_by(desc(Lancamento.data_lancamento), desc(Lancamento.id))
    if filtro_id: query = query.where(Lancamento.usuario_id == filtro_id)
    res = session.exec(query).all()
    if res:
        df = pd.DataFrame([l.model_dump() for l in res])
        st.dataframe(df, hide_index=True, use_container_width=True, column_config={"valor": st.column_config.NumberColumn(format="R$ %.2f")})
        botao_imprimir()
        st.divider()
        with st.expander("🗑️ Corrigir/Excluir Lançamento"):
            st.write(f"Editando lançamentos do período: {d_ini.strftime('%d/%m')} até {d_fim.strftime('%d/%m')}")
            if res:
                lancamento_para_apagar = st.selectbox("Selecione o lançamento:", res, format_func=lambda x: f"ID {x.id} | {x.data_lancamento} | R$ {x.valor:.2f} | {x.historico}")
                if st.button("Confirmar Exclusão", type="secondary"):
                    excluir_lancamento_individual(lancamento_para_apagar.id)
                    st.success("Apagado!"); time.sleep(1); st.rerun()
    else: st.warning(f"Nenhum lançamento encontrado entre {d_ini.strftime('%d/%m/%Y')} e {d_fim.strftime('%d/%m/%Y')}.")

elif menu == "Razonetes (T)":
    st.header("🗂️ Razonetes")
    dados = obter_dados_razonetes(session, filtro_id)
    if not dados: st.info("Faça lançamentos para ver os razonetes.")
    else:
        st.markdown("---")
        cols = st.columns(3)
        for i, c in enumerate(dados):
            with cols[i % 3]:
                html_d = "".join([f"<div>{v:,.2f}</div>" for v in c['mov_debitos']])
                html_c = "".join([f"<div>{v:,.2f}</div>" for v in c['mov_creditos']])
                st.markdown(f"""<div class="razonete-container"><div class="razonete-header">{c['nome']}</div><div class="razonete-body"><div class="col-debito">{html_d}</div><div class="col-credito">{html_c}</div></div><div class="razonete-footer"><div style="width:50%;text-align:right;color:#d63031;">Total: {c['total_d']:,.2f}</div><div style="width:50%;padding-left:10px;color:#0984e3;">Total: {c['total_c']:,.2f}</div></div></div>""", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        botao_imprimir()

elif menu == "Balancete":
    st.header("⚖️ Balancete de Verificação")
    df, td, tc = gerar_balancete(session, filtro_id)
    if not df.empty:
        st.dataframe(df, hide_index=True, use_container_width=True, column_config={"Total Débitos": st.column_config.NumberColumn(format="R$ %.2f"), "Total Créditos": st.column_config.NumberColumn(format="R$ %.2f"), "Saldo Atual": st.column_config.NumberColumn(format="R$ %.2f")})
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Débito", f"R$ {td:,.2f}"); c2.metric("Total Crédito", f"R$ {tc:,.2f}")
        if round(td - tc, 2) == 0: c3.success("✅ Partidas Dobradas: OK!")
        else: c3.error(f"⚠️ Diferença: {td-tc}")
        botao_imprimir()
    else: st.info("Vazio.")

elif menu == "DRE (Resultado)":
    st.header("📉 Demonstração do Resultado (DRE)")
    dados, lucro = gerar_relatorio_dre(session, filtro_id)
    cor_resultado = "normal" if lucro >= 0 else "off"
    st.metric("Resultado Líquido do Exercício", f"R$ {lucro:,.2f}", delta="Lucro" if lucro > 0 else "Prejuízo", delta_color=cor_resultado)
    st.divider()
    for l in dados:
        c1, c2 = st.columns([3, 1])
        if l["Destaque"]: c1.markdown(f"**{l['Descrição']}**"); c2.markdown(f"**R$ {l['Valor']:,.2f}**")
        else: c1.write(l['Descrição']); c2.write(f"R$ {l['Valor']:,.2f}")
        st.markdown("---")
    botao_imprimir()

elif menu == "Balanço Patrimonial":
    st.header("🏛️ Balanço Patrimonial")
    st.markdown("---")
    la, lp, ta, tp = gerar_dados_balanco(session, filtro_id)
    c1, c2, c3 = st.columns([1, 0.1, 1])
    with c1:
        st.subheader("Ativo"); st.markdown("<div style='background:#f0f2f6;padding:10px;border-radius:10px;'>", unsafe_allow_html=True)
        for i in la: st.write(f"**{i['Grupo']}**" if i['Destaque'] else i['Grupo']); st.write(f"R$ {i['Valor']:,.2f}"); st.divider()
        st.markdown("</div>", unsafe_allow_html=True)
    with c3:
        st.subheader("Passivo"); st.markdown("<div style='background:#f0f2f6;padding:10px;border-radius:10px;'>", unsafe_allow_html=True)
        for i in lp: st.write(f"**{i['Grupo']}**" if i['Destaque'] else i['Grupo']); st.write(f"R$ {i['Valor']:,.2f}"); st.divider()
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("---")
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Ativo", f"R$ {ta:,.2f}"); m2.metric("Total Passivo + PL", f"R$ {tp:,.2f}")
    if round(ta - tp, 2) == 0: m3.success("✅ Balanço Fechado!")
    else: m3.error(f"⚠️ Diferença de R$ {ta-tp:,.2f}")
    botao_imprimir()

elif menu == "Gestão de Usuários":
    st.header("👥 Gestão de Usuários")
    opcoes = ["aluno", "professor", "admin"] if perfil == 'admin' else ["aluno"]
    
    with st.expander("➕ Cadastrar Novo Usuário", expanded=True):
        col_cad1, col_cad2 = st.columns(2)
        with col_cad1:
            st.text_input("Nome", key="k_new_name")
            st.text_input("Login", key="k_new_user")
        with col_cad2:
            st.text_input("Senha", type="password", key="k_new_pass")
            st.selectbox("Perfil", opcoes, key="k_new_perf")
        
        st.button("Cadastrar", on_click=callback_criar_usuario)

    st.divider()
    st.subheader("🔐 Alterar Senhas")
    if perfil == 'admin': users_change = session.exec(select(Usuario)).all()
    else: users_change = session.exec(select(Usuario).where(Usuario.perfil == 'aluno')).all()
    if users_change:
        col_u, col_p, col_b = st.columns([2, 2, 1], vertical_alignment="bottom")
        with col_u: user_to_change = st.selectbox("Usuário", users_change, format_func=lambda x: f"{x.nome} ({x.username})")
        with col_p: new_pass = st.text_input("Nova Senha", type="password", key="new_pass_input")
        with col_b:
            if st.button("Alterar Senha", type="primary"):
                if new_pass: alterar_senha_usuario(user_to_change.id, new_pass); st.success(f"Senha alterada!"); time.sleep(1); st.rerun()
                else: st.warning("Digite a nova senha.")
    st.divider()
    st.subheader("🗑️ Excluir Usuários")
    if perfil == 'admin': users_del = session.exec(select(Usuario).where(Usuario.id != usuario_atual.id)).all()
    else: users_del = session.exec(select(Usuario).where(Usuario.perfil == 'aluno')).all()
    if users_del:
        user_to_delete = st.selectbox("Selecione para EXCLUIR:", users_del, format_func=lambda x: f"{x.nome} ({x.perfil})")
        if st.button(f"Excluir {user_to_delete.nome}", type="primary"): deletar_usuario_por_id(user_to_delete.id); st.success("Excluído!"); time.sleep(1); st.rerun()
    st.divider()
    st.subheader("Lista Geral")
    todos_users = session.exec(select(Usuario)).all()
    st.dataframe(pd.DataFrame([{"ID": u.id, "Nome": u.nome, "Login": u.username, "Perfil": u.perfil} for u in todos_users]), hide_index=True)

elif menu == "Configurações":
    st.header("⚙️ Gerenciamento de Dados")
    st.subheader("🧹 Limpar Lançamentos por Usuário")
    if perfil == 'admin': users_clean = session.exec(select(Usuario)).all()
    else: users_clean = session.exec(select(Usuario).where(Usuario.perfil == 'aluno')).all()
    if users_clean:
        target_user = st.selectbox("Usuário para ZERAR lançamentos:", users_clean, format_func=lambda x: f"{x.nome} ({x.perfil})")
        if st.button(f"Apagar Lançamentos de {target_user.nome}"): limpar_lancamentos_por_usuario(target_user.id); st.success("Apagado!"); time.sleep(1); st.rerun()
    st.divider()
    if perfil == 'admin':
        st.subheader("🔥 Reset Global (Perigo)")
        confirm = st.checkbox("Confirmar exclusão global")
        if st.button("ZERAR TUDO", type="primary", disabled=not confirm): limpar_todos_lancamentos(); st.success("Resetado!"); time.sleep(1); st.rerun()