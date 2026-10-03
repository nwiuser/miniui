import pytest
from sqlalchemy import text

from app.core.region_types import form_region, render_report_region, render_static_content_region
from app.core.session.service import SessionService
from app.db import models


@pytest.fixture
def page_with_app(db_session, test_app, test_page):
    return test_page


@pytest.fixture
def session_id(db_session, test_app):
    return SessionService(db_session).create_session(test_app.id)


class TestStaticContentRegion:
    def test_renders_content_key(self, db_session, test_page):
        region = models.Region(
            page_id=test_page.id,
            name="Banner",
            region_type="static_content",
            template_options={"content": "<h1>Welcome</h1>"},
        )
        db_session.add(region)
        db_session.commit()
        db_session.refresh(region)

        html = render_static_content_region(region, db_session)
        assert "<h1>Welcome</h1>" in html
        assert "static-content-region" in html
        assert f"data-region-id='{region.id}'" in html

    def test_missing_options_placeholder(self, db_session, test_page):
        region = models.Region(
            page_id=test_page.id, name="Empty", region_type="static_content", template_options=None
        )
        db_session.add(region)
        db_session.commit()
        db_session.refresh(region)

        html = render_static_content_region(region, db_session)
        assert "No content defined" in html

    def test_json_string_options_are_parsed(self, db_session, test_page):
        region = models.Region(
            page_id=test_page.id,
            name="Json",
            region_type="static_content",
            template_options='{"content": "<p>from json</p>"}',
        )
        db_session.add(region)
        db_session.commit()
        db_session.refresh(region)

        html = render_static_content_region(region, db_session)
        assert "<p>from json</p>" in html

    def test_non_json_options_treated_as_raw_content(self, db_session, test_page):
        region = models.Region(
            page_id=test_page.id,
            name="Raw",
            region_type="static_content",
            template_options="<b>raw html</b>",
        )
        db_session.add(region)
        db_session.commit()
        db_session.refresh(region)

        html = render_static_content_region(region, db_session)
        assert "<b>raw html</b>" in html


class TestFormRegion:
    def test_renders_form_and_items(self, db_session, test_page, session_id):
        db_session.add(
            models.PageItem(
                page_id=test_page.id,
                name="P1_EMAIL",
                item_type="text",
                label="Email",
                is_active=True,
            )
        )
        region = models.Region(
            page_id=test_page.id, name="Form", region_type="form", is_active=True
        )
        db_session.add(region)
        db_session.commit()
        db_session.refresh(region)

        html = form_region(region, db_session, session_id, test_page.id)
        assert "<form class='apex-form'" in html
        assert "P1_EMAIL" in html
        assert f"value='{session_id}'" in html
        assert "p_request" in html

    def test_displays_session_value_over_default(self, db_session, test_page, session_id):
        item = models.PageItem(
            page_id=test_page.id,
            name="P1_NAME",
            item_type="text",
            default_value="DEFAULT",
            is_active=True,
        )
        db_session.add(item)
        region = models.Region(
            page_id=test_page.id, name="Form", region_type="form", is_active=True
        )
        db_session.add(region)
        db_session.commit()
        db_session.refresh(region)

        SessionService(db_session).set_item(session_id, test_page.id, "P1_NAME", "FROM_SESSION")

        html = form_region(region, db_session, session_id, test_page.id)
        assert "FROM_SESSION" in html
        assert "DEFAULT" not in html

    def test_falls_back_to_default_value(self, db_session, test_page, session_id):
        db_session.add(
            models.PageItem(
                page_id=test_page.id,
                name="P1_NAME",
                item_type="text",
                default_value="DEFAULT",
                is_active=True,
            )
        )
        region = models.Region(
            page_id=test_page.id, name="Form", region_type="form", is_active=True
        )
        db_session.add(region)
        db_session.commit()
        db_session.refresh(region)

        html = form_region(region, db_session, session_id, test_page.id)
        assert "DEFAULT" in html

    def test_inactive_items_are_skipped(self, db_session, test_page, session_id):
        db_session.add(
            models.PageItem(
                page_id=test_page.id,
                name="P1_HIDDEN_ITEM",
                item_type="text",
                is_active=False,
            )
        )
        region = models.Region(
            page_id=test_page.id, name="Form", region_type="form", is_active=True
        )
        db_session.add(region)
        db_session.commit()
        db_session.refresh(region)

        html = form_region(region, db_session, session_id, test_page.id)
        assert "P1_HIDDEN_ITEM" not in html

    @pytest.mark.parametrize(
        "item_type,expected",
        [
            ("text", "<input type='text'"),
            ("textarea", "<textarea"),
            ("select", "<select"),
            ("checkbox", "type='checkbox'"),
            ("radio", "type='radio'"),
            ("date_picker", "<input type='date'"),
            ("display_only", "form-display-only"),
            ("hidden", "<input type='hidden'"),
            ("password", "<input type='password'"),
            ("TOTALLY_UNKNOWN", "<input type='text'"),
        ],
    )
    def test_each_item_type_renders(
        self, db_session, test_page, session_id, item_type, expected
    ):
        db_session.add(
            models.PageItem(
                page_id=test_page.id,
                name="P1_X",
                item_type=item_type,
                is_active=True,
            )
        )
        region = models.Region(
            page_id=test_page.id, name="Form", region_type="form", is_active=True
        )
        db_session.add(region)
        db_session.commit()
        db_session.refresh(region)

        html = form_region(region, db_session, session_id, test_page.id)
        assert expected in html

    def test_creates_session_service_when_omitted(self, db_session, test_page, session_id):
        region = models.Region(
            page_id=test_page.id, name="Form", region_type="form", is_active=True
        )
        db_session.add(region)
        db_session.commit()
        db_session.refresh(region)

        html = form_region(region, db_session, session_id, test_page.id)
        assert "<form class='apex-form'" in html


class TestReportRegion:
    def _region(self, db_session, test_page, **options):
        region = models.Region(
            page_id=test_page.id,
            name="Report",
            region_type="report",
            template_options=options,
            is_active=True,
        )
        db_session.add(region)
        db_session.commit()
        db_session.refresh(region)
        return region

    def test_no_query_defined(self, db_session, test_page, session_id):
        region = self._region(db_session, test_page)
        html = render_report_region(region, db_session, session_id, test_page.id)
        assert "No SQL query defined" in html

    def test_renders_rows(self, db_session, test_page, session_id):
        db_session.execute(text("CREATE TABLE emp (id INTEGER, name TEXT)"))
        db_session.execute(text("INSERT INTO emp VALUES (1, 'Alice'), (2, 'Bob')"))
        db_session.commit()

        region = self._region(db_session, test_page, source="SELECT id, name FROM emp")
        html = render_report_region(region, db_session, session_id, test_page.id)

        assert "report-table" in html
        assert "Alice" in html
        assert "Bob" in html
        assert "Showing 1-2 of 2 rows" in html

    def test_pagination_limits_rows(self, db_session, test_page, session_id):
        db_session.execute(text("CREATE TABLE emp (id INTEGER, name TEXT)"))
        db_session.execute(
            text("INSERT INTO emp VALUES (1,'a'),(2,'b'),(3,'c'),(4,'d'),(5,'e')")
        )
        db_session.commit()

        region = self._region(
            db_session, test_page, source="SELECT id, name FROM emp", items_per_page=2
        )
        html = render_report_region(region, db_session, session_id, test_page.id)

        assert "Showing 1-2 of 5 rows" in html
        assert ">a<" in html
        assert ">e<" not in html

    def test_pagination_from_session_page_item(self, db_session, test_page, session_id):
        db_session.execute(text("CREATE TABLE emp (id INTEGER, name TEXT)"))
        db_session.execute(text("INSERT INTO emp VALUES (1,'a'),(2,'b'),(3,'c')"))
        db_session.commit()

        region = self._region(
            db_session,
            test_page,
            source="SELECT id, name FROM emp",
            items_per_page=1,
            page_item="P1_PAGE",
        )
        SessionService(db_session).set_item(session_id, test_page.id, "P1_PAGE", "2")

        html = render_report_region(region, db_session, session_id, test_page.id)
        assert "Showing 2-2 of 3 rows" in html
        assert ">b<" in html

    def test_pagination_state_written_to_session(self, db_session, test_page, session_id):
        db_session.execute(text("CREATE TABLE emp (id INTEGER)"))
        db_session.execute(text("INSERT INTO emp VALUES (1),(2)"))
        db_session.commit()

        region = self._region(
            db_session,
            test_page,
            source="SELECT id FROM emp",
            items_per_page=1,
            sort_column="id",
            sort_direction="DESC",
        )
        render_report_region(region, db_session, session_id, test_page.id)

        ss = SessionService(db_session)
        prefix = f"RP_{region.id}"
        assert ss.get_item(session_id, test_page.id, f"{prefix}_ROW_OFFSET") == "0"
        assert ss.get_item(session_id, test_page.id, f"{prefix}_SORT_COLUMN") == "id"
        assert ss.get_item(session_id, test_page.id, f"{prefix}_SORT_DIRECTION") == "DESC"
        assert ss.get_item(session_id, test_page.id, f"{prefix}_ROW_COUNT") == "1"

    def test_sorting_applied(self, db_session, test_page, session_id):
        db_session.execute(text("CREATE TABLE emp (id INTEGER, name TEXT)"))
        db_session.execute(text("INSERT INTO emp VALUES (1,'b'),(2,'a')"))
        db_session.commit()

        region = self._region(
            db_session,
            test_page,
            source="SELECT id, name FROM emp",
            sort_column="name",
            sort_direction="ASC",
        )
        html = render_report_region(region, db_session, session_id, test_page.id)
        assert html.index(">a<") < html.index(">b<")

    def test_invalid_sort_direction_falls_back_to_asc(self, db_session, test_page, session_id):
        db_session.execute(text("CREATE TABLE emp (id INTEGER, name TEXT)"))
        db_session.execute(text("INSERT INTO emp VALUES (1,'b'),(2,'a')"))
        db_session.commit()

        region = self._region(
            db_session,
            test_page,
            source="SELECT id, name FROM emp",
            sort_column="name",
            sort_direction="SIDEWAYS",
        )
        render_report_region(region, db_session, session_id, test_page.id)
        assert (
            SessionService(db_session).get_item(
                session_id, test_page.id, f"RP_{region.id}_SORT_DIRECTION"
            )
            == "ASC"
        )

    def test_sort_column_injection_is_ignored(self, db_session, test_page, session_id):
        db_session.execute(text("CREATE TABLE emp (id INTEGER)"))
        db_session.execute(text("INSERT INTO emp VALUES (1)"))
        db_session.commit()

        region = self._region(
            db_session,
            test_page,
            source="SELECT id FROM emp",
            sort_column="id; DROP TABLE emp",
        )
        html = render_report_region(region, db_session, session_id, test_page.id)
        assert "Error executing report query" not in html

    def test_query_error_is_reported_in_html(self, db_session, test_page, session_id):
        region = self._region(db_session, test_page, source="SELECT * FROM missing_table")
        html = render_report_region(region, db_session, session_id, test_page.id)
        assert "Error executing report query" in html

    def test_substitution_applies_to_query(self, db_session, test_page, session_id):
        db_session.execute(text("CREATE TABLE emp (id INTEGER, dept TEXT)"))
        db_session.execute(text("INSERT INTO emp VALUES (1, 'SALES'), (2, 'HR')"))
        db_session.commit()

        region = self._region(
            db_session, test_page, source="SELECT id FROM emp WHERE dept = '&P1_DEPT.'"
        )
        SessionService(db_session).set_item(session_id, test_page.id, "P1_DEPT", "HR")

        html = render_report_region(region, db_session, session_id, test_page.id)
        assert "Showing 1-1 of 1 rows" in html

    def test_query_key_aliases(self, db_session, test_page, session_id):
        db_session.execute(text("CREATE TABLE emp (id INTEGER)"))
        db_session.execute(text("INSERT INTO emp VALUES (1)"))
        db_session.commit()

        for key in ("source", "sql_query", "query"):
            region = models.Region(
                page_id=test_page.id,
                name=f"R{key}",
                region_type="report",
                template_options={key: "SELECT id FROM emp"},
                is_active=True,
            )
            db_session.add(region)
            db_session.commit()
            db_session.refresh(region)

            html = render_report_region(region, db_session, session_id, test_page.id)
            assert "No SQL query defined" not in html
            assert "report-table" in html
