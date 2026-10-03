"""Tests for the ``crud`` data-access layer.

The endpoints were exercised through HTTP, which means most of ``crud`` was only
ever covered on the happy path of the one route that called it. These tests pin
the helpers directly, especially the ``skip``/``limit`` pagination and the
``*_by_application`` scoping that authorization depends on.
"""

import pytest

from app import crud
from app import schemas
from app.core.session.service import SessionService
from app.db import models


@pytest.fixture
def two_applications(db, make_app, make_page):
    """Two applications, the first with two pages and the second with one."""
    first = make_app(alias="CRUDA")
    second = make_app(alias="CRUDB")
    make_page(first, page_number=1, name="A1")
    make_page(first, page_number=2, name="A2")
    make_page(second, page_number=1, name="B1")
    return first, second


class TestPagination:
    def test_get_applications_respects_skip_and_limit(self, db, two_applications):
        everything = crud.get_applications(db)
        assert len(everything) == 2

        first_only = crud.get_applications(db, skip=0, limit=1)
        assert [app.alias for app in first_only] == ["CRUDA"]

        second_only = crud.get_applications(db, skip=1, limit=1)
        assert [app.alias for app in second_only] == ["CRUDB"]

    def test_skip_beyond_the_end_returns_nothing(self, db, two_applications):
        assert crud.get_applications(db, skip=99, limit=10) == []

    def test_get_pages_paginates(self, db, two_applications):
        assert len(crud.get_pages(db)) == 3
        assert len(crud.get_pages(db, limit=2)) == 2

    def test_get_users_and_lovs_paginate(self, db, make_user):
        for index in range(3):
            make_user(f"paginated{index}")
        crud.create_lov(db, schemas.LovCreate(lov_name="PAGED_LOV"))

        assert len(crud.get_workspace_users(db, limit=2)) == 2
        assert len(crud.get_lovs(db, limit=1)) == 1


class TestApplicationScoping:
    def test_pages_are_scoped_to_their_application(self, db, two_applications):
        first, second = two_applications

        first_pages = crud.get_pages_by_application(db, application_id=first.id)
        assert sorted(page.name for page in first_pages) == ["A1", "A2"]
        assert all(page.application_id == first.id for page in first_pages)

        second_pages = crud.get_pages_by_application(db, application_id=second.id)
        assert [page.name for page in second_pages] == ["B1"]

    def test_regions_are_scoped_through_their_pages(self, db, two_applications):
        first, second = two_applications
        db.add(models.Region(page_id=first.pages[0].id, name="R1", region_type="report",
                             position=1, is_active=True))
        db.add(models.Region(page_id=second.pages[0].id, name="R2", region_type="report",
                             position=1, is_active=True))
        db.commit()

        regions = crud.get_regions_by_application(db, application_id=first.id)

        assert [region.name for region in regions] == ["R1"]

    def test_validations_are_scoped_through_their_pages(self, db, two_applications):
        first, _ = two_applications
        db.add(models.Validation(page_id=first.pages[0].id, item_name="P1_X",
                                 validation_type="NOT_NULL", is_active=True))
        db.commit()

        validations = crud.get_validations_by_application(db, application_id=first.id)

        assert [validation.item_name for validation in validations] == ["P1_X"]

    def test_validations_by_item_filters_by_name(self, db, two_applications):
        first, _ = two_applications
        page = first.pages[0]
        db.add(models.Validation(page_id=page.id, item_name="P1_EMAIL",
                                 validation_type="NOT_NULL", is_active=True, sequence=1))
        db.add(models.Validation(page_id=page.id, item_name="P1_AGE",
                                 validation_type="NOT_NULL", is_active=True, sequence=2))
        db.commit()

        matches = crud.get_validations_by_item(db, page_id=page.id, item_name="P1_EMAIL")

        assert [validation.item_name for validation in matches] == ["P1_EMAIL"]

    def test_lovs_are_workspace_wide(self, db, two_applications):
        """LOVs have no application foreign key, so the filter is a no-op.

        Documented in ``crud.get_lovs_by_application``; asserted here so the
        behaviour is not mistaken for a bug later.
        """
        crud.create_lov(db, schemas.LovCreate(lov_name="GLOBAL_LOV"))

        assert len(crud.get_lovs_by_application(db, application_id=999)) == 1


class TestSingleRowLookups:
    def test_unknown_ids_return_none(self, db):
        assert crud.get_application(db, 999999) is None
        assert crud.get_page(db, 999999) is None
        assert crud.get_region(db, 999999) is None
        assert crud.get_item(db, 999999) is None
        assert crud.get_validation(db, 999999) is None
        assert crud.get_lov(db, 999999) is None
        assert crud.get_workspace_user(db, 999999) is None
        assert crud.get_session(db, "no-such-session") is None

    def test_updates_and_deletes_of_unknown_rows_return_none(self, db):
        assert crud.update_page(db, page_id=999999, page=schemas.PageUpdate(
            id=999999, application_id=1, name="Ghost")) is None
        assert crud.delete_page(db, page_id=999999) is None
        assert crud.update_lov(db, lov_id=999999, lov=schemas.LovUpdate(lov_name="Ghost")) is None
        assert crud.delete_lov(db, lov_id=999999) is None

    def test_lov_lookup_by_name(self, db):
        crud.create_lov(db, schemas.LovCreate(lov_name="STATUSES"))
        crud.create_lov(db, schemas.LovCreate(lov_name="STATIC2:Y;Yes,N;No", is_static=True))

        dynamic = crud.get_lov_by_name(db, "STATUSES")
        static = crud.get_lov_by_name(db, "STATIC2:Y;Yes,N;No")

        assert dynamic.is_static is False
        assert static.is_static is True

    def test_workspace_user_lookup_by_username(self, db, make_user):
        make_user("lookupme")

        assert crud.get_workspace_user_by_username(db, "lookupme").username == "lookupme"
        assert crud.get_workspace_user_by_username(db, "nobody") is None


class TestUpdateSemantics:
    def test_partial_update_leaves_other_columns_alone(self, db, make_app, make_page):
        app = make_app(alias="UPDAPP", description="Keep me")
        page = make_page(app, name="Before")

        crud.update_page(db, page_id=page.id,
                         page=schemas.PageUpdate(id=page.id, application_id=app.id, name="After"))

        db.refresh(page)
        assert page.name == "After"
        assert page.page_number == 1
        assert app.description == "Keep me"

    def test_update_applies_every_supplied_field(self, db, make_user):
        user = make_user("updateme")

        crud.update_workspace_user(
            db,
            user_id=user.id,
            user=schemas.WorkspaceUserUpdate(first_name="Ada", last_name="Lovelace"),
        )

        db.refresh(user)
        assert (user.first_name, user.last_name) == ("Ada", "Lovelace")
        assert user.username == "updateme"

    def test_delete_returns_the_deleted_row(self, db, make_app, make_page):
        app = make_app()
        page = make_page(app)

        deleted = crud.delete_page(db, page_id=page.id)

        assert deleted is not None and deleted.id == page.id
        assert crud.get_page(db, page_id=page.id) is None

    def test_creating_a_page_returns_a_refreshed_row(self, db, make_app):
        app = make_app()

        page = crud.create_page(db, schemas.PageCreate(
            application_id=app.id, name="Fresh", page_number=7))

        assert page.id is not None
        assert page.created_at is not None


class TestSessionLookups:
    def test_sessions_by_user(self, db, make_app, make_user):
        app = make_app()
        user = make_user("sessionowner")
        service = SessionService(db)
        first = service.create_session(app.id, user_id=user.id)
        second = service.create_session(app.id, user_id=user.id)

        active = crud.get_sessions_by_user(db, user_id=user.id)
        assert {session.session_id for session in active} == {first, second}

        db.query(models.Session).filter(
            models.Session.session_id == second
        ).update({"is_active": False}, synchronize_session=False)
        still_active = crud.get_sessions_by_user(db, user_id=user.id, is_active=True)
        assert [session.session_id for session in still_active] == [first]

    def test_most_recent_session_for_user_and_application(self, db, make_app, make_user):
        app_one = make_app(alias="SESS1")
        app_two = make_app(alias="SESS2")
        user = make_user("multiapp")
        service = SessionService(db)
        in_one = service.create_session(app_one.id, user_id=user.id)
        service.create_session(app_two.id, user_id=user.id)

        latest = crud.get_session_by_user_and_app(
            db, user_id=user.id, application_id=app_one.id)

        assert latest.session_id == in_one

    def test_no_sessions_returns_none(self, db, make_user):
        user = make_user("sessionless")

        assert crud.get_session_by_user_and_app(db, user_id=user.id) is None