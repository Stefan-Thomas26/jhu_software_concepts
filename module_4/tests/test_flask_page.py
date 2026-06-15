"""
tests/test_flask_page.py
========================
Flask App & Page Rendering tests.

Markers: web
"""
import pytest
from bs4 import BeautifulSoup
from conftest import fake_query_func, error_query_func
import app as app_module


# =======
# Helpers
# =======
def _soup(html_bytes):
    return BeautifulSoup(html_bytes, "html.parser")


# ====================
# App factory / config
# ====================
@pytest.mark.web
def test_create_app_returns_flask_app():
    """Check taht create_app() returns a Flask application instance."""
    from flask import Flask
    app_module._reset_state()
    flask_app = app_module.create_app({"TESTING": True,
                                       "QUERY_FUNC": fake_query_func})
    assert isinstance(flask_app, Flask)


@pytest.mark.web
def test_create_app_testing_flag():
    """TESTING config flag is propagated into the app."""
    app_module._reset_state()
    flask_app = app_module.create_app({"TESTING": True,
                                       "QUERY_FUNC": fake_query_func})
    assert flask_app.config["TESTING"] is True


@pytest.mark.web
def test_required_routes_registered():
    """All required routes are registered on the application."""
    app_module._reset_state()
    flask_app = app_module.create_app({"TESTING": True,
                                       "QUERY_FUNC": fake_query_func})
    rules = {r.rule for r in flask_app.url_map.iter_rules()}
    for routes in ["/", "/analysis", "/pull-data", "/update-analysis",
                     "/create-database", "/scraper-status", "/db-init-status"]:
        assert routes in rules, f"Route {routes!r} not found"


# =============
# GET /analysis
# =============
@pytest.mark.web
def test_analysis_returns_200(client):
    """GET /analysis returns HTTP 200."""
    resp = client.get("/analysis")
    assert resp.status_code == 200


@pytest.mark.web
def test_analysis_contains_analysis_heading(client):
    """Page text includes the word 'Analysis'."""
    resp = client.get("/analysis")
    assert b"Analysis" in resp.data


@pytest.mark.web
def test_analysis_contains_pull_data_button(client):
    """Page contains a 'Pull Data' button with correct data-testid."""
    soup = _soup(client.get("/analysis").data)
    btn  = soup.find("button", {"data-testid": "pull-data-btn"})
    assert btn is not None, "Pull Data button not found"
    assert "Pull Data" in btn.get_text()


@pytest.mark.web
def test_analysis_contains_update_analysis_button(client):
    """Page contains an 'Update Analysis' button with correct data-testid."""
    soup = _soup(client.get("/analysis").data)
    btn  = soup.find("button", {"data-testid": "update-analysis-btn"})
    assert btn is not None, "Update Analysis button not found"
    assert "Update Analysis" in btn.get_text()


@pytest.mark.web
def test_analysis_contains_answer_label(client):
    """Page text includes at least one 'Answer:' label."""
    resp = client.get("/analysis")
    assert b"Answer:" in resp.data


@pytest.mark.web
def test_index_route_also_works(client):
    """Root '/' route also returns 200."""
    resp = client.get("/")
    assert resp.status_code == 200


@pytest.mark.web
def test_analysis_graceful_when_db_missing(client_no_db):
    """Page still renders 200 even when the database is unavailable."""
    resp = client_no_db.get("/analysis")
    assert resp.status_code == 200


@pytest.mark.web
def test_analysis_page_has_grad_cafe_text(client):
    """Page contains 'Grad Café' branding text."""
    resp = client.get("/analysis")
    assert b"Grad" in resp.data


@pytest.mark.web
def test_scraper_status_route(client):
    """GET /scraper-status returns 200 with JSON."""
    resp = client.get("/scraper-status")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "running" in data
    assert "message" in data


@pytest.mark.web
def test_db_init_status_route(client):
    """GET /db-init-status returns 200 with JSON."""
    resp = client.get("/db-init-status")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "running" in data