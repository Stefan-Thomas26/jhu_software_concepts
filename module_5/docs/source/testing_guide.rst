Testing Guide
=============

Test Organisation
-----------------

.. list-table::
   :header-rows: 1

   * - File
     - Marker
     - What it tests
   * - ``test_flask_page.py``
     - ``web``
     - App factory, route registration, page rendering
   * - ``test_buttons.py``
     - ``buttons``
     - Pull Data / Update Analysis endpoints, busy-state gating
   * - ``test_analysis_format.py``
     - ``analysis``
     - Answer: labels, two-decimal percentage formatting
   * - ``test_db_insert.py``
     - ``db``
     - Schema, inserts, idempotency, helper functions
   * - ``test_load_data.py``
     - ``db``
     - load_data_into_database() function coverage
   * - ``test_integration_end_to_end.py``
     - ``integration``
     - Full pull -> update -> render flows

Running Tests
-------------

Full suite::

    pytest -m "web or buttons or analysis or db or integration"

Single marker::

    pytest -m web
    pytest -m db

With coverage::

    pytest -m "web or buttons or analysis or db or integration" \
           --cov=src --cov-report=term-missing

Stable Selectors
----------------
The HTML template uses ``data-testid`` attributes for reliable selection:

* ``data-testid="pull-data-btn"`` — Pull Data button
* ``data-testid="update-analysis-btn"`` — Update Analysis button
* ``data-testid="create-database-btn"`` — Create Database button

Example using BeautifulSoup::

    soup = BeautifulSoup(resp.data, "html.parser")
    btn  = soup.find("button", {"data-testid": "pull-data-btn"})

Test Doubles & Fixtures
-----------------------
All test doubles are defined in ``tests/helpers.py``:

* ``fake_query_func()`` — returns ``FAKE_RESULTS`` dict without touching DB
* ``fake_loader_func(filename)`` — no-op loader
* ``fake_scraper_func(path, llm_file)`` — no-op scraper
* ``error_query_func()`` — raises ``RuntimeError`` (simulates DB down)
* ``error_loader_func(filename)`` — raises ``RuntimeError`` (simulates load failure)

Key fixtures in ``conftest.py``:

* ``client`` — Flask test client with all fakes wired in
* ``client_no_db`` — client where query function raises
* ``client_error_loader`` — client where loader raises
* ``clean_table`` — drops and recreates ``applicants`` table around each test
* ``db_conn`` — session-scoped raw psycopg connection

Environment Setup
-----------------
DB tests require ``DATABASE_URL``::

    export DATABASE_URL=postgresql://user:pass@localhost:5432/testdb

Or create a ``.env`` file in ``module_4/``::

    DATABASE_URL=postgresql://user:pass@localhost:5432/testdb