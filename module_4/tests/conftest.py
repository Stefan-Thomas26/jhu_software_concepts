"""
Shared fixtures for the Grad Café test suite.

All DB tests use a real PostgreSQL connection supplied via DATABASE_URL
(set by GitHub Actions / local .env).  No live internet calls are made.
"""
import os
import re
import sys
import decimal
import pytest
import psycopg

# ---------------------------------------------------------------------------
# Make sure the src package is importable when pytest is run from module_4/
# ---------------------------------------------------------------------------
SRC_DIR = os.path.join(os.path.dirname(__file__), "..", "src")
sys.path.insert(0, os.path.abspath(SRC_DIR))

import app as app_module


# ---------------------------------------------------------------------------
# DATABASE_URL helper
# ---------------------------------------------------------------------------
def _db_url():
    url = os.environ.get("DATABASE_URL")
    if not url:
        pytest.skip("DATABASE_URL not set — skipping DB test")
    return url


def _parse_db_url(url):
    """
    Parse ``postgresql://user:pass@host:port/dbname`` into a dict of kwargs
    accepted by psycopg.connect().
    """
    m = re.match(
        r"postgresql://(?P<user>[^:]+):(?P<password>[^@]+)"
        r"@(?P<host>[^:/]+)(?::(?P<port>\d+))?/(?P<dbname>.+)",
        url,
    )
    if not m:
        raise ValueError(f"Cannot parse DATABASE_URL: {url!r}")
    d = m.groupdict()
    kwargs = {k: v for k, v in d.items() if v is not None}
    if "port" in kwargs:
        kwargs["port"] = int(kwargs["port"])
    return kwargs


# ---------------------------------------------------------------------------
# Raw psycopg connection to the test database
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def db_conn():
    """Session-scoped psycopg connection to the test database."""
    url    = _db_url()
    kwargs = _parse_db_url(url)
    conn   = psycopg.connect(**kwargs)
    yield conn
    conn.close()


# ---------------------------------------------------------------------------
# Fresh applicants table for each DB test function
# ---------------------------------------------------------------------------
@pytest.fixture()
def clean_table(db_conn):
    """
    Drop and recreate the *applicants* table before each test, then drop it
    again on teardown.  Guarantees a completely empty starting state.
    """
    cur = db_conn.cursor()
    cur.execute("DROP TABLE IF EXISTS applicants;")
    cur.execute("""
        CREATE TABLE applicants (
            p_id                     INTEGER PRIMARY KEY,
            program                  TEXT,
            degreeType               TEXT,
            datePosted               DATE,
            status                   TEXT,
            statusDate               TEXT,
            semester                 TEXT,
            citizenship              TEXT,
            gpa                      FLOAT,
            gre                      FLOAT,
            gre_v                    FLOAT,
            gre_aw                   FLOAT,
            comment                  TEXT,
            url                      TEXT,
            llm_generated_program    TEXT,
            llm_generated_university TEXT
        );
    """)
    db_conn.commit()
    yield db_conn
    cur.execute("DROP TABLE IF EXISTS applicants;")
    db_conn.commit()
    cur.close()


# ---------------------------------------------------------------------------
# Minimal fake result set returned by QUERY_FN in Flask tests
# ---------------------------------------------------------------------------
FAKE_RESULTS = {
    "q1":  42,
    "q2":  decimal.Decimal("39.28"),
    "q3":  (decimal.Decimal("3.75"), decimal.Decimal("162.00"),
            decimal.Decimal("155.00"), decimal.Decimal("4.00")),
    "q4":  decimal.Decimal("3.80"),
    "q5":  decimal.Decimal("25.50"),
    "q6":  decimal.Decimal("3.90"),
    "q7":  10,
    "q8":  5,
    "q9":  7,
    "q10": [("Fall 2026", 100, 60, decimal.Decimal("60.00")),
            ("Fall 2025", 90,  50, decimal.Decimal("55.56"))],
    "q11": [("Accepted", 30, decimal.Decimal("3.85")),
            ("Rejected", 70, decimal.Decimal("3.60"))],
}


def fake_query_fn():
    """Return FAKE_RESULTS without touching the database."""
    return FAKE_RESULTS


def fake_loader_fn(filename):
    """No-op loader — does not touch the database."""
    pass


def fake_scraper_fn(scraper_path, llm_file):
    """No-op scraper — does not launch a subprocess."""
    pass


def error_query_fn():
    """Simulates a query failure."""
    raise RuntimeError("DB connection refused")


def error_loader_fn(filename):
    """Simulates a loader failure."""
    raise RuntimeError("Loader failed")


# ---------------------------------------------------------------------------
# Flask test clients
# ---------------------------------------------------------------------------
@pytest.fixture()
def client(request):
    """
    Standard test client with fake query/loader/scraper functions.
    Resets busy state before each test.
    """
    app_module._reset_state()
    flask_app = app_module.create_app({
        "TESTING":    True,
        "QUERY_FN":   fake_query_fn,
        "LOADER_FN":  fake_loader_fn,
        "SCRAPER_FN": fake_scraper_fn,
    })
    with flask_app.test_client() as c:
        yield c


@pytest.fixture()
def client_no_db():
    """Test client where QUERY_FN raises — simulates missing database."""
    app_module._reset_state()
    flask_app = app_module.create_app({
        "TESTING":    True,
        "QUERY_FN":   error_query_fn,
        "LOADER_FN":  fake_loader_fn,
        "SCRAPER_FN": fake_scraper_fn,
    })
    with flask_app.test_client() as c:
        yield c


@pytest.fixture()
def client_error_loader():
    """Test client where LOADER_FN raises — simulates loader failure."""
    app_module._reset_state()
    flask_app = app_module.create_app({
        "TESTING":    True,
        "QUERY_FN":   fake_query_fn,
        "LOADER_FN":  error_loader_fn,
        "SCRAPER_FN": fake_scraper_fn,
    })
    with flask_app.test_client() as c:
        yield c