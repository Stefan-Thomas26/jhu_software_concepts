"""
tests/test_integration_end_to_end.py
======================================
End-to-end integration tests: pull -> update -> render.

Markers: integration

DB tests require DATABASE_URL env var.
"""
import re
import decimal
import json
import os
import sys
import pytest
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

import app as app_module
import load_data
import query_data
import configuration
from conftest import (
    _parse_db_url, _db_url, fake_query_func, fake_publish_func,
    FAKE_RESULTS, error_query_func
)


TWO_DECIMAL_PCT_RE = re.compile(r"\d+\.\d{2}%")


# ===========
# DB patching
# ===========
@pytest.fixture(autouse=True)
def patch_config(monkeypatch):
    """Patch configuration to use DATABASE_URL for DB integration tests."""
    try:
        url = _db_url()
    except pytest.skip.Exception:
        return

    kwargs = _parse_db_url(url)
    user   = kwargs.get("user", "postgres")
    passw  = kwargs.get("password", "")
    host   = kwargs.get("host", "localhost")

    monkeypatch.setattr(configuration, "load_configuration_file",
                        lambda: (user, passw, host))

    import psycopg
    dbname = kwargs.get("dbname", "postgres")

    def patched_get_conn():
        return psycopg.connect(**kwargs)

    monkeypatch.setattr(query_data, "get_connection", patched_get_conn)

    original_load_into_db = load_data.load_into_db
    def patched_load_into_db(applicants, _ignored):
        original_load_into_db(applicants, dbname)
    monkeypatch.setattr(load_data, "load_into_db", patched_load_into_db)


# ==============
# Helper factory
# ==============
def _make_client(publish_func=None, query_func=None):
    """Create a test client with injectable functions."""
    flask_app = app_module.create_app({
        "TESTING":      True,
        "QUERY_FUNC":   query_func   or fake_query_func,
        "PUBLISH_FUNC": publish_func or fake_publish_func,
    })
    return flask_app.test_client()


# ======================
# Multi-record fake data
# ======================
MULTI_RECORD_DATA = [
    {"applicantNumber": 2001,
     "university": "MIT",
     "program": "Computer Science",
     "degreeType": "PhD",
     "datePosted": "Jan 10, 2025",
     "status": "Accepted",
     "statusDate": "Mar 01, 2025",
     "semester": "Fall 2026",
     "citizenship": "American",
     "gpa": 3.9,
     "gre": 167.0,
     "gre_v": 160.0,
     "gre_aw": 4.5,
     "comment": "",
     "url": "http://a.com/1",
     "llm_generated_program": "Computer Science",
     "llm_generated_university": "Massachusetts Institute of Technology"},

    {"applicantNumber": 2002,
     "university": "Stanford",
     "program": "Computer Science",
     "degreeType": "PhD",
     "datePosted": "Feb 05, 2025",
     "status": "Rejected",
     "statusDate": "Apr 01, 2025",
     "semester": "Fall 2026",
     "citizenship": "International",
     "gpa": 3.7,
     "gre": 163.0,
     "gre_v": 157.0,
     "gre_aw": 4.0,
     "comment": "",
     "url": "http://a.com/2",
     "llm_generated_program": "Computer Science",
     "llm_generated_university": "Stanford University"},

    {"applicantNumber": 2003,
     "university": "Carnegie Mellon",
     "program": "Computer Science",
     "degreeType": "PhD",
     "datePosted": "Mar 01, 2025",
     "status": "Accepted",
     "statusDate": "May 01, 2025",
     "semester": "Fall 2026",
     "citizenship": "American",
     "gpa": 3.95,
     "gre": 169.0,
     "gre_v": 162.0,
     "gre_aw": 5.0,
     "comment": "",
     "url": "http://a.com/3",
     "llm_generated_program": "Computer Science",
     "llm_generated_university": "Carnegie Mellon University"},
]


# =================================================
# E2E 1: pull -> update -> render (all fake, no DB)
# =================================================
@pytest.mark.integration
def test_e2e_pull_succeeds():
    """POST /pull-data returns 202 with queued status."""
    c    = _make_client()
    resp = c.post("/pull-data")
    assert resp.status_code == 202
    assert resp.get_json().get("status") == "queued"


@pytest.mark.integration
def test_e2e_update_succeeds():
    """POST /update-analysis returns 200."""
    c    = _make_client()
    resp = c.post("/update-analysis")
    assert resp.status_code == 200


@pytest.mark.integration
def test_e2e_render_shows_analysis_heading():
    """GET /analysis shows 'Analysis' heading."""
    c    = _make_client()
    resp = c.get("/analysis")
    assert b"Analysis" in resp.data


@pytest.mark.integration
def test_e2e_render_shows_answer_labels():
    """GET /analysis shows 'Answer:' labels with fake data injected."""
    c    = _make_client()
    resp = c.get("/analysis")
    assert b"Answer:" in resp.data


@pytest.mark.integration
def test_e2e_render_percentages_two_decimals():
    """GET /analysis renders all percentages with exactly two decimal places."""
    c    = _make_client()
    html = c.get("/analysis").data.decode("utf-8")
    pcts = re.findall(r"(\d+(?:\.\d+)?)%", html)
    for pct_str in pcts:
        parts    = pct_str.split(".")
        decimals = len(parts[1]) if len(parts) == 2 else 0
        assert decimals == 2, f"Bad precision: {pct_str}%"


@pytest.mark.integration
def test_e2e_update_analysis_returns_all_keys():
    """POST /update-analysis returns JSON with q1-q11 result keys."""
    c       = _make_client()
    results = c.post("/update-analysis").get_json()["results"]
    for key in [f"q{i}" for i in range(1, 12)]:
        assert key in results


@pytest.mark.integration
def test_e2e_pull_calls_publish():
    """POST /pull-data calls publish with scrape_new_data."""
    called = []

    def tracking_publish(kind, payload=None, headers=None):
        called.append(kind)

    c = _make_client(publish_func=tracking_publish)
    c.post("/pull-data")
    assert called == ["scrape_new_data"]


@pytest.mark.integration
def test_e2e_create_database_calls_publish():
    """POST /create-database calls publish with recompute_analytics."""
    called = []

    def tracking_publish(kind, payload=None, headers=None):
        called.append(kind)

    c = _make_client(publish_func=tracking_publish)
    c.post("/create-database")
    assert called == ["recompute_analytics"]


# ==============================
# E2E 2: real DB insert -> query
# ==============================
@pytest.mark.integration
def test_e2e_insert_rows_into_db(clean_table):
    """Rows inserted via load_into_db appear in the DB."""
    kwargs = _parse_db_url(_db_url())
    dbname = kwargs["dbname"]

    load_data.load_into_db(MULTI_RECORD_DATA, dbname)

    cur = clean_table.cursor()
    cur.execute("SELECT COUNT(*) FROM applicants;")
    count = cur.fetchone()[0]
    cur.close()
    assert count == len(MULTI_RECORD_DATA)


@pytest.mark.integration
def test_e2e_update_analysis_after_db_insert(clean_table):
    """After DB rows inserted, /update-analysis returns real query results."""
    kwargs = _parse_db_url(_db_url())
    dbname = kwargs["dbname"]
    load_data.load_into_db(MULTI_RECORD_DATA, dbname)

    flask_app = app_module.create_app({
        "TESTING":      True,
        "QUERY_FUNC":   query_data.run_all_queries,
        "PUBLISH_FUNC": fake_publish_func,
    })
    c    = flask_app.test_client()
    resp = c.post("/update-analysis")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "ok"
    assert "q1" in data["results"]


# =========================================
# E2E 3: multiple pulls - uniqueness policy
# =========================================
@pytest.mark.integration
def test_e2e_double_insert_no_duplicates(clean_table):
    """Inserting same data twice keeps row count consistent."""
    kwargs = _parse_db_url(_db_url())
    dbname = kwargs["dbname"]

    load_data.load_into_db(MULTI_RECORD_DATA, dbname)
    load_data.load_into_db(MULTI_RECORD_DATA, dbname)

    cur = clean_table.cursor()
    cur.execute("SELECT COUNT(*) FROM applicants;")
    count = cur.fetchone()[0]
    cur.close()
    assert count == len(MULTI_RECORD_DATA)


@pytest.mark.integration
def test_e2e_overlapping_insert_no_duplicates(clean_table):
    """Overlapping data results in correct unique row count."""
    kwargs = _parse_db_url(_db_url())
    dbname = kwargs["dbname"]

    first_batch  = MULTI_RECORD_DATA[:2]
    second_batch = MULTI_RECORD_DATA[1:]  # 1 overlap + 1 new

    load_data.load_into_db(first_batch,  dbname)
    load_data.load_into_db(second_batch, dbname)

    cur = clean_table.cursor()
    cur.execute("SELECT COUNT(*) FROM applicants;")
    count = cur.fetchone()[0]
    cur.close()
    assert count == len(MULTI_RECORD_DATA)


# ==================
# E2E 4: error paths
# ==================
@pytest.mark.integration
def test_e2e_query_error_returns_500(client_no_db):
    """When QUERY_FUNC raises, POST /update-analysis returns 500."""
    resp = client_no_db.post("/update-analysis")
    assert resp.status_code == 500


@pytest.mark.integration
def test_e2e_broker_down_returns_503():
    """When publish raises, POST /pull-data returns 503."""
    def error_publish(kind, payload=None, headers=None):
        raise RuntimeError("broker down")

    c    = _make_client(publish_func=error_publish)
    resp = c.post("/pull-data")
    assert resp.status_code == 503


@pytest.mark.integration
def test_e2e_render_after_update_shows_correct_values():
    """GET /analysis shows correct fake values after update."""
    c    = _make_client()
    html = c.get("/analysis").data.decode("utf-8")
    assert "39.28%" in html
    assert "25.50%" in html


@pytest.mark.integration
def test_e2e_pull_then_update_then_render():
    """Full pull -> update -> render flow works end to end."""
    c = _make_client()

    # Step 1 - pull
    resp = c.post("/pull-data")
    assert resp.status_code == 202

    # Step 2 - update
    resp = c.post("/update-analysis")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"

    # Step 3 - render
    resp = c.get("/analysis")
    assert resp.status_code == 200
    assert b"Answer:" in resp.data
