"""
tests/test_analysis_format.py
==============================
Analysis output label and percentage-formatting tests.

Markers: analysis
"""
import re
import decimal
import pytest
from bs4 import BeautifulSoup
from conftest import FAKE_RESULTS, fake_loader_func, fake_query_func, fake_scraper_func
import app as app_module


TWO_DECIMAL_PCT_RE = re.compile(r"\d+\.\d{2}%")


# ================
# Helper Functions
# ================
def _soup(html_bytes):
    return BeautifulSoup(html_bytes, "html.parser")


def _get_analysis_page(client):
    resp = client.get("/analysis")
    assert resp.status_code == 200
    return resp.data


# ==============
# Answer: labels
# ==============
@pytest.mark.analysis
def test_page_contains_answer_labels(client):
    """Rendered page contains at least one 'Answer:' label."""
    html = _get_analysis_page(client)
    assert b"Answer:" in html


@pytest.mark.analysis
def test_page_contains_multiple_answer_labels(client):
    """Rendered page contains more than one 'Answer:' label (one per question)."""
    html   = _get_analysis_page(client)
    count  = html.count(b"Answer:")
    assert count >= 5, f"Expected >= 5 'Answer:' labels, found {count}"


@pytest.mark.analysis
def test_q1_answer_label_present(client):
    """Q1 card includes an 'Answer:' label."""
    soup = _soup(_get_analysis_page(client))
    q1   = soup.find(id="q1")
    assert q1 is not None
    assert "Answer:" in q1.get_text()


@pytest.mark.analysis
def test_q2_answer_label_present(client):
    """Q2 card includes an 'Answer:' label."""
    soup = _soup(_get_analysis_page(client))
    q2   = soup.find(id="q2")
    assert q2 is not None
    assert "Answer:" in q2.get_text()


@pytest.mark.analysis
def test_q5_answer_label_present(client):
    """Q5 card includes an 'Answer:' label."""
    soup = _soup(_get_analysis_page(client))
    q5   = soup.find(id="q5")
    assert q5 is not None
    assert "Answer:" in q5.get_text()


# ==========================================================
# Percentage formatting — must be exactly two decimal places
# ==========================================================
@pytest.mark.analysis
def test_percentages_have_two_decimals(client):
    """All percentages on the page are formatted with exactly two decimal places."""
    html = _get_analysis_page(client).decode("utf-8")
    # Find all percentage patterns
    all_pcts = re.findall(r"(\d+(?:\.\d+)?)%", html)
    for pct_str in all_pcts:
        parts = pct_str.split(".")
        decimals = len(parts[1]) if len(parts) == 2 else 0
        assert decimals == 2, (
            f"Percentage '{pct_str}%' does not have exactly two decimal places"
        )


@pytest.mark.analysis
def test_q2_percentage_two_decimals(client):
    """Q2 (international %) is rendered with two decimal places."""
    soup = _soup(_get_analysis_page(client))
    q2   = soup.find(id = "q2")
    text = q2.get_text()
    assert TWO_DECIMAL_PCT_RE.search(text), \
        f"Two-decimal % not found in Q2 text: {text!r}"


@pytest.mark.analysis
def test_q5_percentage_two_decimals(client):
    """Q5 (acceptance rate) is rendered with two decimal places."""
    soup = _soup(_get_analysis_page(client))
    q5   = soup.find(id = "q5")
    text = q5.get_text()
    assert TWO_DECIMAL_PCT_RE.search(text), \
        f"Two-decimal % not found in Q5 text: {text!r}"


@pytest.mark.analysis
def test_q10_table_percentages_two_decimals(client):
    """Q10 rejection-rate table shows percentages with two decimal places."""
    soup  = _soup(_get_analysis_page(client))
    q10   = soup.find(id = "q10")
    pills = q10.find_all(class_ = "pill") if q10 else []
    assert len(pills) > 0, "No .pill elements found in Q10"
    for pill in pills:
        text = pill.get_text()
        assert TWO_DECIMAL_PCT_RE.search(text), \
            f"Two-decimal % not found in pill: {text!r}"


@pytest.mark.analysis
def test_fake_results_q2_value_rendered(client):
    """The fake Q2 value (39.28%) appears verbatim on the page."""
    html = _get_analysis_page(client).decode("utf-8")
    assert "39.28%" in html


@pytest.mark.analysis
def test_fake_results_q5_value_rendered(client):
    """The fake Q5 value (25.50%) appears verbatim on the page."""
    html = _get_analysis_page(client).decode("utf-8")
    assert "25.50%" in html


@pytest.mark.analysis
def test_update_analysis_json_has_results_key(client):
    """POST /update-analysis returns JSON with a 'results' key."""
    resp = client.post("/update-analysis")
    data = resp.get_json()
    assert "results" in data


@pytest.mark.analysis
def test_update_analysis_json_results_has_expected_keys(client):
    """The 'results' dict from /update-analysis contains all q1–q11 keys."""
    resp    = client.post("/update-analysis")
    results = resp.get_json()["results"]
    for key in [f"q{i}" for i in range(1, 12)]:
        assert key in results, f"Missing key {key!r} in results"


@pytest.mark.analysis
def test_no_data_shown_when_results_none(client_no_db):
    """Page still renders and shows fallback text when results are None."""
    resp = client_no_db.get("/analysis")
    assert resp.status_code == 200
    assert b"no-data" in resp.data or "—".encode("utf-8") in resp.data or b"N/A" in resp.data


@pytest.mark.analysis
def test_update_analysis_handles_none_values(client):
    """update_analysis serialises None values correctly."""
    results_with_none = {**FAKE_RESULTS, "q9": None}

    def query_with_none():
        return results_with_none

    app_module._reset_state()
    flask_app = app_module.create_app({
        "TESTING":        True,
        "QUERY_FUNC":     query_with_none,
        "DB_LOADER_FUNC": fake_loader_func,
        "SCRAPER_FUNC":   fake_scraper_func,
    })
    c = flask_app.test_client()
    resp = c.post("/update-analysis")
    data = resp.get_json()
    assert data["results"]["q9"] is None


@pytest.mark.analysis
def test_update_analysis_returns_500_on_query_error(client_no_db):
    """POST /update-analysis returns 500 when query raises."""
    resp = client_no_db.post("/update-analysis")
    assert resp.status_code == 500