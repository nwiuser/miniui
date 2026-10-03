"""Liveness endpoint used by the Docker Compose / Kubernetes healthchecks."""


def test_health_reports_ok(client):
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "apexos-backend"
    assert body["version"]
    assert set(body["metadata_cache"]) >= {
        "entries",
        "hits",
        "misses",
        "ttl_seconds",
        "max_entries",
    }


def test_root_points_at_docs(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["docs"] == "/docs"
