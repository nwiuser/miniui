"""Tests for the page builder endpoints (``/api/v1/pages/builder/*``).

These routes back the visual builder in the frontend: the builder loads its
context from ``GET /builder/{application_id}`` and then creates, updates and
deletes pages through the same routes. Nothing covered them before, so both the
happy paths and the role checks are pinned here.
"""

import pytest


class TestBuilderContext:
    def test_returns_application_and_pages(self, client, auth_headers, make_app):
        app = make_app(alias="BUILDER1")
        headers = auth_headers(application=app)

        response = client.get(f"/api/v1/pages/builder/{app.id}", headers=headers)

        assert response.status_code == 200
        body = response.json()
        assert body["application"]["id"] == app.id
        assert body["application"]["alias"] == "BUILDER1"
        assert body["pages"] == []

    def test_only_lists_pages_of_that_application(self, client, auth_headers, make_app, make_page):
        app = make_app(alias="BUILDER2")
        other = make_app(alias="BUILDER3")
        make_page(app, page_number=1, name="Mine")
        make_page(app, page_number=2, name="Also mine")
        make_page(other, page_number=1, name="Not mine")
        headers = auth_headers(application=app)

        body = client.get(f"/api/v1/pages/builder/{app.id}", headers=headers).json()

        names = [page["name"] for page in body["pages"]]
        assert names == ["Mine", "Also mine"]

    def test_unknown_application_returns_404(self, client, auth_headers, make_app):
        app = make_app()
        headers = auth_headers(application=app)

        response = client.get("/api/v1/pages/builder/999999", headers=headers)

        assert response.status_code == 404
        assert response.json()["detail"] == "Application not found"

    def test_requires_authentication(self, client, make_app):
        app = make_app()

        assert client.get(f"/api/v1/pages/builder/{app.id}").status_code == 401

    def test_end_user_cannot_open_the_builder(self, client, auth_headers, make_app):
        app = make_app()
        headers = auth_headers(role="END_USER", application=app)

        response = client.get(f"/api/v1/pages/builder/{app.id}", headers=headers)

        assert response.status_code == 403

    def test_end_user_cannot_read_another_application(self, client, auth_headers, make_app):
        mine = make_app(alias="MINE1")
        theirs = make_app(alias="THEIRS1")
        headers = auth_headers(role="END_USER", application=mine)

        response = client.get(f"/api/v1/pages/builder/{theirs.id}", headers=headers)

        assert response.status_code == 403


class TestBuilderGetPage:
    def test_returns_single_page_not_context(self, client, auth_headers, make_app, make_page):
        app = make_app(alias="BUILDERGET1")
        page = make_page(app, page_number=1, name="Home")
        headers = auth_headers(application=app)

        response = client.get(f"/api/v1/pages/builder/page/{page.id}", headers=headers)

        assert response.status_code == 200
        body = response.json()
        assert body["id"] == page.id
        assert body["name"] == "Home"
        assert "application" not in body
        assert "pages" not in body

    def test_unknown_page_returns_404(self, client, auth_headers, make_app):
        app = make_app()
        headers = auth_headers(application=app)

        response = client.get("/api/v1/pages/builder/page/999999", headers=headers)

        assert response.status_code == 404

    def test_requires_authentication(self, client, make_app, make_page):
        app = make_app(alias="BUILDERGET2")
        page = make_page(app, page_number=1)

        assert client.get(f"/api/v1/pages/builder/page/{page.id}").status_code == 401

    def test_end_user_cannot_fetch_page(self, client, auth_headers, make_app, make_page):
        app = make_app()
        page = make_page(app, page_number=1)
        headers = auth_headers(role="END_USER", application=app)

        response = client.get(f"/api/v1/pages/builder/page/{page.id}", headers=headers)

        assert response.status_code == 403


class TestBuilderCreatePage:
    def test_admin_creates_page(self, client, auth_headers, make_app):
        app = make_app(alias="CREATE1")
        headers = auth_headers(application=app)

        response = client.post(
            "/api/v1/pages/builder/",
            json={
                "application_id": app.id,
                "name": "Orders",
                "alias": "ORDERS",
                "page_number": 10,
            },
            headers=headers,
        )

        assert response.status_code == 200
        body = response.json()
        assert body["name"] == "Orders"
        assert body["page_number"] == 10
        assert body["application_id"] == app.id

    def test_developer_creates_page(self, client, auth_headers, make_app):
        app = make_app(alias="CREATE2")
        headers = auth_headers(role="DEVELOPER", application=app)

        response = client.post(
            "/api/v1/pages/builder/",
            json={"application_id": app.id, "name": "Dev page", "page_number": 3},
            headers=headers,
        )

        assert response.status_code == 200

    def test_end_user_cannot_create_page(self, client, auth_headers, make_app):
        app = make_app()
        headers = auth_headers(role="END_USER", application=app)

        response = client.post(
            "/api/v1/pages/builder/",
            json={"application_id": app.id, "name": "Sneaky", "page_number": 4},
            headers=headers,
        )

        assert response.status_code == 403

    def test_end_user_cannot_create_page_in_another_application(self, client, auth_headers, make_app):
        mine = make_app(alias="CREATE3")
        theirs = make_app(alias="CREATE4")
        headers = auth_headers(role="END_USER", application=mine)

        response = client.post(
            "/api/v1/pages/builder/",
            json={"application_id": theirs.id, "name": "Sneaky", "page_number": 1},
            headers=headers,
        )

        assert response.status_code == 403

    def test_requires_authentication(self, client, make_app):
        app = make_app()

        response = client.post(
            "/api/v1/pages/builder/",
            json={"application_id": app.id, "name": "Anon", "page_number": 1},
        )

        assert response.status_code == 401

    def test_invalid_payload_is_rejected(self, client, auth_headers, make_app):
        app = make_app()
        headers = auth_headers(application=app)

        response = client.post(
            "/api/v1/pages/builder/",
            json={"application_id": app.id},
            headers=headers,
        )

        assert response.status_code == 422


class TestBuilderUpdatePage:
    def test_admin_updates_page(self, client, auth_headers, make_app, make_page):
        app = make_app(alias="UPDATE1")
        page = make_page(app, page_number=1, name="Before")
        headers = auth_headers(application=app)

        response = client.put(
            f"/api/v1/pages/builder/{page.id}",
            json={"id": page.id, "application_id": app.id, "name": "After", "page_number": 1},
            headers=headers,
        )

        assert response.status_code == 200
        assert response.json()["name"] == "After"

    def test_developer_updates_page(self, client, auth_headers, make_app, make_page):
        app = make_app(alias="UPDATE2")
        page = make_page(app)
        headers = auth_headers(role="DEVELOPER", application=app)

        response = client.put(
            f"/api/v1/pages/builder/{page.id}",
            json={"id": page.id, "application_id": app.id, "name": "Dev update", "page_number": 1},
            headers=headers,
        )

        assert response.status_code == 200

    def test_end_user_cannot_update_page(self, client, auth_headers, make_app, make_page):
        app = make_app()
        page = make_page(app)
        headers = auth_headers(role="END_USER", application=app)

        response = client.put(
            f"/api/v1/pages/builder/{page.id}",
            json={"id": page.id, "application_id": app.id, "name": "Hacked", "page_number": 1},
            headers=headers,
        )

        assert response.status_code == 403

    def test_unknown_page_returns_404(self, client, auth_headers, make_app):
        app = make_app()
        headers = auth_headers(application=app)

        response = client.put(
            "/api/v1/pages/builder/999999",
            json={"id": 999999, "application_id": app.id, "name": "Ghost", "page_number": 1},
            headers=headers,
        )

        assert response.status_code == 404

    def test_requires_authentication(self, client, make_app, make_page):
        app = make_app()
        page = make_page(app)

        response = client.put(
            f"/api/v1/pages/builder/{page.id}",
            json={"id": page.id, "application_id": app.id, "name": "Anon", "page_number": 1},
        )

        assert response.status_code == 401


class TestBuilderDeletePage:
    def test_admin_deletes_page(self, client, auth_headers, make_app, make_page):
        app = make_app(alias="DELETE1")
        page = make_page(app)
        headers = auth_headers(application=app)

        response = client.delete(f"/api/v1/pages/builder/{page.id}", headers=headers)

        assert response.status_code == 200
        assert response.json()["id"] == page.id
        assert client.get(
            f"/api/v1/pages/builder/{app.id}", headers=headers
        ).json()["pages"] == []

    def test_developer_cannot_delete_page(self, client, auth_headers, make_app, make_page):
        app = make_app()
        page = make_page(app)
        headers = auth_headers(role="DEVELOPER", application=app)

        response = client.delete(f"/api/v1/pages/builder/{page.id}", headers=headers)

        assert response.status_code == 403

    def test_end_user_cannot_delete_page(self, client, auth_headers, make_app, make_page):
        app = make_app()
        page = make_page(app)
        headers = auth_headers(role="END_USER", application=app)

        assert client.delete(
            f"/api/v1/pages/builder/{page.id}", headers=headers
        ).status_code == 403

    def test_unknown_page_returns_404(self, client, auth_headers, make_app):
        app = make_app()
        headers = auth_headers(application=app)

        assert client.delete("/api/v1/pages/builder/999999", headers=headers).status_code == 404

    def test_requires_authentication(self, client, make_app, make_page):
        app = make_app()
        page = make_page(app)

        assert client.delete(f"/api/v1/pages/builder/{page.id}").status_code == 401


class TestBuilderRoundTrip:
    def test_page_lifecycle_through_builder_routes(self, client, auth_headers, make_app):
        """Create, read, update and delete in the order the builder does it."""
        app = make_app(alias="ROUNDTRIP")
        headers = auth_headers(application=app)

        created = client.post(
            "/api/v1/pages/builder/",
            json={"application_id": app.id, "name": "Step 1", "page_number": 1},
            headers=headers,
        ).json()

        context = client.get(f"/api/v1/pages/builder/{app.id}", headers=headers).json()
        assert [page["id"] for page in context["pages"]] == [created["id"]]

        client.put(
            f"/api/v1/pages/builder/{created['id']}",
            json={"id": created["id"], "application_id": app.id, "name": "Step 2", "page_number": 2},
            headers=headers,
        )

        context = client.get(f"/api/v1/pages/builder/{app.id}", headers=headers).json()
        assert context["pages"][0]["name"] == "Step 2"
        assert context["pages"][0]["page_number"] == 2

        client.delete(f"/api/v1/pages/builder/{created['id']}", headers=headers)

        context = client.get(f"/api/v1/pages/builder/{app.id}", headers=headers).json()
        assert context["pages"] == []


@pytest.mark.parametrize("route", ["get", "delete"])
def test_builder_routes_reject_anonymous_users(client, route):
    """A single sweep so no builder route can silently lose its auth check."""
    request = getattr(client, route)
    assert request("/api/v1/pages/builder/1").status_code == 401