import pytest

import httpx
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import Base, get_db
from app.db import models
from app.core.security.password import get_password_hash
from app.core.session.service import SessionService
from app.core.rest import RestDataSourceService, RestClientError
from app.core.rest.service import RestDataSourceService as RestService
from app.core.region_types.rest import render_rest_region
from main import app


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


@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as c:
            yield c
    finally:
        app.dependency_overrides.pop(get_db, None)


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
    inst = models.Application(name=name, alias=alias, is_active=True)
    db.add(inst)
    db.commit()
    db.refresh(inst)
    return inst


def _make_source(db, app, name="Customers API", method="GET", url="https://api.test.com/customers",
                 response_mapping=None, query_params=None):
    source = models.RestDataSource(
        application_id=app.id,
        name=name,
        url=url,
        method=method,
        headers={"Authorization": "Bearer test"},
        query_params=query_params,
        request_body=None,
        response_mapping=response_mapping,
        timeout=5,
        is_active=True,
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


def _make_page(db, app, page_number=1):
    page = models.Page(
        application_id=app.id,
        name=f"Page {page_number}",
        alias=f"PAGE{page_number}",
        page_number=page_number,
        is_active=True,
    )
    db.add(page)
    db.commit()
    db.refresh(page)
    return page


class TestRestDataSourceServiceUnit:
    def test_get_merges_payload_into_query_params(self, db):
        source = _make_source(db, _make_app(db, alias="SVC1"), query_params={"limit": "10"})
        captured = {}

        def handler(request: httpx.Request) -> httpx.Response:
            captured["url"] = str(request.url)
            return httpx.Response(200, json={"rows": [1, 2]})

        service = RestService(db, transport=httpx.MockTransport(handler))
        result = service.execute(source, payload={"filter": "active"})

        assert "filter=active" in captured["url"]
        assert "limit=10" in captured["url"]
        assert result["status_code"] == 200
        assert result["data"] == {"rows": [1, 2]}

    def test_post_sends_payload_as_json_body(self, db):
        source = _make_source(db, _make_app(db, alias="SVC2"), method="POST",
                              url="https://api.test.com/orders")
        captured = {}

        def handler(request: httpx.Request) -> httpx.Response:
            captured["json"] = request.content
            return httpx.Response(201, json={"id": 42})

        service = RestService(db, transport=httpx.MockTransport(handler))
        service.execute(source, payload={"customer_id": 7})

        assert b'"customer_id"' in captured["json"]

    def test_non_http_scheme_rejected(self, db):
        source = _make_source(db, _make_app(db, alias="SVC3"), url="file:///etc/passwd")
        service = RestService(db)
        with pytest.raises(RestClientError, match="http"):
            service.execute(source)

    def test_upstream_error_raises(self, db):
        source = _make_source(db, _make_app(db, alias="SVC4"))

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(500, text="boom")

        service = RestService(db, transport=httpx.MockTransport(handler))
        result = service.execute(source)
        assert result["status_code"] == 500

    def test_resolve_path(self):
        service = RestService(db=None)
        data = {"address": {"city": "Paris"}, "items": [{"sku": "A"}, {"sku": "B"}]}
        assert service.resolve_path(data, "address.city") == "Paris"
        assert service.resolve_path(data, "items.1.sku") == "B"
        assert service.resolve_path(data, "missing.key") is None

    def test_apply_response_mapping_sets_session_items(self, db):
        app = _make_app(db, alias="SVC5")
        page = _make_page(db, app)
        source = _make_source(db, app, response_mapping={"P1_CITY": "address.city"})
        ss = SessionService(db)
        token = ss.create_session(app.id)

        service = RestService(db)
        mapped = service.apply_response_mapping(
            source, {"address": {"city": "Paris"}}, token, page.id, ss
        )

        assert mapped == {"P1_CITY": "Paris"}
        assert ss.get_item(token, page.id, "P1_CITY") == "Paris"


class TestRestDataSourceEndpoints:
    def test_permissions(self, client, db):
        app = _make_app(db, alias="RESTA")
        source = _make_source(db, app)

        admin = _make_user(db, username="admin1", role="ADMIN")
        dev = _make_user(db, username="dev1", role="DEVELOPER")
        end = _make_user(db, username="end1", role="END_USER")
        ss = SessionService(db)
        admin_token = ss.create_session(app.id, user_id=admin.id)
        dev_token = ss.create_session(app.id, user_id=dev.id)
        end_token = ss.create_session(app.id, user_id=end.id)
        admin_h = {"Authorization": f"Bearer {admin_token}"}
        dev_h = {"Authorization": f"Bearer {dev_token}"}
        end_h = {"Authorization": f"Bearer {end_token}"}

        # END_USER cannot create
        r = client.post("/api/v1/rest-data-sources", json={
            "application_id": app.id, "name": "X", "url": "https://x.test", "method": "GET",
        }, headers=end_h)
        assert r.status_code == 403

        # ADMIN creates
        r = client.post("/api/v1/rest-data-sources", json={
            "application_id": app.id, "name": "Orders", "url": "https://x.test/orders", "method": "GET",
        }, headers=admin_h)
        assert r.status_code == 201
        created = r.json()
        assert created["name"] == "Orders"

        # DEVELOPER updates
        r = client.put(f"/api/v1/rest-data-sources/{created['id']}",
                       json={"name": "Orders v2"}, headers=dev_h)
        assert r.status_code == 200
        assert r.json()["name"] == "Orders v2"

        # END_USER can read own app's sources
        r = client.get("/api/v1/rest-data-sources", headers=end_h)
        assert r.status_code == 200
        assert any(s["id"] == created["id"] for s in r.json())

        # Admin can delete; END_USER cannot
        r = client.delete(f"/api/v1/rest-data-sources/{created['id']}", headers=end_h)
        assert r.status_code == 403
        r = client.delete(f"/api/v1/rest-data-sources/{created['id']}", headers=admin_h)
        assert r.status_code == 204

    def test_end_user_cross_app_denied(self, client, db):
        app_a = _make_app(db, alias="RESTA1")
        app_b = _make_app(db, alias="RESTB1")
        source_b = _make_source(db, app_b, name="B secret")

        end = _make_user(db, username="cross1")
        ss = SessionService(db)
        end_token = ss.create_session(app_a.id, user_id=end.id)

        r = client.get(f"/api/v1/rest-data-sources/{source_b.id}",
                       headers={"Authorization": f"Bearer {end_token}"})
        assert r.status_code == 403

        r = client.post(f"/api/v1/rest-data-sources/{source_b.id}/execute",
                        json={}, headers={"Authorization": f"Bearer {end_token}"})
        assert r.status_code == 403

    def test_execute_endpoint_with_mapping(self, client, db, monkeypatch):
        app = _make_app(db, alias="RESTC1")
        page = _make_page(db, app)
        source = _make_source(db, app, name="Weather",
                              response_mapping={"P1_CITY": "city"})
        end = _make_user(db, username="weather1")
        ss = SessionService(db)
        end_token = ss.create_session(app.id, user_id=end.id)

        def fake_execute(self, data_source, payload=None):
            assert payload == {"unit": "metric"}
            return {"status_code": 200, "data": {"city": "Tokyo"}, "content_type": "application/json"}

        monkeypatch.setattr(RestDataSourceService, "execute", fake_execute)

        r = client.post(
            f"/api/v1/rest-data-sources/{source.id}/execute",
            json={"payload": {"unit": "metric"}, "page_id": page.id},
            headers={"Authorization": f"Bearer {end_token}"},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["name"] == "Weather"
        assert body["status_code"] == 200
        assert body["data"] == {"city": "Tokyo"}
        assert body["mapped_items"] == {"P1_CITY": "Tokyo"}

        # Mapping was applied to session state
        assert ss.get_item(end_token, page.id, "P1_CITY") == "Tokyo"

    def test_end_user_cannot_execute_state_changing_source(self, client, db):
        app = _make_app(db, alias="RESTD1")
        source = _make_source(db, app, method="POST", url="https://x.test/create")
        end = _make_user(db, username="poster1")
        ss = SessionService(db)
        end_token = ss.create_session(app.id, user_id=end.id)

        r = client.post(f"/api/v1/rest-data-sources/{source.id}/execute",
                        json={}, headers={"Authorization": f"Bearer {end_token}"})
        assert r.status_code == 403


class TestRestRegion:
    def test_render_rest_region_table(self, db, monkeypatch):
        app = _make_app(db, alias="RGNA")
        page = _make_page(db, app)
        source = _make_source(db, app, name="Customers")
        region = models.Region(
            page_id=page.id,
            name="Customers Region",
            region_type="rest",
            template_options={"data_source_id": source.id},
            position=1,
            is_active=True,
        )
        db.add(region)
        db.commit()

        def fake_execute(self, data_source, payload=None):
            return {"status_code": 200, "data": [{"id": 1, "name": "Ada"}, {"id": 2, "name": "Bob"}],
                    "content_type": "application/json"}

        monkeypatch.setattr(RestDataSourceService, "execute", fake_execute)

        ss = SessionService(db)
        token = ss.create_session(app.id)
        html = render_rest_region(region, db, token, page.id, ss)

        assert "Ada" in html
        assert "Bob" in html
        assert "report-table rest-table" in html

    def test_render_rest_region_object_and_mapping(self, db, monkeypatch):
        app = _make_app(db, alias="RGNB")
        page = _make_page(db, app)
        source = _make_source(db, app, name="Profile", response_mapping={"P1_CITY": "city"})
        region = models.Region(
            page_id=page.id,
            name="Profile Region",
            region_type="rest",
            template_options={"data_source_id": source.id},
            position=1,
            is_active=True,
        )
        db.add(region)
        db.commit()

        def fake_execute(self, data_source, payload=None):
            return {"status_code": 200, "data": {"city": "Madrid", "country": "ES"},
                    "content_type": "application/json"}

        monkeypatch.setattr(RestDataSourceService, "execute", fake_execute)

        ss = SessionService(db)
        token = ss.create_session(app.id)
        html = render_rest_region(region, db, token, page.id, ss)

        assert "Madrid" in html
        assert "ES" in html
        # response mapping applied to session
        assert ss.get_item(token, page.id, "P1_CITY") == "Madrid"

    def test_render_rest_region_unconfigured(self, db):
        app = _make_app(db, alias="RGNC")
        page = _make_page(db, app)
        region = models.Region(
            page_id=page.id,
            name="Empty",
            region_type="rest",
            template_options={},
            position=1,
            is_active=True,
        )
        db.add(region)
        db.commit()

        ss = SessionService(db)
        token = ss.create_session(app.id)
        html = render_rest_region(region, db, token, page.id, ss)
        assert "No REST data source configured" in html


class TestApplicationMetadataEndpoint:
    def test_metadata_requires_admin(self, client, db):
        app = _make_app(db, alias="META1")
        _make_page(db, app)

        end = _make_user(db, username="meta1", role="END_USER")
        admin = _make_user(db, username="meta2", role="ADMIN")
        ss = SessionService(db)
        end_token = ss.create_session(app.id, user_id=end.id)
        admin_token = ss.create_session(app.id, user_id=admin.id)

        r = client.get(f"/api/v1/applications/{app.id}/metadata",
                       headers={"Authorization": f"Bearer {end_token}"})
        assert r.status_code == 403

        r = client.get(f"/api/v1/applications/{app.id}/metadata",
                       headers={"Authorization": f"Bearer {admin_token}"})
        assert r.status_code == 200
        body = r.json()
        assert body["application"]["alias"] == "META1"
        assert len(body["pages"]) == 1
        assert body["pages"][0]["name"] == "Page 1"

    def test_metadata_requires_auth(self, client, db):
        app = _make_app(db, alias="META2")
        r = client.get(f"/api/v1/applications/{app.id}/metadata")
        assert r.status_code == 401