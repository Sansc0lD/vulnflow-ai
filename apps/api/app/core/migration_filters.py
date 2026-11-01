"""Autogenerate/compare filters for Alembic — keeps partitions out of diffs.

`audit_logs` is RANGE-partitioned (SDD §2.4.4) and its partitions
(`audit_logs_default`, `audit_logs_y2026m10`, ...) are created by raw DDL, so
they exist in the database but never in `Base.metadata`. PostgreSQL reflection
reports a partition as an ordinary table, so without this filter
`alembic revision --autogenerate` emits

    op.drop_index(...); op.drop_table('audit_logs_default')

into the next migration — verified behaviour, not a hypothetical. That would
destroy the immutable audit trail those partitions hold, and the generated
downgrade recreates them as a plain inherited table rather than a partition,
so the loss would not even be reversible.

Lives here rather than in `migrations/env.py` because `env.py` runs migrations
as an import side effect and therefore cannot be imported by tests that want
the same filter (see `tests/models/test_postgres_semantics.py`).
"""

from collections.abc import Callable
from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Connection

IncludeObject = Callable[[Any, str | None, str, bool, Any], bool]

_PARTITION_QUERY = (
    "SELECT c.relname FROM pg_class c "
    "JOIN pg_namespace n ON n.oid = c.relnamespace "
    "WHERE c.relispartition AND n.nspname = current_schema()"
)


def load_partition_names(connection: Connection) -> set[str]:
    """Partitions are detected via `pg_class.relispartition`, never by name
    matching, so monthly partitions provisioned later are covered too.
    """
    if connection.dialect.name != "postgresql":
        return set()
    return set(connection.execute(text(_PARTITION_QUERY)).scalars())


def make_include_object(partition_names: set[str]) -> IncludeObject:
    def include_object(
        object_: Any, name: str | None, type_: str, reflected: bool, compare_to: Any
    ) -> bool:
        if not reflected or type_ not in {"table", "index"}:
            return True
        if type_ == "table":
            return name not in partition_names
        table = getattr(object_, "table", None)
        return table is None or table.name not in partition_names

    return include_object
