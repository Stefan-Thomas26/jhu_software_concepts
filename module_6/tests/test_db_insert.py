"""
tests/test_db_insert.py
========================
Database schema, insert, idempotency, and query function tests.

Markers: db

Requires DATABASE_URL env var pointing at a running PostgreSQL instance.
"""
import decimal
import pytest
import psycopg
from conftest import _parse_db_url, _db_url

# Make src known on python path
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from db import load_data
import query_data
import configuration


# ---------------------------------------------------------------------------
# Patch configuration so DB tests use DATABASE_URL, not userConfig.json
# ---------------------------------------------------------------------------
@pytest.fixture(autouse = True)
def patch_config(monkeypatch):
    """Override load_configuration_file() to use DATABASE_URL."""
    url    = _db_url()
    kwargs = _parse_db_url(url)
    user   = kwargs.get("user", "postgres")
    password  = kwargs.get("password", "")
    host   = kwargs.get("host", "localhost")

    monkeypatch.setattr(configuration, "load_configuration_file",
                        lambda: (user, password, host))

    # Also patch get_connection in query_data to use the test DB name
    original_get_conn = query_data.get_connection

    def patched_get_conn():
        return psycopg.connect(**kwargs)

    monkeypatch.setattr(query_data, "get_connection", patched_get_conn)

    # Patch load_into_db to use the test DB name
    dbname = kwargs.get("dbname", "postgres")

    original_load_into_db = load_data.load_into_db

    def patched_load_into_db(applicants, _ignored_name):
        original_load_into_db(applicants, dbname)

    monkeypatch.setattr(load_data, "load_into_db", patched_load_into_db)


# ========================
# Sample applicant records
# ========================
SAMPLE_APPLICANTS = [
    {
        "applicantNumber": 1001,
        "university":      "Johns Hopkins University",
        "program":         "Computer Science",
        "degreeType":      "Master",
        "datePosted":      "Jan 15, 2025",
        "status":          "Accepted",
        "statusDate":      "Mar 01, 2025",
        "semester":        "Fall 2026",
        "citizenship":     "American",
        "gpa":             3.85,
        "gre":             165.0,
        "gre_v":           158.0,
        "gre_aw":          4.5,
        "comment":         "Test applicant",
        "url":             "https://example.com/1",
        "llm_generated_program":    "Computer Science",
        "llm_generated_university": "Johns Hopkins University",
    },
    {
        "applicantNumber": 1002,
        "university":      "Stanford University",
        "program":         "Computer Science",
        "degreeType":      "PhD",
        "datePosted":      "Feb 10, 2025",
        "status":          "Rejected",
        "statusDate":      "Apr 01, 2025",
        "semester":        "Fall 2026",
        "citizenship":     "International",
        "gpa":             3.60,
        "gre":             160.0,
        "gre_v":           155.0,
        "gre_aw":          3.5,
        "comment":         "Another test applicant",
        "url":             "https://example.com/2",
        "llm_generated_program":    "Computer Science",
        "llm_generated_university": "Stanford University",
    },
]


# ========================
# Test: table starts empty
# ========================
@pytest.mark.db
def test_table_empty_before_insert(clean_table):
    """Applicants table is empty before any inserts."""
    cur = clean_table.cursor()
    cur.execute("SELECT COUNT(*) FROM applicants;")
    count = cur.fetchone()[0]
    cur.close()
    assert count == 0


# ===================================
# Test: rows are written after insert
# ===================================
@pytest.mark.db
def test_insert_adds_rows(clean_table):
    """After load_into_db(), the table contains the expected number of rows."""
    kwargs = _parse_db_url(_db_url())
    dbname = kwargs["dbname"]
    load_data.load_into_db(SAMPLE_APPLICANTS, dbname)

    cur = clean_table.cursor()
    cur.execute("SELECT COUNT(*) FROM applicants;")
    count = cur.fetchone()[0]
    cur.close()
    assert count == len(SAMPLE_APPLICANTS)


# ============================================
# Test: required (non-null) fields are present
# ============================================
@pytest.mark.db
def test_required_fields_non_null(clean_table):
    """Inserted rows have non-null values for all required schema fields."""
    kwargs = _parse_db_url(_db_url())
    dbname = kwargs["dbname"]
    load_data.load_into_db(SAMPLE_APPLICANTS, dbname)

    cur = clean_table.cursor()
    cur.execute("""
        SELECT p_id, program, degreeType, status, semester, citizenship
        FROM applicants;
    """)
    rows = cur.fetchall()
    cur.close()

    assert len(rows) == len(SAMPLE_APPLICANTS)
    for row in rows:
        for field in row:
            assert field is not None, f"Unexpected NULL in row: {row}"


# ==================================================================
# Test: idempotency — duplicate inserts do not create duplicate rows
# ==================================================================
@pytest.mark.db
def test_duplicate_insert_is_idempotent(clean_table):
    """Inserting the same data twice results in the same row count."""
    kwargs = _parse_db_url(_db_url())
    dbname = kwargs["dbname"]
    load_data.load_into_db(SAMPLE_APPLICANTS, dbname)
    load_data.load_into_db(SAMPLE_APPLICANTS, dbname)   # second pass

    cur = clean_table.cursor()
    cur.execute("SELECT COUNT(*) FROM applicants;")
    count = cur.fetchone()[0]
    cur.close()
    assert count == len(SAMPLE_APPLICANTS), \
        f"Expected {len(SAMPLE_APPLICANTS)} rows after duplicate insert, got {count}"

# =================
# Test insert error
# =================
@pytest.mark.db
def test_insert_error_is_handled_gracefully(clean_table):
    """Insert errors are caught and rolled back without crashing."""
    kwargs = _parse_db_url(_db_url())
    dbname = kwargs["dbname"]

    bad_applicant = [{
        "applicantNumber": None,  # violates PRIMARY KEY — triggers except branch
        "university":      "Test University",
        "program":         "Computer Science",
        "degreeType":      "Master",
        "datePosted":      None,
        "status":          "Accepted",
        "statusDate":      None,
        "semester":        "Fall 2026",
        "citizenship":     "American",
        "gpa":             3.5,
        "gre":             None,
        "gre_v":           None,
        "gre_aw":          None,
        "comment":         None,
        "url":             None,
        "llm_generated_program":    None,
        "llm_generated_university": None,
    }]

    # Should not raise even though the insert fails
    load_data.load_into_db(bad_applicant, dbname)

    # Table should still be empty — bad row was rolled back
    cur = clean_table.cursor()
    cur.execute("SELECT COUNT(*) FROM applicants;")
    count = cur.fetchone()[0]
    cur.close()
    assert count == 0


# =====================================
# Test: primary key constraint enforced
# =====================================
@pytest.mark.db
def test_primary_key_is_p_id(clean_table):
    """p_id is the primary key — inserting a duplicate p_id is silently skipped."""
    kwargs = _parse_db_url(_db_url())
    dbname = kwargs["dbname"]

    first = [SAMPLE_APPLICANTS[0]]
    modified = [{**SAMPLE_APPLICANTS[0], "status": "Rejected"}]  # same p_id, different status

    load_data.load_into_db(first,    dbname)
    load_data.load_into_db(modified, dbname)

    cur = clean_table.cursor()
    cur.execute("SELECT status FROM applicants WHERE p_id = 1001;")
    status = cur.fetchone()[0]
    cur.close()
    # ON CONFLICT DO NOTHING — original status preserved
    assert status == "Accepted"


# ====================================================
# Test: query function returns dict with expected keys
# ====================================================
@pytest.mark.db
def test_run_all_queries_returns_expected_keys(clean_table):
    """run_all_queries() returns a dict containing all q1–q11 keys."""
    kwargs = _parse_db_url(_db_url())
    dbname = kwargs["dbname"]
    load_data.load_into_db(SAMPLE_APPLICANTS, dbname)

    results = query_data.run_all_queries()
    for key in [f"q{i}" for i in range(1, 12)]:
        assert key in results, f"Key {key!r} missing from run_all_queries() result"


# =====================================================
# Test: individual query functions return correct types
# =====================================================
@pytest.mark.db
def test_q1_returns_integer(clean_table):
    """q1_fall2026_count returns an integer."""
    kwargs = _parse_db_url(_db_url())
    dbname = kwargs["dbname"]
    load_data.load_into_db(SAMPLE_APPLICANTS, dbname)

    conn   = psycopg.connect(**kwargs)
    cursor = conn.cursor()
    result = query_data.q1_fall2026_count(cursor)
    cursor.close()
    conn.close()
    assert isinstance(result, int)


@pytest.mark.db
def test_q2_returns_decimal_or_none(clean_table):
    """q2_international_percent returns a Decimal (or None if no data)."""
    kwargs = _parse_db_url(_db_url())
    dbname = kwargs["dbname"]
    load_data.load_into_db(SAMPLE_APPLICANTS, dbname)

    conn   = psycopg.connect(**kwargs)
    cursor = conn.cursor()
    result = query_data.q2_international_percent(cursor)
    cursor.close()
    conn.close()
    assert result is None or isinstance(result, decimal.Decimal)


@pytest.mark.db
def test_q3_returns_tuple(clean_table):
    """q3_average_scores returns a tuple of four values."""
    kwargs = _parse_db_url(_db_url())
    dbname = kwargs["dbname"]
    load_data.load_into_db(SAMPLE_APPLICANTS, dbname)

    conn   = psycopg.connect(**kwargs)
    cursor = conn.cursor()
    result = query_data.q3_average_scores(cursor)
    cursor.close()
    conn.close()
    assert len(result) == 4

@pytest.mark.db
def test_run_all_queries_handles_query_error(monkeypatch):
    """run_all_queries() catches exceptions and returns partial results."""
    def bad_q1(cursor):
        raise RuntimeError("forced error")
    
    monkeypatch.setattr(query_data, "q1_fall2026_count", bad_q1)
    results = query_data.run_all_queries()
    assert isinstance(results, dict)


# =======================
# Test: parse_date helper
# =======================
@pytest.mark.db
def test_parse_date_valid():
    """parse_date converts 'Jan 15, 2025' correctly."""
    from datetime import date
    result = load_data.parse_date("Jan 15, 2025")
    assert result == date(2025, 1, 15)


@pytest.mark.db
def test_parse_date_empty():
    """parse_date returns None for empty string."""
    assert load_data.parse_date("") is None


@pytest.mark.db
def test_parse_date_none():
    """parse_date returns None for None input."""
    assert load_data.parse_date(None) is None


@pytest.mark.db
def test_parse_date_invalid():
    """parse_date returns None for unparseable string."""
    assert load_data.parse_date("not-a-date") is None


# ================================
# Test: combine_uni_program helper
# ================================
@pytest.mark.db
def test_combine_uni_program_both():
    """combine_uni_program joins university and program with ' - '."""
    result = load_data.combine_uni_program("MIT", "CS")
    assert result == "MIT - CS"


@pytest.mark.db
def test_combine_uni_program_only_uni():
    """combine_uni_program returns university when program is None."""
    assert load_data.combine_uni_program("MIT", None) == "MIT"


@pytest.mark.db
def test_combine_uni_program_only_program():
    """combine_uni_program returns program when university is None."""
    assert load_data.combine_uni_program(None, "CS") == "CS"


@pytest.mark.db
def test_combine_uni_program_both_none():
    """combine_uni_program returns None when both inputs are None."""
    assert load_data.combine_uni_program(None, None) is None


# =======================================
# Test create new database and connection
# =======================================
@pytest.mark.db
def test_create_new_database_already_exists(clean_table):
    """create_new_database handles DuplicateDatabase gracefully."""
    kwargs = _parse_db_url(_db_url())
    dbname = kwargs["dbname"]
    # Call twice — second call hits the DuplicateDatabase except branch
    load_data.create_new_database(dbname)
    load_data.create_new_database(dbname)  # should not raise

@pytest.mark.db
def test_get_connection_returns_connection(clean_table):
    """get_connection() returns a live psycopg connection."""
    conn = query_data.get_connection()
    assert conn is not None
    conn.close()