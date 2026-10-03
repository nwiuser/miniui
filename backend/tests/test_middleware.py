"""Tests for the middleware stack in ``main.py``.

Three middlewares sit in front of every request: security headers, CSRF
protection and login rate limiting. Each one is a security control, so each
gets a test that proves it actually blocks or annotates traffic rather than
merely existing.
"""

import pytest

from app.core.security.rate_limit import RateLimitStore, rate_limit_store


class TestSecurityHeaders:
    """Every response, error or not, must carry the hardening headers."""

    def test_headers_present_on_success(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"
        assert response.headers["X-XSS-Protection"] == "1; mode=block"
        assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
        assert "default-src 'self'" in response.headers["Content-Security-Policy"]

    def test_headers_present_on_error_response(self, raw_client):
        """A 404 must not leak a header-free response."""
        response = raw_client.get("/api/v1/does-not-exist")
        assert response.status_code == 404
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert "Content-Security-Policy" in response.headers

    def test_hsts_only_over_https(self, client):
        """HSTS is meaningless (and harmful) over plain HTTP."""
        assert "Strict-Transport-Security" not in client.get("/").headers

    def test_hsts_added_for_https_requests(self, client):
        response = client.get("https://testserver/")
        assert response.headers["Strict-Transport-Security"] == (
            "max-age=31536000; includeSubDomains"
        )


class TestCSRFProtection:
    """Unsafe methods must carry ``X-Requested-With`` or be rejected."""

    def test_unsafe_method_without_header_is_rejected(self, raw_client):
        response = raw_client.post("/api/v1/applications", json={"name": "X", "alias": "X"})
        assert response.status_code == 403
        assert "CSRF validation failed" in response.json()["detail"]

    @pytest.mark.parametrize("method", ["post", "put", "delete"])
    def test_all_unsafe_methods_are_guarded(self, raw_client, method):
        request = getattr(raw_client, method)
        response = request("/api/v1/applications/1") if method == "delete" else request(
            "/api/v1/applications/1", json={"name": "nope"}
        )
        assert response.status_code == 403

    def test_safe_methods_pass_without_header(self, raw_client):
        assert raw_client.get("/").status_code == 200

    def test_request_with_header_is_allowed(self, raw_client):
        response = raw_client.post(
            "/api/v1/auth/login",
            json={"username": "nobody", "password": "whatever1"},
            headers={"X-Requested-With": "XMLHttpRequest"},
        )
        assert response.status_code != 403

    def test_login_is_exempt_but_similar_path_is_not(self):
        """The exempt list is matched per path segment.

        ``/api/v1/auth/login`` is exempt so the login form works, but
        ``/api/v1/auth/login-extra`` must not inherit the exemption.
        """
        from main import CSRFProtectionMiddleware

        middleware = CSRFProtectionMiddleware(app=None, exempt_paths=["/api/v1/auth/login"])
        assert middleware._is_exempt("/api/v1/auth/login") is True
        assert middleware._is_exempt("/api/v1/auth/login/") is True
        assert middleware._is_exempt("/api/v1/auth/login-extra") is False
        assert middleware._is_exempt("/api/v1/applications") is False

    def test_root_prefix_does_not_exempt_everything(self):
        """Regression: ``"/"`` in the exempt list matched every path.

        Because every URL path starts with ``/``, a plain ``startswith`` check
        made the middleware a no-op for the whole API.
        """
        from main import CSRFProtectionMiddleware

        middleware = CSRFProtectionMiddleware(app=None, exempt_paths=["/"])
        assert middleware._is_exempt("/api/v1/applications") is False
        assert middleware._is_exempt("/") is True


class TestRateLimiting:
    """The login endpoint is rate limited per client IP."""

    def test_login_is_blocked_after_max_attempts(self, raw_client, db):
        for _ in range(10):
            response = raw_client.post(
                "/api/v1/auth/login",
                json={"username": "ghost", "password": "WrongPass1!"},
            )
            assert response.status_code != 429

        blocked = raw_client.post(
            "/api/v1/auth/login",
            json={"username": "ghost", "password": "WrongPass1!"},
        )
        assert blocked.status_code == 429
        assert "Too many login attempts" in blocked.json()["detail"]

    def test_other_endpoints_are_not_rate_limited(self, client, db):
        for _ in range(15):
            assert client.get("/").status_code == 200

    def test_get_requests_are_not_rate_limited(self, raw_client):
        for _ in range(15):
            assert raw_client.get("/api/v1/auth/login").status_code in (405, 422)

    def test_window_prunes_old_attempts(self, monkeypatch):
        """Attempts older than the window stop counting."""
        store = RateLimitStore()
        now = 1_000_000.0
        clock = {"now": now}
        monkeypatch.setattr("app.core.security.rate_limit.time.time", lambda: clock["now"])

        for _ in range(10):
            store.record_attempt("auth:1.2.3.4")
        assert store.is_rate_limited("auth:1.2.3.4") is True

        clock["now"] = now + store._window + 1
        assert store.is_rate_limited("auth:1.2.3.4") is False

    def test_keys_are_isolated_per_client(self, monkeypatch):
        store = RateLimitStore()
        monkeypatch.setattr("app.core.security.rate_limit.time.time", lambda: 1000.0)

        for _ in range(10):
            store.record_attempt("auth:1.1.1.1")

        assert store.is_rate_limited("auth:1.1.1.1") is True
        assert store.is_rate_limited("auth:2.2.2.2") is False

    def test_reset_clears_attempts(self):
        rate_limit_store.reset()
        for _ in range(10):
            rate_limit_store.record_attempt("auth:9.9.9.9")
        assert rate_limit_store.is_rate_limited("auth:9.9.9.9") is True

        rate_limit_store.reset()
        assert rate_limit_store.is_rate_limited("auth:9.9.9.9") is False

