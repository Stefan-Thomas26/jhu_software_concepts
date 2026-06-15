"""
tests/test_buttons.py
=====================
Button endpoint & busy-state behavior tests.

Markers: buttons
"""
import time
import pytest
import app as app_module
from conftest import fake_query_func, fake_loader_func, fake_scraper_func


# =======
# Helpers
# =======
def _make_client(scraper_func = None, loader_func = None, query_func = None):
    app_module._reset_state()
    flask_app = app_module.create_app({
        "TESTING":    True,
        "QUERY_FUNC":   query_func   or fake_query_func,
        "LOADER_FUNC":  loader_func  or fake_loader_func,
        "SCRAPER_FUNC": scraper_func or fake_scraper_func,
    })
    return flask_app.test_client()


# ===============
# POST /pull-data
# ===============
@pytest.mark.buttons
def test_pull_data_returns_200(client):
    """POST /pull-data returns 200 when not busy."""
    resp = client.post("/pull-data")
    assert resp.status_code == 200


@pytest.mark.buttons
def test_pull_data_returns_ok_true(client):
    """POST /pull-data response body contains ok=true."""
    resp = client.post("/pull-data")
    data = resp.get_json()
    assert data.get("ok") is True


@pytest.mark.buttons
def test_pull_data_triggers_scraper():
    """POST /pull-data calls the injected scraper function."""
    called = []

    def tracking_scraper(path, llm_file):
        called.append((path, llm_file))

    c = _make_client(scraper_func = tracking_scraper)
    c.post("/pull-data")
    # Give the background thread some time to start
    time.sleep(0.05)
    assert len(called) == 1, "Scraper was not called"


@pytest.mark.buttons
def test_pull_data_sets_running_state():
    """POST /pull-data sets scraper_state['running'] = True while running."""
    import threading
    # Need two threads to ensure testing while scraper is running
    started = threading.Event()
    done    = threading.Event()

    def slow_scraper(path, llm_file):
        started.set()
        # pause
        done.wait(timeout = 2)

    c = _make_client(scraper_func = slow_scraper)
    c.post("/pull-data")
    started.wait(timeout = 1)
    assert app_module.scraper_state["running"] is True
    done.set()


# ---------------------------------------------------------------------------
# GET/POST /update-analysis
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Busy-state gating
# ---------------------------------------------------------------------------
@pytest.mark.buttons
def test_update_analysis_returns_409_when_scraper_busy():
    """POST /update-analysis returns 409 when a scrape is in progress."""
    import threading
    started = threading.Event()
    done    = threading.Event()

    def slow_scraper(path, llm_file):
        started.set()
        done.wait(timeout=2)

    c = _make_client(scraper_func=slow_scraper)
    c.post("/pull-data")
    started.wait(timeout=1)

    resp = c.post("/update-analysis")
    assert resp.status_code == 409
    done.set()


@pytest.mark.buttons
def test_update_analysis_busy_returns_busy_true():
    """409 response from /update-analysis contains busy=true."""
    import threading
    started = threading.Event()
    done    = threading.Event()

    def slow_scraper(path, llm_file):
        started.set()
        done.wait(timeout=2)

    c = _make_client(scraper_func=slow_scraper)
    c.post("/pull-data")
    started.wait(timeout=1)

    data = c.post("/update-analysis").get_json()
    assert data.get("busy") is True
    done.set()


@pytest.mark.buttons
def test_pull_data_returns_409_when_already_running():
    """Second POST /pull-data returns 409 while first is still running."""
    import threading
    started = threading.Event()
    done    = threading.Event()

    def slow_scraper(path, llm_file):
        started.set()
        done.wait(timeout=2)

    c = _make_client(scraper_func=slow_scraper)
    c.post("/pull-data")
    started.wait(timeout=1)

    resp = c.post("/pull-data")
    assert resp.status_code == 409
    done.set()


@pytest.mark.buttons
def test_pull_data_busy_returns_busy_true():
    """Second /pull-data while busy returns busy=true in JSON."""
    import threading
    started = threading.Event()
    done    = threading.Event()

    def slow_scraper(path, llm_file):
        started.set()
        done.wait(timeout=2)

    c = _make_client(scraper_func=slow_scraper)
    c.post("/pull-data")
    started.wait(timeout=1)

    data = c.post("/pull-data").get_json()
    assert data.get("busy") is True
    done.set()


@pytest.mark.buttons
def test_update_analysis_no_longer_busy_after_scrape_completes():
    """After scrape finishes, /update-analysis returns 200 again."""
    import threading
    done = threading.Event()

    def fast_scraper(path, llm_file):
        done.set()

    c = _make_client(scraper_func=fast_scraper)
    c.post("/pull-data")
    done.wait(timeout=2)
    time.sleep(0.05)   # let the finally block flip running=False

    resp = c.post("/update-analysis")
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Error path — loader failure
# ---------------------------------------------------------------------------
@pytest.mark.buttons
def test_create_database_returns_200_when_idle(client):
    """POST /create-database returns 200 when not busy."""
    resp = client.post("/create-database")
    assert resp.status_code == 200


@pytest.mark.buttons
def test_create_database_returns_409_when_scraper_busy():
    """POST /create-database returns 409 when scraper is running."""
    import threading
    started = threading.Event()
    done    = threading.Event()

    def slow_scraper(path, llm_file):
        started.set()
        done.wait(timeout=2)

    c = _make_client(scraper_func = slow_scraper)
    c.post("/pull-data")
    started.wait(timeout=1)

    resp = c.post("/create-database")
    assert resp.status_code == 409
    done.set()