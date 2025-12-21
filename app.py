import streamlit as st
import pandas as pd
from datetime import date
from sqlmodel import select, desc
import time
import streamlit.components.v1 as components
# Removido: import base64

# --- CONFIGURAÇÕES DO PROJETO ---
VERSAO_SISTEMA = "1.0.5"
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

# --- CSS GLOBAL ---
st.markdown(f"""
<style>
    /* Estilos Gerais */
    .block-container {{padding-top: 1rem; padding-bottom: 2rem; max-width: 100%;}}
    
    /* Alinhamento da logo nas telas de login/páginas */
    div[data-testid="stImage"] {{display: flex; justify-content: flex-end; align-items: center; padding-right: 20px;}}
    
    /* Reset do alinhamento da logo na sidebar para centralizar */
    [data-testid="stSidebar"] div[data-testid="stImage"] {{justify-content: center; padding-right: 0px;}}

    .razonete-container {{border: 1px solid #ddd; border-radius: 5px; padding: 10px; background-color: #ffffff; margin-bottom: 20px; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); page-break-inside: avoid;}}
    .razonete-header {{text-align: center; font-weight: bold; border-bottom: 2px solid #333; padding-bottom: 5px; margin-bottom: 5px; color: #333; font-size: 1.1em;}}
    .razonete-body {{display: flex; min-height: 100px;}}
    .col-debito {{width: 50%; border-right: 2px solid #333; text-align: right; padding-right: 10px; color: #d63031;}}
    .col-credito {{width: 50%; text-align: left; padding-left: 10px; color: #0984e3;}}
    .razonete-footer {{border-top: 1px solid #aaa; margin-top: 5px; padding-top: 5px; display: flex; font-weight: bold; font-size: 0.9em;}}
    
    .footer-text {{font-size: 0.8em; color: gray; text-align: center; margin-top: 20px;}}

    /* Modo Impressão */
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

def criar_novo_usuario(username, senha, nome, perfil):
    session = get_session()
    if session.exec(select(Usuario).where(Usuario.username == username)).first(): return False, "Usuário já existe!"
    session.add(Usuario(username=username, senha=senha, nome=nome, perfil=perfil))
    session.commit()
    return True, f"Usuário {nome} criado!"

if not st.session_state["usuario_logado"]:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col_logo, col_form = st.columns([1, 1], gap="small", vertical_alignment="center")
    with col_logo: st.image("assets/logo.png", width=350)
    with col_form:
        st.markdown("### Acesso ao Sistema")
        # REMOVIDO AQUI: st.caption(f"v{VERSAO_SISTEMA}")
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
        data_op = st.date_input("Data do Fato", value=date.today(), max_value=date.today(), help="Data em que o fato contábil ocorreu.")
        valor = st.number_input("Valor (R$)", min_value=0.01, step=10.00, help="Valor financeiro da transação.")
    with col2:
        historico = st.text_input("Histórico", help="Descreva brevemente o que aconteceu.")
    st.divider()
    lista = carregar_contas_analiticas()
    c_deb, c_cred = st.columns(2)
    with c_deb: conta_deb = st.selectbox("Débito (Destino/Aplicação)", lista, index=None, help="Conta que recebe o recurso.")
    with c_cred: conta_cred = st.selectbox("Crédito (Origem/Fonte)", lista, index=None, help="Conta de onde sai o recurso.")
    if st.button("💾 Salvar Lançamento", type="primary"):
        if conta_deb and conta_cred and valor > 0 and conta_deb != conta_cred:
            novo_lancamento = Lancamento(data_lancamento=data_op, historico=historico, valor=valor, conta_debito=conta_deb.split(" - ")[0], conta_credito=conta_cred.split(" - ")[0], usuario_id=usuario_atual.id)
            salvar_lancamento(novo_lancamento)
            st.success("Lançamento salvo com sucesso!"); time.sleep(1); st.rerun()
        else: st.error("Erro nos dados: Verifique contas e valores.")

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
        with st.form("new_user"):
            n = st.text_input("Nome"); u = st.text_input("Login"); p = st.text_input("Senha", type="password")
            perf = st.selectbox("Perfil", opcoes)
            if st.form_submit_button("Cadastrar"):
                if n and u and p:
                    ok, msg = criar_novo_usuario(u, p, n, perf)
                    if ok: st.success(msg); time.sleep(1); st.rerun()
                    else: st.error(msg)
                else: st.warning("Preencha tudo.")
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