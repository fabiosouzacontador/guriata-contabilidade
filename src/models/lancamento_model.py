from sqlmodel import SQLModel, Field
from datetime import date
from typing import Optional

class Lancamento(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    data_lancamento: date
    historico: str
    valor: float
    conta_debito: str
    conta_credito: str
    usuario_id: int = Field(foreign_key="usuario.id")
    # Campo professor_responsavel REMOVIDO daqui