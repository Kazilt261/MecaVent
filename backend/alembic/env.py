import asyncio
import importlib
import os
import pkgutil
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from src.models.db_declarations import AppMetadata, MasterMetadata

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

db_url = os.getenv("URL_DB") or config.get_main_option("sqlalchemy.url")
if db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)
if db_url.startswith("driver://"):
    raise RuntimeError(
        "Invalid SQLAlchemy URL. Set URL_DB in environment (e.g. "
        "postgresql+psycopg://user:pass@host:5432/dbname)."
    )
# Alembic uses configparser interpolation, so '%' must be escaped.
config.set_main_option("sqlalchemy.url", db_url.replace("%", "%%"))

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
def _load_models(package_name: str) -> None:
    """Import all modules in the given package so SQLModel tables are registered."""
    package = importlib.import_module(package_name)
    package_path = getattr(package, "__path__", None)
    if not package_path:
        return

    for module_info in pkgutil.walk_packages(package_path, prefix=f"{package_name}."):
        importlib.import_module(module_info.name)


x_args = context.get_x_argument(as_dictionary=True)
metadata_scope = (x_args.get("metadata") or "client").strip().lower()

if metadata_scope == "master":
    _load_models("src.models.master")
    target_metadata = MasterMetadata.metadata
    version_table = "alembic_version_master"
elif metadata_scope == "client":
    _load_models("src.models.clients")
    target_metadata = AppMetadata.metadata
    version_table = "alembic_version_client"
else:
    raise RuntimeError("Invalid metadata scope. Use -x metadata=master or -x metadata=client")

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        version_table=version_table,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        version_table=version_table,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """In this scenario we need to create an Engine
    and associate a connection with the context.

    """

    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""

    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()