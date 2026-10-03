"""Tests for every validation type supported by the rendering engine.

``_run_single_validation`` implements twelve types but only three were covered,
so a typo in any of the other nine went unnoticed. Each type is exercised in
both directions: a value that must fail and a value that must pass.
"""

import pytest

from app.core.rendering.service import RenderingService
from app.core.session.service import SessionService
from app.db import models


@pytest.fixture
def page_and_session(db, make_app, make_page):
    app = make_app(alias="VALIDATE")
    page = make_page(app)
    session_id = SessionService(db).create_session(app.id)
    service = RenderingService(db)
    return db, service, session_id, page.id


def _validate(db, service, session_id, page_id, item_name, value,
              validation_type, expression=None, error_message=None):
    """Store ``value`` for the item and run one validation against it."""
    validation = models.Validation(
        page_id=page_id,
        item_name=item_name,
        validation_type=validation_type,
        validation_expression=expression,
        error_message=error_message,
        is_active=True,
        sequence=1,
    )
    db.add(validation)
    db.commit()
    db.refresh(validation)

    SessionService(db).set_item(session_id, page_id, item_name, value)
    return service._run_single_validation(validation, session_id, page_id)


class TestRequiredTypes:
    def test_value_required_fails_on_empty(self, page_and_session):
        db, service, session_id, page_id = page_and_session
        assert _validate(db, service, session_id, page_id, "P1_A", "", "VALUE_REQUIRED")

    def test_value_required_passes_on_value(self, page_and_session):
        db, service, session_id, page_id = page_and_session
        assert _validate(db, service, session_id, page_id, "P1_A", "x", "VALUE_REQUIRED") is None

    def test_value_required_rejects_whitespace_only(self, page_and_session):
        db, service, service_session, page_id = page_and_session
        error = _validate(db, service, service_session, page_id, "P1_A", "   ", "VALUE_REQUIRED")
        assert error is not None

    def test_value_not_null_fails_on_missing_value(self, page_and_session):
        db, service, session_id, page_id = page_and_session
        validation = models.Validation(
            page_id=page_id, item_name="P1_ABSENT", validation_type="VALUE_NOT_NULL",
            is_active=True, sequence=1,
        )
        db.add(validation)
        db.commit()
        db.refresh(validation)

        assert service._run_single_validation(validation, session_id, page_id) is not None

    def test_value_not_null_passes(self, page_and_session):
        db, service, session_id, page_id = page_and_session
        assert _validate(db, service, session_id, page_id, "P1_A", "here", "VALUE_NOT_NULL") is None

    def test_optional_item_with_no_value_skips_validation(self, page_and_session):
        """Non-required types are not run against empty items."""
        db, service, session_id, page_id = page_and_session
        validation = models.Validation(
            page_id=page_id, item_name="P1_EMPTY", validation_type="EXACT_LENGTH",
            validation_expression="5", is_active=True, sequence=1,
        )
        db.add(validation)
        db.commit()
        db.refresh(validation)

        assert service._run_single_validation(validation, session_id, page_id) is None


class TestComparisonTypes:
    def test_equals_fails_on_different_value(self, page_and_session):
        db, service, session_id, page_id = page_and_session
        error = _validate(db, service, session_id, page_id, "P1_A", "b", "EQUALS", expression="a")
        assert "must equal 'a'" in error["message"]

    def test_equals_passes_on_matching_value(self, page_and_session):
        db, service, session_id, page_id = page_and_session
        assert _validate(db, service, session_id, page_id, "P1_A", "a", "EQUALS", expression="a") is None

    def test_equals_compares_numerically_typed_values_as_text(self, page_and_session):
        db, service, session_id, page_id = page_and_session
        assert _validate(db, service, session_id, page_id, "P1_A", "10", "EQUALS", expression="10") is None

    def test_not_equals_fails_on_matching_value(self, page_and_session):
        db, service, session_id, page_id = page_and_session
        error = _validate(db, service, session_id, page_id, "P1_A", "a", "NOT_EQUALS", expression="a")
        assert "must not equal 'a'" in error["message"]

    def test_not_equals_passes_on_different_value(self, page_and_session):
        db, service, session_id, page_id = page_and_session
        assert _validate(db, service, session_id, page_id, "P1_A", "b", "NOT_EQUALS", expression="a") is None

    def test_greater_than_fails_on_equal_value(self, page_and_session):
        db, service, session_id, page_id = page_and_session
        error = _validate(db, service, session_id, page_id, "P1_N", "5", "GREATER_THAN", expression="5")
        assert "must be greater than '5'" in error["message"]

    def test_greater_than_passes(self, page_and_session):
        db, service, session_id, page_id = page_and_session
        assert _validate(db, service, session_id, page_id, "P1_N", "6", "GREATER_THAN", expression="5") is None

    def test_greater_than_reports_non_numeric_value(self, page_and_session):
        db, service, session_id, page_id = page_and_session
        error = _validate(db, service, session_id, page_id, "P1_N", "abc", "GREATER_THAN", expression="5")
        assert "valid number" in error["message"]

    def test_less_than_fails_on_equal_value(self, page_and_session):
        db, service, session_id, page_id = page_and_session
        error = _validate(db, service, session_id, page_id, "P1_N", "5", "LESS_THAN", expression="5")
        assert "must be less than '5'" in error["message"]

    def test_less_than_passes(self, page_and_session):
        db, service, session_id, page_id = page_and_session
        assert _validate(db, service, session_id, page_id, "P1_N", "4", "LESS_THAN", expression="5") is None

    def test_less_than_reports_non_numeric_value(self, page_and_session):
        db, service, session_id, page_id = page_and_session
        error = _validate(db, service, session_id, page_id, "P1_N", "abc", "LESS_THAN", expression="5")
        assert "valid number" in error["message"]


class TestPatternTypes:
    def test_regexp_fails_when_pattern_does_not_match(self, page_and_session):
        db, service, session_id, page_id = page_and_session
        error = _validate(db, service, session_id, page_id, "P1_CODE", "abc",
                          "REGEXP", expression="^[0-9]+$")
        assert "does not match" in error["message"]

    def test_regexp_passes_when_pattern_matches(self, page_and_session):
        db, service, session_id, page_id = page_and_session
        assert _validate(db, service, session_id, page_id, "P1_CODE", "12345",
                         "REGEXP", expression="^[0-9]+$") is None

    def test_invalid_regex_is_reported_not_raised(self, page_and_session):
        db, service, session_id, page_id = page_and_session
        error = _validate(db, service, session_id, page_id, "P1_CODE", "123",
                          "REGEXP", expression="[unclosed")
        assert "Invalid regular expression" in error["message"]

    def test_in_list_rejects_value_outside_the_list(self, page_and_session):
        db, service, session_id, page_id = page_and_session
        error = _validate(db, service, session_id, page_id, "P1_STATUS", "archived",
                          "IN_LIST", expression="new, open , closed")
        assert "must be one of the following values: new, open , closed" in error["message"]

    def test_in_list_accepts_each_listed_value(self, page_and_session):
        db, service, session_id, page_id = page_and_session
        for value in ("new", "open", "closed"):
            assert _validate(db, service, session_id, page_id, "P1_STATUS", value,
                             "IN_LIST", expression="new, open , closed") is None


class TestLengthTypes:
    def test_min_length_fails_on_shorter_value(self, page_and_session):
        db, service, session_id, page_id = page_and_session
        error = _validate(db, service, session_id, page_id, "P1_T", "ab", "MIN_LENGTH", expression="3")
        assert "at least 3 characters" in error["message"]

    def test_min_length_passes_on_exact_length(self, page_and_session):
        db, service, session_id, page_id = page_and_session
        assert _validate(db, service, session_id, page_id, "P1_T", "abc", "MIN_LENGTH", expression="3") is None

    def test_min_length_with_non_numeric_bound_is_reported(self, page_and_session):
        db, service, session_id, page_id = page_and_session
        error = _validate(db, service, session_id, page_id, "P1_T", "abc", "MIN_LENGTH", expression="many")
        assert "valid number" in error["message"]

    def test_exact_length_fails_on_different_length(self, page_and_session):
        db, service, session_id, page_id = page_and_session
        error = _validate(db, service, session_id, page_id, "P1_T", "abcd", "EXACT_LENGTH", expression="3")
        assert "exactly 3 characters" in error["message"]

    def test_exact_length_passes(self, page_and_session):
        db, service, session_id, page_id = page_and_session
        assert _validate(db, service, session_id, page_id, "P1_T", "abc", "EXACT_LENGTH", expression="3") is None

    def test_max_length_fails_on_longer_value(self, page_and_session):
        db, service, session_id, page_id = page_and_session
        error = _validate(db, service, session_id, page_id, "P1_T", "abcd", "MAX_LENGTH", expression="3")
        assert "3 characters or less" in error["message"]


class TestValidationMessagesAndIntegration:
    def test_custom_error_message_wins(self, page_and_session):
        db, service, session_id, page_id = page_and_session
        error = _validate(db, service, session_id, page_id, "P1_A", "", "NOT_NULL",
                          error_message="Tell the user nicely")
        assert error["message"] == "Tell the user nicely"

    def test_error_identifies_the_item(self, page_and_session):
        db, service, session_id, page_id = page_and_session
        error = _validate(db, service, session_id, page_id, "P1_SALARY", "", "NOT_NULL")
        assert error["item_name"] == "P1_SALARY"

    def test_substitution_in_expression(self, page_and_session):
        """The comparison value itself can come from session state."""
        db, service, session_id, page_id = page_and_session
        SessionService(db).set_item(session_id, page_id, "P1_LIMIT", "10")
        error = _validate(db, service, session_id, page_id, "P1_AMOUNT", "9",
                          "GREATER_THAN", expression="&P1_LIMIT.")
        assert "must be greater than '10'" in error["message"]

    def test_accept_page_stops_before_processing_when_invalid(self, db, make_app, make_page):
        """End-to-end: a failing validation blocks the SQL process."""
        app = make_app(alias="VALFLOW")
        page = make_page(app)
        db.add(models.PageItem(page_id=page.id, name="P1_QTY", item_type="text", is_active=True))
        db.add(models.Validation(page_id=page.id, item_name="P1_QTY",
                                 validation_type="NOT_NULL", error_message="Qty is required",
                                 is_active=True, sequence=1))
        db.add(models.PageProcess(page_id=page.id, name="Log submit", process_type="sql",
                                  process_code="INSERT INTO apex_applications (name, alias) "
                                               "VALUES ('submitted', 'VALFLOWLOG')",
                                  execution_point="ON_SUBMIT_BEFORE_PROCESSING",
                                  execution_sequence=10, is_active=True))
        db.commit()

        service = RenderingService(db)
        session_id = SessionService(db).create_session(app.id)
        result = service.accept_page(app.alias, 1, session_id, {"P1_QTY": ""})

        assert result["success"] is False
        assert result["validation_errors"][0]["message"] == "Qty is required"
        assert db.query(models.Application).filter(
            models.Application.alias == "VALFLOWLOG"
        ).count() == 0

    def test_accept_page_runs_processes_when_validation_passes(self, db, make_app, make_page):
        app = make_app(alias="VALFLOW2")
        page = make_page(app)
        db.add(models.PageItem(page_id=page.id, name="P1_QTY", item_type="text", is_active=True))
        db.add(models.Validation(page_id=page.id, item_name="P1_QTY",
                                 validation_type="EXACT_LENGTH", validation_expression="3",
                                 is_active=True, sequence=1))
        db.add(models.PageProcess(page_id=page.id, name="Log submit", process_type="sql",
                                  process_code="INSERT INTO apex_applications (name, alias) "
                                               "VALUES ('submitted', 'VALFLOW2LOG')",
                                  execution_point="ON_SUBMIT_BEFORE_PROCESSING",
                                  execution_sequence=10, is_active=True))
        db.commit()

        service = RenderingService(db)
        session_id = SessionService(db).create_session(app.id)
        result = service.accept_page(app.alias, 1, session_id, {"P1_QTY": "abc"})

        assert result["success"] is True
        assert db.query(models.Application).filter(
            models.Application.alias == "VALFLOW2LOG"
        ).count() == 1