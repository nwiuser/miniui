import pytest
from app.db import models
from app.core.rendering.service import RenderingService


class TestShowPage:
    def test_show_page_returns_html(self, db_session, test_app, test_page):
        region = models.Region(
            page_id=test_page.id,
            name="Welcome",
            region_type="static_content",
            template_options={"content": "<h1>Hello World</h1>"},
            position=1,
            is_active=True,
        )
        db_session.add(region)
        db_session.commit()

        service = RenderingService(db_session)
        result = service.show_page(application_alias="TESTAPP", page_number=1)

        assert result["application_name"] == "Test App"
        assert result["page_name"] == "Home Page"
        assert "<h1>Hello World</h1>" in result["html"]
        assert result["session_id"] is not None
        assert len(result["regions"]) == 1

    def test_show_page_creates_session(self, db_session, test_app, test_page):
        service = RenderingService(db_session)
        result = service.show_page(application_alias="TESTAPP", page_number=1)

        session = db_session.query(models.Session).filter(
            models.Session.session_id == result["session_id"]
        ).first()
        assert session is not None
        assert session.application_id == test_app.id
        assert session.is_active is True

    def test_show_page_reuses_session(self, db_session, test_app, test_page):
        service = RenderingService(db_session)
        result1 = service.show_page(application_alias="TESTAPP", page_number=1)
        session_id = result1["session_id"]

        result2 = service.show_page(
            application_alias="TESTAPP", page_number=1, session_id=session_id
        )
        assert result2["session_id"] == session_id

    def test_show_page_invalid_app(self, db_session):
        service = RenderingService(db_session)
        with pytest.raises(Exception):
            service.show_page(application_alias="NONEXISTENT", page_number=1)

    def test_show_page_invalid_page(self, db_session, test_app):
        service = RenderingService(db_session)
        with pytest.raises(Exception):
            service.show_page(application_alias="TESTAPP", page_number=999)

    def test_show_page_with_items(self, db_session, test_app, test_page):
        item = models.PageItem(
            page_id=test_page.id,
            name="P1_NAME",
            alias="P_NAME",
            item_type="text",
            label="Name",
            placeholder="Enter name",
            is_active=True,
        )
        db_session.add(item)
        db_session.commit()

        svc = RenderingService(db_session)
        result = svc.show_page(application_alias="TESTAPP", page_number=1)

        assert result["application_name"] == "Test App"
        assert "session_id" in result

    def test_show_page_with_form_region(self, db_session, test_app, test_page):
        item = models.PageItem(
            page_id=test_page.id,
            name="P1_EMAIL",
            alias="P_EMAIL",
            item_type="text",
            label="Email",
            is_active=True,
        )
        db_session.add(item)

        region = models.Region(
            page_id=test_page.id,
            name="Contact Form",
            region_type="form",
            position=1,
            is_active=True,
        )
        db_session.add(region)
        db_session.commit()

        service = RenderingService(db_session)
        result = service.show_page(application_alias="TESTAPP", page_number=1)

        assert "P1_EMAIL" in result["html"]

    def test_show_page_default_item_values(self, db_session, test_app, test_page):
        item = models.PageItem(
            page_id=test_page.id,
            name="P1_STATUS",
            alias="P_STATUS",
            item_type="text",
            label="Status",
            default_value="ACTIVE",
            is_active=True,
        )
        db_session.add(item)
        db_session.commit()

        service = RenderingService(db_session)
        result = service.show_page(application_alias="TESTAPP", page_number=1)

        assert "ACTIVE" in result["item_values"].values() or result["item_values"].get("P1_STATUS") == "ACTIVE"


class TestAcceptPage:
    def test_accept_page_stores_values(self, db_session, test_app, test_page):
        item = models.PageItem(
            page_id=test_page.id,
            name="P1_NAME",
            alias="P_NAME",
            item_type="text",
            label="Name",
            is_active=True,
        )
        db_session.add(item)
        db_session.commit()

        service = RenderingService(db_session)
        result = service.show_page(application_alias="TESTAPP", page_number=1)
        session_id = result["session_id"]

        accept_result = service.accept_page(
            application_alias="TESTAPP",
            page_number=1,
            session_id=session_id,
            form_data={"P1_NAME": "John Doe"},
        )

        assert accept_result["success"] is True

        from app.core.session.service import SessionService
        ss = SessionService(db_session)
        value = ss.get_item(session_id, test_page.id, "P1_NAME")
        assert value == "John Doe"

    def test_accept_page_checkbox_handling(self, db_session, test_app, test_page):
        item = models.PageItem(
            page_id=test_page.id,
            name="P1_AGREE",
            alias="P_AGREE",
            item_type="checkbox",
            label="I Agree",
            is_active=True,
        )
        db_session.add(item)
        db_session.commit()

        service = RenderingService(db_session)
        result = service.show_page(application_alias="TESTAPP", page_number=1)
        session_id = result["session_id"]

        service.accept_page(
            application_alias="TESTAPP",
            page_number=1,
            session_id=session_id,
            form_data={"P1_AGREE": "on"},
        )

        from app.core.session.service import SessionService
        ss = SessionService(db_session)
        value = ss.get_item(session_id, test_page.id, "P1_AGREE")
        assert value == "Y"

    def test_accept_page_invalid_session(self, db_session, test_app, test_page):
        service = RenderingService(db_session)
        with pytest.raises(Exception):
            service.accept_page(
                application_alias="TESTAPP",
                page_number=1,
                session_id="invalid-session-id",
                form_data={},
            )

    def test_accept_page_redirect(self, db_session, test_app, test_page):
        service = RenderingService(db_session)
        result = service.show_page(application_alias="TESTAPP", page_number=1)
        session_id = result["session_id"]

        from app.core.session.service import SessionService
        ss = SessionService(db_session)
        ss.set_item(session_id, test_page.id, "F_REDIRECT_URL", "/TESTAPP/2")

        accept_result = service.accept_page(
            application_alias="TESTAPP",
            page_number=1,
            session_id=session_id,
            form_data={},
        )

        assert accept_result["redirect_url"] == "/TESTAPP/2"


class TestValidations:
    def test_not_null_validation(self, db_session, test_app, test_page):
        item = models.PageItem(
            page_id=test_page.id,
            name="P1_REQUIRED",
            alias="P_REQUIRED",
            item_type="text",
            label="Required Field",
            is_active=True,
        )
        db_session.add(item)

        validation = models.Validation(
            page_id=test_page.id,
            item_name="P1_REQUIRED",
            validation_type="NOT_NULL",
            error_message="This field is required",
            sequence=1,
            is_active=True,
        )
        db_session.add(validation)
        db_session.commit()

        service = RenderingService(db_session)
        result = service.show_page(application_alias="TESTAPP", page_number=1)
        session_id = result["session_id"]

        accept_result = service.accept_page(
            application_alias="TESTAPP",
            page_number=1,
            session_id=session_id,
            form_data={"P1_REQUIRED": ""},
        )

        assert accept_result["success"] is False
        assert len(accept_result["validation_errors"]) > 0

    def test_max_length_validation(self, db_session, test_app, test_page):
        item = models.PageItem(
            page_id=test_page.id,
            name="P1_SHORT",
            alias="P_SHORT",
            item_type="text",
            label="Short Field",
            is_active=True,
        )
        db_session.add(item)

        validation = models.Validation(
            page_id=test_page.id,
            item_name="P1_SHORT",
            validation_type="MAX_LENGTH",
            validation_expression="5",
            error_message="Too long",
            sequence=1,
            is_active=True,
        )
        db_session.add(validation)
        db_session.commit()

        service = RenderingService(db_session)
        result = service.show_page(application_alias="TESTAPP", page_number=1)
        session_id = result["session_id"]

        accept_result = service.accept_page(
            application_alias="TESTAPP",
            page_number=1,
            session_id=session_id,
            form_data={"P1_SHORT": "123456"},
        )

        assert accept_result["success"] is False

    def test_in_list_validation(self, db_session, test_app, test_page):
        item = models.PageItem(
            page_id=test_page.id,
            name="P1_COLOR",
            alias="P_COLOR",
            item_type="text",
            label="Color",
            is_active=True,
        )
        db_session.add(item)

        validation = models.Validation(
            page_id=test_page.id,
            item_name="P1_COLOR",
            validation_type="IN_LIST",
            validation_expression="red,green,blue",
            error_message="Must be red, green, or blue",
            sequence=1,
            is_active=True,
        )
        db_session.add(validation)
        db_session.commit()

        service = RenderingService(db_session)
        result = service.show_page(application_alias="TESTAPP", page_number=1)
        session_id = result["session_id"]

        accept_result = service.accept_page(
            application_alias="TESTAPP",
            page_number=1,
            session_id=session_id,
            form_data={"P1_COLOR": "yellow"},
        )

        assert accept_result["success"] is False


class TestSubstitutions:
    def test_substitute_app_session(self, db_session, test_app, test_page):
        service = RenderingService(db_session)
        result = service.show_page(application_alias="TESTAPP", page_number=1)
        session_id = result["session_id"]

        substituted = service._substitute_strings("&APP_SESSION.", session_id, test_page.id)
        assert substituted == session_id

    def test_substitute_item_value(self, db_session, test_app, test_page):
        item = models.PageItem(
            page_id=test_page.id,
            name="P1_NAME",
            alias="P_NAME",
            item_type="text",
            label="Name",
            is_active=True,
        )
        db_session.add(item)
        db_session.commit()

        service = RenderingService(db_session)
        result = service.show_page(application_alias="TESTAPP", page_number=1)
        session_id = result["session_id"]

        from app.core.session.service import SessionService
        ss = SessionService(db_session)
        ss.set_item(session_id, test_page.id, "P1_NAME", "Alice")

        substituted = service._substitute_strings("&P1_NAME.", session_id, test_page.id)
        assert substituted == "Alice"
