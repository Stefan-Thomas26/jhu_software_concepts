# Grad Café Analytics — Module 5

A Flask + PostgreSQL web application that scrapes graduate school application
data from [The Grad Café](https://www.thegradcafe.com), stores it in
PostgreSQL, and presents SQL-driven analysis via a browser UI.

This module adds security hardening: SQL injection defenses, least-privilege
database configuration, dependency analysis, Snyk scanning, and CI enforcement.

📖 **[Documentation](https://gradcafe-analytics-stefan.readthedocs.io)**

---

## Project Structure

```
module_5/
├── src/                                        # Application source code
│   ├── app.py                                  # Flask app factory + routes
│   ├── load_data.py                            # ETL: create DB, insert applicants
│   ├── query_data.py                           # SQL queries (q1–q11)
│   ├── configuration.py                        # Config / credential loading
│   └── web_scraper/                            # Web scraper functionality
|       ├── llm_hosting                         # Folder containing local LLM
│       ├── run_web_scraper.py                  # Top-level scraper entry point
│       ├── scrape_data.py                      # HTTP scraping logic
│       ├── clean_data.py                       # HTML parsing + data cleaning
│       ├── grad_applicant.py                   # GradApplicant dataclass
│       ├── save_data.py                        # Save applicants to JSON
│       ├── load_data.py                        # Load JSON files
│       └── confirm_robots.py                   # robots.txt compliance check
│
├── templates/
│   └── index.html                              # Jinja2 template
│
├── static/
│   └── style.css                               # Application CSS
│
├── tests/
│   ├── conftest.py                             # Fixtures & DB setup
│   ├── test_flask_page.py                      # [web] Page rendering tests
│   ├── test_buttons.py                         # [buttons] Endpoint behavior tests
│   ├── test_analysis_format.py                 # [analysis] Labels & formatting tests
│   ├── test_db_insert.py                       # [db] Schema & insert tests
│   ├── test_load_data.py                       # [db] load_data_into_database() tests
│   └── test_integration_end_to_end.py          # [integration] E2E flow tests
│
├── docs/                                       # Sphinx documentation
│
├── dependency.svg                              # pydeps dependency graph
├── snyk-analysis.png                           # Snyk scan screenshot
├── setup.py                                    # Package installation config
├── .env.example                                # Template for environment setup
├── pytest.ini                                  # Pytest configuration
├── requirements.txt                            # Python dependencies
├── coverage_summary.txt                        # Pytest coverage output
├── module_5_report.pdf                         # Assignment report
└── README.md                                   # This file
```

---

## Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Graphviz (`dot` command available in PATH)
- Node.js (for Snyk CLI)

---

## Fresh Install

### Using pip

```bash
git clone git@github.com:Stefan-Thomas26/jhu_software_concepts.git
cd jhu_software_concepts/module_5

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate.bat

pip install --upgrade pip
pip install -r requirements.txt
pip install -e .

cp .env.example .env
# Fill in your credentials in .env

python src/app.py
```

### Using uv

```bash
git clone git@github.com:Stefan-Thomas26/jhu_software_concepts.git
cd jhu_software_concepts/module_5

pip install uv
uv venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate.bat

uv pip sync requirements.txt
pip install -e .

cp .env.example .env
# Fill in your credentials in .env

python src/app.py
```

Open `http://localhost:8080` in your browser.

---

## Environment Variables

Copy `.env.example` to `.env` and fill in your values:

```dotenv
DB_HOST=localhost
DB_PORT=5432
DB_NAME=applicantdata
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DATA_FILE=src/web_scraper/llm_extended_applicant_data.json
SECRET_KEY=your_secret_key
DATABASE_URL=postgresql://your_db_user:your_db_password@localhost:5432/applicantdata
```

| Variable | Description |
|----------|-------------|
| `DB_HOST` | PostgreSQL host (usually `localhost`) |
| `DB_PORT` | PostgreSQL port (usually `5432`) |
| `DB_NAME` | Database name (`applicantdata`) |
| `DB_USER` | Least-privilege DB user (`gradcafe_reader`) |
| `DB_PASSWORD` | DB user password |
| `DATA_FILE` | Path to the LLM-enriched applicant JSON file |
| `SECRET_KEY` | Flask session signing key |
| `DATABASE_URL` | Full connection string (used by tests) |

> ⚠️ Never commit `.env` — it is listed in `.gitignore`

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

## Linting

Run Pylint on all source files:

```bash
cd module_5/
pylint src/
```

Expected output:

```
Your code has been rated at 10.00/10
```

All Python files under `module_5/src/` achieve a score of 10.00/10 with no
warnings or errors.

---

## SQL Injection Defenses

All SQL queries use `psycopg` safe composition:

- **No f-strings or string concatenation** in SQL construction
- **`pg_sql.SQL()`** wraps every query statement
- **`pg_sql.Identifier()`** safely quotes table and column names
- **`%s` parameter binding** passes all user-supplied values
- **`LIMIT` enforced on every query**, clamped to 1–100 via `clamp_limit()`

Example pattern:

```python
stmt = pg_sql.SQL("SELECT {col} FROM {tbl} LIMIT %s").format(
    col=pg_sql.Identifier(column_name),
    tbl=pg_sql.Identifier(table_name)
)
cursor.execute(stmt, [clamp_limit(limit)])
```

---

## Database Hardening

Credentials are loaded exclusively from environment variables — no secrets
appear in source code.

A least-privilege PostgreSQL user `gradcafe_reader` was created with
SELECT-only access on the `applicants` table:

```sql
CREATE USER gradcafe_reader WITH PASSWORD '...';
GRANT CONNECT ON DATABASE applicantdata TO gradcafe_reader;
GRANT USAGE ON SCHEMA public TO gradcafe_reader;
GRANT SELECT ON TABLE applicants TO gradcafe_reader;
```

This user cannot INSERT, UPDATE, DELETE, DROP, or ALTER any data or schema.

---

## Dependency Graph

Generated using pydeps and Graphviz:

```bash
pydeps src --noshow -T svg -o dependency.svg --max-bacon=3
```

The output is saved as `dependency.svg` in `module_5/`.

---

## Running Tests

### 1. Set up the test database

```bash
cp .env.example .env
# Fill in your PostgreSQL credentials
```

### 2. Run the full suite

```bash
cd module_5/
pytest tests/
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
pytest tests/ --cov=src --cov-report=term-missing
```

---

## Snyk Dependency Scan

```bash
# Install Snyk CLI
npm install -g snyk
snyk auth

# Run dependency scan
snyk test

# Run SAST scan (extra credit)
snyk code test
```

Results are saved as `snyk-analysis.png`.

---

## CI / GitHub Actions

The workflow at `.github/workflows/ci.yml` runs on every push and PR:

1. **Pylint** — enforces `--fail-under=10`
2. **pydeps** — generates `dependency.svg` and fails if missing
3. **Snyk** — runs `snyk test` for dependency scanning
4. **Pytest** — runs full test suite with 100% coverage enforcement

[![CI](https://github.com/Stefan-Thomas26/jhu_software_concepts/actions/workflows/ci.yml/badge.svg)](https://github.com/Stefan-Thomas26/jhu_software_concepts/actions/workflows/ci.yml)

---

## Packaging

Install as an editable package:

```bash
pip install -e .
```

This ensures imports behave consistently across local runs, tests, and CI,
eliminating path-related "it works on my machine" issues.

---

## Sphinx Documentation

Build locally:

```bash
cd module_5/docs
sphinx-build -b html source build/html
start build/html/index.html
```

Published at: **[Read the Docs](https://gradcafe-analytics-stefan.readthedocs.io)**

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

**Least-Privilege DB** — App connects as `gradcafe_reader` with SELECT-only
permissions. Even if credentials are compromised, no data can be modified.

**Safe SQL Composition** — All queries use `psycopg.sql` composition.
User input never touches SQL text directly.