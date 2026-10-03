"""Throwaway PostgreSQL database management for the test suite.

The tests run against PostgreSQL rather than SQLite because the two dialects
disagree in exactly the places this project has broken before: column type
changes, foreign key constraints, and DDL. A migration that passes on SQLite
can fail on PostgreSQL, and vice versa, so the tests use the real engine.

Nothing here touches the development database. A uniquely named scratch
database is created for the test session and dropped afterwards, so the suite
is safe to run while the application is up.
"""

import os
import uuid

from sqlalchemy import create_engine, text

# The server the scratch database is created on. It only needs to be reachable
# and to allow CREATE DATABASE; the database named in the URL is never used.
DEFAULT_TEST_SERVER = os.getenv(
    "TEST_DATABASE_URL",
    os.getenv(
        "DATABASE_URL",
        "postgresql://apexos_user:apexos_pass@localhost:5432/apexos",
    ),
)


def _split(url):
    """Split a database URL into (server_url_prefix, database_name)."""
    base, _, name = url.rpartition("/")
    return base, name


def create_test_database(server_url=None, prefix="apexos_test"):
    """Create a uniquely named scratch database and return its URL."""
    server_url = server_url or DEFAULT_TEST_SERVER
    base, _ = _split(server_url)

    name = f"{prefix}_{uuid.uuid4().hex[:12]}"
    admin = create_engine(server_url, isolation_level="AUTOCOMMIT")
    try:
        with admin.connect() as connection:
            connection.execute(text(f'CREATE DATABASE "{name}"'))
    finally:
        admin.dispose()

    return f"{base}/{name}"


def drop_test_database(database_url, server_url=None):
    """Drop a scratch database, forcibly terminating any leftover sessions."""
    server_url = server_url or DEFAULT_TEST_SERVER
    _, name = _split(database_url)
    if not name:
        return

    admin = create_engine(server_url, isolation_level="AUTOCOMMIT")
    try:
        with admin.connect() as connection:
            connection.execute(text(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)'))
    finally:
        admin.dispose()
