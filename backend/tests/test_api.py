import pytest

from app.db import models
from app.core.security.password import get_password_hash


@pytest.fixture
def admin_user(db_session):
    user = models.WorkspaceUser(
        username="admin",
        password_hash=get_password_hash("admin123"),
        first_name="Admin",
        last_name="User",
        email="admin@test.com",
        administrator_role="ADMIN",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_application(db_session):
    app = models.Application(
        name="Test App",
        alias="TESTAPP",
        description="Test",
    )
    db_session.add(app)
    db_session.commit()
    db_session.refresh(app)
    return app


@pytest.fixture
def auth_headers(client, admin_user, test_application):
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "admin", "password": "admin123", "application_id": str(test_application.id)},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_page(db_session, test_application):
    page = models.Page(
        application_id=test_application.id,
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
def end_user(client, test_application, db_session):
    user = models.WorkspaceUser(
        username="enduser",
        password_hash=get_password_hash("StrongPass1!"),
        first_name="End",
        last_name="User",
        email="enduser@test.com",
        administrator_role="END_USER",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def end_user_headers(client, end_user, test_application):
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "enduser", "password": "StrongPass1!", "application_id": str(test_application.id)},
    )
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


class TestAuthEndpoints:
    def test_login_success(self, client, admin_user, test_application):
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "admin", "password": "admin123", "application_id": str(test_application.id)},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["username"] == "admin"

    def test_login_wrong_password(self, client, admin_user, test_application):
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "admin", "password": "wrong", "application_id": str(test_application.id)},
        )
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client):
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "nobody", "password": "pass", "application_id": "999"},
        )
        assert response.status_code in (401, 404)


class TestApplicationEndpoints:
    def test_create_application(self, client, auth_headers):
        response = client.post(
            "/api/v1/applications",
            json={"name": "My App", "alias": "MYAPP", "description": "Test"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "My App"
        assert data["alias"] == "MYAPP"

    def test_get_applications(self, client, auth_headers):
        client.post(
            "/api/v1/applications",
            json={"name": "App1", "alias": "APP1"},
            headers=auth_headers,
        )
        response = client.get("/api/v1/applications", headers=auth_headers)
        assert response.status_code == 200
        assert len(response.json()) >= 1

    def test_get_application_by_id(self, client, auth_headers):
        create_resp = client.post(
            "/api/v1/applications",
            json={"name": "Test", "alias": "TST"},
            headers=auth_headers,
        )
        app_id = create_resp.json()["id"]
        response = client.get(f"/api/v1/applications/{app_id}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["alias"] == "TST"

    def test_update_application(self, client, auth_headers):
        create_resp = client.post(
            "/api/v1/applications",
            json={"name": "Old", "alias": "OLD"},
            headers=auth_headers,
        )
        app_id = create_resp.json()["id"]
        response = client.put(
            f"/api/v1/applications/{app_id}",
            json={"name": "New"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["name"] == "New"

    def test_delete_application(self, client, auth_headers):
        create_resp = client.post(
            "/api/v1/applications",
            json={"name": "Del", "alias": "DEL"},
            headers=auth_headers,
        )
        app_id = create_resp.json()["id"]
        response = client.delete(f"/api/v1/applications/{app_id}", headers=auth_headers)
        assert response.status_code == 200


class TestRegionEndpoints:
    def test_create_region(self, client, auth_headers, test_page):
        response = client.post(
            "/api/v1/regions/",
            json={
                "page_id": test_page.id,
                "name": "Banner",
                "region_type": "static_content",
                "template_options": {"content": "<h1>Hi</h1>"},
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Banner"
        assert data["region_type"] == "static_content"
        assert data["page_id"] == test_page.id
        assert data["template_options"] == {"content": "<h1>Hi</h1>"}

    def test_create_region_unknown_page_returns_404(self, client, auth_headers):
        response = client.post(
            "/api/v1/regions/",
            json={"page_id": 9999, "name": "Orphan", "region_type": "form"},
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_get_regions(self, client, auth_headers, test_page):
        client.post(
            "/api/v1/regions/",
            json={"page_id": test_page.id, "name": "R1", "region_type": "form"},
            headers=auth_headers,
        )
        response = client.get("/api/v1/regions/", headers=auth_headers)
        assert response.status_code == 200
        assert any(r["name"] == "R1" for r in response.json())

    def test_get_regions_by_page(self, client, auth_headers, test_page):
        client.post(
            "/api/v1/regions/",
            json={"page_id": test_page.id, "name": "Scoped", "region_type": "form"},
            headers=auth_headers,
        )
        response = client.get(f"/api/v1/regions/?page_id={test_page.id}", headers=auth_headers)
        assert response.status_code == 200
        assert [r["name"] for r in response.json()] == ["Scoped"]

    def test_get_region_by_id(self, client, auth_headers, test_page):
        created = client.post(
            "/api/v1/regions/",
            json={"page_id": test_page.id, "name": "One", "region_type": "form"},
            headers=auth_headers,
        ).json()
        response = client.get(f"/api/v1/regions/{created['id']}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["id"] == created["id"]

    def test_get_unknown_region_returns_404(self, client, auth_headers):
        assert client.get("/api/v1/regions/9999", headers=auth_headers).status_code == 404

    def test_update_region(self, client, auth_headers, test_page):
        created = client.post(
            "/api/v1/regions/",
            json={"page_id": test_page.id, "name": "Before", "region_type": "form"},
            headers=auth_headers,
        ).json()

        response = client.put(
            f"/api/v1/regions/{created['id']}",
            json={
                "id": created["id"],
                "page_id": test_page.id,
                "name": "After",
                "region_type": "report",
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["name"] == "After"
        assert response.json()["region_type"] == "report"

    def test_delete_region(self, client, auth_headers, test_page):
        created = client.post(
            "/api/v1/regions/",
            json={"page_id": test_page.id, "name": "Doomed", "region_type": "form"},
            headers=auth_headers,
        ).json()

        assert client.delete(f"/api/v1/regions/{created['id']}", headers=auth_headers).status_code == 200
        assert client.get(f"/api/v1/regions/{created['id']}", headers=auth_headers).status_code == 404

    def test_end_user_cannot_delete_region(self, client, end_user_headers, test_page):
        created = client.post(
            "/api/v1/regions/",
            json={"page_id": test_page.id, "name": "Protected", "region_type": "form"},
            headers=end_user_headers,
        ).json()
        response = client.delete(f"/api/v1/regions/{created['id']}", headers=end_user_headers)
        assert response.status_code == 403


class TestItemEndpoints:
    def test_create_item(self, client, auth_headers, test_page):
        response = client.post(
            "/api/v1/items/",
            json={
                "page_id": test_page.id,
                "name": "P1_EMAIL",
                "item_type": "text",
                "label": "Email",
                "is_required": True,
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "P1_EMAIL"
        assert data["item_type"] == "text"
        assert data["is_required"] is True

    def test_get_items_by_page(self, client, auth_headers, test_page):
        client.post(
            "/api/v1/items/",
            json={"page_id": test_page.id, "name": "P1_A", "item_type": "text"},
            headers=auth_headers,
        )
        client.post(
            "/api/v1/items/",
            json={"page_id": test_page.id, "name": "P1_B", "item_type": "textarea"},
            headers=auth_headers,
        )
        response = client.get(f"/api/v1/items/?page_id={test_page.id}", headers=auth_headers)
        assert response.status_code == 200
        assert {i["name"] for i in response.json()} == {"P1_A", "P1_B"}

    def test_get_item_by_id(self, client, auth_headers, test_page):
        created = client.post(
            "/api/v1/items/",
            json={"page_id": test_page.id, "name": "P1_ONE", "item_type": "text"},
            headers=auth_headers,
        ).json()
        response = client.get(f"/api/v1/items/{created['id']}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["name"] == "P1_ONE"

    def test_get_unknown_item_returns_404(self, client, auth_headers):
        assert client.get("/api/v1/items/9999", headers=auth_headers).status_code == 404

    def test_update_item(self, client, auth_headers, test_page):
        created = client.post(
            "/api/v1/items/",
            json={"page_id": test_page.id, "name": "P1_OLD", "item_type": "text"},
            headers=auth_headers,
        ).json()

        response = client.put(
            f"/api/v1/items/{created['id']}",
            json={
                "id": created["id"],
                "page_id": test_page.id,
                "name": "P1_NEW",
                "item_type": "text",
                "label": "Renamed",
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["name"] == "P1_NEW"
        assert response.json()["label"] == "Renamed"

    def test_delete_item(self, client, auth_headers, test_page):
        created = client.post(
            "/api/v1/items/",
            json={"page_id": test_page.id, "name": "P1_TEMP", "item_type": "text"},
            headers=auth_headers,
        ).json()
        assert client.delete(f"/api/v1/items/{created['id']}", headers=auth_headers).status_code == 200
        assert client.get(f"/api/v1/items/{created['id']}", headers=auth_headers).status_code == 404


class TestValidationEndpoints:
    def test_create_validation(self, client, auth_headers, test_page):
        response = client.post(
            "/api/v1/validations/",
            json={
                "page_id": test_page.id,
                "item_name": "P1_EMAIL",
                "validation_type": "NOT_NULL",
                "error_message": "Email is required",
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["item_name"] == "P1_EMAIL"
        assert data["validation_type"] == "NOT_NULL"
        assert data["page_id"] == test_page.id

    def test_create_validation_unknown_page_returns_404(self, client, auth_headers):
        response = client.post(
            "/api/v1/validations/",
            json={
                "page_id": 9999,
                "item_name": "P1_X",
                "validation_type": "NOT_NULL",
            },
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_get_validations_by_page(self, client, auth_headers, test_page):
        client.post(
            "/api/v1/validations/",
            json={
                "page_id": test_page.id,
                "item_name": "P1_EMAIL",
                "validation_type": "NOT_NULL",
            },
            headers=auth_headers,
        )
        client.post(
            "/api/v1/validations/",
            json={
                "page_id": test_page.id,
                "item_name": "P1_AGE",
                "validation_type": "MAX_LENGTH",
                "validation_expression": "3",
            },
            headers=auth_headers,
        )

        response = client.get(f"/api/v1/validations/by-page/{test_page.id}", headers=auth_headers)
        assert response.status_code == 200
        assert {v["item_name"] for v in response.json()} == {"P1_EMAIL", "P1_AGE"}

    def test_get_validations_by_item(self, client, auth_headers, test_page):
        client.post(
            "/api/v1/validations/",
            json={
                "page_id": test_page.id,
                "item_name": "P1_EMAIL",
                "validation_type": "NOT_NULL",
            },
            headers=auth_headers,
        )
        client.post(
            "/api/v1/validations/",
            json={
                "page_id": test_page.id,
                "item_name": "P1_OTHER",
                "validation_type": "NOT_NULL",
            },
            headers=auth_headers,
        )

        response = client.get(
            f"/api/v1/validations/by-item/{test_page.id}/P1_EMAIL", headers=auth_headers
        )
        assert response.status_code == 200
        assert [v["item_name"] for v in response.json()] == ["P1_EMAIL"]

    def test_get_validations_by_page_unknown_page_returns_404(self, client, auth_headers):
        response = client.get("/api/v1/validations/by-page/9999", headers=auth_headers)
        assert response.status_code == 404

    def test_get_validation_by_id(self, client, auth_headers, test_page):
        created = client.post(
            "/api/v1/validations/",
            json={
                "page_id": test_page.id,
                "item_name": "P1_EMAIL",
                "validation_type": "NOT_NULL",
            },
            headers=auth_headers,
        ).json()
        response = client.get(f"/api/v1/validations/{created['id']}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["id"] == created["id"]

    def test_update_validation(self, client, auth_headers, test_page):
        created = client.post(
            "/api/v1/validations/",
            json={
                "page_id": test_page.id,
                "item_name": "P1_EMAIL",
                "validation_type": "NOT_NULL",
                "error_message": "Required",
            },
            headers=auth_headers,
        ).json()

        response = client.put(
            f"/api/v1/validations/{created['id']}",
            json={
                "page_id": test_page.id,
                "item_name": "P1_EMAIL",
                "validation_type": "IN_LIST",
                "validation_expression": "a,b,c",
                "error_message": "Pick a valid value",
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["validation_type"] == "IN_LIST"
        assert response.json()["error_message"] == "Pick a valid value"

    def test_delete_validation(self, client, auth_headers, test_page):
        created = client.post(
            "/api/v1/validations/",
            json={
                "page_id": test_page.id,
                "item_name": "P1_EMAIL",
                "validation_type": "NOT_NULL",
            },
            headers=auth_headers,
        ).json()
        assert (
            client.delete(f"/api/v1/validations/{created['id']}", headers=auth_headers).status_code
            == 200
        )
        assert (
            client.get(f"/api/v1/validations/{created['id']}", headers=auth_headers).status_code
            == 404
        )

    def test_end_user_cannot_delete_validation(self, client, end_user_headers, test_page):
        created = client.post(
            "/api/v1/validations/",
            json={
                "page_id": test_page.id,
                "item_name": "P1_EMAIL",
                "validation_type": "NOT_NULL",
            },
            headers=end_user_headers,
        ).json()
        response = client.delete(
            f"/api/v1/validations/{created['id']}", headers=end_user_headers
        )
        assert response.status_code == 403


class TestLovEndpoints:
    def test_create_lov(self, client, auth_headers):
        response = client.post(
            "/api/v1/lovs/",
            json={"lov_name": "COLORS", "is_static": True, "static_values": "r;Red,g;Green"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        assert response.json()["lov_name"] == "COLORS"

    def test_get_lov_by_name(self, client, auth_headers):
        client.post(
            "/api/v1/lovs/",
            json={"lov_name": "COLORS", "is_static": True, "static_values": "r;Red"},
            headers=auth_headers,
        )
        response = client.get("/api/v1/lovs/name/COLORS", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["static_values"] == "r;Red"

    def test_get_unknown_lov_by_name_returns_404(self, client, auth_headers):
        assert client.get("/api/v1/lovs/name/NOPE", headers=auth_headers).status_code == 404

    def test_update_lov(self, client, auth_headers):
        created = client.post(
            "/api/v1/lovs/",
            json={"lov_name": "SIZES", "is_static": True, "static_values": "S;Small"},
            headers=auth_headers,
        ).json()
        response = client.put(
            f"/api/v1/lovs/{created['id']}",
            json={"lov_name": "SIZES", "is_static": True, "static_values": "S;Small,L;Large"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["static_values"] == "S;Small,L;Large"

    def test_delete_lov(self, client, auth_headers):
        created = client.post(
            "/api/v1/lovs/",
            json={"lov_name": "TEMP", "is_static": True, "static_values": "a;A"},
            headers=auth_headers,
        ).json()
        assert client.delete(f"/api/v1/lovs/{created['id']}", headers=auth_headers).status_code == 200
        assert client.get(f"/api/v1/lovs/{created['id']}", headers=auth_headers).status_code == 404


class TestWorkspaceUserEndpoints:
    def test_create_workspace_user(self, client, auth_headers):
        response = client.post(
            "/api/v1/workspace-users/",
            json={
                "username": "newdev",
                "password_hash": get_password_hash("StrongPass1!"),
                "first_name": "New",
                "last_name": "Dev",
                "email": "newdev@test.com",
                "administrator_role": "DEVELOPER",
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newdev"
        assert data["administrator_role"] == "DEVELOPER"
        assert "password_hash" not in data

    def test_get_workspace_users(self, client, auth_headers):
        response = client.get("/api/v1/workspace-users/", headers=auth_headers)
        assert response.status_code == 200
        assert any(u["username"] == "admin" for u in response.json())

    def test_get_workspace_user_by_username(self, client, auth_headers):
        response = client.get("/api/v1/workspace-users/username/admin", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["username"] == "admin"

    def test_get_workspace_user_unknown_username_returns_404(self, client, auth_headers):
        assert (
            client.get("/api/v1/workspace-users/username/nobody", headers=auth_headers).status_code
            == 404
        )

    def test_update_workspace_user(self, client, auth_headers, admin_user):
        response = client.put(
            f"/api/v1/workspace-users/{admin_user.id}",
            json={"first_name": "Renamed"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["first_name"] == "Renamed"

    def test_delete_workspace_user(self, client, auth_headers):
        created = client.post(
            "/api/v1/workspace-users/",
            json={
                "username": "throwaway",
                "password_hash": get_password_hash("StrongPass1!"),
                "email": "throwaway@test.com",
                "administrator_role": "END_USER",
            },
            headers=auth_headers,
        ).json()
        assert (
            client.delete(f"/api/v1/workspace-users/{created['id']}", headers=auth_headers).status_code
            == 200
        )

    def test_end_user_cannot_list_users(self, client, end_user_headers):
        assert client.get("/api/v1/workspace-users/", headers=end_user_headers).status_code == 403

    def test_end_user_cannot_read_other_profile(self, client, end_user_headers, admin_user):
        response = client.get(f"/api/v1/workspace-users/{admin_user.id}", headers=end_user_headers)
        assert response.status_code == 403
