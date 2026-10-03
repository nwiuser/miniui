"""Tests for authentication: login, logout, lockout and session cookies.

Phase 5 covered the password policy and change-password flow; what was missing
is the login/logout surface itself, including the account lockout counters and
the session cookie that the runtime pages rely on.
"""

import pytest

from app.core.auth.service import AuthService
from app.core.security.password import verify_password
from app.core.session.service import SessionService
from app.db import models


@pytest.fixture
def app_and_user(db, make_app, make_user):
    instance = make_app(alias="AUTHTEST")
    user = make_user("authuser", role="DEVELOPER", password="StrongPass1!")
    return instance, user


def _login(client, app, username="authuser", password="StrongPass1!"):
    response = client.post(
        "/api/v1/auth/login",
        data={"username": username, "password": password, "application_id": str(app.id)},
    )
    return response


class TestLogin:
    def test_successful_login_returns_token_and_user(self, client, app_and_user):
        app, user = app_and_user

        response = _login(client, app)

        assert response.status_code == 200
        body = response.json()
        assert body["token_type"] == "bearer"
        assert body["username"] == "authuser"
        assert body["administrator_role"] == "DEVELOPER"
        assert body["user_id"] == user.id
        assert "password" not in body
        assert "password_hash" not in body

    def test_token_authenticates_subsequent_requests(self, client, app_and_user):
        app, _ = app_and_user
        token = _login(client, app).json()["access_token"]

        response = client.get(
            "/api/v1/applications", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200

    def test_session_is_bound_to_the_application(self, client, app_and_user, db):
        app, _ = app_and_user

        token = _login(client, app).json()["access_token"]

        session = db.query(models.Session).filter(
            models.Session.session_id == token
        ).one()
        assert session.application_id == app.id
        assert session.user.username == "authuser"

    def test_wrong_password_is_rejected(self, client, app_and_user):
        app, _ = app_and_user

        response = _login(client, app, password="WrongPass1!")

        assert response.status_code == 401
        assert response.headers["WWW-Authenticate"] == "Bearer"

    def test_unknown_user_gets_the_same_message(self, client, app_and_user):
        """No user enumeration: unknown user and wrong password look identical."""
        app, _ = app_and_user

        unknown = _login(client, app, username="ghost")
        wrong = _login(client, app, password="WrongPass1!")

        assert unknown.status_code == wrong.status_code == 401
        assert unknown.json()["detail"] == wrong.json()["detail"]

    def test_missing_fields_are_rejected(self, client, app_and_user):
        app, _ = app_and_user

        response = client.post("/api/v1/auth/login", data={"username": "authuser"})

        assert response.status_code == 422

    def test_failed_attempts_are_counted_and_reset_on_success(self, client, app_and_user, db):
        app, user = app_and_user

        for _ in range(3):
            assert _login(client, app, password="WrongPass1!").status_code == 401
        db.refresh(user)
        assert user.failed_access_attempts == 3

        assert _login(client, app).status_code == 200
        db.refresh(user)
        assert user.failed_access_attempts == 0


class TestAccountLockout:
    def test_account_locks_after_five_failures(self, client, app_and_user, db):
        app, user = app_and_user

        for _ in range(5):
            _login(client, app, password="WrongPass1!")

        db.refresh(user)
        assert user.account_locked is True

        # The correct password no longer works while the account is locked.
        assert _login(client, app).status_code == 401

    def test_locked_account_stays_locked_even_after_the_wait(self, client, app_and_user, db):
        app, user = app_and_user
        user.account_locked = True
        db.commit()

        assert _login(client, app).status_code == 401


class TestLogout:
    def test_logout_invalidates_the_session(self, client, app_and_user):
        app, _ = app_and_user
        token = _login(client, app).json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        assert client.get("/api/v1/applications", headers=headers).status_code == 200

        response = client.post("/api/v1/auth/logout", data={"session_id": token})

        assert response.status_code == 200
        assert response.json()["msg"] == "Successfully logged out"
        # The same token must stop working immediately.
        assert client.get("/api/v1/applications", headers=headers).status_code == 401

    def test_logout_twice_still_succeeds(self, client, app_and_user):
        """Logout is idempotent: the row survives, so it reports success again.

        The token is already dead after the first call, which is what matters to
        the client clearing its stored session.
        """
        app, _ = app_and_user
        token = _login(client, app).json()["access_token"]
        client.post("/api/v1/auth/logout", data={"session_id": token})

        response = client.post("/api/v1/auth/logout", data={"session_id": token})

        assert response.status_code == 200

    def test_logout_with_unknown_session(self, client):
        response = client.post("/api/v1/auth/logout", data={"session_id": "nope"})

        assert response.status_code == 400


class TestAuthServiceUnits:
    def test_invalidate_user_sessions_keeps_the_current_one(self, db, app_and_user):
        app, user = app_and_user
        service = SessionService(db)
        keep = service.create_session(app.id, user_id=user.id)
        other = service.create_session(app.id, user_id=user.id)

        count = AuthService(db).invalidate_user_sessions(user.id, keep_session_id=keep)

        assert count == 1
        assert service.validate_session(keep) is True
        assert service.validate_session(other) is False

    def test_invalidate_all_sessions(self, db, app_and_user):
        app, user = app_and_user
        service = SessionService(db)
        first = service.create_session(app.id, user_id=user.id)
        second = service.create_session(app.id, user_id=user.id)

        assert AuthService(db).invalidate_user_sessions(user.id) == 2
        assert service.validate_session(first) is False
        assert service.validate_session(second) is False

    def test_current_user_lookup_for_dead_session(self, db, app_and_user):
        app, user = app_and_user
        service = SessionService(db)
        token = service.create_session(app.id, user_id=user.id)
        auth = AuthService(db)

        assert auth.get_current_user(token).username == "authuser"

        service.clear_session(token)
        assert auth.get_current_user(token) is None
        assert auth.get_current_user("never-existed") is None

    def test_locked_account_is_not_authenticated(self, db, app_and_user):
        app, user = app_and_user
        user.account_locked = True
        db.commit()

        assert AuthService(db).authenticate_user("authuser", "StrongPass1!") is None

    def test_locked_account_is_not_unlocked_by_knowing_the_password(self, db, app_and_user):
        """Recovery is an ADMIN action, not something the holder can trigger."""
        app, user = app_and_user
        user.account_locked = True
        user.failed_access_attempts = 9
        db.commit()

        assert AuthService(db).authenticate_user("authuser", "StrongPass1!") is None
        db.refresh(user)
        assert user.account_locked is True
        assert user.failed_access_attempts == 9

    def test_admin_can_unlock_an_account(self, client, db, make_app, make_user):
        """The documented recovery path: an ADMIN clears the lock."""
        target_app = make_app(alias="UNLOCKAPP")
        locked = make_user("lockeduser", role="END_USER", password="StrongPass1!")
        locked.account_locked = True
        locked.failed_access_attempts = 5
        db.commit()

        assert _login(client, target_app, username="lockeduser").status_code == 401

        make_user("unlockadmin", role="ADMIN", password="StrongPass1!")
        admin_headers = {
            "Authorization": f"Bearer {_login(client, target_app, username='unlockadmin').json()['access_token']}"
        }

        response = client.put(
            f"/api/v1/workspace-users/{locked.id}",
            json={"account_locked": False, "failed_access_attempts": 0},
            headers=admin_headers,
        )

        assert response.status_code == 200
        assert response.json()["account_locked"] is False
        assert _login(client, target_app, username="lockeduser").status_code == 200


class TestSessionCookieOnRuntimePages:
    def test_public_page_sets_a_session_cookie(self, client, db, make_app, make_page):
        app = make_app(alias="COOKIE1")
        page = make_page(app)
        page.is_public = True
        db.commit()

        response = client.get(f"/api/v1/pages/{app.alias}/1")

        assert response.status_code == 200
        cookie_header = response.headers.get("set-cookie", "")
        assert "miniui_session=" in cookie_header
        assert "HttpOnly" in cookie_header
        assert "SameSite=lax" in cookie_header.replace("samesite", "SameSite")

    def test_protected_page_without_session_is_401(self, client, db, make_app, make_page):
        app = make_app(alias="COOKIE2")
        make_page(app)

        response = client.get(f"/api/v1/pages/{app.alias}/1")

        assert response.status_code == 401

    def test_unknown_alias_is_404(self, client):
        assert client.get("/api/v1/pages/NOSUCHAPP/1").status_code == 404

    def test_unknown_page_number_is_404(self, client, db, make_app, make_page):
        app = make_app()
        make_page(app, page_number=1)

        assert client.get(f"/api/v1/pages/{app.alias}/99").status_code == 404

    def test_inactive_page_is_not_rendered(self, client, db, make_app, make_page):
        app = make_app(alias="COOKIE3")
        page = make_page(app)
        page.is_active = False
        db.commit()

        assert client.get(f"/api/v1/pages/{app.alias}/1").status_code == 404

    def test_inactive_application_is_not_rendered(self, client, db, make_app, make_page):
        app = make_app(alias="COOKIE4")
        make_page(app)
        app.is_active = False
        db.commit()

        assert client.get(f"/api/v1/pages/{app.alias}/1").status_code == 404

    def test_session_of_another_application_cannot_view_a_protected_page(
        self, client, db, make_app, make_page, make_user
    ):
        target = make_app(alias="COOKIE5")
        make_page(target)
        intruder = make_user("intruder", role="END_USER")
        foreign_token = SessionService(db).create_session(intruder_application := make_app().id,
                                                           user_id=intruder.id)

        response = client.get(
            f"/api/v1/pages/{target.alias}/1",
            params={"session_id": foreign_token},
        )

        assert response.status_code == 403
        assert intruder_application is not None


class TestPasswordHashing:
    def test_hash_is_not_the_password(self, db, make_user):
        user = make_user("hashcheck", password="StrongPass1!")

        assert user.password_hash != "StrongPass1!"
        assert verify_password("StrongPass1!", user.password_hash) is True
        assert verify_password("strongpass1!", user.password_hash) is False

    def test_same_password_hashes_differently_each_time(self, db, make_user, make_app):
        from app.core.security.password import get_password_hash

        first = make_user("salt1", password="StrongPass1!")
        second = make_user("salt2", password="StrongPass1!")

        assert first.password_hash != second.password_hash