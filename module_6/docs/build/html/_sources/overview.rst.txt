Overview & Setup
================

Grad Café Analytics is a Flask web application that scrapes graduate school
application data from The Grad Café, stores it in PostgreSQL, and presents
SQL-driven analysis via a browser UI.

Prerequisites
-------------
* Python 3.11+
* PostgreSQL 15+

Environment Variables
---------------------

.. list-table::
   :header-rows: 1

   * - Variable
     - Description
     - Example
   * - ``DATABASE_URL``
     - PostgreSQL connection string used by tests and CI
     - ``postgresql://user:pass@localhost:5432/testdb``

Local Setup
-----------

1. Clone the repository::

    git clone git@github.com:Stefan-Thomas26/jhu_software_concepts.git

2. Install dependencies::

    cd module_4
    pip install -r requirements.txt

3. Create ``src/userConfig.json``::

    [{"user": "postgres", "password": "yourpassword", "host": "localhost",
      "data_file": "../../module_2/llm_extended_applicant_data.json"}]

4. Run the app::

    python src/app.py

5. Open ``http://localhost:8080`` in your browser.

Running Tests
-------------
::

    cd module_4
    cp .env.example .env
    # fill in your PostgreSQL credentials in .env
    pytest -m "web or buttons or analysis or db or integration"