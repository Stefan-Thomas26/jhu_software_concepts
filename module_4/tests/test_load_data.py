"""
tests/test_load_data.py
========================
Tests for load_data_into_database().
Separate file to avoid patch_config autouse from test_db_insert.py.

Markers: db
"""
import json
import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

import load_data
import configuration
from conftest import _parse_db_url, _db_url


@pytest.fixture(autouse=True)
def patch_load_data_config(monkeypatch):
    """Patch configuration so load_data uses DATABASE_URL credentials."""
    url    = _db_url()
    kwargs = _parse_db_url(url)
    monkeypatch.setattr(configuration, "load_configuration_file",
                        lambda: (kwargs["user"], kwargs.get("password", ""), kwargs["host"]))


@pytest.fixture()
def clean_applicants(db_conn):
    """Fresh applicants table for each test."""
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


SAMPLE = [{
    "applicantNumber": 4001,
    "university": "MIT",
    "program": "CS",
    "degreeType": "PhD",
    "datePosted": None,
    "status": "Accepted",
    "statusDate": None,
    "semester": "Fall 2026",
    "citizenship": "American",
    "gpa": 3.9,
    "gre": None,
    "gre_v": None,
    "gre_aw": None,
    "comment": None,
    "url": None,
    "llm_generated_program": None,
    "llm_generated_university": None
}]


@pytest.mark.db
def test_load_data_into_database_with_filename(monkeypatch):
    """load_data_into_database() calls load_into_db with correct args."""
    called = []

    monkeypatch.setattr(load_data, "create_new_database", lambda name: None)
    monkeypatch.setattr(load_data, "load_into_db",
                        lambda applicants, db: called.append((applicants, db)))
    monkeypatch.setattr(configuration, "load_json",
                        lambda path: SAMPLE)

    tmpfile = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
    json.dump(SAMPLE, tmpfile)
    tmpfile.close()

    try:
        load_data.load_data_into_database(tmpfile.name)
    finally:
        os.unlink(tmpfile.name)

    assert len(called) == 1
    assert called[0][1] == "applicantdata"


@pytest.mark.db
def test_load_data_into_database_none_filename_reads_config(monkeypatch, clean_applicants):
    """load_data_into_database(None) reads filename from config."""
    import psycopg as _psycopg
    kwargs = _parse_db_url(_db_url())
    dbname = kwargs["dbname"]

    monkeypatch.setattr(load_data, "create_new_database", lambda name: None)

    original_connect = _psycopg.connect
    def patched_connect(**kw):
        kw["dbname"] = dbname
        return original_connect(**kw)
    monkeypatch.setattr(load_data.psycopg, "connect", patched_connect)

    sample2 = [{**SAMPLE[0], "applicantNumber": 4002}]
    tmpfile  = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
    json.dump(sample2, tmpfile)
    tmpfile.close()

    monkeypatch.setattr(configuration, "get_configuration_filepath",
                        lambda: "fake")
    monkeypatch.setattr(configuration, "load_json",
                        lambda path: [{"dataFile": tmpfile.name}]
                        if path == "fake"
                        else json.load(open(path)))

    try:
        load_data.load_data_into_database(None)
    finally:
        os.unlink(tmpfile.name)

    # Use fresh connection to avoid stale transaction view
    import psycopg
    fresh_conn = psycopg.connect(**kwargs)
    fresh_cur  = fresh_conn.cursor()
    fresh_cur.execute("SELECT COUNT(*) FROM applicants WHERE p_id = 4002;")
    count = fresh_cur.fetchone()[0]
    fresh_cur.close()
    fresh_conn.close()

    assert count == 1



@pytest.mark.db
def test_load_data_into_database_config_exception_uses_fallback(monkeypatch):
    """load_data_into_database(None) falls back to default when config fails."""
    monkeypatch.setattr(load_data, "create_new_database", lambda name: None)

    # Make config reading raise to hit the except branch
    monkeypatch.setattr(configuration, "get_configuration_filepath",
                        lambda: (_ for _ in ()).throw(RuntimeError("no config")))

    # Capture what filename gets used after fallback
    captured = []
    def fake_load_json(path):
        captured.append(str(path))
        return []
    monkeypatch.setattr(configuration, "load_json", fake_load_json)
    monkeypatch.setattr(load_data, "load_into_db", lambda a, d: None)

    load_data.load_data_into_database(None)

    # Fallback filename should contain the default path
    assert any("llm_extended_applicant_data.json" in p for p in captured)