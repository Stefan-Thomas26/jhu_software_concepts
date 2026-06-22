Operational Notes
=================

Busy-State Policy
-----------------
The application maintains two boolean flags (``scraper_state["running"]``
and ``db_init_state["running"]``) protected by ``threading.Lock``.

* While either flag is ``True``, ``POST /update-analysis`` returns **409**
* While ``scraper_state["running"]`` is ``True``, a second ``POST /pull-data``
  returns **409**
* While ``scraper_state["running"]`` is ``True``, ``POST /create-database``
  returns **409**
* While ``db_init_state["running"]`` is ``True``, ``POST /pull-data``
  returns **409**

Idempotency Strategy
--------------------
All inserts use ``ON CONFLICT (p_id) DO NOTHING``. The ``p_id`` field
maps to ``applicantNumber`` from the Grad Café scrape. Pulling the same
data twice is always safe.

Uniqueness Keys
---------------
* **Primary key**: ``p_id`` (``applicantNumber`` from the scraper)
* Duplicate ``p_id`` values are silently ignored on insert
* Failed individual inserts are rolled back and the loop continues

Troubleshooting
---------------

*Tests skip with "DATABASE_URL not set"*
    Export ``DATABASE_URL`` before running tests::

        export DATABASE_URL=postgresql://user:pass@localhost:5432/testdb

*psycopg connection refused*
    Ensure PostgreSQL is running and credentials are correct.

*100% coverage not reached*
    Run with ``--cov-report=html`` and open ``htmlcov/index.html`` to
    see which lines are uncovered.

*GitHub Actions Postgres not ready*
    Increase ``--health-retries`` in the workflow YAML.