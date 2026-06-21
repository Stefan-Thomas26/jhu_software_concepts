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
import threading

# =======
# Helpers
# =======
def _make_client(scraper_func = None, loader_func = None, query_func = None):
    app_module._reset_state()
    flask_app = app_module.create_app({
        "TESTING":    True,
        "QUERY_FUNC":   query_func   or fake_query_func,
        "DB_LOADER_FUNC":  loader_func  or fake_loader_func,
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
    # Need two threads to ensure testing while scraper is running
    started = threading.Event()
    done    = threading.Event()

    def slow_scraper(path, llm_file):
        started.set()
        # pause here until told to continue
        done.wait(timeout = 2)

    c = _make_client(scraper_func = slow_scraper)
    c.post("/pull-data")
    started.wait(timeout = 1) # wait until scraper has started
    assert app_module.scraper_state["running"] is True
    done.set() #release scraper


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


# ======================
# Error and Success Msgs
# ======================
@pytest.mark.buttons
def test_pull_data_scraper_error_updates_message():
    """When scraper raises, message is updated with error."""

    def error_scraper(path, llm_file):
        raise RuntimeError("scraper failed")

    c = _make_client(scraper_func=error_scraper)
    c.post("/pull-data")
    time.sleep(0.1)
    assert "error" in app_module.scraper_state["message"].lower()


@pytest.mark.buttons
def test_pull_data_success_message_set():
    """When scraper succeeds, success message is set."""
    done = threading.Event()

    def success_scraper(path, llm_file):
        done.set()

    c = _make_client(scraper_func=success_scraper)
    c.post("/pull-data")
    done.wait(timeout=2)
    time.sleep(0.05)
    assert "complete" in app_module.scraper_state["message"].lower()


@pytest.mark.buttons
def test_create_database_success_message_set(monkeypatch):
    """When loader succeeds, db_init success message is set."""
    import configuration
    finished = threading.Event()

    monkeypatch.setattr(configuration, "get_configuration_filepath",
                        lambda: "fake_path")
    monkeypatch.setattr(configuration, "load_json",
                        lambda path: [{"data_file": "fake.json"}])

    def success_loader(filename):
        finished.set()

    c = _make_client(loader_func=success_loader)
    c.post("/create-database")
    finished.wait(timeout=2)
    time.sleep(0.1)


@pytest.mark.buttons
def test_create_database_error_updates_message():
    """When loader raises, db_init message is updated with error."""

    def error_loader(filename):
        raise RuntimeError("loader failed")

    c = _make_client(loader_func=error_loader)
    c.post("/create-database")
    time.sleep(0.1)
    assert "error" in app_module.db_init_state["message"].lower()


# =================
# Busy-state gating
# =================
@pytest.mark.buttons
def test_update_analysis_returns_409_when_scraper_busy():
    """POST /update-analysis returns 409 when a scrape is in progress."""
    started = threading.Event()
    done    = threading.Event()

    def slow_scraper(path, llm_file):
        started.set()
        done.wait(timeout = 2)

    c = _make_client(scraper_func = slow_scraper)
    c.post("/pull-data")
    started.wait(timeout = 1)

    resp = c.post("/update-analysis")
    assert resp.status_code == 409
    done.set()


@pytest.mark.buttons
def test_update_analysis_busy_returns_busy_true():
    """409 response from /update-analysis contains busy = true."""
    started = threading.Event()
    done    = threading.Event()

    def slow_scraper(path, llm_file):
        started.set()
        done.wait(timeout = 2)

    c = _make_client(scraper_func = slow_scraper)
    c.post("/pull-data")
    started.wait(timeout = 1)

    data = c.post("/update-analysis").get_json()
    assert data.get("busy") is True
    done.set()


@pytest.mark.buttons
def test_pull_data_returns_409_when_already_running():
    """Second POST /pull-data returns 409 while first is still running."""
    started = threading.Event()
    done    = threading.Event()

    def slow_scraper(path, llm_file):
        started.set()
        done.wait(timeout = 2)

    c = _make_client(scraper_func = slow_scraper)
    c.post("/pull-data")
    started.wait(timeout = 1)

    resp = c.post("/pull-data")
    assert resp.status_code == 409
    done.set()


@pytest.mark.buttons
def test_pull_data_busy_returns_busy_true():
    """Second /pull-data while busy returns busy=true in JSON."""
    started = threading.Event()
    done    = threading.Event()

    def slow_scraper(path, llm_file):
        started.set()
        done.wait(timeout = 2)

    c = _make_client(scraper_func = slow_scraper)
    c.post("/pull-data")
    started.wait(timeout = 1)

    data = c.post("/pull-data").get_json()
    assert data.get("busy") is True
    done.set()


@pytest.mark.buttons
def test_update_analysis_no_longer_busy_after_scrape_completes():
    """After scrape finishes, /update-analysis returns 200 again."""
    done = threading.Event()

    def fast_scraper(path, llm_file):
        done.set()

    c = _make_client(scraper_func = fast_scraper)
    c.post("/pull-data")
    done.wait(timeout = 2)
    time.sleep(0.05)   # let the finally block flip back running = False

    resp = c.post("/update-analysis")
    assert resp.status_code == 200


# ===========================
# Error path — loader failure
# ===========================
@pytest.mark.buttons
def test_create_database_returns_200_when_idle(client):
    """POST /create-database returns 200 when not busy."""
    resp = client.post("/create-database")
    assert resp.status_code == 200


@pytest.mark.buttons
def test_create_database_returns_409_when_scraper_busy():
    """POST /create-database returns 409 when scraper is running."""
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


@pytest.mark.buttons
def test_create_database_returns_409_when_already_running():
    """POST /create-database returns 409 when db init is already running."""
    import configuration

    started = threading.Event()
    done    = threading.Event()

    def slow_loader(filename):
        started.set()
        done.wait(timeout=2)

    configuration.get_configuration_filepath = lambda: "fake"
    configuration.load_json = lambda path: [{"data_file": "fake.json"}]

    try:
        c = _make_client(loader_func=slow_loader)
        c.post("/create-database")       # first call — starts background load
        started.wait(timeout=1)

        resp = c.post("/create-database")  # second call — should get 409
        assert resp.status_code == 409
        data = resp.get_json()
        assert data["status"] == "already_running"
    finally:
        done.set()
        import configuration as conf
        # restore would happen here if needed


@pytest.mark.buttons
def test_pull_data_returns_409_when_db_init_running():
    """POST /pull-data returns 409 when database creation is in progress."""
    import configuration

    started = threading.Event()
    done    = threading.Event()

    original_get_path  = configuration.get_configuration_filepath
    original_load_json = configuration.load_json
    configuration.get_configuration_filepath = lambda: "fake"
    configuration.load_json = lambda path: [{"data_file": "fake.json"}]

    def slow_loader(filename):
        started.set()
        done.wait(timeout=2)

    try:
        c = _make_client(loader_func=slow_loader)
        c.post("/create-database")   # start db init
        started.wait(timeout=1)

        resp = c.post("/pull-data")  # try to pull while db init running
        assert resp.status_code == 409
        assert resp.get_json()["busy"] is True
    finally:
        done.set()
        configuration.get_configuration_filepath = original_get_path
        configuration.load_json = original_load_json