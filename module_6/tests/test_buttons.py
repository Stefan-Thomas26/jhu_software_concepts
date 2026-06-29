"""
tests/test_buttons.py
=====================
Button endpoint behavior tests.

Markers: buttons
"""
import pytest
from conftest import app_module


# =======
# Helpers
# =======
def fake_publish_func(kind, payload=None, headers=None):
    """Do nothing publisher — does not connect to RabbitMQ."""


def error_publish_func(kind, payload=None, headers=None):
    """Publisher that always fails — simulates broker down."""
    raise RuntimeError("RabbitMQ unavailable")


def _make_client(publish_func=None, query_func=None):
    """Create a test client with injectable functions."""
    from conftest import fake_query_func
    flask_app = app_module.create_app({
        "TESTING": True,
        "QUERY_FUNC": query_func or fake_query_func,
        "PUBLISH_FUNC": publish_func or fake_publish_func,
    })
    return flask_app.test_client()


# ===============
# POST /pull-data
# ===============
@pytest.mark.buttons
def test_pull_data_returns_202(client):
    """POST /pull-data returns 202 when task is queued."""
    resp = client.post("/pull-data")
    assert resp.status_code == 202


@pytest.mark.buttons
def test_pull_data_returns_queued_status(client):
    """POST /pull-data returns status='queued' in JSON body."""
    resp = client.post("/pull-data")
    data = resp.get_json()
    assert data.get("status") == "queued"


@pytest.mark.buttons
def test_pull_data_calls_publish_func():
    """POST /pull-data calls the injected publish function."""
    called = []

    def tracking_publish(kind, payload=None, headers=None):
        called.append(kind)

    c = _make_client(publish_func=tracking_publish)
    c.post("/pull-data")
    assert called == ["scrape_new_data"]


@pytest.mark.buttons
def test_pull_data_returns_503_when_broker_down():
    """POST /pull-data returns 503 when publish raises."""
    c = _make_client(publish_func=error_publish_func)
    resp = c.post("/pull-data")
    assert resp.status_code == 503


@pytest.mark.buttons
def test_pull_data_503_contains_error_status():
    """POST /pull-data 503 response contains status='error'."""
    c = _make_client(publish_func=error_publish_func)
    data = c.post("/pull-data").get_json()
    assert data.get("status") == "error"


# ====================
# POST /create-database
# ====================
@pytest.mark.buttons
def test_create_database_returns_202(client):
    """POST /create-database returns 202 when task is queued."""
    resp = client.post("/create-database")
    assert resp.status_code == 202


@pytest.mark.buttons
def test_create_database_returns_queued_status(client):
    """POST /create-database returns status='queued' in JSON body."""
    resp = client.post("/create-database")
    data = resp.get_json()
    assert data.get("status") == "queued"


@pytest.mark.buttons
def test_create_database_calls_publish_func():
    """POST /create-database calls publish with recompute_analytics."""
    called = []

    def tracking_publish(kind, payload=None, headers=None):
        called.append(kind)

    c = _make_client(publish_func=tracking_publish)
    c.post("/create-database")
    assert called == ["recompute_analytics"]


@pytest.mark.buttons
def test_create_database_returns_503_when_broker_down():
    """POST /create-database returns 503 when publish raises."""
    c = _make_client(publish_func=error_publish_func)
    resp = c.post("/create-database")
    assert resp.status_code == 503


@pytest.mark.buttons
def test_create_database_503_contains_error_status():
    """POST /create-database 503 response contains status='error'."""
    c = _make_client(publish_func=error_publish_func)
    data = c.post("/create-database").get_json()
    assert data.get("status") == "error"


# =========================
# GET/POST /update-analysis
# =========================
@pytest.mark.buttons
def test_update_analysis_returns_200_when_idle(client):
    """POST /update-analysis returns 200 when no task is running."""
    resp = client.post("/update-analysis")
    assert resp.status_code == 200


@pytest.mark.buttons
def test_update_analysis_get_returns_200_when_idle(client):
    """GET /update-analysis returns 200 when no task is running."""
    resp = client.get("/update-analysis")
    assert resp.status_code == 200


@pytest.mark.buttons
def test_update_analysis_returns_ok_status(client):
    """POST /update-analysis returns status='ok' in JSON body."""
    resp = client.post("/update-analysis")
    data = resp.get_json()
    assert data.get("status") == "ok"