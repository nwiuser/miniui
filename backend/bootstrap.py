"""Prepare the database before the API starts.

Runs Alembic migrations. Databases created by an older version of this project
used SQLAlchemy's ``create_all`` and contain the application tables but no
``alembic_version`` row; those are stamped at the current head first, so the
upgrade below is a no-op instead of failing with "table already exists".

Used by the container entrypoint and safe to run repeatedly.
"""

import os

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

HERE = os.path.dirname(os.path.abspath(__file__))
ALEMBIC_INI = os.path.join(HERE, "alembic.ini")
DEFAULT_DATABASE_URL = "postgresql://apexos_user:apexos_pass@localhost:5432/apexos"


def database_url() -> str:
    return os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)


def _alembic_config() -> Config:
    config = Config(ALEMBIC_INI)
    config.set_main_option("script_location", os.path.join(HERE, "alembic"))
    return config


def needs_stamp(engine) -> bool:
    """True for a schema that exists but was never tracked by Alembic."""
    inspector = inspect(engine)
    if not inspector.has_table("apex_applications"):
        return False
    if not inspector.has_table("alembic_version"):
        return True
    with engine.connect() as connection:
        tracked = connection.execute(text("SELECT count(*) FROM alembic_version")).scalar()
    return not tracked


def seed_admin() -> None:
    """Create the first administrator when BOOTSTRAP_ADMIN_* is provided."""
    username = os.getenv("BOOTSTRAP_ADMIN_USERNAME")
    password = os.getenv("BOOTSTRAP_ADMIN_PASSWORD")
    if not username or not password:
        return

    from app.core.security.password import get_password_hash
    from app.db import models
    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        existing = (
            db.query(models.WorkspaceUser)
            .filter(models.WorkspaceUser.username == username)
            .first()
        )
        if existing is not None:
            print(f"User '{username}' already exists; skipping admin seed.")
            return

        db.add(
            models.WorkspaceUser(
                username=username,
                password_hash=get_password_hash(password),
                email=os.getenv("BOOTSTRAP_ADMIN_EMAIL"),
                administrator_role="ADMIN",
                account_locked=False,
                failed_access_attempts=0,
            )
        )
        db.commit()
        print(f"Created administrator '{username}'.")
    finally:
        db.close()


def main() -> None:
    engine = create_engine(database_url())
    try:
        stamp = needs_stamp(engine)
    finally:
        engine.dispose()

    config = _alembic_config()
    if stamp:
        print("Found an untracked schema; stamping it at the latest revision.")
        command.stamp(config, "head")
    command.upgrade(config, "head")
    seed_admin()
    print("Database is at the latest revision.")


if __name__ == "__main__":
    main()
