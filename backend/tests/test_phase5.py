import pytest
from datetime import datetime, timedelta

from app.db import models
from app.core.security.password import get_password_hash, verify_password, validate_password_strength, ensure_valid_password
from app.core.session.service import SessionService
from app.core.auth.service import AuthService


@pytest.fixture
def db(db_session):
    """Alias so the tests read the same as the other modules."""
    return db_session


def _make_user(db, username="enduser", role="END_USER", password="StrongPass1!"):
    user = models.WorkspaceUser(
        username=username,
        password_hash=get_password_hash(password),
        email=f"{username}@test.com",
        administrator_role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _make_app(db, name="Test App", alias="TESTAPP"):
    app = models.Application(name=name, alias=alias, is_active=True)
    db.add(app)
    db.commit()
    db.refresh(app)
    return app


def _make_page(db, app, page_number=1, is_public=False):
    page = models.Page(
        application_id=app.id,
        name=f"Page {page_number}",
        alias=f"PAGE{page_number}",
        page_number=page_number,
        is_active=True,
        is_public=is_public,
    )
    db.add(page)
    db.commit()
    db.refresh(page)
    return page


class TestPasswordPolicy:
    def test_weak_password_rejected(self):
        errors = validate_password_strength("short")
        assert errors

    def test_missing_complexity_rejected(self):
        errors = validate_password_strength("longenoughpassword")
        assert any("uppercase" in e for e in errors)

    def test_strong_password_accepted(self):
        assert validate_password_strength("StrongPass1!a") == []

    def test_ensure_valid_password_raises(self):
        with pytest.raises(ValueError):
            ensure_valid_password("weak")
        ensure_valid_password("StrongPass1!a")

    def test_empty_password_rejected(self):
        assert validate_password_strength("") != []


class TestSessionRenewal:
    def test_session_renewed_when_near_expiry(self, db):
        app = _make_app(db, alias="RENEW1")
        near_expiry = models.Session(
            session_id="renew-me",
            application_id=app.id,
            expires_at=datetime.utcnow() + timedelta(minutes=30),
            is_active=True,
        )
        db.add(near_expiry)
        db.commit()

        ss = SessionService(db)
        session = ss.get_session("renew-me")

        assert session is not None
        assert session.expires_at > datetime.utcnow() + timedelta(hours=23)

    def test_session_not_renewed_early(self, db):
        app = _make_app(db, alias="RENEW2")
        fresh = models.Session(
            session_id="fresh-session",
            application_id=app.id,
            expires_at=datetime.utcnow() + timedelta(hours=20),
            is_active=True,
        )
        db.add(fresh)
        db.commit()
        original = fresh.expires_at

        ss = SessionService(db)
        session = ss.get_session("fresh-session")
        assert session.expires_at == original


class TestChangePassword:
    def test_change_password_succeeds(self, db):
        user = _make_user(db, password="OldStrong1!a")
        auth = AuthService(db)
        auth.change_password(user, "OldStrong1!a", "NewStrong123!a")
        db.refresh(user)
        assert verify_password("NewStrong123!a", user.password_hash) is True

    def test_change_password_wrong_current(self, db):
        user = _make_user(db, password="OldStrong1!a")
        auth = AuthService(db)
        with pytest.raises(ValueError):
            auth.change_password(user, "wrong", "NewStrong123!a")

    def test_change_password_weak_new(self, db):
        user = _make_user(db, password="OldStrong1!a")
        auth = AuthService(db)
        with pytest.raises(ValueError):
            auth.change_password(user, "OldStrong1!a", "weak")

    def test_change_password_invalidates_sessions(self, db):
        user = _make_user(db, password="OldStrong1!a")
        app = _make_app(db, alias="APPX")
        ss = SessionService(db)
        keep = ss.create_session(app.id, user_id=user.id)
        other = ss.create_session(app.id, user_id=user.id)

        auth = AuthService(db)
        auth.change_password(user, "OldStrong1!a", "NewStrong123!a", keep_session_id=keep)

        assert ss.get_session(keep) is not None
        assert ss.get_session(other) is None


class TestChangePasswordEndpoint:
    def test_change_password_endpoint(self, client, db):
        user = _make_user(db, password="OldStrong1!a")
        app = _make_app(db, alias="APPX1")
        ss = SessionService(db)
        token = ss.create_session(app.id, user_id=user.id)

        response = client.post(
            "/api/v1/auth/change-password",
            data={"current_password": "OldStrong1!a", "new_password": "NewStrong123!a"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

        # Current session survives the change; old password no longer works
        assert ss.get_session(token) is not None
        bad = client.post(
            "/api/v1/auth/login",
            data={"username": user.username, "password": "OldStrong1!a", "application_id": str(app.id)},
        )
        assert bad.status_code == 401

    def test_change_password_weak_rejected(self, client, db):
        user = _make_user(db, password="OldStrong1!a")
        app = _make_app(db, alias="APPX2")
        ss = SessionService(db)
        token = ss.create_session(app.id, user_id=user.id)

        response = client.post(
            "/api/v1/auth/change-password",
            data={"current_password": "OldStrong1!a", "new_password": "weak"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 400


class TestPageVisibility:
    def test_protected_page_requires_session(self, client, db):
        app = _make_app(db, alias="PRIV1")
        _make_page(db, app, page_number=1, is_public=False)
        response = client.get("/api/v1/pages/PRIV1/1")
        assert response.status_code == 401

    def test_public_page_no_session(self, client, db):
        app = _make_app(db, alias="PUB1")
        _make_page(db, app, page_number=1, is_public=True)
        response = client.get("/api/v1/pages/PUB1/1")
        assert response.status_code == 200

    def test_protected_page_with_valid_session(self, client, db):
        user = _make_user(db)
        app = _make_app(db, alias="PRIV2")
        _make_page(db, app, page_number=1, is_public=False)
        ss = SessionService(db)
        token = ss.create_session(app.id, user_id=user.id)
        response = client.get(f"/api/v1/pages/PRIV2/1?session_id={token}")
        assert response.status_code == 200

    def test_protected_page_wrong_application(self, client, db):
        user = _make_user(db)
        app_a = _make_app(db, alias="PRIV3A")
        app_b = _make_app(db, alias="PRIV3B")
        _make_page(db, app_b, page_number=1, is_public=False)
        ss = SessionService(db)
        token = ss.create_session(app_a.id, user_id=user.id)
        response = client.get(f"/api/v1/pages/PRIV3B/1?session_id={token}")
        assert response.status_code == 403

    def test_render_endpoint_respects_visibility(self, client, db):
        app = _make_app(db, alias="RENDPRIV")
        _make_page(db, app, page_number=1, is_public=False)
        response = client.get("/api/v1/app/RENDPRIV/1")
        assert response.status_code == 401


class TestEndUserProcessComputationAccess:
    def test_end_user_cannot_see_other_app_processes(self, client, db):
        user = _make_user(db)
        app_a = _make_app(db, alias="PROCA")
        app_b = _make_app(db, alias="PROCB")
        page_b = _make_page(db, app_b, page_number=1)
        db.add(models.PageProcess(
            page_id=page_b.id, name="Hidden", process_type="sql",
            process_code="SELECT 1", execution_sequence=10, is_active=True,
        ))
        db.commit()

        ss = SessionService(db)
        token = ss.create_session(app_a.id, user_id=user.id)
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get("/api/v1/processes", headers=headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_end_user_can_see_own_app_processes(self, client, db):
        user = _make_user(db)
        app = _make_app(db, alias="PROC1")
        page = _make_page(db, app, page_number=1)
        db.add(models.PageProcess(
            page_id=page.id, name="Visible", process_type="sql",
            process_code="SELECT 1", execution_sequence=10, is_active=True,
        ))
        db.commit()

        ss = SessionService(db)
        token = ss.create_session(app.id, user_id=user.id)
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get("/api/v1/processes", headers=headers)
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["name"] == "Visible"

    def test_end_user_cannot_create_process_in_other_app(self, client, db):
        user = _make_user(db)
        app_a = _make_app(db, alias="PROCCR1")
        app_b = _make_app(db, alias="PROCCR2")
        page_b = _make_page(db, app_b, page_number=1)

        ss = SessionService(db)
        token = ss.create_session(app_a.id, user_id=user.id)
        headers = {"Authorization": f"Bearer {token}"}

        response = client.post(
            "/api/v1/processes",
            json={
                "page_id": page_b.id,
                "name": "Sneaky",
                "process_type": "sql",
                "process_code": "SELECT 1",
            },
            headers=headers,
        )
        assert response.status_code == 403

    def test_end_user_cannot_access_other_app_computation(self, client, db):
        user = _make_user(db)
        app_a = _make_app(db, alias="COMPA")
        app_b = _make_app(db, alias="COMPB")
        page_b = _make_page(db, app_b, page_number=1)
        comp = models.Computation(
            page_id=page_b.id, computation_point="ON_LOAD",
            computation_type="STATIC_ASSIGNMENT",
            computation_item="P1_X", computation_value="1",
            sequence=1, is_active=True,
        )
        db.add(comp)
        db.commit()

        ss = SessionService(db)
        token = ss.create_session(app_a.id, user_id=user.id)
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get("/api/v1/computations", headers=headers)
        assert response.status_code == 200
        assert response.json() == []

        response = client.get(f"/api/v1/computations/{comp.id}", headers=headers)
        assert response.status_code == 403