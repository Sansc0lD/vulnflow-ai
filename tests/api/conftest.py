"""Shared fixtures for FastAPI router tests — PLAN.md FASE 4.

`db_session` overrides `get_db` so router tests hit a real (SQLite) DB
through the actual HTTP stack rather than mocking the ORM. StaticPool +
check_same_thread=False share one connection across the TestClient's worker
thread and the test's main thread (standard FastAPI testing pattern);
production uses Postgres, which has no such restriction.
"""

from collections.abc import Generator

import pytest
from app.core.dependencies import get_db
from app.main import app
from app.models.base import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool


@pytest.fixture
def db_session(monkeypatch: pytest.MonkeyPatch) -> Generator[Session, None, None]:
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key-at-least-32-bytes-long!")
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        app.dependency_overrides[get_db] = lambda: session
        yield session
    app.dependency_overrides.pop(get_db, None)
    engine.dispose()
