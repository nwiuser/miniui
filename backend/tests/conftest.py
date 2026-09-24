import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.db.session import Base
from app.db import models


@pytest.fixture(scope="function")
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


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
