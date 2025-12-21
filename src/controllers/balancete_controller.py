import pandas as pd
from sqlmodel import select
from src.models.lancamento_model import Lancamento
from src.models.account_model import ContaContabil

def gerar_balancete(session, usuario_id=None):
    contas = session.exec(select(ContaContabil).order_by(ContaContabil.codigo)).all()
    dados = []
    
    # Filtro de usuário
    query = select(Lancamento)
    if usuario_id:
        query = query.where(Lancamento.usuario_id == usuario_id)
    lancamentos = session.exec(query).all()

    total_geral_deb = 0
    total_geral_cred = 0

    for conta in contas:
        if conta.tipo == "Analítica":
            debitos = sum([l.valor for l in lancamentos if l.conta_debito == conta.codigo])
            creditos = sum([l.valor for l in lancamentos if l.conta_credito == conta.codigo])
        else:
            # Lógica simplificada para sintéticas (soma das filhas seria o ideal, mas aqui zeramos para visualização)
            debitos = 0
            creditos = 0
            
        saldo = debitos - creditos
        
        # Só adiciona se tiver movimento
        if debitos > 0 or creditos > 0:
            dados.append({
                "Código": conta.codigo,
                "Conta": conta.nome,
                "Total Débitos": debitos,
                "Total Créditos": creditos,
                "Saldo Atual": saldo
            })
            total_geral_deb += debitos
            total_geral_cred += creditos

    return pd.DataFrame(dados), total_geral_deb, total_geral_cred