"""Unit tests — PLAN.md FASE 2.1: koneksi basis data & session factory."""

import pytest
from app.core.database import get_database_url, get_db, make_engine, make_session_factory
from sqlalchemy import text


def test_make_engine_connects_and_executes_query() -> None:
    engine = make_engine("sqlite:///:memory:")

    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        assert result.scalar() == 1


def test_make_session_factory_yields_working_session() -> None:
    engine = make_engine("sqlite:///:memory:")
    session_factory = make_session_factory(engine)

    with session_factory() as session:
        result = session.execute(text("SELECT 1"))
        assert result.scalar() == 1


def test_get_database_url_reads_env_var(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://u:p@localhost/vulnflow")

    assert get_database_url() == "postgresql+psycopg://u:p@localhost/vulnflow"


def test_get_database_url_raises_when_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        get_database_url()


def test_get_db_yields_and_closes_session() -> None:
    engine = make_engine("sqlite:///:memory:")
    session_factory = make_session_factory(engine)

    generator = get_db(session_factory)
    session = next(generator)
    assert session.execute(text("SELECT 1")).scalar() == 1

    with pytest.raises(StopIteration):
        next(generator)
