from typing import Optional
from sqlmodel import Field, SQLModel

class ContaContabil(SQLModel, table=True):
    # Esta linha corrige o erro "Table is already defined"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    codigo: str = Field(index=True, unique=True)  # Ex: "1.1.1"
    nome: str                                     # Ex: "Caixa"
    nivel: int                                    # Ex: 3
    tipo: str                                     # "Analítica" ou "Sintética"
    natureza: str                                 # "Devedora" ou "Credora"
    grupo: str                                    # "Ativo", "Passivo", "Resultado"

    def __str__(self):
        return f"{self.codigo} - {self.nome}"