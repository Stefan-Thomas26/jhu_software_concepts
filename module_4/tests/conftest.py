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

# =========================================================================
# Make sure the src package is importable when pytest is run from module_4/
# =========================================================================
SRC_DIR = os.path.join(os.path.dirname(__file__), "..", "src")
sys.path.insert(0, os.path.abspath(SRC_DIR))

import app as app_module


# =============================
# Load Machine Environment file
# =============================
def _load_env_file():
    """Load .env file if it exists — so users don't need to export manually."""
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    env_path = os.path.abspath(env_path)
    
    if not os.path.exists(env_path):
        return
    
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                # Skip comment line
                continue
            
            if "=" in line:
                key, val = line.split("=", 1)
                os.environ.setdefault(key.strip(), val.strip())


_load_env_file()  # runs immediately when conftest is loaded


# ===================
# DATABASE_URL helper
# ===================
def _db_url():
    url = os.environ.get("DATABASE_URL")
    if not url:
        pytest.skip(
            "\n\nDATABASE_URL environment not set. To run DB tests:\n"
            "  1. Copy module_4/.env.example to module_4/.env\n"
            "  2. Fill in your PostgreSQL credentials\n"
            "  3. Re-run pytest\n"
        )
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


# ===========================================
# Raw psycopg connection to the test database
# ===========================================
@pytest.fixture(scope = "session", autouse = True)
def ensure_test_database():
    """
    Creates the test database if it does not already exist.
    Runs once per session before any other fixture.
    Skips silently if DATABASE_URL is not set.
    """
    url = os.environ.get("DATABASE_URL")
    if not url:
        return  # DB tests will skip themselves via _db_url()

    kwargs  = _parse_db_url(url)
    dbname  = kwargs.pop("dbname")  # remove target DB from kwargs
    
    # Connect to the default postgres database to create our test DB
    conn = psycopg.connect(**kwargs, dbname="postgres")
    conn.autocommit = True

    try:
        conn.execute(f"CREATE DATABASE {dbname}")
        print(f"\nCreated test database '{dbname}'")
    except psycopg.errors.DuplicateDatabase:
        print(f"\nTest database '{dbname}' already exists — skipping creation")
    finally:
        conn.close()

@pytest.fixture(scope = "session") #fixture runs once for entire test session, not once per test
def db_conn():
    """Session-scoped psycopg connection to the test database."""
    url    = _db_url()
    kwargs = _parse_db_url(url)
    conn   = psycopg.connect(**kwargs)
    yield conn
    # Teardown - last thing to run
    conn.close()


# ================================================
# Fresh applicants table for each DB test function
# ================================================
@pytest.fixture()
def clean_table(db_conn):
    """
    Drop and recreate the *applicants* table before each test, then drop it
    again on teardown.  Guarantees an empty database starting state.
    """
    cur = db_conn.cursor()
    cur.execute("DROP TABLE IF EXISTS applicants")
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
    yield db_conn #hand connection over to the test via 'yield'
    # Teardown
    cur.execute("DROP TABLE IF EXISTS applicants;")
    db_conn.commit()
    cur.close()


# =============================================================
# Minimal fake result set returned by QUERY_FUNC in Flask tests
# =============================================================
FAKE_RESULTS = {
    "q1":  42,
    "q2":  decimal.Decimal("39.28"),
    "q3":  (decimal.Decimal("3.75"),
            decimal.Decimal("162.00"),
            decimal.Decimal("155.00"),
            decimal.Decimal("4.00")),
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


def fake_query_func():
    """Return FAKE_RESULTS without touching the database."""
    return FAKE_RESULTS


def fake_loader_func(filename):
    """Do nothing loader — does not touch the database."""
    pass


def fake_scraper_func(scraper_path, llm_file):
    """Do nothing scraper — does not launch a subprocess."""
    pass


def error_query_func():
    """Tests a query failure."""
    raise RuntimeError("DB Query failure")


def error_loader_func(filename):
    """Tests a loader failure."""
    raise RuntimeError("Loader failed")


# ==================
# Flask test clients
# ==================
@pytest.fixture()
def client(request):
    """
    Standard test client with fake query/loader/scraper functions.
    Resets busy state before each test.
    """
    app_module._reset_state()
    flask_app = app_module.create_app({
        "TESTING":    True,
        "QUERY_FN":   fake_query_func,
        "LOADER_FN":  fake_loader_func,
        "SCRAPER_FN": fake_scraper_func,
    })
    with flask_app.test_client() as c:
        yield c


@pytest.fixture()
def client_no_db():
    """Test client where QUERY_FUNC raises — simulates missing database."""
    app_module._reset_state()
    flask_app = app_module.create_app({
        "TESTING":    True,
        "QUERY_FN":   error_query_func,
        "LOADER_FN":  fake_loader_func,
        "SCRAPER_FN": fake_scraper_func,
    })
    with flask_app.test_client() as c:
        yield c


@pytest.fixture()
def client_error_loader():
    """Test client where LOADER_FUNC raises — simulates loader failure."""
    app_module._reset_state()
    flask_app = app_module.create_app({
        "TESTING":    True,
        "QUERY_FN":   fake_query_func,
        "LOADER_FN":  error_loader_func,
        "SCRAPER_FN": fake_scraper_func,
    })
    with flask_app.test_client() as c:
        yield c