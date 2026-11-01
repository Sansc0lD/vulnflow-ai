from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context
from app.core.database import get_database_url
from app.core.migration_filters import load_partition_names, make_include_object
from app.models import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option("sqlalchemy.url", get_database_url())

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # Offline mode has no connection to introspect, so no partition is
        # reflected and the filter is a pass-through; it is wired up anyway so
        # both modes stay configured identically.
        include_object=make_include_object(set()),
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    # Introspected on a SEPARATE connection on purpose. Querying the migration
    # connection before `context.configure()` leaves an implicit transaction
    # open, and Alembic's `begin_transaction()` then becomes a no-op because a
    # transaction is already active — so nothing is committed and every
    # migration silently rolls back while still reporting success.
    with connectable.connect() as probe:
        partition_names = load_partition_names(probe)

    with connectable.connect() as connection:
        # Without this filter, autogenerate renders
        # `op.drop_table('audit_logs_default')` into the next migration — see
        # app/core/migration_filters.py.
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=make_include_object(partition_names),
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
