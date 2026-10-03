"""Tests for the Phase 7 cache layer and the hot-path indexes.

The cache is deliberately tiny (a dict with deadlines). What matters is that it
expires on its own, that ``get_or_set`` only calls the factory on a miss, and
that the metadata endpoint actually uses it. The index tests assert the
declarations in ``app.db.models`` reach PostgreSQL, since a missing FK index is
invisible until the table is large.
"""

import threading
import time

import pytest
from sqlalchemy import text

from app.core.cache import TTLCache, application_metadata_cache


@pytest.fixture(autouse=True)
def clean_metadata_cache():
    """The cache is a module-level singleton; never leak state between tests."""
    application_metadata_cache.clear()
    original_ttl = application_metadata_cache.ttl_seconds
    yield
    application_metadata_cache.ttl_seconds = original_ttl
    application_metadata_cache.clear()


class TestTTLCache:
    def test_set_then_get_returns_the_value(self):
        cache = TTLCache(ttl_seconds=60)

        cache.set("k", {"a": 1})

        assert cache.get("k") == {"a": 1}

    def test_missing_key_returns_none_and_counts_a_miss(self):
        cache = TTLCache(ttl_seconds=60)

        assert cache.get("nope") is None
        assert cache.stats()["misses"] == 1

    def test_entry_expires(self):
        cache = TTLCache(ttl_seconds=0.02)
        cache.set("k", "v")

        assert cache.get("k") == "v"
        time.sleep(0.2)
        assert cache.get("k") is None

    def test_get_or_set_only_calls_the_factory_on_a_miss(self):
        cache = TTLCache(ttl_seconds=60)
        calls = []

        def factory():
            calls.append(1)
            return "value"

        assert cache.get_or_set("k", factory) == "value"
        assert cache.get_or_set("k", factory) == "value"

        assert calls == [1]
        assert cache.stats()["hits"] == 1
        assert cache.stats()["misses"] == 1

    def test_get_or_set_recomputes_after_expiry(self):
        cache = TTLCache(ttl_seconds=0.02)
        calls = []

        def factory():
            calls.append(1)
            return len(calls)

        assert cache.get_or_set("k", factory) == 1
        time.sleep(0.2)
        assert cache.get_or_set("k", factory) == 2

    def test_invalidate_drops_one_key(self):
        cache = TTLCache(ttl_seconds=60)
        cache.set("a", 1)
        cache.set("b", 2)

        cache.invalidate("a")

        assert cache.get("a") is None
        assert cache.get("b") == 2

    def test_invalidate_prefix_drops_a_family(self):
        cache = TTLCache(ttl_seconds=60)
        cache.set("app:1", 1)
        cache.set("app:2", 2)
        cache.set("other", 3)

        removed = cache.invalidate_prefix("app:")

        assert removed == 2
        assert cache.stats()["entries"] == 1
        assert cache.get("other") == 3

    def test_max_entries_evicts_instead_of_growing(self):
        cache = TTLCache(ttl_seconds=60, max_entries=2)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)

        assert cache.stats()["entries"] == 2
        assert cache.get("c") == 3

    def test_clear_resets_counters(self):
        cache = TTLCache(ttl_seconds=60)
        cache.set("a", 1)
        cache.get("a")
        cache.get("missing")

        cache.clear()

        assert cache.stats() == {
            "entries": 0,
            "hits": 0,
            "misses": 0,
            "ttl_seconds": 60,
            "max_entries": 128,
        }

    def test_concurrent_access_does_not_corrupt_the_store(self):
        cache = TTLCache(ttl_seconds=60)
        errors = []

        def worker(n):
            try:
                for i in range(200):
                    cache.set((n, i), i)
                    cache.get((n, i))
                    cache.get_or_set(("shared", i % 5), lambda: n)
            except Exception as exc:  # pragma: no cover - only fails on a bug
                errors.append(exc)

        threads = [threading.Thread(target=worker, args=(n,)) for n in range(8)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        assert errors == []


class TestMetadataCache:
    def test_second_metadata_request_is_served_from_cache(
        self, client, auth_headers, make_app, make_page
    ):
        app = make_app()
        make_page(app, page_number=1)
        headers = auth_headers(application=app)

        first = client.get(f"/api/v1/applications/{app.id}/metadata", headers=headers)
        second = client.get(f"/api/v1/applications/{app.id}/metadata", headers=headers)

        assert first.status_code == second.status_code == 200
        assert first.json() == second.json()
        assert application_metadata_cache.stats()["hits"] >= 1

    def test_updating_an_application_invalidates_the_cache(
        self, client, auth_headers, make_app
    ):
        app = make_app(name="Before")
        headers = auth_headers(application=app)
        assert client.get(
            f"/api/v1/applications/{app.id}/metadata", headers=headers
        ).json()["application"]["name"] == "Before"

        updated = client.put(
            f"/api/v1/applications/{app.id}",
            json={"name": "After"},
            headers=headers,
        )
        assert updated.status_code == 200, updated.text

        assert client.get(
            f"/api/v1/applications/{app.id}/metadata", headers=headers
        ).json()["application"]["name"] == "After"

    def test_ttl_expiry_is_respected_by_the_endpoint(
        self, client, auth_headers, make_app, db
    ):
        app = make_app(name="Before")
        headers = auth_headers(application=app)
        application_metadata_cache.ttl_seconds = 0.05

        client.get(f"/api/v1/applications/{app.id}/metadata", headers=headers)

        app.name = "After"
        db.commit()
        time.sleep(0.2)

        body = client.get(f"/api/v1/applications/{app.id}/metadata", headers=headers).json()

        assert body["application"]["name"] == "After"

    def test_unknown_application_metadata_is_404(self, client, auth_headers):
        headers = auth_headers()

        response = client.get("/api/v1/applications/999999/metadata", headers=headers)

        assert response.status_code == 404


class TestHotPathIndexes:
    @pytest.mark.parametrize(
        "table, expected_index",
        [
            ("apex_pages", "ix_apex_pages_application_id_page_number"),
            ("apex_regions", "ix_apex_regions_page_id"),
            ("apex_page_items", "ix_apex_page_items_page_id"),
            ("apex_page_processes", "ix_apex_page_processes_page_id"),
            ("apex_computations", "ix_apex_computations_page_id"),
            ("apex_validations", "ix_apex_validations_page_id"),
            ("apex_sessions", "ix_apex_sessions_application_id"),
        ],
    )
    def test_index_exists_in_the_database(self, db, table, expected_index):
        rows = db.execute(
            text("SELECT indexname FROM pg_indexes WHERE tablename = :table"),
            {"table": table},
        ).fetchall()
        names = {row[0] for row in rows}

        assert expected_index in names, names


class TestRenderPerformance:
    def _build_page_with(self, client, headers, application, *, items, regions, page_number=1):
        page = client.post(
            "/api/v1/pages/builder/",
            json={
                "application_id": application.id,
                "name": "Perf",
                "page_number": page_number,
                "is_public": True,
            },
            headers=headers,
        ).json()
        for position in range(regions):
            client.post(
                "/api/v1/regions/",
                json={
                    "page_id": page["id"],
                    "name": f"Region {position}",
                    "region_type": "form" if position == 0 else "static_content",
                    "template_options": {"content": "<p>block</p>"},
                    "position": position,
                },
                headers=headers,
            )
        for index in range(items):
            client.post(
                "/api/v1/items/",
                json={
                    "page_id": page["id"],
                    "name": f"item_{index}",
                    "item_type": "text",
                    "label": f"Item {index}",
                },
                headers=headers,
            )
        return page

    @pytest.fixture
    def loaded(self, client, auth_headers, make_app):
        app = make_app(alias="PERF")
        return app, auth_headers(application=app)

    def test_rendering_a_large_page_stays_within_budget(self, client, loaded):
        application, headers = loaded
        page = self._build_page_with(client, headers, application, items=60, regions=8)

        started = time.perf_counter()
        for _ in range(5):
            response = client.get(f"/api/v1/pages/{application.alias}/{page['page_number']}")
            assert response.status_code == 200
            assert f"name='item_59'" in response.text or 'name="item_59"' in response.text
        elapsed = time.perf_counter() - started

        assert elapsed < 10.0, f"5 renders took {elapsed:.2f}s"

    def test_metadata_export_for_a_large_application_stays_within_budget(self, client, loaded):
        application, headers = loaded
        for page_number in range(1, 6):
            self._build_page_with(
                client, headers, application, items=40, regions=5, page_number=page_number
            )

        started = time.perf_counter()
        response = client.get(f"/api/v1/applications/{application.id}/metadata", headers=headers)
        elapsed = time.perf_counter() - started

        assert response.status_code == 200
        assert len(response.json()["pages"]) == 5
        assert elapsed < 10.0, f"metadata build took {elapsed:.2f}s"
