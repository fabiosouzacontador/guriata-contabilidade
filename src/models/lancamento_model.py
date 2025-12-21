from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import date

class Lancamento(SQLModel, table=True):
    # Esta linha abaixo corrige o erro da tela vermelha
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    data_lancamento: date
    historico: str
    valor: float
    conta_debito: str
    conta_credito: str
    usuario_id: Optional[int] = Field(default=None, foreign_key="usuario.id")