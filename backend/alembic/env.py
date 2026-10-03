"""Alembic environment configuration"""
from __future__ import with_statement
from logging.config import fileConfig
import os
import sys
from sqlalchemy import engine_from_config, pool
from alembic import context

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Import your models here for 'autogenerate' support
from app.db import models  # noqa

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# The ini file carries a localhost default, which is wrong inside a container.
# DATABASE_URL (the same variable the application uses) replaces that default,
# but an explicitly configured URL -- e.g. a per-test database set on the Config
# object -- is always preserved.
DEFAULT_URL = "postgresql://apexos_user:apexos_pass@localhost:5432/apexos"
database_url = os.getenv("DATABASE_URL")
if database_url and config.get_main_option("sqlalchemy.url") in (None, "", DEFAULT_URL):
    config.set_main_option("sqlalchemy.url", database_url)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = models.Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This scenario configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation, we don't even
    need a DBAPI to be available.  Database needs to be a dialect
    and DBAPI available.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()