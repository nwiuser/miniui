"""Tests for page processes and computations.

Two layers are covered:

* the ``/api/v1/processes`` and ``/api/v1/computations`` endpoints, which the
  builder uses to author server-side logic, and
* the execution engine inside ``RenderingService``, which actually runs them
  during ``show_page`` / ``accept_page``.

The engine branches were previously untested, so a process that silently did
nothing (a typo in a process type, a condition that never matched) could not be
detected.
"""

import pytest

from app.core.rendering.service import RenderingService
from app.core.session.service import SessionService
from app.db import models


def _process(db, page, name="Do thing", process_type="sql", code=None,
             execution_point="ON_SUBMIT_BEFORE_PROCESSING", sequence=10):
    process = models.PageProcess(
        page_id=page.id,
        name=name,
        process_type=process_type,
        process_code=code,
        execution_point=execution_point,
        execution_sequence=sequence,
        is_active=True,
    )
    db.add(process)
    db.commit()
    db.refresh(process)
    return process


def _computation(db, page, point="ON_LOAD", computation_type="STATIC_ASSIGNMENT",
                 item="P1_VALUE", value=None, condition_type=None,
                 condition_expression=None, sequence=1):
    computation = models.Computation(
        page_id=page.id,
        computation_point=point,
        computation_type=computation_type,
        computation_item=item,
        computation_value=value,
        computation_condition_type=condition_type,
        computation_condition_expression=condition_expression,
        sequence=sequence,
        is_active=True,
    )
    db.add(computation)
    db.commit()
    db.refresh(computation)
    return computation


class TestProcessExecution:
    def test_sql_process_inserts_a_row(self, db, make_app, make_page):
        app = make_app(alias="PROCSQL")
        page = make_page(app)
        _process(db, page, name="Insert log", process_type="sql",
                 code="INSERT INTO apex_applications (name, alias) "
                      "VALUES ('from process', 'PROCLOG1')")

        service = RenderingService(db)
        session_id = SessionService(db).create_session(app.id)
        service.accept_page(app.alias, page_number=1, session_id=session_id, form_data={})

        rows = db.query(models.Application).filter(
            models.Application.alias == "PROCLOG1"
        ).all()
        assert len(rows) == 1

    def test_sql_process_uses_substitution_strings(self, db, make_app, make_page):
        app = make_app(alias="PROCSUB")
        page = make_page(app)
        _process(db, page, process_type="sql",
                 code="INSERT INTO apex_page_items (page_id, name, item_type) VALUES ("
                      f"{page.id}, '&P1_NAME.', 'text')")

        item = models.PageItem(
            page_id=page.id, name="P1_NAME", item_type="text", is_active=True
        )
        db.add(item)
        db.commit()

        service = RenderingService(db)
        session_id = SessionService(db).create_session(app.id)
        service.accept_page(app.alias, page_number=1, session_id=session_id,
                            form_data={"P1_NAME": "SUBSTITUTED"})

        created = db.query(models.PageItem).filter(
            models.PageItem.name == "SUBSTITUTED"
        ).all()
        assert len(created) == 1

    def test_sql_process_with_empty_code_is_a_noop(self, db, make_app, make_page):
        app = make_app()
        page = make_page(app)
        _process(db, page, process_type="sql", code=None)

        service = RenderingService(db)
        session_id = SessionService(db).create_session(app.id)
        result = service.accept_page(app.alias, 1, session_id, {})

        assert result["success"] is True

    def test_broken_sql_reports_the_process_name(self, db, make_app, make_page):
        app = make_app()
        page = make_page(app)
        _process(db, page, name="Broken SQL", process_type="sql",
                 code="INSERT INTO table_that_does_not_exist (x) VALUES (1)")

        service = RenderingService(db)
        session_id = SessionService(db).create_session(app.id)

        with pytest.raises(Exception) as excinfo:
            service.accept_page(app.alias, 1, session_id, {})

        assert "Broken SQL" in str(excinfo.value)

    def test_plsql_process_runs_with_restricted_builtins(self, db, make_app, make_page):
        app = make_app()
        page = make_page(app)
        _process(db, page, process_type="plsql",
                 code="session_service.set_item(session_id, page_id, 'P1_RAN', 'yes')")

        service = RenderingService(db)
        session_id = SessionService(db).create_session(app.id)
        service.accept_page(app.alias, 1, session_id, {})

        assert SessionService(db).get_item(session_id, page.id, "P1_RAN") == "yes"

    def test_plsql_process_cannot_reach_the_filesystem(self, db, make_app, make_page):
        """The sandbox exposes a tiny builtin set; ``open`` must not be there."""
        app = make_app()
        page = make_page(app)
        _process(db, page, process_type="plsql", code="open('/etc/passwd')")

        service = RenderingService(db)
        session_id = SessionService(db).create_session(app.id)

        with pytest.raises(Exception) as excinfo:
            service.accept_page(app.alias, 1, session_id, {})

        assert "PL/SQL process" in str(excinfo.value)

    def test_unknown_process_type_is_ignored(self, db, make_app, make_page):
        app = make_app()
        page = make_page(app)
        _process(db, page, process_type="send_email", code="whatever")

        service = RenderingService(db)
        session_id = SessionService(db).create_session(app.id)
        result = service.accept_page(app.alias, 1, session_id, {})

        assert result["success"] is True

    def test_on_load_process_runs_on_show(self, db, make_app, make_page):
        app = make_app(alias="PROCONLOAD")
        page = make_page(app)
        _process(db, page, process_type="plsql", execution_point="ON_LOAD",
                 code="session_service.set_item(session_id, page_id, 'P1_LOADED', str(page_id))")

        service = RenderingService(db)
        result = service.show_page(app.alias, 1)

        assert SessionService(db).get_item(result["session_id"], page.id, "P1_LOADED") == str(page.id)

    def test_reset_pagination_resets_a_single_region(self, db, make_app, make_page):
        app = make_app()
        page = make_page(app)
        region = models.Region(page_id=page.id, name="R1", region_type="report",
                               position=1, is_active=True)
        db.add(region)
        db.commit()
        db.refresh(region)

        session_id = SessionService(db).create_session(app.id)
        session_service = SessionService(db)
        session_service.set_item(session_id, page.id, f"RP_{region.id}_ROW_OFFSET", 40)
        session_service.set_item(session_id, page.id, f"RP_{region.id}_SORT_COLUMN", "NAME")

        service = RenderingService(db)
        service._reset_pagination(
            _process(db, page, process_type="reset_pagination", code=str(region.id)),
            session_id,
            page.id,
        )

        assert session_service.get_item(session_id, page.id, f"RP_{region.id}_ROW_OFFSET") == "0"
        assert session_service.get_item(session_id, page.id, f"RP_{region.id}_SORT_COLUMN") == ""

    def test_reset_pagination_without_region_resets_all_reports(self, db, make_app, make_page):
        app = make_app()
        page = make_page(app)
        report = models.Region(page_id=page.id, name="Report", region_type="report",
                               position=1, is_active=True)
        form = models.Region(page_id=page.id, name="Form", region_type="form",
                             position=2, is_active=True)
        db.add_all([report, form])
        db.commit()
        db.refresh(report)

        session_id = SessionService(db).create_session(app.id)
        session_service = SessionService(db)
        session_service.set_item(session_id, page.id, f"RP_{report.id}_ROW_OFFSET", 25)
        session_service.set_item(session_id, page.id, f"RP_{form.id}_ROW_OFFSET", 25)

        service = RenderingService(db)
        service._reset_pagination(
            _process(db, page, process_type="reset_pagination", code=None),
            session_id,
            page.id,
        )

        assert session_service.get_item(session_id, page.id, f"RP_{report.id}_ROW_OFFSET") == "0"
        # Forms are not reports, so their pagination state is untouched.
        assert session_service.get_item(session_id, page.id, f"RP_{form.id}_ROW_OFFSET") == "25"

    def test_clear_cache_process_does_not_fail(self, db, make_app, make_page):
        app = make_app()
        page = make_page(app)

        service = RenderingService(db)
        session_id = SessionService(db).create_session(app.id)
        service._execute_single_process(
            _process(db, page, process_type="clear_cache", code=None), session_id, page.id
        )


class TestComputationExecution:
    def test_static_assignment_sets_the_item(self, db, make_app, make_page):
        app = make_app()
        page = make_page(app)
        _computation(db, page, point="ON_LOAD", item="P1_GREETING", value="hello")

        service = RenderingService(db)
        result = service.show_page(app.alias, 1)

        assert SessionService(db).get_item(result["session_id"], page.id, "P1_GREETING") == "hello"

    def test_static_assignment_substitutes_session_values(self, db, make_app, make_page):
        app = make_app()
        page = make_page(app)
        _computation(db, page, point="ON_LOAD", item="P1_FULL",
                     value="&P1_FIRST. &P1_LAST.")

        service = RenderingService(db)
        session_id = SessionService(db).create_session(app.id)
        session_service = SessionService(db)
        session_service.set_item(session_id, page.id, "P1_FIRST", "Ada")
        session_service.set_item(session_id, page.id, "P1_LAST", "Lovelace")

        service.show_page(app.alias, 1, session_id=session_id)

        assert session_service.get_item(session_id, page.id, "P1_FULL") == "Ada Lovelace"

    def test_sql_query_computation_stores_first_column(self, db, make_app, make_page):
        app = make_app()
        page = make_page(app)
        _computation(db, page, point="ON_LOAD", computation_type="SQL_QUERY",
                     item="P1_COUNT", value="SELECT COUNT(*) FROM apex_applications")

        service = RenderingService(db)
        result = service.show_page(app.alias, 1)

        assert int(SessionService(db).get_item(result["session_id"], page.id, "P1_COUNT")) >= 1

    def test_sql_query_computation_with_no_rows_sets_empty_string(self, db, make_app, make_page):
        app = make_app()
        page = make_page(app)
        _computation(db, page, point="ON_LOAD", computation_type="SQL_QUERY",
                     item="P1_MISSING",
                     value="SELECT name FROM apex_applications WHERE alias = 'NO_SUCH_ALIAS'")

        service = RenderingService(db)
        result = service.show_page(app.alias, 1)

        assert SessionService(db).get_item(result["session_id"], page.id, "P1_MISSING") == ""

    def test_broken_sql_computation_names_the_item(self, db, make_app, make_page):
        app = make_app()
        page = make_page(app)
        _computation(db, page, point="ON_LOAD", computation_type="SQL_QUERY",
                     item="P1_BROKEN", value="SELECT * FROM nope_not_a_table")

        service = RenderingService(db)
        with pytest.raises(Exception) as excinfo:
            service.show_page(app.alias, 1)

        assert "P1_BROKEN" in str(excinfo.value)

    def test_plsql_computation_runs(self, db, make_app, make_page):
        app = make_app()
        page = make_page(app)
        _computation(db, page, point="ON_LOAD", computation_type="PLSQL_EXPRESSION",
                     item="P1_PL", value="session_service.set_item(session_id, page_id, 'P1_TOUCHED', '1')")

        service = RenderingService(db)
        result = service.show_page(app.alias, 1)

        assert SessionService(db).get_item(result["session_id"], page.id, "P1_TOUCHED") == "1"

    def test_condition_val_not_null_blocks_when_item_is_empty(self, db, make_app, make_page):
        app = make_app()
        page = make_page(app)
        _computation(db, page, point="ON_LOAD", item="P1_DERIVED", value="derived",
                     condition_type="VAL_NOT_NULL", condition_expression="P1_TRIGGER")

        service = RenderingService(db)
        result = service.show_page(app.alias, 1)
        session_service = SessionService(db)

        # No value for P1_TRIGGER yet: the computation must not run.
        assert session_service.get_item(result["session_id"], page.id, "P1_DERIVED") is None

        session_service.set_item(result["session_id"], page.id, "P1_TRIGGER", "go")
        service.show_page(app.alias, 1, session_id=result["session_id"])
        assert session_service.get_item(result["session_id"], page.id, "P1_DERIVED") == "derived"

    def test_on_new_instance_runs_once_per_session(self, db, make_app, make_page):
        app = make_app(alias="COMPNEW")
        page = make_page(app)
        read_tick = "session_service.get_item(session_id, page_id, 'P1_TICK') or 'first'"
        _computation(db, page, point="ON_NEW_INSTANCE", computation_type="PLSQL_EXPRESSION",
                     item="P1_TICK",
                     value=f"session_service.set_item(session_id, page_id, 'P1_TICK', {read_tick})")
        _computation(db, page, point="ON_LOAD", computation_type="PLSQL_EXPRESSION",
                     item="P1_TICK", sequence=2,
                     value=f"session_service.set_item(session_id, page_id, 'P1_TICK', ({read_tick}) + '-load')")

        service = RenderingService(db)
        session_service = SessionService(db)

        first = service.show_page(app.alias, 1)
        assert session_service.get_item(first["session_id"], page.id, "P1_TICK") == "first-load"

        second = service.show_page(app.alias, 1, session_id=first["session_id"])
        assert session_service.get_item(second["session_id"], page.id, "P1_TICK") == "first-load-load"

    def test_inactive_computations_are_skipped(self, db, make_app, make_page):
        app = make_app()
        page = make_page(app)
        computation = _computation(db, page, point="ON_LOAD", item="P1_SKIPPED", value="nope")
        computation.is_active = False
        db.commit()

        service = RenderingService(db)
        result = service.show_page(app.alias, 1)

        assert SessionService(db).get_item(result["session_id"], page.id, "P1_SKIPPED") is None


class TestProcessEndpoints:
    def test_crud_round_trip(self, client, auth_headers, make_app, make_page):
        app = make_app(alias="PROCAPI")
        page = make_page(app)
        headers = auth_headers(application=app)

        created = client.post("/api/v1/processes", json={
            "page_id": page.id,
            "name": "Insert audit",
            "process_type": "sql",
            "process_code": "INSERT INTO apex_page_processes (name, process_type) VALUES ('a','sql')",
        }, headers=headers)
        assert created.status_code == 201
        process_id = created.json()["id"]

        assert client.get(f"/api/v1/processes/{process_id}", headers=headers).json()["name"] == "Insert audit"

        listed = client.get(f"/api/v1/processes?page_id={page.id}", headers=headers).json()
        assert [p["id"] for p in listed] == [process_id]

        updated = client.put(f"/api/v1/processes/{process_id}",
                             json={"name": "Renamed"}, headers=headers)
        assert updated.status_code == 200
        assert updated.json()["name"] == "Renamed"

        assert client.delete(f"/api/v1/processes/{process_id}", headers=headers).status_code == 204
        assert client.get(f"/api/v1/processes/{process_id}", headers=headers).status_code == 404

    def test_end_user_cannot_create_process(self, client, auth_headers, make_app, make_page):
        app = make_app()
        page = make_page(app)
        headers = auth_headers(role="END_USER", application=app)

        response = client.post("/api/v1/processes", json={
            "page_id": page.id, "name": "Nope", "process_type": "sql",
        }, headers=headers)

        assert response.status_code == 403

    def test_end_user_cannot_delete_process(self, client, auth_headers, make_app, make_page):
        app = make_app()
        page = make_page(app)
        headers = auth_headers(role="END_USER", application=app)

        created = client.post("/api/v1/processes", json={
            "page_id": page.id, "name": "Admin made", "process_type": "sql",
        }, headers=auth_headers(role="ADMIN", application=app)).json()

        response = client.delete(f"/api/v1/processes/{created['id']}", headers=headers)
        assert response.status_code == 403

    def test_unknown_page_returns_404(self, client, auth_headers, make_app):
        app = make_app()
        headers = auth_headers(application=app)

        response = client.post("/api/v1/processes", json={
            "page_id": 999999, "name": "Ghost", "process_type": "sql",
        }, headers=headers)

        assert response.status_code == 404

    def test_requires_authentication(self, client, make_app, make_page):
        app = make_app()
        page = make_page(app)

        assert client.get("/api/v1/processes").status_code == 401
        assert client.post("/api/v1/processes", json={
            "page_id": page.id, "name": "Anon", "process_type": "sql",
        }).status_code == 401


class TestComputationEndpoints:
    def test_crud_round_trip(self, client, auth_headers, make_app, make_page):
        app = make_app(alias="COMPAPI")
        page = make_page(app)
        headers = auth_headers(application=app)

        created = client.post("/api/v1/computations", json={
            "page_id": page.id,
            "computation_point": "ON_LOAD",
            "computation_type": "STATIC_ASSIGNMENT",
            "computation_item": "P1_TOTAL",
            "computation_value": "42",
        }, headers=headers)
        assert created.status_code == 201
        computation_id = created.json()["id"]

        assert client.get(f"/api/v1/computations/{computation_id}",
                          headers=headers).json()["computation_item"] == "P1_TOTAL"

        listed = client.get(f"/api/v1/computations?page_id={page.id}", headers=headers).json()
        assert [c["id"] for c in listed] == [computation_id]

        updated = client.put(f"/api/v1/computations/{computation_id}",
                             json={"computation_value": "43"}, headers=headers)
        assert updated.json()["computation_value"] == "43"

        assert client.delete(f"/api/v1/computations/{computation_id}",
                             headers=headers).status_code == 204

    def test_end_user_cannot_create_computation(self, client, auth_headers, make_app, make_page):
        app = make_app()
        page = make_page(app)
        headers = auth_headers(role="END_USER", application=app)

        response = client.post("/api/v1/computations", json={
            "page_id": page.id,
            "computation_point": "ON_LOAD",
            "computation_type": "STATIC_ASSIGNMENT",
            "computation_item": "P1_X",
        }, headers=headers)

        assert response.status_code == 403

    def test_developer_cannot_delete_computation(self, client, auth_headers, make_app, make_page):
        app = make_app()
        page = make_page(app)
        created = client.post("/api/v1/computations", json={
            "page_id": page.id,
            "computation_point": "ON_LOAD",
            "computation_type": "STATIC_ASSIGNMENT",
            "computation_item": "P1_Y",
        }, headers=auth_headers(role="ADMIN", application=app)).json()

        response = client.delete(f"/api/v1/computations/{created['id']}",
                                 headers=auth_headers(role="DEVELOPER", application=app))
        assert response.status_code == 403

    def test_requires_authentication(self, client):
        assert client.get("/api/v1/computations").status_code == 401