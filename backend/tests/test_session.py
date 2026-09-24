import pytest
from app.db import models
from app.core.session.service import SessionService


class TestSessionService:
    def test_create_session(self, db_session, test_app):
        ss = SessionService(db_session)
        session_id = ss.create_session(application_id=test_app.id)

        assert session_id is not None
        assert len(session_id) > 0

        session = db_session.query(models.Session).filter(
            models.Session.session_id == session_id
        ).first()
        assert session is not None
        assert session.application_id == test_app.id

    def test_create_session_with_user(self, db_session, test_app):
        user = models.WorkspaceUser(
            username="testuser",
            password_hash="hashed",
            email="test@test.com",
            administrator_role="END_USER",
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        ss = SessionService(db_session)
        session_id = ss.create_session(application_id=test_app.id, user_id=user.id)

        session = db_session.query(models.Session).filter(
            models.Session.session_id == session_id
        ).first()
        assert session.user_id == user.id

    def test_get_session(self, db_session, test_app):
        ss = SessionService(db_session)
        session_id = ss.create_session(application_id=test_app.id)

        session = ss.get_session(session_id)
        assert session is not None
        assert session.session_id == session_id

    def test_get_session_invalid(self, db_session):
        ss = SessionService(db_session)
        session = ss.get_session("nonexistent-id")
        assert session is None

    def test_validate_session(self, db_session, test_app):
        ss = SessionService(db_session)
        session_id = ss.create_session(application_id=test_app.id)

        assert ss.validate_session(session_id) is True
        assert ss.validate_session("invalid-id") is False

    def test_set_and_get_item(self, db_session, test_app, test_page):
        ss = SessionService(db_session)
        session_id = ss.create_session(application_id=test_app.id)

        ss.set_item(session_id, test_page.id, "P1_NAME", "Alice")
        value = ss.get_item(session_id, test_page.id, "P1_NAME")

        assert value == "Alice"

    def test_set_item_overwrites(self, db_session, test_app, test_page):
        ss = SessionService(db_session)
        session_id = ss.create_session(application_id=test_app.id)

        ss.set_item(session_id, test_page.id, "P1_NAME", "Alice")
        ss.set_item(session_id, test_page.id, "P1_NAME", "Bob")
        value = ss.get_item(session_id, test_page.id, "P1_NAME")

        assert value == "Bob"

    def test_get_item_nonexistent(self, db_session, test_app, test_page):
        ss = SessionService(db_session)
        session_id = ss.create_session(application_id=test_app.id)

        value = ss.get_item(session_id, test_page.id, "P1_MISSING")
        assert value is None

    def test_get_items_for_page(self, db_session, test_app, test_page):
        ss = SessionService(db_session)
        session_id = ss.create_session(application_id=test_app.id)

        ss.set_item(session_id, test_page.id, "P1_A", "1")
        ss.set_item(session_id, test_page.id, "P1_B", "2")

        items = ss.get_items_for_page(session_id, test_page.id)
        assert items == {"P1_A": "1", "P1_B": "2"}

    def test_clear_session(self, db_session, test_app):
        ss = SessionService(db_session)
        session_id = ss.create_session(application_id=test_app.id)

        result = ss.clear_session(session_id)
        assert result is True

        session = ss.get_session(session_id)
        assert session is None

    def test_clear_session_nonexistent(self, db_session):
        ss = SessionService(db_session)
        result = ss.clear_session("nonexistent")
        assert result is False

    def test_cleanup_expired_sessions(self, db_session, test_app):
        from datetime import datetime, timedelta

        expired = models.Session(
            session_id="expired-session",
            application_id=test_app.id,
            expires_at=datetime.utcnow() - timedelta(hours=1),
        )
        db_session.add(expired)
        db_session.commit()

        ss = SessionService(db_session)
        count = ss.cleanup_expired_sessions()

        assert count >= 1
        remaining = db_session.query(models.Session).filter(
            models.Session.session_id == "expired-session"
        ).first()
        assert remaining is None
