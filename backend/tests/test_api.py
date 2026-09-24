import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.db.session import Base, get_db
from app.db import models
from main import app
from app.core.security.password import get_password_hash


SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function")
def client():
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def admin_user():
    db = TestingSessionLocal()
    user = models.WorkspaceUser(
        username="admin",
        password_hash=get_password_hash("admin123"),
        first_name="Admin",
        last_name="User",
        email="admin@test.com",
        administrator_role="ADMIN",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return user


@pytest.fixture
def test_application():
    db = TestingSessionLocal()
    app = models.Application(
        name="Test App",
        alias="TESTAPP",
        description="Test",
    )
    db.add(app)
    db.commit()
    db.refresh(app)
    db.close()
    return app


@pytest.fixture
def auth_headers(client, admin_user, test_application):
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "admin", "password": "admin123", "application_id": str(test_application.id)},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


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
    @pytest.mark.skip(reason="Requires missing crud.create_region")
    def test_create_region(self, client, auth_headers):
        pass


class TestItemEndpoints:
    @pytest.mark.skip(reason="Requires missing crud.create_item")
    def test_create_item(self, client, auth_headers):
        pass


class TestValidationEndpoints:
    @pytest.mark.skip(reason="Requires missing crud.create_validation")
    def test_create_validation(self, client, auth_headers):
        pass

    @pytest.mark.skip(reason="Requires missing crud.create_validation")
    def test_get_validations_by_page(self, client, auth_headers):
        pass
