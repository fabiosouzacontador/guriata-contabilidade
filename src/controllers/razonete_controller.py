from sqlmodel import select
from src.models.lancamento_model import Lancamento
from src.models.account_model import ContaContabil

def obter_dados_razonetes(session, usuario_id=None):
    # 1. Busca todas as contas
    contas = session.exec(select(ContaContabil).where(ContaContabil.tipo == "Analítica")).all()
    dados_razonetes = []

    # 2. Define o filtro base
    query_base = select(Lancamento)
    if usuario_id:
        query_base = query_base.where(Lancamento.usuario_id == usuario_id)
    
    # 3. Busca lançamentos filtrados
    todos_lancamentos = session.exec(query_base).all()

    for conta in contas:
        # Filtra na memória (mais rápido para poucos dados)
        mov_deb = [l.valor for l in todos_lancamentos if l.conta_debito == str(conta.codigo)]
        mov_cred = [l.valor for l in todos_lancamentos if l.conta_credito == str(conta.codigo)]

        if not mov_deb and not mov_cred:
            continue

        total_d = sum(mov_deb)
        total_c = sum(mov_cred)
        saldo = total_d - total_c
        tipo = "D" if saldo >= 0 else "C"

        dados_razonetes.append({
            "nome": conta.nome,
            "mov_debitos": mov_deb,
            "mov_creditos": mov_cred,
            "total_d": total_d,
            "total_c": total_c,
            "saldo_final": abs(saldo),
            "tipo_saldo": tipo
        })
    
    return dados_razonetes