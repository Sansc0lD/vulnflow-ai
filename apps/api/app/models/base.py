"""Shared declarative base & cross-dialect column types — PLAN.md FASE 2.3.

SDD §2.4.2 specifies PostgreSQL-native types (UUID, JSONB, TIMESTAMPTZ, BYTEA).
`JSONVariant` compiles to JSONB on PostgreSQL and to plain JSON elsewhere
(e.g. SQLite in unit tests, which have no Docker dependency) so the same
model definitions produce correct production DDL while staying testable
without a live Postgres instance.

CAVEAT — cross-dialect equivalence is NOT total. `DateTime(timezone=True)`
compiles to TIMESTAMPTZ on PostgreSQL (aware datetimes in, aware datetimes
out) but SQLite has no timezone-aware storage: SQLAlchemy's SQLite DATETIME
silently drops `tzinfo` on write, so the same column hands back a *naive*
datetime under the test dialect. Logic that compares persisted timestamps
(EC-05 ROE expiry is the obvious one) therefore cannot be trusted on the
strength of SQLite tests alone — `tests/models/test_postgres_semantics.py`
covers those paths against real PostgreSQL and is required before any
datetime-comparison or JSONB-operator code is considered done.

`NAMING_CONVENTION` makes every implicitly-created constraint name
deterministic and known to the models. Without it, foreign keys are named by
the server (`audit_logs_workspace_id_fkey`) and Alembic cannot render a
`drop_constraint()` for them — it emits `op.drop_constraint(None, ...)` plus
a warning, producing a migration that fails when run. `ck` and `pk` are
deliberately omitted: every CheckConstraint here is already explicitly named
`ck_<table>_<column>`, and the `ck` token would re-prefix those into
`ck_users_ck_user_status`, while PostgreSQL's own `<table>_pkey` is already
deterministic and nothing references primary keys by name.
"""

from sqlalchemy import MetaData
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.types import JSON

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


JSONVariant = JSON().with_variant(JSONB(), "postgresql")
