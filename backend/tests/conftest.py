import os
import uuid

import pytest
from sqlalchemy import create_engine, text

from app.db.session import Base
from app.db import models
from app.core.security.rate_limit import rate_limit_store

from tests.database import create_test_database, drop_test_database


@pytest.fixture(autouse=True)
def reset_rate_limit_store():
    """Clear the process-global login rate limiter between tests.

    The store is a module-level singleton, so without this a suite that logs in
    more than ``_max_attempts`` times within the window starts failing logins
    with 429 for reasons unrelated to the test.
    """
    rate_limit_store.reset()
    yield
    rate_limit_store.reset()


@pytest.fixture(scope="session")
def test_database_url():
    """A throwaway PostgreSQL database, created once for the whole session.

    Never the development database, so the suite is safe to run while the
    application is up.
    """
    url = create_test_database()
    try:
        yield url
    finally:
        drop_test_database(url)


@pytest.fixture(scope="session")
def test_engine(test_database_url):
    """Session-wide engine with the schema in place.

    The schema is created once rather than per test; isolation comes from the
    transaction rollback in ``db_session``.
    """
    engine = create_engine(test_database_url, pool_pre_ping=True)
    Base.metadata.create_all(bind=engine)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def db_connection(test_engine):
    """A connection inside an open transaction that the test can roll back."""
    connection = test_engine.connect()
    transaction = connection.begin()
    try:
        yield connection
    finally:
        transaction.rollback()
        connection.close()


@pytest.fixture
def db_session(db_connection):
    """A session whose writes are discarded when the test finishes.

    ``join_transaction_mode="create_savepoint"`` makes the session's own
    ``commit()`` calls release savepoints instead of committing for real, so
    tests can commit freely while everything still rolls back afterwards.
    """
    from sqlalchemy.orm import Session

    session = Session(
        bind=db_connection,
        autoflush=False,
        join_transaction_mode="create_savepoint",
    )
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def db(db_session):
    """Alias for ``db_session``, the spelling most test modules use."""
    return db_session


@pytest.fixture
def test_app(db_session):
    app = models.Application(
        name="Test App",
        alias="TESTAPP",
        description="Test application",
        is_active=True,
    )
    db_session.add(app)
    db_session.commit()
    db_session.refresh(app)
    return app


@pytest.fixture
def test_page(db_session, test_app):
    page = models.Page(
        application_id=test_app.id,
        name="Home Page",
        alias="HOME",
        page_number=1,
        is_active=True,
    )
    db_session.add(page)
    db_session.commit()
    db_session.refresh(page)
    return page


@pytest.fixture
def make_user(db):
    """Factory for workspace users: ``make_user(role="ADMIN")``."""

    def factory(username="user", role="END_USER", password="StrongPass1!", **kwargs):
        from app.core.security.password import get_password_hash

        user = models.WorkspaceUser(
            username=username,
            password_hash=get_password_hash(password),
            email=f"{username}@example.test",
            administrator_role=role,
            **kwargs,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    return factory


@pytest.fixture
def make_app(db):
    """Factory for applications; the alias defaults to a unique value."""

    counter = {"n": 0}

    def factory(alias=None, name="Test App", **kwargs):
        counter["n"] += 1
        instance = models.Application(
            name=name,
            alias=alias or f"APP{counter['n']}",
            is_active=True,
            **kwargs,
        )
        db.add(instance)
        db.commit()
        db.refresh(instance)
        return instance

    return factory


@pytest.fixture
def make_page(db):
    """Factory for pages inside an application."""

    def factory(application, page_number=1, name=None, **kwargs):
        page = models.Page(
            application_id=application.id,
            name=name or f"Page {page_number}",
            alias=f"PAGE{page_number}",
            page_number=page_number,
            is_active=True,
            **kwargs,
        )
        db.add(page)
        db.commit()
        db.refresh(page)
        return page

    return factory


@pytest.fixture
def auth_headers(client, db, make_user, make_app):
    """Factory returning auth headers for a user bound to an application.

    ``auth_headers()`` gives a fresh ADMIN, ``auth_headers(role="END_USER")``
    an end user. The session token is minted directly, the same way the auth
    endpoints do, so tests do not depend on the login flow to set up
    authorization.
    """
    from app.core.session.service import SessionService

    counter = {"n": 0}

    def factory(role="ADMIN", application=None, username=None, password="StrongPass1!"):
        counter["n"] += 1
        app = application or make_app()
        user = make_user(username or f"{role.lower()}{counter['n']}", role=role, password=password)
        token = SessionService(db).create_session(app.id, user_id=user.id)
        return {"Authorization": f"Bearer {token}"}

    return factory


@pytest.fixture
def client(db_session):
    """A TestClient whose requests share the test's transaction.

    The dependency override yields the same session the test uses, so data the
    test inserts is visible to the endpoints and vice versa, and all of it is
    rolled back when the test ends.

    ``X-Requested-With`` is sent on every request because the CSRF middleware
    rejects unsafe methods without it, which is how the real frontend calls the
    API. Use ``raw_client`` to exercise the rejection itself.
    """
    yield from _make_client(db_session, csrf=True)


@pytest.fixture
def raw_client(db_session):
    """A TestClient that sends no ``X-Requested-With`` header.

    Same transaction as ``client``; used by the middleware tests that assert
    requests without the header are rejected.
    """
    yield from _make_client(db_session, csrf=False)


def _make_client(db_session, csrf: bool):
    from fastapi.testclient import TestClient
    from app.db.session import get_db
    from main import app as fastapi_app

    def override_get_db():
        yield db_session

    fastapi_app.dependency_overrides[get_db] = override_get_db
    headers = {"X-Requested-With": "XMLHttpRequest"} if csrf else {}
    try:
        with TestClient(fastapi_app, headers=headers) as test_client:
            yield test_client
    finally:
        # Removed only after the client is done: the endpoints must keep using
        # the test's session for the whole request, transaction rollback aside.
        fastapi_app.dependency_overrides.pop(get_db, None)
