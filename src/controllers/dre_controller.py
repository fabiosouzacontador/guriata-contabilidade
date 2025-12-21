from sqlmodel import select
from src.models.lancamento_model import Lancamento

def gerar_relatorio_dre(session, usuario_id=None):
    # Filtro
    query = select(Lancamento)
    if usuario_id:
        query = query.where(Lancamento.usuario_id == usuario_id)
    lancamentos = session.exec(query).all()

    def calc_saldo(codigo_conta):
        # Créditos (Vendas) aumentam o lucro, Débitos (Despesas) diminuem
        cre = sum([l.valor for l in lancamentos if l.conta_credito.startswith(codigo_conta)])
        deb = sum([l.valor for l in lancamentos if l.conta_debito.startswith(codigo_conta)])
        return cre - deb

    receita_bruta = calc_saldo("3.1")
    deducoes = 0.0 
    receita_liquida = receita_bruta - deducoes
    cmv = sum([l.valor for l in lancamentos if l.conta_debito.startswith("4.1")]) # CMV é despesa, pega débito
    lucro_bruto = receita_liquida - cmv
    
    desp_admin = sum([l.valor for l in lancamentos if l.conta_debito.startswith("4.2")])
    desp_pessoal = sum([l.valor for l in lancamentos if l.conta_debito.startswith("4.3")])
    desp_trib = sum([l.valor for l in lancamentos if l.conta_debito.startswith("4.4")])
    
    res_financeiro = calc_saldo("3.2") # Receitas financeiras
    
    lucro_liquido = lucro_bruto - desp_admin - desp_pessoal - desp_trib + res_financeiro

    estrutura_dre = [
        {"Descrição": "1. RECEITA OPERACIONAL BRUTA", "Valor": receita_bruta, "Destaque": True},
        {"Descrição": "(-) Deduções", "Valor": deducoes, "Destaque": False},
        {"Descrição": "2. RECEITA LÍQUIDA", "Valor": receita_liquida, "Destaque": True},
        {"Descrição": "(-) Custo da Mercadoria Vendida (CMV)", "Valor": -cmv, "Destaque": False},
        {"Descrição": "3. LUCRO BRUTO", "Valor": lucro_bruto, "Destaque": True},
        {"Descrição": "(-) Despesas Administrativas", "Valor": -desp_admin, "Destaque": False},
        {"Descrição": "(-) Despesas com Pessoal", "Valor": -desp_pessoal, "Destaque": False},
        {"Descrição": "(-) Despesas Tributárias", "Valor": -desp_trib, "Destaque": False},
        {"Descrição": "(+/-) Resultado Financeiro", "Valor": res_financeiro, "Destaque": False},
        {"Descrição": "4. LUCRO/PREJUÍZO LÍQUIDO", "Valor": lucro_liquido, "Destaque": True},
    ]
    return estrutura_dre, lucro_liquido