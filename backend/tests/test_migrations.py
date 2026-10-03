import importlib.util
import os

import pytest
from alembic.autogenerate import compare_metadata
from alembic.command import downgrade, upgrade
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.operations import Operations
from alembic.script import ScriptDirectory
from sqlalchemy import inspect, text

from app.db import models
from tests.database import create_test_database, drop_test_database

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALEMBIC_INI = os.path.join(BACKEND_DIR, "alembic.ini")
SESSIONS_MIGRATION = os.path.join(
    BACKEND_DIR, "alembic", "versions",
    "9c8d7f012c3a_add_sessions_table_and_fix_session_state.py",
)

BASE_REVISION = "base"
PRE_STRING_SESSION_ID_REVISION = "8b5b30923eb2"


def _config(db_url):
    cfg = Config(ALEMBIC_INI)
    cfg.set_main_option("sqlalchemy.url", db_url)
    return cfg


@pytest.fixture
def db_url():
    url = create_test_database(prefix="apexos_migration_test")
    try:
        yield url
    finally:
        drop_test_database(url)


def _load_sessions_migration():
    """Load the session migration by path, since its module name is not a valid
    Python identifier."""
    spec = importlib.util.spec_from_file_location(
        "sessions_migration_under_test", SESSIONS_MIGRATION
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def engine(db_url):
    from sqlalchemy import create_engine

    eng = create_engine(db_url)
    try:
        yield eng
    finally:
        eng.dispose()


class TestMigrationChain:
    def test_single_head(self):
        heads = ScriptDirectory.from_config(_config(":memory:")).get_heads()
        assert heads == ["b3c4d5e6f7a8"]

    def test_migrations_are_linear(self):
        script = ScriptDirectory.from_config(_config(":memory:"))
        heads = script.get_heads()
        assert len(heads) == 1

        walked = []
        revision = heads[0]
        while revision is not None:
            walked.append(revision)
            revision = script.get_revision(revision).down_revision

        assert walked == [
            "b3c4d5e6f7a8",
            "a2b3c4d5e6f7",
            "f1a2b3c4d5e6",
            "e2f3a4b5c6d7",
            "d1e2f3a4b5c6",
            "9c8d7f012c3a",
            "8b5b30923eb2",
        ]
        assert script.get_revision("8b5b30923eb2").down_revision is None


class TestUpgrade:
    def test_creates_all_tables(self, db_url, engine):
        upgrade(_config(db_url), "head")

        tables = set(inspect(engine).get_table_names())
        expected = {table.name for table in models.Base.metadata.sorted_tables}
        assert expected <= tables

    def test_tables_and_columns_match_models(self, db_url, engine):
        """Every model table must exist with exactly the model's columns."""
        upgrade(_config(db_url), "head")

        inspector = inspect(engine)
        mismatches = []

        for table in models.Base.metadata.sorted_tables:
            if not inspector.has_table(table.name):
                mismatches.append(f"missing table {table.name}")
                continue

            actual = {c["name"] for c in inspector.get_columns(table.name)}
            expected = {c.name for c in table.columns}
            if actual != expected:
                mismatches.append(
                    f"{table.name}: missing={sorted(expected - actual)} extra={sorted(actual - expected)}"
                )

        assert mismatches == []

    def test_no_structural_drift(self, db_url, engine):
        """Alembic must not want to add/remove/alter any table or column.

        Index-only differences are tolerated: the migrations create indexes on
        foreign key columns that the models do not declare, which is a harmless
        superset for query performance.
        """
        upgrade(_config(db_url), "head")

        with engine.connect() as connection:
            context = MigrationContext.configure(connection)
            diff = compare_metadata(context, models.Base.metadata)

        structural = [entry for entry in diff if entry[0] not in ("add_index", "remove_index")]
        assert structural == [], f"migration history does not match models: {structural}"

    def test_computations_table(self, db_url, engine):
        """apex_computations is used by the /computations endpoints."""
        upgrade(_config(db_url), "head")

        inspector = inspect(engine)
        assert "apex_computations" in inspector.get_table_names()
        columns = {c["name"] for c in inspector.get_columns("apex_computations")}
        assert {
            "page_id",
            "computation_point",
            "computation_type",
            "computation_item",
            "computation_value",
            "sequence",
        } <= columns

    def test_phase5_session_tables(self, db_url, engine):
        upgrade(_config(db_url), "head")

        inspector = inspect(engine)
        assert "apex_sessions" in inspector.get_table_names()
        assert "apex_session_state" in inspector.get_table_names()

        columns = {c["name"] for c in inspector.get_columns("apex_sessions")}
        assert {"session_id", "application_id", "user_id", "expires_at", "is_active"} <= columns

    def test_phase5_is_public_on_pages(self, db_url, engine):
        upgrade(_config(db_url), "head")

        columns = {c["name"] for c in inspect(engine).get_columns("apex_pages")}
        assert "is_public" in columns

    def test_phase6_rest_data_sources(self, db_url, engine):
        upgrade(_config(db_url), "head")

        inspector = inspect(engine)
        assert "apex_rest_data_sources" in inspector.get_table_names()
        columns = {c["name"] for c in inspector.get_columns("apex_rest_data_sources")}
        assert {"application_id", "url", "method", "response_mapping", "timeout"} <= columns

    def test_execution_point_fits_its_default(self, db_url, engine):
        """The column must be wide enough for the value it defaults to, or every
        insert that relies on the default fails on PostgreSQL."""
        upgrade(_config(db_url), "head")

        column = next(
            c
            for c in inspect(engine).get_columns("apex_page_processes")
            if c["name"] == "execution_point"
        )
        assert column["type"].length >= len("ON_SUBMIT_BEFORE_COMPUTATION")

    def test_session_state_unique_index(self, db_url, engine):
        upgrade(_config(db_url), "head")

        indexes = inspect(engine).get_indexes("apex_session_state")
        unique = [i for i in indexes if i.get("unique")]
        assert any(i["name"] == "ux_session_page_item" for i in unique)

    def test_upgrade_is_idempotent_at_head(self, db_url, engine):
        cfg = _config(db_url)
        upgrade(cfg, "head")
        upgrade(cfg, "head")

        assert "apex_applications" in inspect(engine).get_table_names()


class TestDowngrade:
    def test_downgrade_to_base_removes_apex_tables(self, db_url, engine):
        cfg = _config(db_url)
        upgrade(cfg, "head")
        downgrade(cfg, BASE_REVISION)

        remaining = [t for t in inspect(engine).get_table_names() if t.startswith("apex_")]
        assert remaining == []

    def test_upgrade_downgrade_upgrade_round_trip(self, db_url, engine):
        cfg = _config(db_url)

        upgrade(cfg, "head")
        tables_after_first_upgrade = set(inspect(engine).get_table_names())

        downgrade(cfg, BASE_REVISION)
        upgrade(cfg, "head")

        assert set(inspect(engine).get_table_names()) == tables_after_first_upgrade


class TestSessionStateDataRemap:
    """apex_session_state.session_id switches between the string session id and
    apex_sessions.id, so the migration has to translate the stored values."""

    def _seed(self, engine):
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO apex_applications (id, name, alias) "
                    "VALUES (1, 'app', 'app')"
                )
            )
            connection.execute(
                text(
                    "INSERT INTO apex_sessions "
                    "(id, session_id, application_id, expires_at) "
                    "VALUES (1, 'string-session-id', 1, '2030-01-01 00:00:00')"
                )
            )
            connection.execute(
                text(
                    "INSERT INTO apex_session_state "
                    "(id, session_id, page_id, item_name, item_value) "
                    "VALUES (1, 1, 1, 'P1_ITEM', 'kept')"
                )
            )

    def test_downgrade_restores_string_session_id(self, db_url, engine):
        cfg = _config(db_url)
        upgrade(cfg, "head")
        self._seed(engine)

        downgrade(cfg, PRE_STRING_SESSION_ID_REVISION)

        with engine.connect() as connection:
            value = connection.execute(
                text("SELECT session_id FROM apex_session_state WHERE id = 1")
            ).scalar()
        assert value == "string-session-id"

    def test_upgrade_drops_state_rows_when_no_sessions_exist(self, db_url, engine):
        """The revision that introduces apex_sessions creates it empty, so on a
        real upgrade every pre-existing state row is orphaned and must go."""
        cfg = _config(db_url)
        upgrade(cfg, "head")
        downgrade(cfg, PRE_STRING_SESSION_ID_REVISION)

        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO apex_session_state "
                    "(id, session_id, page_id, item_name, item_value) "
                    "VALUES (1, 'string-session-id', 1, 'P1_ITEM', 'kept')"
                )
            )

        upgrade(cfg, "head")

        with engine.connect() as connection:
            remaining = connection.execute(
                text("SELECT count(*) FROM apex_session_state")
            ).scalar()
        assert remaining == 0



    def test_remap_translates_against_existing_sessions(self, db_url, engine):
        """_remap_session_state translates string session ids to apex_sessions.id
        and drops rows whose session is gone."""
        sessions_migration = _load_sessions_migration()

        cfg = _config(db_url)
        upgrade(cfg, PRE_STRING_SESSION_ID_REVISION)

        # Stand in for sessions that exist by the time the remap runs. The
        # revision being tested would create this table itself, so it is
        # created here and the remap helper is invoked on its own.
        with engine.begin() as connection:
            connection.execute(
                text(
                    "CREATE TABLE apex_sessions ("
                    "id INTEGER NOT NULL PRIMARY KEY, "
                    "session_id VARCHAR(255) NOT NULL, "
                    "application_id INTEGER NOT NULL, "
                    "user_id INTEGER, "
                    "expires_at TIMESTAMP NOT NULL, "
                    "is_active BOOLEAN, "
                    "created_at TIMESTAMP, "
                    "updated_at TIMESTAMP)"
                )
            )
            connection.execute(
                text(
                    "INSERT INTO apex_applications (id, name, alias) "
                    "VALUES (1, 'app', 'app')"
                )
            )
            connection.execute(
                text(
                    "INSERT INTO apex_sessions "
                    "(id, session_id, application_id, expires_at) "
                    "VALUES (1, 'alive', 1, '2030-01-01 00:00:00'), "
                    "(2, 'also-alive', 1, '2030-01-01 00:00:00')"
                )
            )
            connection.execute(
                text(
                    "INSERT INTO apex_session_state "
                    "(id, session_id, page_id, item_name, item_value) "
                    "VALUES (1, 'alive', 1, 'P1_ITEM', 'a'), "
                    "(2, 'also-alive', 1, 'P2_ITEM', 'b'), "
                    "(3, 'dead', 1, 'P3_ITEM', 'c')"
                )
            )

        with engine.begin() as connection:
            context = MigrationContext.configure(connection)
            with Operations.context(context):
                sessions_migration._remap_session_state(to_session_id=True)

        with engine.connect() as connection:
            rows = dict(
                connection.execute(
                    text("SELECT id, session_id FROM apex_session_state")
                ).all()
            )
        assert rows == {1: "1", 2: "2"}

    def test_upgrade_drops_orphaned_state_rows(self, db_url, engine):
        cfg = _config(db_url)
        upgrade(cfg, "head")
        downgrade(cfg, PRE_STRING_SESSION_ID_REVISION)

        # The pre-9c8d7f012c3a schema has no foreign key, so a row can reference
        # a session that no longer exists. Upgrading must not leave it behind,
        # because the new foreign key could not accept it.
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO apex_session_state "
                    "(id, session_id, page_id, item_name, item_value) "
                    "VALUES (1, 'deleted-session', 1, 'P1_ITEM', 'orphan')"
                )
            )

        upgrade(cfg, "head")

        with engine.connect() as connection:
            remaining = connection.execute(
                text("SELECT count(*) FROM apex_session_state")
            ).scalar()
        assert remaining == 0


class TestDatabaseUrlOverride:
    """The container applies migrations using DATABASE_URL, not alembic.ini."""

    def test_env_database_url_replaces_ini_default(self, db_url, engine, monkeypatch):
        monkeypatch.setenv("DATABASE_URL", db_url)

        # No explicit URL: env.py must fall back to DATABASE_URL so migrations
        # land in the scratch database instead of the ini's localhost default.
        upgrade(Config(ALEMBIC_INI), "head")

        assert inspect(engine).has_table("apex_pages")

    def test_explicit_config_url_wins_over_env(self, db_url, engine, monkeypatch):
        # A per-test URL set on the Config object must never be clobbered, even
        # if DATABASE_URL points somewhere unreachable.
        monkeypatch.setenv(
            "DATABASE_URL", "postgresql://nobody:nope@127.0.0.1:1/nowhere"
        )

        upgrade(_config(db_url), "head")

        assert inspect(engine).has_table("apex_pages")


class TestBootstrap:
    """bootstrap.py prepares legacy create_all() databases for Alembic."""

    def test_stamps_a_create_all_schema_and_is_idempotent(
        self, db_url, engine, monkeypatch
    ):
        import bootstrap

        # Reproduce the old initialization path: tables exist, no version row.
        models.Base.metadata.create_all(engine)
        monkeypatch.setenv("DATABASE_URL", db_url)

        bootstrap.main()
        bootstrap.main()

        with engine.connect() as connection:
            version = connection.execute(
                text("SELECT version_num FROM alembic_version")
            ).scalar()
        assert version == "b3c4d5e6f7a8"

    def test_a_fresh_database_is_migrated_and_not_stamped(
        self, db_url, engine, monkeypatch
    ):
        import bootstrap

        monkeypatch.setenv("DATABASE_URL", db_url)

        bootstrap.main()

        assert inspect(engine).has_table("apex_applications")
