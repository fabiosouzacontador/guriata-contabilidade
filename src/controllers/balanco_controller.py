from sqlmodel import select
from src.models.lancamento_model import Lancamento
from src.controllers.dre_controller import gerar_relatorio_dre

def gerar_dados_balanco(session, usuario_id=None):
    # Filtro
    query = select(Lancamento)
    if usuario_id:
        query = query.where(Lancamento.usuario_id == usuario_id)
    lancamentos = session.exec(query).all()
    
    def saldo_conta(codigo_inicio):
        # Ativo (Devedora): Deb - Cred
        # Passivo (Credora): Cred - Deb
        deb = sum([l.valor for l in lancamentos if l.conta_debito.startswith(codigo_inicio)])
        cre = sum([l.valor for l in lancamentos if l.conta_credito.startswith(codigo_inicio)])
        return deb, cre

    # ATIVO
    d1, c1 = saldo_conta("1") # Pega todo grupo 1
    # Cálculo detalhado para subgrupos
    d_circ, c_circ = saldo_conta("1.1")
    ativo_circ = d_circ - c_circ
    
    d_nao_circ, c_nao_circ = saldo_conta("1.2")
    ativo_nao_circ = d_nao_circ - c_nao_circ
    
    total_ativo = ativo_circ + ativo_nao_circ

    # PASSIVO
    d_pass_circ, c_pass_circ = saldo_conta("2.1")
    passivo_circ = c_pass_circ - d_pass_circ
    
    d_pass_nc, c_pass_nc = saldo_conta("2.2")
    passivo_nao_circ = c_pass_nc - d_pass_nc
    
    d_pl, c_pl = saldo_conta("2.3")
    patrimonio_liquido = c_pl - d_pl
    
    # Importante: O Lucro do Exercício vem da DRE para fechar o balanço
    _, lucro_exercicio = gerar_relatorio_dre(session, usuario_id) # Passa o ID aqui também
    
    # Adiciona o lucro ao PL
    patrimonio_liquido += lucro_exercicio
    
    total_passivo = passivo_circ + passivo_nao_circ + patrimonio_liquido

    lista_ativo = [
        {"Grupo": "Ativo Circulante", "Valor": ativo_circ, "Destaque": False},
        {"Grupo": "Ativo Não Circulante", "Valor": ativo_nao_circ, "Destaque": False},
        {"Grupo": "TOTAL ATIVO", "Valor": total_ativo, "Destaque": True},
    ]
    
    lista_passivo = [
        {"Grupo": "Passivo Circulante", "Valor": passivo_circ, "Destaque": False},
        {"Grupo": "Passivo Não Circulante", "Valor": passivo_nao_circ, "Destaque": False},
        {"Grupo": "Patrimônio Líquido (Capital + Reservas)", "Valor": patrimonio_liquido - lucro_exercicio, "Destaque": False},
        {"Grupo": "Lucro/Prejuízo Acumulado (da DRE)", "Valor": lucro_exercicio, "Destaque": False},
        {"Grupo": "TOTAL PASSIVO + PL", "Valor": total_passivo, "Destaque": True},
    ]

    return lista_ativo, lista_passivo, total_ativo, total_passivo