from sqlmodel import SQLModel, Field
from typing import Optional

class Usuario(SQLModel, table=True):
    __table_args__ = {"extend_existing": True} # <--- ESSA LINHA CORRIGE O ERRO DA IMAGEM 3
    
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    senha: str
    nome: str
    perfil: str