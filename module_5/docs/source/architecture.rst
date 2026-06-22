Architecture
============

The system is divided into three layers:

Web Layer (Flask)
-----------------
``src/app.py`` exposes the HTTP interface via a ``create_app(test_config)``
factory. Dependencies (``QUERY_FUNC``, ``DB_LOADER_FUNC``, ``SCRAPER_FUNC``)
are injected via ``app.config`` so tests can substitute fakes without
touching the network or database.

Routes:

.. list-table::
   :header-rows: 1

   * - Route
     - Method
     - Purpose
   * - ``/analysis``
     - GET
     - Render the main analysis page
   * - ``/pull-data``
     - POST
     - Start background scrape + DB load (returns 409 if busy)
   * - ``/update-analysis``
     - GET / POST
     - Re-run queries and return JSON (returns 409 if busy)
   * - ``/create-database``
     - POST
     - Initialise DB from archive JSON file
   * - ``/scraper-status``
     - GET
     - Poll scraper running state
   * - ``/db-init-status``
     - GET
     - Poll DB init running state

ETL Layer
---------
``src/load_data.py`` handles:

* Creating the ``applicantdata`` PostgreSQL database
* Creating the ``applicants`` table (idempotent)
* Inserting records with ``ON CONFLICT (p_id) DO NOTHING``
* Helper utilities: ``parse_date()``, ``combine_uni_program()``

Database / Query Layer
----------------------
``src/query_data.py`` contains eleven named query functions (``q1``
through ``q11``) and ``run_all_queries()`` which executes them all
and returns a plain ``dict``. All percentage values are rounded to
two decimal places inside PostgreSQL using ``ROUND(..., 2)``.

Configuration
-------------
``src/configuration.py`` reads ``userConfig.json`` for local credentials
and exposes ``load_configuration_file()``, ``load_json()``, and
``get_configuration_filepath()``.