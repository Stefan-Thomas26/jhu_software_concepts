# Grad Café Analytics — Module 4

A Flask + PostgreSQL web application that scrapes graduate school application
data from [The Grad Café](https://www.thegradcafe.com), stores it in
PostgreSQL, and presents SQL-driven analysis via a browser UI.

📖 **[Documentation](https://gradcafe-analytics-stefan.readthedocs.io)**

---

## Project Structure

```
module_4/
├── src/                                 # Application source code
│   ├── app.py                           # Flask app factory + routes
│   ├── load_data.py                     # ETL: create DB, insert applicants
│   ├── query_data.py                    # SQL queries (q1–q11)
│   ├── configuration.py                 # Config / credential loading
|   └── Module_2/                        # Contains web scraper functionality
|
├── templates/
│   └── index.html                       # Jinja2 template (data-testid selectors)
|
├── static/
│   └── style.css                        # Application CSS
|
├── tests/
│   ├── conftest.py                      # Fixtures & DB setup
│   ├── helpers.py                       # Fake functions & shared test data
│   ├── test_flask_page.py               # [web] Page rendering tests
│   ├── test_buttons.py                  # [buttons] Endpoint behavior tests
│   ├── test_analysis_format.py          # [analysis] Labels & formatting tests
│   ├── test_db_insert.py                # [db] Schema & insert tests
│   ├── test_load_data.py                # [db] load_data_into_database() tests
│   └── test_integration_end_to_end.py   # [integration] E2E flow tests
|
├── docs/                                # Sphinx documentation
│   └── source/
│       ├── conf.py
│       ├── index.rst
│       ├── overview.rst
│       ├── architecture.rst
│       ├── api_reference.rst
│       ├── testing_guide.rst
│       └── operational_notes.rst
|
├── .github/
│   └── workflows/
│       └── tests.yml                    # GitHub Actions CI
|
├── .env.example                         # Template for local environment setup
├── pytest.ini                           # Pytest configuration
├── requirements.txt                     # Python dependencies
├── coverage_summary.txt                 # Pytest coverage output
└── README.md                            # This file
```

---

## Prerequisites

- Python 3.11+
- PostgreSQL 15+

---

## Setup

### 1. Clone the repository

```bash
git clone git@github.com:Stefan-Thomas26/jhu_software_concepts.git
cd jhu_software_concepts
```

### 2. Install dependencies

```bash
cd module_4
pip install -r requirements.txt
```

### 3. Configure PostgreSQL credentials

Create `module_4/src/userConfig.json`:

```json
[{
    "user": "your_postgres_username",
    "password": "your_postgres_password",
    "host": "localhost",
    "data_file": "../../module_2/llm_extended_applicant_data.json"
}]
```

> ⚠️ Never commit this file — it is listed in `.gitignore`

### 4. Run the Flask app

```bash
python src/app.py
```

Open `http://localhost:8080` in your browser.

---

## Using the App

The browser UI has three buttons:

| Button | What it does |
|--------|-------------|
| **Create Database** | Creates the PostgreSQL database and loads the archive JSON file |
| **Pull Data** | Scrapes new entries from Grad Café and adds them to the database |
| **Update Analysis** | Refreshes all analysis results from the database |

All three buttons are non-blocking — they run in background threads and show a
status bar while running. If a task is already running, subsequent requests
return a 409 Busy response.

---

## Running Tests

### 1. Set up the test database

Create a `.env` file in `module_4/`:

```bash
cp .env.example .env
```

Edit `.env` with your PostgreSQL credentials:

```
DATABASE_URL=postgresql://your_user:your_password@localhost:5432/testdb
```

The test database (`testdb`) will be created automatically on first run.

### 2. Run the full suite

```bash
cd module_4
pytest -m "web or buttons or analysis or db or integration"
```

### 3. Run individual markers

```bash
pytest -m web          # Page rendering tests
pytest -m buttons      # Endpoint behavior tests
pytest -m analysis     # Formatting tests
pytest -m db           # Database tests
pytest -m integration  # End-to-end tests
```

### 4. Run with coverage report

```bash
pytest -m "web or buttons or analysis or db or integration" --cov=src --cov-report=term-missing
```

### 5. Save coverage summary

```bash
pytest -m "web or buttons or analysis or db or integration" | tee coverage_summary.txt
```

---

## Test Coverage

100% coverage across all source modules:

```
Name                   Stmts   Miss  Cover
------------------------------------------
src/__init__.py            0      0   100%
src/app.py               118      0   100%
src/configuration.py      10      0   100%
src/load_data.py          70      0   100%
src/query_data.py         98      0   100%
------------------------------------------
TOTAL                    296      0   100%
```

---


## CI / GitHub Actions

The workflow at `.github/workflows/tests.yml`:

1. Starts a PostgreSQL 15 service container
2. Installs Python 3.11 and dependencies
3. Runs the full pytest suite with 100% coverage enforcement
4. Saves `coverage_summary.txt` as a build artifact

[![Pytest Suite](https://github.com/Stefan-Thomas26/jhu_software_concepts/actions/workflows/tests.yml/badge.svg)](https://github.com/Stefan-Thomas26/jhu_software_concepts/actions/workflows/tests.yml)

---

## Sphinx Documentation

Build locally:

```bash
cd module_4/docs
sphinx-build -b html source build/html
start build/html/index.html
```

Published at: **[Read the Docs](https://gradcafe-analytics-stefan.readthedocs.io)**

The docs cover:
- **Overview & Setup** — environment variables, how to run app and tests
- **Architecture** — web, ETL, and database layers
- **API Reference** — autodoc for all key modules
- **Testing Guide** — markers, selectors, fixtures, test doubles
- **Operational Notes** — busy-state policy, idempotency, troubleshooting

---

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string for tests | `postgresql://user:pass@localhost:5432/testdb` |

---

## Key Design Decisions

**Dependency Injection** — `create_app(test_config)` accepts injectable
functions for the scraper, loader, and query layer. Tests pass fakes;
production uses real functions.

**Busy-State Gating** — Threading locks prevent concurrent DB mutations.
All endpoints return 409 when a background task is running.

**Idempotency** — All inserts use `ON CONFLICT (p_id) DO NOTHING`.
Pulling the same data twice is always safe.

**100% Test Coverage** — Enforced via `pytest-cov` with
`--cov-fail-under=100` in `pytest.ini`.