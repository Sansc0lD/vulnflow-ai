"""Shared declarative base & cross-dialect column types — PLAN.md FASE 2.3.

SDD §2.4.2 specifies PostgreSQL-native types (UUID, JSONB, TIMESTAMPTZ, BYTEA).
`JSONVariant` compiles to JSONB on PostgreSQL and to plain JSON elsewhere
(e.g. SQLite in unit tests, which have no Docker dependency) so the same
model definitions produce correct production DDL while staying testable
without a live Postgres instance.
"""

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.types import JSON


class Base(DeclarativeBase):
    pass


JSONVariant = JSON().with_variant(JSONB(), "postgresql")
