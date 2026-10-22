"""Shared fixtures — in-memory SQLite stand-in for PostgreSQL in model tests.

Column types (app/models/base.py) are cross-dialect, so the same model
definitions that produce PostgreSQL DDL (UUID, JSONB, TIMESTAMPTZ, BYTEA)
also run against SQLite here — no Docker/live Postgres required for FASE 2
model-structure unit tests.
"""

from collections.abc import Generator

import pytest
from app.models.base import Base
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session


@pytest.fixture
def session() -> Generator[Session, None, None]:
    engine = create_engine("sqlite:///:memory:")

    # SQLite ignores ON DELETE CASCADE unless FK enforcement is explicitly
    # enabled per-connection; PostgreSQL enforces it unconditionally.
    @event.listens_for(engine, "connect")
    def _enable_sqlite_fk(dbapi_connection: object, _: object) -> None:
        cursor = dbapi_connection.cursor()  # type: ignore[attr-defined]
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()
