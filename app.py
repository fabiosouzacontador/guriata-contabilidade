import streamlit as st
import pandas as pd
import numpy as np
from datetime import date
from sqlmodel import select, desc, text
import time
import requests
import streamlit.components.v1 as components
from streamlit_option_menu import option_menu

# --- CONFIGURAÇÕES ---
VERSAO_SISTEMA = "2.9.64" # Ajuste Final: Seletor de Alunos + Correção ROI + Logo
ANO_COPYRIGHT = "2025"
NOME_INSTITUICAO = "Guriatã Tecnologia Educacional"
CMC_API_KEY = "aa6076bc93d749528552e68c14b0f10e"

try:
    import yfinance as yf
except ImportError:
    st.warning("Instale: pip install yfinance requests numpy")

# --- Importações Internas ---
# Tenta importar da estrutura de pastas correta
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
    # Fallback para execução local simplificada se necessário
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

# --- ATUALIZAÇÃO DO BANCO (MIGRATIONS) ---
def verificar_atualizacao_banco():
    session = get_session()
    try:
        session.exec(text("SELECT termos_aceitos FROM usuario LIMIT 1"))
    except Exception:
        session.rollback()
        try:
            session.exec(text("ALTER TABLE usuario ADD COLUMN termos_aceitos BOOLEAN DEFAULT FALSE"))
            session.commit()
        except: pass
    
    try:
        session.exec(text("SELECT criado_por_id FROM usuario LIMIT 1"))
    except Exception:
        session.rollback()
        try:
            session.exec(text("ALTER TABLE usuario ADD COLUMN criado_por_id INTEGER"))
            session.commit()
        except: pass

# --- Configuração Inicial ---
st.set_page_config(page_title="Guriatã - Gestão Contábil", layout="wide", page_icon="assets/logo.png")
create_db_and_tables()
verificar_atualizacao_banco()
populate_initial_data()

# --- CSS GLOBAL ---
st.markdown(f"""
<style>
    /* CORREÇÃO DE MARGEM SUPERIOR PARA A LOGO NÃO CORTAR */
    .block-container {{padding-top: 5rem; padding-bottom: 3rem; max-width: 100%;}}
    
    div[data-testid="stVerticalBlock"] > div {{gap: 0.5rem;}}
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    
    .stTextInput > div > div, .stNumberInput > div > div, .stDateInput > div > div {{
        background-color: #ffffff !important; border: 1px solid #ced4da !important; color: #495057 !important; border-radius: 4px;
    }}
    
    /* RODAPÉ EM UMA LINHA */
    .footer-text {{
        font-size: 10px; 
        color: #666; 
        text-align: center; 
        margin-top: 20px;
        white-space: nowrap; 
        overflow: hidden;
        text-overflow: ellipsis;
    }}

    .market-box {{ text-align: left; padding: 5px 0; line-height: 1.2; }}
    .market-label {{ font-size: 0.8em; color: #666; font-weight: 600; margin-bottom: 2px; display: flex; align-items: center; gap: 5px; }}
    .market-data-row {{ display: flex; align-items: baseline; gap: 6px; white-space: nowrap; }}
    .market-value-small {{ font-size: 1.0em; font-weight: 800; color: #333; }}
    .market-delta-pos {{ color: #27ae60; font-size: 0.8em; font-weight: 700; }}
    .market-delta-neg {{ color: #c0392b; font-size: 0.8em; font-weight: 700; }}

    .kpi-card {{ background-color: white; border-left: 5px solid #004b8d; padding: 15px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); text-align: center; height: 100%; }}
    .kpi-title {{ font-size: 1.1em; color: #555; font-weight: bold; text-transform: uppercase; margin-bottom: 8px; letter-spacing: 0.5px; }}
    .kpi-value {{ font-size: 1.4em; font-weight: 800; }}
    .val-receita {{ color: #27ae60 !important; }} .val-custo {{ color: #e67e22 !important; }}
    .val-despesa {{ color: #c0392b !important; }} .val-resultado-pos {{ color: #2980b9 !important; }} .val-resultado-neg {{ color: #c0392b !important; }}

    .razonete-container {{border: 1px solid #ddd; border-radius: 5px; padding: 10px; background-color: #ffffff; margin-bottom: 20px; box-shadow: 2px 2px 5px rgba(0,0,0,0.1);}}
    .razonete-header {{text-align: center; font-weight: bold; border-bottom: 2px solid #333; padding-bottom: 5px; margin-bottom: 5px; color: #333; font-size: 1.1em;}}
    .razonete-body {{display: flex; min-height: 100px; justify-content: space-between;}}
    .col-debito {{width: 48%; border-right: 2px solid #333; text-align: right; padding-right: 10px; color: #d63031; font-family: monospace; font-size: 1em;}}
    .col-credito {{width: 48%; text-align: left; padding-left: 10px; color: #0984e3; font-family: monospace; font-size: 1em;}}
    .razonete-footer {{border-top: 1px solid #aaa; margin-top: 5px; padding-top: 5px; display: flex; font-weight: bold; font-size: 0.9em; justify-content: space-between;}}

    .indicator-card {{ background-color: #f8f9fa; border: 1px solid #e9ecef; border-radius: 8px; padding: 25px; text-align: center; height: 100%; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }}
    .indicator-title {{ font-size: 1.1em; color: #444; font-weight: bold; margin-bottom: 15px; text-transform: uppercase; border-bottom: 1px solid #ddd; padding-bottom: 10px; }}
    .indicator-value {{ font-size: 2.5em; font-weight: 900; margin-bottom: 10px; }}
    .indicator-desc {{ font-size: 0.9em; color: #666; font-style: italic; }}
    .text-green {{color: #27ae60 !important;}} .text-purple {{color: #8e44ad !important;}}

    @media print {{ [data-testid="stSidebar"], header, footer {{display: none !important;}} .block-container {{background-color: white !important; padding: 0 !important;}} }}
</style>
""", unsafe_allow_html=True)

# --- FUNÇÕES ---
def fmt_num_br(valor):
    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def fmt_moeda_br(valor):
    return f"R$ {fmt_num_br(valor)}"

def botao_imprimir():
    components.html("""<script>function printPage(){window.parent.print();}</script><div style="display: flex; justify-content: center; margin-top: 20px;"><button onclick="printPage()" style="background-color: #004b8d; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer;">🖨️ Imprimir Página</button></div>""", height=50)

def rodape_institucional():
    st.markdown(f"""<div class='footer-text'>{NOME_INSTITUICAO} • v{VERSAO_SISTEMA} • © {ANO_COPYRIGHT}</div>""", unsafe_allow_html=True)

def verificar_credenciais():
    session = get_session()
    u = st.session_state.get("login_user"); s = st.session_state.get("login_pass")
    user = session.exec(select(Usuario).where(Usuario.username == u).where(Usuario.senha == s)).first()
    if user: st.session_state["usuario_logado"] = user; st.rerun()
    else: st.error("Dados inválidos.")

def realizar_logout(): st.session_state["usuario_logado"] = None; st.rerun()

def callback_criar_usuario():
    u = st.session_state.get("k_new_user"); p = st.session_state.get("k_new_pass"); n = st.session_state.get("k_new_name"); perf = st.session_state.get("k_new_perf", "aluno")
    criador_id = st.session_state["usuario_logado"].id 
    if n and u and p:
        session = get_session()
        if session.exec(select(Usuario).where(Usuario.username == u)).first(): st.toast("⚠️ Usuário já existe!"); return
        
        # Cria usuario
        novo_user = Usuario(username=u, senha=p, nome=n, perfil=perf)
        # Tenta salvar o vínculo
        try: setattr(novo_user, 'criado_por_id', criador_id)
        except: pass
        
        session.add(novo_user); session.commit()
        
        # Garante o vínculo no banco
        if hasattr(novo_user, 'id'):
             try:
                 session.exec(text(f"UPDATE usuario SET criado_por_id = {criador_id} WHERE id = {novo_user.id}"))
                 session.commit()
             except: pass
             
        st.toast(f"✅ Criado!")
    else: st.toast("⚠️ Preencha tudo.")

def callback_salvar_lancamento():
    dt = st.session_state.get("k_data"); val = st.session_state.get("k_valor", 0.0); hist = st.session_state.get("k_hist"); deb = st.session_state.get("k_debito"); cred = st.session_state.get("k_credito")
    
    # SEGURANÇA: Lança sempre no ID de quem está logado
    usuario_id_lancamento = st.session_state["usuario_logado"].id
    
    if deb and cred and val > 0 and deb != cred:
        salvar_lancamento(Lancamento(data_lancamento=dt, historico=hist, valor=val, conta_debito=deb.split(" - ")[0], conta_credito=cred.split(" - ")[0], usuario_id=usuario_id_lancamento))
        st.toast("✅ Salvo!"); st.session_state["k_valor"] = 0.0; st.session_state["k_hist"] = ""
    else: st.toast("❌ Erro nos dados.")

def carregar_contas_analiticas():
    results = get_session().exec(select(ContaContabil).where(ContaContabil.tipo == "Analítica")).all()
    results.sort(key=lambda x: x.codigo)
    return [f"{c.codigo} - {c.nome}" for c in results]

def widget_filtro_data():
    with st.expander("📅 Filtrar Período", expanded=False):
        c1, c2 = st.columns(2); return c1.date_input("Início", value=date(date.today().year, 1, 1)), c2.date_input("Fim", value=date.today())

@st.cache_data(ttl=600)
def obter_dados_mercado_pro():
    resultados = {}
    try: 
        url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest'
        resp = requests.get(url, headers={'Accepts':'application/json','X-CMC_PRO_API_KEY':CMC_API_KEY}, params={'id':'1,1027','convert':'BRL'}, timeout=5)
        if resp.status_code == 200:
            d = resp.json()['data']
            resultados['Bitcoin'] = (d['1']['quote']['BRL']['price'], d['1']['quote']['BRL']['percent_change_24h'])
            resultados['Ethereum'] = (d['1027']['quote']['BRL']['price'], d['1027']['quote']['BRL']['percent_change_24h'])
    except: pass 
    dolar_val, dolar_delta = 0.0, 0.0
    try:
        r_usd = requests.get("https://last-d.awesomeapi.com.br/last/USD-BRL", timeout=3)
        if r_usd.status_code == 200: d = r_usd.json()['USDBRL']; dolar_val, dolar_delta = float(d['bid']), float(d['pctChange'])
    except: pass
    if dolar_val == 0.0:
        try:
            h = yf.Ticker("USDBRL=X").history(period="5d"); c = h['Close'].dropna()
            if len(c)>=2: dolar_val, dolar_delta = float(c.iloc[-1]), ((float(c.iloc[-1])/float(c.iloc[-2]))-1)*100
        except: pass
    resultados['Dólar'] = (dolar_val, dolar_delta)
    for n, t in {'Ibovespa':'^BVSP', 'S&P 500':'^GSPC', 'Nasdaq':'^IXIC'}.items():
        try:
            h = yf.Ticker(t).history(period="1mo"); c = h['Close'].dropna()
            if len(c)>=2: resultados[n] = (float(c.iloc[-1]), ((float(c.iloc[-1])/float(c.iloc[-2]))-1)*100)
            else: resultados[n] = (0.0,0.0)
        except: resultados[n] = (0.0,0.0)
    return resultados

def exibir_mini_ticker(titulo, icono, valor, delta, eh_moeda=False):
    cor = "market-delta-pos" if delta > 0 else "market-delta-neg" if delta < 0 else "text-muted"
    sinal = "+" if delta > 0 else ""
    if eh_moeda or titulo == 'Dólar': val_fmt = fmt_moeda_br(valor)
    else: val_fmt = f"{fmt_num_br(valor)} pts"
    st.markdown(f"""<div class="market-box"><div class="market-label">{icono} {titulo}</div><div class="market-data-row"><span class="market-value-small">{val_fmt}</span><span class="{cor}" style="margin-left:4px;">{sinal}{delta:.2f}%</span></div></div>""", unsafe_allow_html=True)

def classificar_lancamento(row):
    cd = str(row['conta_debito']); cc = str(row['conta_credito'])
    if cc.startswith('3'): return 'Receita'
    if cd.startswith('4'): return 'Custos' if cd.startswith('4.1') else 'Despesas'
    return 'Outros'

# --- LOGIN (MANUTENÇÃO DE SEGURANÇA E LAYOUT) ---
if "usuario_logado" not in st.session_state: st.session_state["usuario_logado"] = None
if not st.session_state["usuario_logado"]:
    c1, c2, c3 = st.columns([1, 0.8, 1])
    with c2:
        st.write(""); st.columns([1, 2, 1])[1].image("assets/logo.png", width=220)
        with st.form("l"):
            st.text_input("Usuário", key="login_user"); st.text_input("Senha", type="password", key="login_pass")
            if st.form_submit_button("Entrar", type="primary", use_container_width=True): verificar_credenciais()
        st.markdown(f"<div style='text-align:center;color:gray;font-size:0.8em;margin-top:10px'>© {ANO_COPYRIGHT} {NOME_INSTITUICAO}</div>", unsafe_allow_html=True)
    st.stop()

# --- VERIFICAÇÃO DE TERMOS (SEM LOGO) ---
usuario_atual = st.session_state["usuario_logado"]
termos_aceitos = getattr(usuario_atual, "termos_aceitos", False) 

if not termos_aceitos:
    session = get_session()
    try:
        res = session.exec(text(f"SELECT termos_aceitos FROM usuario WHERE id = {usuario_atual.id}")).first()
        if res: termos_aceitos = res[0]
    except: pass

if not termos_aceitos:
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    c_left, c_center, c_right = st.columns([1, 2, 1])
    with c_center:
        st.markdown("<h2 style='text-align: center; color: #333;'>Termo de Responsabilidade</h2>", unsafe_allow_html=True)
        st.info("""
        **Bem-vindo ao Guriatã!**
        
        Ao utilizar este sistema educacional, você concorda que:
        
        1.  **Fins Educacionais:** O software é destinado exclusivamente ao ensino e prática contábil.
        2.  **Dados Fictícios:** Recomenda-se o uso de dados simulados para aprendizado.
        3.  **Responsabilidade:** A integridade dos lançamentos é de responsabilidade do usuário.
        4.  **Segurança:** Evite inserir dados pessoais sensíveis reais (CPF, RG, Senhas Bancárias).
        """)
        if st.button("✅ Li e Aceito os Termos", type="primary", use_container_width=True):
            session = get_session()
            session.exec(text(f"UPDATE usuario SET termos_aceitos = TRUE WHERE id = {usuario_atual.id}"))
            session.commit()
            try: usuario_atual.termos_aceitos = True
            except: pass
            st.success("Acesso liberado!")
            time.sleep(1)
            st.rerun()
    st.stop()

# --- SISTEMA PRINCIPAL ---
session = get_session(); perfil = usuario_atual.perfil

# DEFINIÇÃO DE HIERARQUIA
usuarios_disponiveis = []
if perfil == 'admin':
    usuarios_disponiveis = session.exec(select(Usuario)).all()
elif perfil == 'professor':
    try:
        query_alunos = text("SELECT id FROM usuario WHERE id = :uid OR criado_por_id = :uid")
        res_alunos = session.exec(query_alunos, params={"uid": usuario_atual.id}).all()
        ids_found = [r[0] for r in res_alunos]
        usuarios_disponiveis = session.exec(select(Usuario).where(Usuario.id.in_(ids_found))).all()
    except:
        usuarios_disponiveis = [usuario_atual]
else:
    usuarios_disponiveis = [usuario_atual]

# SELETOR DE ALUNO (SOLUÇÃO PARA O CRASH)
filtro_id = usuario_atual.id

with st.sidebar:
    st.columns([1, 8, 1])[1].image("assets/logo.png", width=200); st.write("")
    
    if perfil in ['admin', 'professor']:
        st.markdown("---")
        st.markdown("###### 🎓 Selecionar Aluno")
        opcoes = {f"{u.nome} ({u.username})": u.id for u in usuarios_disponiveis}
        
        default_idx = 0
        keys = list(opcoes.keys())
        for i, (k, v) in enumerate(opcoes.items()):
            if v == usuario_atual.id: default_idx = i; break
            
        escolha = st.selectbox("Visualizar dados de:", keys, index=default_idx)
        filtro_id = opcoes[escolha]
        
        if filtro_id != usuario_atual.id:
            st.info(f"Visualizando: {escolha.split('(')[0]}")
        st.markdown("---")

    opts = ["Visão Geral", "Plano de Contas", "Novo Lançamento", "Diário (Extrato)", "Razonetes (T)", "Balancete", "DRE (Resultado)", "Balanço Patrimonial"]
    icons = ["house", "list-columns", "pencil-square", "journal-text", "grid-3x3", "calculator", "bar-chart-line", "building"]
    if perfil in ['admin', 'professor']: opts.extend(["Gestão de Usuários", "Configurações"]); icons.extend(["people", "gear"])
    selected = option_menu(None, opts, icons=icons, default_index=0, styles={"container": {"padding": "0!important", "background-color": "#f8f9fa"}, "icon": {"color": "#004b8d"}, "nav-link-selected": {"background-color": "#004b8d"}})
    st.divider(); st.markdown(f"<div style='text-align:center;'>Olá, <b>{usuario_atual.nome.split()[0]}</b></div>", unsafe_allow_html=True)
    if st.button("Sair", use_container_width=True): realizar_logout()
    rodape_institucional()

def get_query_lancamentos():
    return select(Lancamento).where(Lancamento.usuario_id == filtro_id)

# --- LÓGICA DAS PÁGINAS ---
if selected == "Visão Geral":
    st.header("📊 Visão Geral"); 
    if filtro_id != usuario_atual.id: st.caption(f"Visualizando dados do aluno: {escolha.split('(')[0]}")
    
    st.markdown("###### 🌐 Tendências de Mercado")
    md = obter_dados_mercado_pro(); md = md if md else {}
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1: val, d = md.get('Ibovespa', (0,0)); exibir_mini_ticker('Ibovespa', '🇧🇷', val, d)
    with c2: val, d = md.get('S&P 500', (0,0)); exibir_mini_ticker('S&P 500', '🇺🇸', val, d)
    with c3: val, d = md.get('Nasdaq', (0,0)); exibir_mini_ticker('Nasdaq', '💻', val, d)
    with c4: val, d = md.get('Dólar', (0,0)); exibir_mini_ticker('Dólar', '💵', val, d)
    with c5: val, d = md.get('Bitcoin', (0,0)); exibir_mini_ticker('Bitcoin', '₿', val, d, True)
    with c6: val, d = md.get('Ethereum', (0,0)); exibir_mini_ticker('Ethereum', 'Ξ', val, d, True)
    st.divider()
    
    q = get_query_lancamentos()
    all_lancs = session.exec(q).all()
    
    if not all_lancs: st.info("👋 Nenhum lançamento encontrado para este usuário.")
    else:
        df = pd.DataFrame([l.model_dump() for l in all_lancs]); df['Categoria'] = df.apply(classificar_lancamento, axis=1)
        tr = df[df['Categoria']=='Receita']['valor'].sum(); tc = df[df['Categoria']=='Custos']['valor'].sum()
        td = df[df['Categoria']=='Despesas']['valor'].sum(); rl = tr - (tc + td)
        
        # CÁLCULO DE ROI E LIQUIDEZ CORRIGIDO
        at = 0.0; pt = 0.0
        for _, row in df.iterrows():
            cd = str(row['conta_debito']).strip(); cc = str(row['conta_credito']).strip()
            val = float(row['valor'])
            if cd.startswith('1'): at += val
            elif cd.startswith('2'): pt -= val
            if cc.startswith('1'): at -= val
            elif cc.startswith('2'): pt += val
            
        pt = max(pt, 0)
        roi = (rl/at*100) if at > 0 else 0.0
        liq = (at/pt) if pt > 0 else (0.0 if pt == 0 else 999.0)
        
        st.markdown("<br>", unsafe_allow_html=True); c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f"""<div class="kpi-card"><div class="kpi-title">Receitas Totais</div><div class="kpi-value val-receita">{fmt_moeda_br(tr)}</div></div>""", unsafe_allow_html=True)
        c2.markdown(f"""<div class="kpi-card"><div class="kpi-title">Custos Totais</div><div class="kpi-value val-custo">{fmt_moeda_br(tc)}</div></div>""", unsafe_allow_html=True)
        c3.markdown(f"""<div class="kpi-card"><div class="kpi-title">Despesas Totais</div><div class="kpi-value val-despesa">{fmt_moeda_br(td)}</div></div>""", unsafe_allow_html=True)
        c4.markdown(f"""<div class="kpi-card"><div class="kpi-title">Resultado Líquido</div><div class="kpi-value {'val-resultado-pos' if rl>=0 else 'val-resultado-neg'}">{fmt_moeda_br(rl)}</div></div>""", unsafe_allow_html=True)
        st.divider(); st.subheader("📈 Saúde Financeira"); st.markdown("<br>", unsafe_allow_html=True); col1, col2 = st.columns(2)
        with col1: st.markdown(f"""<div class="indicator-card"><div class="indicator-title">ROI</div><div class="indicator-value text-purple">{roi:.1f}%</div><div class="indicator-desc">Retorno sobre Ativos</div></div>""", unsafe_allow_html=True)
        with col2: st.markdown(f"""<div class="indicator-card"><div class="indicator-title">Liquidez Geral</div><div class="indicator-value text-green">{f'{liq:.2f}'.replace('.',',') if liq<999 else '∞'}</div><div class="indicator-desc">Solvência</div></div>""", unsafe_allow_html=True)

# --- MANTENDO AS OUTRAS PÁGINAS ---
elif selected == "Plano de Contas":
    st.header("📂 Plano de Contas"); df = pd.DataFrame([c.model_dump() for c in session.exec(select(ContaContabil).order_by(ContaContabil.codigo)).all()])
    st.dataframe(df.style.apply(lambda r: [f'padding-left:{(r["nivel"]-1)*20}px;font-weight:{"bold" if r["tipo"]=="Sintética" else "normal"}' if c=='nome' else '' for c in r.index], axis=1), hide_index=True, use_container_width=True, height=600)

elif selected == "Novo Lançamento":
    st.header("📝 Escrituração"); 
    if filtro_id != usuario_atual.id:
        st.info(f"ℹ️ Nota: Você está visualizando o aluno {escolha.split('(')[0]}, mas novos lançamentos serão salvos na SUA conta de professor.")
        
    c1, c2 = st.columns(2); c1.date_input("Data", key="k_data"); c1.number_input("Valor", min_value=0.0, step=10.0, key="k_valor")
    c2.text_input("Histórico", key="k_hist"); st.divider(); l = carregar_contas_analiticas(); d, c = st.columns(2); d.selectbox("Débito", l, index=None, key="k_debito"); c.selectbox("Crédito", l, index=None, key="k_credito")
    st.markdown("<br>", unsafe_allow_html=True); st.button("💾 Salvar", type="primary", on_click=callback_salvar_lancamento, use_container_width=True)

elif selected == "Diário (Extrato)":
    st.header("📖 Livro Diário"); ini, fim = widget_filtro_data()
    q = get_query_lancamentos().where(Lancamento.data_lancamento >= ini).where(Lancamento.data_lancamento <= fim).order_by(desc(Lancamento.data_lancamento), desc(Lancamento.id))
    res = session.exec(q).all(); contas_db = session.exec(select(ContaContabil)).all(); mapa_contas = {c.codigo: c.nome for c in contas_db}
    
    if res:
        data_exib = []
        for l in res:
            dono = session.get(Usuario, l.usuario_id)
            nome_dono = dono.nome if dono else "Desconhecido"
            data_exib.append({
                "Data": l.data_lancamento.strftime("%d/%m/%Y"),
                "ID": l.id,
                "Conta Devedora": f"{l.conta_debito} - {mapa_contas.get(l.conta_debito,'')}",
                "Conta Credora": f"{l.conta_credito} - {mapa_contas.get(l.conta_credito,'')}",
                "Valor": fmt_moeda_br(l.valor), 
                "Histórico": l.historico
            })
        st.dataframe(pd.DataFrame(data_exib), hide_index=True, use_container_width=True)
        botao_imprimir()
        
        with st.expander("🗑️ Excluir Lançamento"): 
            sel = st.selectbox("Selecionar Lançamento:", res, format_func=lambda x: f"ID {x.id} | {fmt_moeda_br(x.valor)} | {x.historico}"); 
            if st.button("Apagar"): 
                excluir_lancamento_individual(sel.id); st.success("Apagado!"); st.rerun()
    else: st.warning("Vazio.")

elif selected == "Razonetes (T)":
    st.header("🗂️ Razonetes"); 
    q = get_query_lancamentos()
    lancs = session.exec(q).all()
    
    contas = {}
    for l in lancs:
        cd = l.conta_debito; cc = l.conta_credito
        if cd not in contas: contas[cd] = {'d':[], 'c':[]}
        contas[cd]['d'].append(l.valor)
        if cc not in contas: contas[cc] = {'d':[], 'c':[]}
        contas[cc]['c'].append(l.valor)
    
    if contas:
        st.markdown("---"); cols = st.columns(3)
        i = 0
        for cod, vals in contas.items():
            nome_conta = session.exec(select(ContaContabil).where(ContaContabil.codigo == cod)).first()
            nome_display = f"{cod} - {nome_conta.nome}" if nome_conta else cod
            td = sum(vals['d']); tc = sum(vals['c'])
            with cols[i%3]:
                d_html = "".join([f"<div>{fmt_num_br(v)}</div>" for v in vals['d']])
                c_html = "".join([f"<div>{fmt_num_br(v)}</div>" for v in vals['c']])
                st.markdown(f"""<div class="razonete-container"><div class="razonete-header">{nome_display}</div><div class="razonete-body"><div class="col-debito">{d_html}</div><div class="col-credito">{c_html}</div></div><div class="razonete-footer"><div style="width:50%;text-align:right;color:#d63031;">{fmt_num_br(td)}</div><div style="width:50%;padding-left:10px;color:#0984e3;">{fmt_num_br(tc)}</div></div></div>""", unsafe_allow_html=True)
            i+=1
        botao_imprimir()
    else: st.info("Sem dados para o usuário selecionado.")

elif selected == "Balancete":
    st.header("⚖️ Balancete"); 
    df, td, tc = gerar_balancete(session, filtro_id) 
    
    if not df.empty:
        df['Total Débitos'] = df['Total Débitos'].apply(fmt_num_br)
        df['Total Créditos'] = df['Total Créditos'].apply(fmt_num_br)
        df['Saldo Atual'] = df['Saldo Atual'].apply(fmt_num_br)
        st.dataframe(df, hide_index=True, use_container_width=True)
        c1, c2, c3 = st.columns(3)
        c1.metric("Débito", fmt_moeda_br(td))
        c2.metric("Crédito", fmt_moeda_br(tc))
        diff = round(td - tc, 2)
        if diff == 0: c3.success("✅ Fechado")
        else: c3.error(f"⚠️ Diferença: {fmt_num_br(diff)}")
        botao_imprimir()
    else: st.info("Vazio.")

elif selected == "DRE (Resultado)":
    st.header("📉 DRE com Análise Vertical")
    dados, luc = gerar_relatorio_dre(session, filtro_id)
    st.metric("Resultado", fmt_moeda_br(luc), delta_color="normal" if luc>=0 else "inverse")
    
    if dados:
        df_dre = pd.DataFrame(dados)
        renomear = {}
        for c in df_dre.columns:
            if c.lower() in ['valor', 'saldo', 'saldo atual', 'total']: renomear[c] = 'Saldo'
            if c.lower() in ['descrição', 'historico', 'conta', 'item']: renomear[c] = 'Conta'
        df_dre.rename(columns=renomear, inplace=True)
        
        if 'Destaque' in df_dre.columns: df_dre = df_dre.drop(columns=['Destaque'])
        
        receita_bruta = 0.0
        if 'Conta' in df_dre.columns and 'Saldo' in df_dre.columns:
            try:
                filtro_rb = df_dre[df_dre['Conta'].str.contains("Receita Operacional Bruta|Receita Bruta|Receita de Vendas", case=False, na=False)]
                if not filtro_rb.empty: receita_bruta = filtro_rb['Saldo'].max()
            except: pass
            
            if receita_bruta > 0: df_dre['AV (%)'] = (df_dre['Saldo'] / receita_bruta * 100).apply(lambda x: f"{x:.2f}%".replace('.', ','))
            else: df_dre['AV (%)'] = "0,00%"
            
            df_dre['Saldo'] = df_dre['Saldo'].apply(fmt_num_br)
            st.dataframe(df_dre, hide_index=True, use_container_width=True)
    
    botao_imprimir()

elif selected == "Balanço Patrimonial":
    st.header("🏛️ Balanço Patrimonial")
    
    q = get_query_lancamentos()
    lancs = session.exec(q).all()
    contas_db = session.exec(select(ContaContabil)).all(); mapa = {c.codigo: c.nome for c in contas_db}
    
    if not lancs: st.info("Sem dados.")
    else:
        d = pd.DataFrame([l.model_dump() for l in lancs]); d['T'] = d.apply(classificar_lancamento, axis=1)
        lucro = d[d['T']=='Receita']['valor'].sum() - (d[d['T']=='Custos']['valor'].sum() + d[d['T']=='Despesas']['valor'].sum())
        
        ac, anc, pc, pnc, pl = {}, {}, {}, {}, {}
        for l in lancs:
            val = l.valor; dc = l.conta_debito.split(" - ")[0].strip(); cc = l.conta_credito.split(" - ")[0].strip()
            dn3 = ".".join(dc.split(".")[:3]); cn3 = ".".join(cc.split(".")[:3])
            
            if dn3.startswith('1.1'): ac[dn3] = ac.get(dn3, 0) + val
            elif dn3.startswith('1.2'): anc[dn3] = anc.get(dn3, 0) + val
            if cn3.startswith('1.1'): ac[cn3] = ac.get(cn3, 0) - val
            elif cn3.startswith('1.2'): anc[cn3] = anc.get(cn3, 0) - val
            
            if cn3.startswith('2.1'): pc[cn3] = pc.get(cn3, 0) + val
            elif cn3.startswith('2.2'): pnc[cn3] = pnc.get(cn3, 0) + val
            elif cn3.startswith('2.3'): pl[cn3] = pl.get(cn3, 0) + val
            if dn3.startswith('2.1'): pc[dn3] = pc.get(dn3, 0) - val
            elif dn3.startswith('2.2'): pnc[dn3] = pnc.get(dn3, 0) - val
            elif dn3.startswith('2.3'): pl[dn3] = pl.get(dn3, 0) - val
            
        pl['2.3.9'] = pl.get('2.3.9', 0) + lucro 

        def montar_df_av(saldos, total_grupo):
            lista = []
            for k, v in saldos.items():
                if v != 0:
                    nm = mapa.get(k, "Resultado do Exercício" if k == '2.3.9' else "Conta")
                    av = (v / total_grupo * 100) if total_grupo > 0 else 0.0
                    lista.append({"Código": k, "Conta": nm, "Saldo": fmt_num_br(v), "AV (%)": f"{av:.2f}%".replace('.', ',')})
            if not lista: return pd.DataFrame(columns=["Código", "Conta", "Saldo", "AV (%)"])
            return pd.DataFrame(lista).sort_values("Código")

        tac = sum(ac.values()); tanc = sum(anc.values()); tativo = tac + tanc
        tpc = sum(pc.values()); tpnc = sum(pnc.values()); tpl = sum(pl.values()); tpassivo = tpc + tpnc + tpl
        
        def exibir_cabecalho_grupo(titulo, valor):
            val_fmt = fmt_moeda_br(valor)
            st.markdown(f"""<div style="background-color: #d1ecf1; color: #0c5460; padding: 10px; border-radius: 5px; font-weight: bold; display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;"><span>{titulo}</span><span>{val_fmt}</span></div>""", unsafe_allow_html=True)

        col_ativo, col_passivo = st.columns(2)
        
        with col_ativo:
            st.subheader(f"ATIVO")
            exibir_cabecalho_grupo("CIRCULANTE", tac)
            st.dataframe(montar_df_av(ac, tativo), hide_index=True, use_container_width=True)
            exibir_cabecalho_grupo("NÃO CIRCULANTE", tanc)
            st.dataframe(montar_df_av(anc, tativo), hide_index=True, use_container_width=True)
            st.markdown("---")
            exibir_cabecalho_grupo("TOTAL ATIVO", tativo)

        with col_passivo:
            st.subheader(f"PASSIVO")
            exibir_cabecalho_grupo("CIRCULANTE", tpc)
            st.dataframe(montar_df_av(pc, tpassivo), hide_index=True, use_container_width=True)
            exibir_cabecalho_grupo("NÃO CIRCULANTE", tpnc)
            st.dataframe(montar_df_av(pnc, tpassivo), hide_index=True, use_container_width=True)
            exibir_cabecalho_grupo("PATRIMÔNIO LÍQUIDO", tpl)
            st.dataframe(montar_df_av(pl, tpassivo), hide_index=True, use_container_width=True)
            st.markdown("---")
            exibir_cabecalho_grupo("TOTAL PASSIVO + PL", tpassivo)
    
    botao_imprimir()

elif selected == "Gestão de Usuários":
    st.header("👥 Gestão de Usuários")
    with st.expander("Novo Usuário", expanded=True):
        c1, c2 = st.columns(2); c1.text_input("Nome", key="k_new_name"); c1.text_input("Login", key="k_new_user")
        c2.text_input("Senha", type="password", key="k_new_pass"); c2.selectbox("Perfil", ["aluno", "professor", "admin"], key="k_new_perf")
        st.button("Cadastrar", on_click=callback_criar_usuario)
    
    st.divider()
    data_users = [{"ID":u.id, "Nome":u.nome, "Login":u.username, "Perfil":u.perfil} for u in usuarios_disponiveis]
    st.dataframe(pd.DataFrame(data_users), hide_index=True, use_container_width=True)
    
    st.divider(); st.subheader("Excluir Usuário")
    users_del = [u for u in usuarios_disponiveis if u.id != usuario_atual.id]
    if users_del:
        ud = st.selectbox("Selecione o Usuário para Excluir:", users_del, format_func=lambda x: f"{x.nome} ({x.perfil})")
        if st.button("Excluir Usuário"): deletar_usuario_por_id(ud.id); st.success("OK!"); st.rerun()
    else:
        st.info("Nenhum usuário disponível para exclusão.")

elif selected == "Configurações":
    st.header("⚙️ Configurações")
    if perfil == 'admin':
        confirmacao = st.checkbox("🔴 Tenho certeza que desejo apagar TODOS os dados.")
        if st.button("🗑️ ZERAR TUDO", type="primary", disabled=not confirmacao): 
            limpar_todos_lancamentos()
            st.success("Feito! Todos os lançamentos foram apagados.")
            time.sleep(1)
            st.rerun()