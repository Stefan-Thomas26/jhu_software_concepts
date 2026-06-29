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
# Make sure the src package is importable when pytest is run from module_6/
# =========================================================================
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src/web/webapp")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src/web")))

import app as app_module
# Register so test files that do 'import app as app_module' get the same object
sys.modules["app"] = app_module


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
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                os.environ.setdefault(key.strip(), val.strip())


_load_env_file()


# ===================
# DATABASE_URL helper
# ===================
def _db_url():
    """Return DATABASE_URL or skip the test if not set."""
    url = os.environ.get("DATABASE_URL")
    if not url:
        pytest.skip(
            "\n\nDATABASE_URL environment not set. To run DB tests:\n"
            "  1. Copy .env.example to .env\n"
            "  2. Fill in your PostgreSQL credentials\n"
            "  3. Re-run pytest\n"
        )
    return url


def _parse_db_url(url):
    """
    Parse ``postgresql://user:pass@host:port/dbname`` into kwargs
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
@pytest.fixture(scope="session", autouse=True)
def ensure_test_database():
    """Create the test database if it does not already exist."""
    url = os.environ.get("DATABASE_URL")
    if not url:
        return

    kwargs = _parse_db_url(url)
    dbname = kwargs.pop("dbname")

    conn = psycopg.connect(**kwargs, dbname="postgres")
    conn.autocommit = True
    try:
        conn.execute(f"CREATE DATABASE {dbname}")
        print(f"\nCreated test database '{dbname}'")
    except psycopg.errors.DuplicateDatabase:
        print(f"\nTest database '{dbname}' already exists — skipping creation")
    finally:
        conn.close()


@pytest.fixture(scope="session")
def db_conn():
    """Session-scoped psycopg connection to the test database."""
    url = _db_url()
    kwargs = _parse_db_url(url)
    conn = psycopg.connect(**kwargs)
    yield conn
    conn.close()


# ================================================
# Fresh applicants table for each DB test function
# ================================================
@pytest.fixture()
def clean_table(db_conn):
    """Drop and recreate the applicants table before each test."""
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
    yield db_conn
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


def fake_publish_func(kind, payload=None, headers=None):
    """Do nothing publisher — does not connect to RabbitMQ."""


def error_query_func():
    """Simulate a query failure."""
    raise RuntimeError("DB Query failure")


# ==================
# Flask test clients
# ==================
@pytest.fixture()
def client():
    """Standard test client with fake query and publish functions."""
    flask_app = app_module.create_app({
        "TESTING": True,
        "QUERY_FUNC": fake_query_func,
        "PUBLISH_FUNC": fake_publish_func,
    })
    with flask_app.test_client() as c:
        yield c


@pytest.fixture()
def client_no_db():
    """Test client where QUERY_FUNC raises — simulates missing database."""
    flask_app = app_module.create_app({
        "TESTING": True,
        "QUERY_FUNC": error_query_func,
        "PUBLISH_FUNC": fake_publish_func,
    })
    with flask_app.test_client() as c:
        yield c