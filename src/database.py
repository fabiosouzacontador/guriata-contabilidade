from sqlmodel import SQLModel, Session, create_engine, select, delete
import streamlit as st
# Ajuste de importação para garantir que funcione em diferentes estruturas de pasta
try:
    from src.models.account_model import ContaContabil
    from src.models.lancamento_model import Lancamento 
    from src.models.usuario_model import Usuario 
except ImportError:
    from models.account_model import ContaContabil
    from models.lancamento_model import Lancamento 
    from models.usuario_model import Usuario
import os

# --- CONEXÃO INTELIGENTE (LOCAL OU NUVEM) ---
try:
    # Tenta pegar a conexão da Nuvem (Streamlit Cloud)
    database_url = st.secrets["DATABASE_URL"]
    
    # Ajuste para PostgreSQL se necessário (O Streamlit exige postgresql://)
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
        
    # print("☁️ Conectado na Nuvem!") # Debug silencioso

except (FileNotFoundError, KeyError):
    # Se não achar segredo (PC local), usa o arquivo SQLite
    # Garante que o pasta data exista
    if not os.path.exists("data"):
        os.makedirs("data")
        
    database_url = f"sqlite:///data/contabilidade.db"
    # print("💻 Conectado Localmente")

# thread_check_same_thread=False é necessário para SQLite com Streamlit
connect_args = {"check_same_thread": False} if "sqlite" in database_url else {}
engine = create_engine(database_url, connect_args=connect_args)

# --- FUNÇÕES DO BANCO ---
def get_session():
    return Session(engine)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def salvar_lancamento(lancamento: Lancamento):
    with Session(engine) as session:
        session.add(lancamento)
        session.commit()
        session.refresh(lancamento)
    return lancamento

def excluir_lancamento_individual(lancamento_id):
    """Apaga apenas um lançamento específico pelo ID"""
    with Session(engine) as session:
        statement = delete(Lancamento).where(Lancamento.id == lancamento_id)
        session.exec(statement)
        session.commit()

def limpar_todos_lancamentos():
    with Session(engine) as session:
        statement = delete(Lancamento)
        session.exec(statement)
        session.commit()

def limpar_lancamentos_por_usuario(user_id):
    with Session(engine) as session:
        statement = delete(Lancamento).where(Lancamento.usuario_id == user_id)
        session.exec(statement)
        session.commit()

def deletar_usuario_por_id(user_id):
    with Session(engine) as session:
        # Primeiro apaga os lançamentos desse usuário para não dar erro de chave estrangeira
        session.exec(delete(Lancamento).where(Lancamento.usuario_id == user_id))
        # Depois apaga o usuário
        session.exec(delete(Usuario).where(Usuario.id == user_id))
        session.commit()

def alterar_senha_usuario(user_id, nova_senha):
    with Session(engine) as session:
        usuario = session.get(Usuario, user_id)
        if usuario:
            usuario.senha = nova_senha
            session.add(usuario)
            session.commit()
            return True
    return False

def populate_initial_data():
    with Session(engine) as session:
        # 1. PLANO DE CONTAS EXPANDIDO
        if not session.exec(select(ContaContabil)).first():
            print("Inserindo Plano de Contas Completo...")
            contas_iniciais = [
                # --- ATIVO ---
                ContaContabil(codigo="1", nome="ATIVO", nivel=1, tipo="Sintética", natureza="Devedora", grupo="Ativo"),
                ContaContabil(codigo="1.1", nome="ATIVO CIRCULANTE", nivel=2, tipo="Sintética", natureza="Devedora", grupo="Ativo"),
                ContaContabil(codigo="1.1.1", nome="Caixa e Equivalentes de Caixa", nivel=3, tipo="Sintética", natureza="Devedora", grupo="Ativo"),
                ContaContabil(codigo="1.1.1.01", nome="Caixa Geral", nivel=4, tipo="Analítica", natureza="Devedora", grupo="Ativo"),
                ContaContabil(codigo="1.1.1.02", nome="Bancos Conta Movimento", nivel=4, tipo="Analítica", natureza="Devedora", grupo="Ativo"),
                ContaContabil(codigo="1.1.1.03", nome="Aplicações Financeiras de Liquidez Imediata", nivel=4, tipo="Analítica", natureza="Devedora", grupo="Ativo"),
                ContaContabil(codigo="1.1.2", nome="Créditos a Receber", nivel=3, tipo="Sintética", natureza="Devedora", grupo="Ativo"),
                ContaContabil(codigo="1.1.2.01", nome="Clientes (Duplicatas a Receber)", nivel=4, tipo="Analítica", natureza="Devedora", grupo="Ativo"),
                ContaContabil(codigo="1.1.2.02", nome="Adiantamentos a Fornecedores", nivel=4, tipo="Analítica", natureza="Devedora", grupo="Ativo"),
                ContaContabil(codigo="1.1.3", nome="Estoques", nivel=3, tipo="Sintética", natureza="Devedora", grupo="Ativo"),
                ContaContabil(codigo="1.1.3.01", nome="Mercadorias para Revenda", nivel=4, tipo="Analítica", natureza="Devedora", grupo="Ativo"),
                ContaContabil(codigo="1.1.3.02", nome="Material de Consumo (Almoxarifado)", nivel=4, tipo="Analítica", natureza="Devedora", grupo="Ativo"),
                ContaContabil(codigo="1.1.4", nome="Impostos a Recuperar", nivel=3, tipo="Sintética", natureza="Devedora", grupo="Ativo"),
                ContaContabil(codigo="1.1.4.01", nome="ICMS a Recuperar", nivel=4, tipo="Analítica", natureza="Devedora", grupo="Ativo"),
                
                ContaContabil(codigo="1.2", nome="ATIVO NÃO CIRCULANTE", nivel=2, tipo="Sintética", natureza="Devedora", grupo="Ativo"),
                ContaContabil(codigo="1.2.1", nome="Realizável a Longo Prazo", nivel=3, tipo="Sintética", natureza="Devedora", grupo="Ativo"),
                ContaContabil(codigo="1.2.2", nome="Investimentos", nivel=3, tipo="Sintética", natureza="Devedora", grupo="Ativo"),
                ContaContabil(codigo="1.2.3", nome="Imobilizado", nivel=3, tipo="Sintética", natureza="Devedora", grupo="Ativo"),
                ContaContabil(codigo="1.2.3.01", nome="Móveis e Utensílios", nivel=4, tipo="Analítica", natureza="Devedora", grupo="Ativo"),
                ContaContabil(codigo="1.2.3.02", nome="Veículos", nivel=4, tipo="Analítica", natureza="Devedora", grupo="Ativo"),
                ContaContabil(codigo="1.2.3.03", nome="Máquinas e Equipamentos", nivel=4, tipo="Analítica", natureza="Devedora", grupo="Ativo"),
                ContaContabil(codigo="1.2.3.04", nome="(-) Depreciação Acumulada", nivel=4, tipo="Analítica", natureza="Credora", grupo="Ativo"), # Conta Retificadora
                ContaContabil(codigo="1.2.4", nome="Intangível", nivel=3, tipo="Sintética", natureza="Devedora", grupo="Ativo"),
                ContaContabil(codigo="1.2.4.01", nome="Marcas e Patentes", nivel=4, tipo="Analítica", natureza="Devedora", grupo="Ativo"),
                
                # --- PASSIVO ---
                ContaContabil(codigo="2", nome="PASSIVO", nivel=1, tipo="Sintética", natureza="Credora", grupo="Passivo"),
                ContaContabil(codigo="2.1", nome="PASSIVO CIRCULANTE", nivel=2, tipo="Sintética", natureza="Credora", grupo="Passivo"),
                ContaContabil(codigo="2.1.1", nome="Obrigações Operacionais", nivel=3, tipo="Sintética", natureza="Credora", grupo="Passivo"),
                ContaContabil(codigo="2.1.1.01", nome="Fornecedores (Duplicatas a Pagar)", nivel=4, tipo="Analítica", natureza="Credora", grupo="Passivo"),
                ContaContabil(codigo="2.1.2", nome="Obrigações Trabalhistas e Previdenciárias", nivel=3, tipo="Sintética", natureza="Credora", grupo="Passivo"),
                ContaContabil(codigo="2.1.2.01", nome="Salários a Pagar", nivel=4, tipo="Analítica", natureza="Credora", grupo="Passivo"),
                ContaContabil(codigo="2.1.2.02", nome="INSS a Recolher", nivel=4, tipo="Analítica", natureza="Credora", grupo="Passivo"),
                ContaContabil(codigo="2.1.2.03", nome="FGTS a Recolher", nivel=4, tipo="Analítica", natureza="Credora", grupo="Passivo"),
                ContaContabil(codigo="2.1.3", nome="Obrigações Fiscais", nivel=3, tipo="Sintética", natureza="Credora", grupo="Passivo"),
                ContaContabil(codigo="2.1.3.01", nome="ICMS a Recolher", nivel=4, tipo="Analítica", natureza="Credora", grupo="Passivo"),
                ContaContabil(codigo="2.1.3.02", nome="Simples Nacional a Recolher", nivel=4, tipo="Analítica", natureza="Credora", grupo="Passivo"),
                ContaContabil(codigo="2.1.4", nome="Empréstimos e Financiamentos (Curto Prazo)", nivel=3, tipo="Analítica", natureza="Credora", grupo="Passivo"),
                
                ContaContabil(codigo="2.2", nome="PASSIVO NÃO CIRCULANTE", nivel=2, tipo="Sintética", natureza="Credora", grupo="Passivo"),
                ContaContabil(codigo="2.2.1", nome="Empréstimos e Financiamentos (Longo Prazo)", nivel=3, tipo="Analítica", natureza="Credora", grupo="Passivo"),
                
                ContaContabil(codigo="2.3", nome="PATRIMÔNIO LÍQUIDO", nivel=2, tipo="Sintética", natureza="Credora", grupo="Patrimônio Líquido"),
                ContaContabil(codigo="2.3.1", nome="Capital Social Realizado", nivel=3, tipo="Analítica", natureza="Credora", grupo="Patrimônio Líquido"),
                ContaContabil(codigo="2.3.2", nome="Reservas de Lucros", nivel=3, tipo="Sintética", natureza="Credora", grupo="Patrimônio Líquido"),
                ContaContabil(codigo="2.3.3", nome="Lucros ou Prejuízos Acumulados", nivel=3, tipo="Analítica", natureza="Credora", grupo="Patrimônio Líquido"), # Pode ser devedora se prejuízo

                # --- RESULTADO (DRE) ---
                ContaContabil(codigo="3", nome="RECEITAS", nivel=1, tipo="Sintética", natureza="Credora", grupo="Resultado"),
                ContaContabil(codigo="3.1", nome="RECEITA BRUTA OPERACIONAL", nivel=2, tipo="Sintética", natureza="Credora", grupo="Resultado"),
                ContaContabil(codigo="3.1.1", nome="Venda de Mercadorias", nivel=3, tipo="Analítica", natureza="Credora", grupo="Resultado"),
                ContaContabil(codigo="3.1.2", nome="Prestação de Serviços", nivel=3, tipo="Analítica", natureza="Credora", grupo="Resultado"),
                ContaContabil(codigo="3.2", nome="(-) DEDUÇÕES DA RECEITA BRUTA", nivel=2, tipo="Sintética", natureza="Devedora", grupo="Resultado"),
                ContaContabil(codigo="3.2.1", nome="(-) Devoluções de Vendas", nivel=3, tipo="Analítica", natureza="Devedora", grupo="Resultado"),
                ContaContabil(codigo="3.2.2", nome="(-) Impostos sobre Vendas (ICMS/ISS)", nivel=3, tipo="Analítica", natureza="Devedora", grupo="Resultado"),
                ContaContabil(codigo="3.3", nome="OUTRAS RECEITAS OPERACIONAIS", nivel=2, tipo="Sintética", natureza="Credora", grupo="Resultado"),
                ContaContabil(codigo="3.3.1", nome="Receitas Financeiras (Juros Obtidos)", nivel=3, tipo="Analítica", natureza="Credora", grupo="Resultado"),
                
                ContaContabil(codigo="4", nome="CUSTOS E DESPESAS", nivel=1, tipo="Sintética", natureza="Devedora", grupo="Resultado"),
                ContaContabil(codigo="4.1", nome="CUSTOS OPERACIONAIS", nivel=2, tipo="Sintética", natureza="Devedora", grupo="Resultado"),
                ContaContabil(codigo="4.1.1", nome="CMV (Custo da Mercadoria Vendida)", nivel=3, tipo="Analítica", natureza="Devedora", grupo="Resultado"),
                ContaContabil(codigo="4.1.2", nome="CSP (Custo do Serviço Prestado)", nivel=3, tipo="Analítica", natureza="Devedora", grupo="Resultado"),
                
                ContaContabil(codigo="4.2", nome="DESPESAS OPERACIONAIS", nivel=2, tipo="Sintética", natureza="Devedora", grupo="Resultado"),
                ContaContabil(codigo="4.2.1", nome="Despesas com Pessoal", nivel=3, tipo="Sintética", natureza="Devedora", grupo="Resultado"),
                ContaContabil(codigo="4.2.1.01", nome="Salários e Ordenados", nivel=4, tipo="Analítica", natureza="Devedora", grupo="Resultado"),
                ContaContabil(codigo="4.2.1.02", nome="Pró-labore", nivel=4, tipo="Analítica", natureza="Devedora", grupo="Resultado"),
                ContaContabil(codigo="4.2.1.03", nome="FGTS", nivel=4, tipo="Analítica", natureza="Devedora", grupo="Resultado"),
                
                ContaContabil(codigo="4.2.2", nome="Despesas Administrativas e Gerais", nivel=3, tipo="Sintética", natureza="Devedora", grupo="Resultado"),
                ContaContabil(codigo="4.2.2.01", nome="Aluguéis e Condomínios", nivel=4, tipo="Analítica", natureza="Devedora", grupo="Resultado"),
                ContaContabil(codigo="4.2.2.02", nome="Energia Elétrica", nivel=4, tipo="Analítica", natureza="Devedora", grupo="Resultado"),
                ContaContabil(codigo="4.2.2.03", nome="Água e Esgoto", nivel=4, tipo="Analítica", natureza="Devedora", grupo="Resultado"),
                ContaContabil(codigo="4.2.2.04", nome="Telefone e Internet", nivel=4, tipo="Analítica", natureza="Devedora", grupo="Resultado"),
                ContaContabil(codigo="4.2.2.05", nome="Material de Escritório/Consumo", nivel=4, tipo="Analítica", natureza="Devedora", grupo="Resultado"),
                ContaContabil(codigo="4.2.2.06", nome="Despesa com Depreciação", nivel=4, tipo="Analítica", natureza="Devedora", grupo="Resultado"),
                
                ContaContabil(codigo="4.2.3", nome="Despesas Comerciais (Vendas)", nivel=3, tipo="Sintética", natureza="Devedora", grupo="Resultado"),
                ContaContabil(codigo="4.2.3.01", nome="Publicidade e Propaganda", nivel=4, tipo="Analítica", natureza="Devedora", grupo="Resultado"),
                
                ContaContabil(codigo="4.2.4", nome="Despesas Financeiras", nivel=3, tipo="Sintética", natureza="Devedora", grupo="Resultado"),
                ContaContabil(codigo="4.2.4.01", nome="Juros Passivos e Multas", nivel=4, tipo="Analítica", natureza="Devedora", grupo="Resultado"),
                ContaContabil(codigo="4.2.4.02", nome="Tarifas Bancárias", nivel=4, tipo="Analítica", natureza="Devedora", grupo="Resultado"),
            ]
            session.add_all(contas_iniciais)
            session.commit()

        # 2. USUÁRIOS PADRÃO
        if not session.exec(select(Usuario).where(Usuario.username == "admin")).first():
            print("Criando usuários padrão...")
            admin = Usuario(username="admin", senha="123", nome="Administrador", perfil="admin")
            prof = Usuario(username="professor", senha="123", nome="Professor Padrão", perfil="professor")
            aluno = Usuario(username="aluno", senha="123", nome="Aluno Exemplo", perfil="aluno")
            session.add(admin)
            session.add(prof)
            session.add(aluno)
            session.commit()