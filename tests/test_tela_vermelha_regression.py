"""
Regression test for the "tela vermelha" (red screen) bug fixed in commit 0cc3efaf.

Bug: When the Lancamento model was imported multiple times (e.g. via different
import paths in try/except blocks in app.py and database.py), SQLAlchemy raised
    InvalidRequestError: Table 'lancamento' is already defined for this MetaData instance.
This caused Streamlit to display a red error screen ("tela vermelha").

Fix: Adding __table_args__ = {"extend_existing": True} to the Lancamento model
allows SQLAlchemy to silently accept a re-declaration of the same table, preventing
the error.
"""

import pytest
from sqlalchemy.exc import InvalidRequestError
from sqlmodel import SQLModel, Field, Session, create_engine
from typing import Optional
from datetime import date


def test_lancamento_model_has_extend_existing():
    """Verify the Lancamento model has __table_args__ with extend_existing=True."""
    from src.models.lancamento_model import Lancamento

    assert hasattr(Lancamento, "__table_args__"), (
        "Lancamento model must have __table_args__ to prevent 'tela vermelha' bug"
    )
    assert Lancamento.__table_args__.get("extend_existing") is True, (
        "Lancamento.__table_args__ must include 'extend_existing': True"
    )


def test_lancamento_table_redefinition_without_extend_existing_fails():
    """
    Prove the bug: defining the same table twice on a fresh MetaData WITHOUT
    extend_existing raises InvalidRequestError (the root cause of 'tela vermelha').
    """
    # Use a fresh, isolated MetaData to avoid polluting the global one
    from sqlalchemy import MetaData, Table, Column, Integer, String, Float, Date

    metadata = MetaData()

    # First definition — succeeds
    Table(
        "lancamento_test_dup",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("data_lancamento", Date),
        Column("historico", String),
        Column("valor", Float),
        Column("conta_debito", String),
        Column("conta_credito", String),
        Column("usuario_id", Integer),
    )

    # Second definition of the same table name — must raise the error
    with pytest.raises(InvalidRequestError, match="already defined"):
        Table(
            "lancamento_test_dup",
            metadata,
            Column("id", Integer, primary_key=True),
            Column("data_lancamento", Date),
            Column("historico", String),
            Column("valor", Float),
            Column("conta_debito", String),
            Column("conta_credito", String),
            Column("usuario_id", Integer),
        )


def test_lancamento_table_redefinition_with_extend_existing_succeeds():
    """
    Prove the fix: defining the same table twice WITH extend_existing=True
    does NOT raise an error — the exact behaviour the fix provides.
    """
    from sqlalchemy import MetaData, Table, Column, Integer, String, Float, Date

    metadata = MetaData()

    # First definition
    Table(
        "lancamento_test_fix",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("data_lancamento", Date),
        Column("historico", String),
        Column("valor", Float),
        Column("conta_debito", String),
        Column("conta_credito", String),
        Column("usuario_id", Integer),
    )

    # Second definition with extend_existing — must NOT raise
    t2 = Table(
        "lancamento_test_fix",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("data_lancamento", Date),
        Column("historico", String),
        Column("valor", Float),
        Column("conta_debito", String),
        Column("conta_credito", String),
        Column("usuario_id", Integer),
        extend_existing=True,
    )
    assert t2 is not None


def test_lancamento_model_reimport_no_error():
    """
    Simulate the real-world scenario: importing the Lancamento model class
    multiple times and creating/using its table should not raise any errors.
    This directly mirrors the dual-import pattern in app.py and database.py.
    """
    # Import all models so foreign key references (usuario) can be resolved
    from src.models.usuario_model import Usuario  # noqa: F401
    from src.models.lancamento_model import Lancamento

    # Create an in-memory SQLite engine and tables
    engine = create_engine("sqlite://", echo=False)
    SQLModel.metadata.create_all(engine)

    # Force a re-import by removing the module from sys.modules cache
    import sys

    module_name = "src.models.lancamento_model"
    if module_name in sys.modules:
        del sys.modules[module_name]

    # Re-import — this is what triggers the bug without the fix
    from src.models.lancamento_model import Lancamento as LancamentoReloaded

    # Create tables again — should succeed thanks to extend_existing
    SQLModel.metadata.create_all(engine)

    # Verify we can actually insert and query data
    with Session(engine) as session:
        lancamento = LancamentoReloaded(
            data_lancamento=date(2025, 12, 21),
            historico="Teste regressão tela vermelha",
            valor=100.50,
            conta_debito="1.1.1.01",
            conta_credito="2.1.1.01",
            usuario_id=None,
        )
        session.add(lancamento)
        session.commit()
        session.refresh(lancamento)

        assert lancamento.id is not None
        assert lancamento.historico == "Teste regressão tela vermelha"
        assert lancamento.valor == 100.50


def test_all_models_have_extend_existing():
    """
    Guard against the same bug recurring in other models.
    All table=True SQLModel models must have extend_existing=True.
    """
    from src.models.lancamento_model import Lancamento
    from src.models.usuario_model import Usuario
    from src.models.account_model import ContaContabil

    for model in [Lancamento, Usuario, ContaContabil]:
        assert hasattr(model, "__table_args__"), (
            f"{model.__name__} must have __table_args__ to prevent 'tela vermelha' bug"
        )
        assert model.__table_args__.get("extend_existing") is True, (
            f"{model.__name__}.__table_args__ must include 'extend_existing': True"
        )
