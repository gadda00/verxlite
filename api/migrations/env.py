from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
from verxlite_api.db.base import Base  # noqa: E402
from verxlite_api.models.tenant import Tenant  # noqa: E402,F401
from verxlite_api.models.user import User  # noqa: E402,F401
from verxlite_api.models.connection import Connection  # noqa: E402,F401
from verxlite_api.models.workflow import Workflow  # noqa: E402,F401
from verxlite_api.models.workflow_run import WorkflowRun  # noqa: E402,F401
from verxlite_api.models.workflow_step import WorkflowStep  # noqa: E402,F401
from verxlite_api.models.artifact import Artifact  # noqa: E402,F401

target_metadata = Base.metadata

# Override the URL from alembic.ini with the runtime settings value.
from verxlite_api.config import settings  # noqa: E402
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)


def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_options={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
