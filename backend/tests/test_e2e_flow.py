"""End-to-end flows exercised over HTTP only.

These tests never touch the ORM directly (apart from the ``db`` fixture needed to
create the initial application and to seed a redirect). Everything else goes
through the public API the same way the frontend does: log in, build a page,
render it, submit it, inspect the report, then delete the page.

The goal is to catch the seams between endpoints - route shadowing, region/item
placement, form submission, report rendering and cleanup - which unit tests on
each service do not cover.
"""

import pytest

from app.core.session.service import SessionService
from app.db import models


@pytest.fixture
def application(db):
    """A single application, created outside the API to keep ids predictable."""
    app = models.Application(name="E2E App", alias="E2E", description="end to end")
    db.add(app)
    db.commit()
    db.refresh(app)
    return app


@pytest.fixture
def admin_client(client, make_user, application):
    """A logged-in ADMIN, which is the role that can build and delete."""
    make_user("e2eadmin", role="ADMIN", password="StrongPass1!")
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "e2eadmin",
            "password": "StrongPass1!",
            "application_id": str(application.id),
        },
    )
    assert response.status_code == 200, response.text
    client.headers["Authorization"] = f"Bearer {response.json()['access_token']}"
    return client


@pytest.fixture
def session_id_of():
    """Extract the session the runtime endpoint handed back."""

    def _extract(response):
        cookie = response.headers.get("set-cookie", "")
        assert "miniui_session=" in cookie, cookie
        return cookie.split("miniui_session=")[1].split(";")[0]

    return _extract


@pytest.fixture
def built_page(admin_client, application):
    """A public page with a static region, a form region and two text items."""
    page = admin_client.post(
        "/api/v1/pages/builder/",
        json={
            "application_id": application.id,
            "name": "Contact",
            "alias": "contact",
            "page_number": 1,
            "description": "Contact form",
            "is_public": True,
        },
    )
    assert page.status_code == 200, page.text
    page_id = page.json()["id"]

    static_region = admin_client.post(
        "/api/v1/regions/",
        json={
            "page_id": page_id,
            "name": "Intro",
            "region_type": "static_content",
            "template_options": {"content": "<p>Say hello</p>"},
            "position": 0,
        },
    )
    assert static_region.status_code == 201, static_region.text

    form_region = admin_client.post(
        "/api/v1/regions/",
        json={
            "page_id": page_id,
            "name": "Form",
            "region_type": "form",
            "position": 1,
        },
    )
    assert form_region.status_code == 201, form_region.text

    for name, label in (("name", "Your name"), ("message", "Your message")):
        item = admin_client.post(
            "/api/v1/items/",
            json={
                "page_id": page_id,
                "name": name,
                "alias": name,
                "item_type": "text",
                "label": label,
                "is_required": True,
            },
        )
        assert item.status_code == 201, item.text

    return admin_client.get(f"/api/v1/pages/{application.alias}/1"), page_id


class TestBuildAndRender:
    def test_public_page_renders_html_without_a_session(self, built_page):
        response, _ = built_page

        assert response.status_code == 200
        assert "<!DOCTYPE html>" in response.text
        assert "Contact" in response.text

    def test_rendered_page_contains_the_form_controls(self, built_page):
        response, _ = built_page

        body = response.text
        assert "name='name'" in body or 'name="name"' in body
        assert "name='message'" in body or 'name="message"' in body

    def test_static_region_content_is_included(self, built_page):
        response, _ = built_page

        assert "Say hello" in response.text

    def test_form_posts_to_the_runtime_endpoint(self, built_page):
        """A rendered form must post somewhere that actually accepts it."""
        response, _ = built_page

        assert "action='/api/v1/pages/E2E/1'" in response.text
        assert "p_session_id" not in response.text
        assert "p_request" in response.text  # APEX-style submit flag is kept

    def test_page_sets_a_session_cookie(self, built_page):
        response, _ = built_page

        assert "miniui_session=" in response.headers.get("set-cookie", "")
        assert "HttpOnly" in response.headers.get("set-cookie", "")

    def test_preview_endpoint_renders_the_same_page(self, client, built_page, application):
        _, page_id = built_page

        response = client.get(f"/api/v1/app/{application.alias}/1")

        assert response.status_code == 200
        assert "Contact" in response.text
        assert "Page Items" in response.text
        assert page_id is not None


class TestSubmit:
    def test_submitting_the_form_redirects_back_to_the_page(
        self, client, built_page, application, session_id_of
    ):
        response, _ = built_page

        submit = client.post(
            f"/api/v1/pages/{application.alias}/1",
            data={"session_id": session_id_of(response), "name": "Ada", "message": "Hello there"},
            follow_redirects=False,
        )

        assert submit.status_code == 303
        assert submit.headers["location"] == "/api/v1/pages/E2E/1"

    def test_submitted_values_are_kept_in_session_state(
        self, client, db, built_page, application, session_id_of
    ):
        response, _ = built_page
        session_id = session_id_of(response)

        client.post(
            f"/api/v1/pages/{application.alias}/1",
            data={"session_id": session_id, "name": "Ada", "message": "Hello there"},
            follow_redirects=False,
        )

        service = SessionService(db)
        _, page_id = built_page
        assert service.get_item(session_id, page_id, "name") == "Ada"
        assert service.get_item(session_id, page_id, "message") == "Hello there"

    def test_apex_style_session_field_is_accepted(
        self, client, built_page, application, session_id_of
    ):
        response, _ = built_page

        submit = client.post(
            f"/api/v1/pages/{application.alias}/1",
            data={
                "p_session_id": session_id_of(response),
                "p_request": "SUBMIT",
                "name": "Ada",
                "message": "Hi",
            },
            follow_redirects=False,
        )

        assert submit.status_code == 303

    def test_process_redirect_is_honoured(self, client, db, built_page, application, session_id_of):
        response, _ = built_page
        session_id = session_id_of(response)
        _, page_id = built_page
        SessionService(db).set_item(session_id, page_id, "F_REDIRECT_URL", "/api/v1/pages/E2E/2")

        submit = client.post(
            f"/api/v1/pages/{application.alias}/1",
            data={"session_id": session_id, "name": "Ada", "message": "Hi"},
            follow_redirects=False,
        )

        assert submit.status_code == 303
        assert submit.headers["location"] == "/api/v1/pages/E2E/2"

    def test_failed_validation_returns_the_errors_without_redirecting(
        self, admin_client, client, db, application, session_id_of
    ):
        page = admin_client.post(
            "/api/v1/pages/builder/",
            json={"application_id": application.id, "name": "Validated", "page_number": 4, "is_public": True},
        )
        page_id = page.json()["id"]
        admin_client.post("/api/v1/items/", json={"page_id": page_id, "name": "email", "item_type": "text"})
        admin_client.post(
            "/api/v1/validations/",
            json={
                "page_id": page_id,
                "item_name": "email",
                "validation_type": "NOT_NULL",
                "error_message": "Email is required",
                "sequence": 1,
                "is_active": True,
            },
        )
        first = client.get(f"/api/v1/pages/{application.alias}/4")
        session_id = session_id_of(first)

        submit = client.post(
            f"/api/v1/pages/{application.alias}/4",
            data={"session_id": session_id, "email": ""},
            follow_redirects=False,
        )

        assert submit.status_code == 200
        payload = submit.json()
        assert payload["success"] is False
        assert payload["message"] == "Validation failed"
        errors = payload["validation_errors"]
        assert len(errors) == 1
        assert errors[0]["item_name"] == "email"
        assert errors[0]["message"] == "Email is required"

    def test_submit_to_unknown_page_is_404(self, admin_client, application):
        response = admin_client.post(f"/api/v1/pages/{application.alias}/99", data={})

        assert response.status_code == 404

    def test_submit_without_a_session_is_rejected(self, admin_client, db, application):
        page = admin_client.post(
            "/api/v1/pages/builder/",
            json={"application_id": application.id, "name": "Secret", "page_number": 2, "is_public": False},
        )
        assert page.status_code == 200, page.text

        assert admin_client.post(f"/api/v1/pages/{application.alias}/2", data={}).status_code == 401


class TestReportRegion:
    def test_report_renders_rows_from_its_query(
        self, admin_client, client, db, application, session_id_of
    ):
        page = admin_client.post(
            "/api/v1/pages/builder/",
            json={"application_id": application.id, "name": "List", "page_number": 3, "is_public": True},
        )
        page_id = page.json()["id"]
        admin_client.post("/api/v1/items/", json={"page_id": page_id, "name": "name", "item_type": "text"})
        admin_client.post(
            "/api/v1/regions/",
            json={
                "page_id": page_id,
                "name": "Rows",
                "region_type": "report",
                "template_options": {
                    "source": (
                        "SELECT item_value FROM apex_session_state "
                        f"WHERE page_id = {page_id} AND item_name = 'name'"
                    )
                },
            },
        )

        first = client.get(f"/api/v1/pages/{application.alias}/3")
        client.post(
            f"/api/v1/pages/{application.alias}/3",
            data={"session_id": session_id_of(first), "name": "Ada"},
            follow_redirects=False,
        )

        rendered = client.get(f"/api/v1/pages/{application.alias}/3")

        assert rendered.status_code == 200
        assert "Ada" in rendered.text


class TestCleanup:
    def test_deleting_a_page_removes_its_regions_and_items(
        self, admin_client, db, built_page, application
    ):
        _, page_id = built_page
        assert db.query(models.Region).filter(models.Region.page_id == page_id).count() == 2
        assert db.query(models.PageItem).filter(models.PageItem.page_id == page_id).count() == 2

        deleted = admin_client.delete(f"/api/v1/pages/builder/{page_id}")

        assert deleted.status_code == 200
        assert db.query(models.Page).filter(models.Page.id == page_id).first() is None
        assert db.query(models.Region).filter(models.Region.page_id == page_id).count() == 0
        assert db.query(models.PageItem).filter(models.PageItem.page_id == page_id).count() == 0
        assert admin_client.get(f"/api/v1/pages/{application.alias}/1").status_code == 404

    def test_developer_cannot_delete_a_page(self, client, db, make_user, built_page, application):
        _, page_id = built_page
        make_user("e2edev", role="DEVELOPER", password="StrongPass1!")
        token = client.post(
            "/api/v1/auth/login",
            data={
                "username": "e2edev",
                "password": "StrongPass1!",
                "application_id": str(application.id),
            },
        ).json()["access_token"]

        response = client.delete(
            f"/api/v1/pages/builder/{page_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 403