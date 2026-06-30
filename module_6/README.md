# Module 6 — GradCafe Microservice Application

A containerized, microservice version of the GradCafe Data Analysis app. The
Flask web tier, PostgreSQL database, RabbitMQ message broker, and a Python
background worker run as four independent services orchestrated by Docker
Compose. Long-running and data-modifying work (scraping new applicants,
recomputing analytics) is offloaded from the web tier to the worker via
RabbitMQ, so the UI stays fast and responsive regardless of how long a task
takes to complete.

---

## Docker Installation Assumptions

This project requires **Docker Desktop** (macOS / Windows) or **Docker Engine
+ Compose plugin** (Linux). Installation instructions are at
https://docs.docker.com/get-docker/. The commands below assume:

- `docker` and `docker compose` (v2) are on your PATH
- Docker Desktop is running (or the Docker daemon is active on Linux)
- You have at least 4 GB of RAM available for Docker (the worker loads a local
  LLM model at build time)

Tested on: Docker Desktop 4.x, Docker Compose v2.x, Python 3.14.

---

## Architecture

```
Browser → Flask (web:8080) → RabbitMQ (tasks_q) → Worker → PostgreSQL (db:5432)
```

| Service      | Image                        | Port(s)           | Role                                      |
|--------------|------------------------------|-------------------|-------------------------------------------|
| `web`        | `stefanthomas26/module_6:web-v1`    | `8080` (HTTP)     | Flask UI + RabbitMQ publisher             |
| `worker`     | `stefanthomas26/module_6:worker-v1` | —                 | RabbitMQ consumer + scraper + DB writer   |
| `db`         | `postgres:16`                | `5432` (internal) | PostgreSQL — applicant data + watermarks  |
| `rabbitmq`   | `rabbitmq:3.13-management`   | `15672` (mgmt UI) | AMQP message broker                       |

### How the services connect

- `web` publishes a JSON task message to the `tasks` exchange (routing key
  `tasks`) whenever a button is clicked. It returns `202 Accepted` immediately.
- `rabbitmq` routes the message to the durable `tasks_q` queue.
- `worker` consumes one message at a time (`prefetch_count=1`), runs the
  handler inside a database transaction, commits, and acks. On any error it
  rolls back and nacks without requeue.
- `db` stores applicant records (`applicants` table) and an
  `ingestion_watermarks` table that ensures incremental scraping is idempotent.

### Task buttons

| Button            | Published task kind    | Worker handler               | What it does                                              |
|--------------------|------------------------|-------------------------------|-----------------------------------------------------------|
| **Pull Data**      | `scrape_new_data`      | `handle_scrape_new_data`      | Scrapes new GradCafe entries, runs LLM enrichment, inserts idempotently, advances watermark |
| **Create Database**| `recompute_analytics`  | `handle_recompute_analytics`  | Ensures the DB schema (`applicants` table) exists         |
| **Update Analysis**| (direct query, no queue) | —                           | Re-runs all SQL queries and refreshes the UI charts       |

---

## Quickstart

### 1. Prerequisites

- Docker Desktop installed and running
- Git

### 2. Clone and configure

```bash
git clone <your-repo-url>
cd module_6
cp .env.example .env
# Edit .env and fill in DB_USER, DB_PASSWORD, and DB_NAME
```

### 3. Build and run

```bash
docker compose up --build
```

The first build takes several minutes — the worker image compiles
`llama_cpp_python` from source and pre-downloads the TinyLlama GGUF model
(~700 MB). Subsequent builds use Docker's layer cache and are fast.

### 4. Access the services

| Service              | URL                          | Credentials          |
|-----------------------|------------------------------|----------------------|
| Flask app             | http://localhost:8080         | —                    |
| RabbitMQ management   | http://localhost:15672        | `guest` / `guest`    |

### 5. Load data and run analysis

1. Click **Create Database** — initializes the schema (returns immediately, worker processes asynchronously)
2. Click **Pull Data** — enqueues a live GradCafe scrape (runs in background via worker; LLM enrichment can take several minutes)
3. Click **Update Analysis** — re-runs all SQL queries and updates the dashboard

Alternatively, to instantly seed the database with pre-existing data:

```bash
docker compose exec web python -c "
import sys; sys.path.insert(0, 'db'); sys.path.insert(0, 'shared')
from db import load_data
load_data.load_data_into_database('/data/llm_extended_applicant_data.json')
"
```

### 6. Stop the stack

```bash
docker compose down        # stops containers, preserves DB volume
docker compose down -v     # stops containers AND wipes DB (full reset)
```

---

## Environment Variables

Copy `.env.example` to `.env` and fill in your values. Docker Compose
automatically wires `DATABASE_URL`, `DB_HOST`, and `DATA_DIR` to point at
internal service names — you do not need to set Docker-specific values manually.

| Variable        | Required for         | Description                                                   |
|-----------------|----------------------|---------------------------------------------------------------|
| `DB_USER`       | Docker + local tests | PostgreSQL username                                           |
| `DB_PASSWORD`   | Docker + local tests | PostgreSQL password                                           |
| `DB_NAME`       | Docker + local tests | PostgreSQL database name (e.g. `applicantdata`)               |
| `DB_HOST`       | Local tests only     | Postgres host outside Docker (e.g. `localhost`)               |
| `DB_PORT`       | Local tests only     | Postgres port outside Docker (e.g. `5432`)                    |
| `DATABASE_URL`  | Local tests only     | Full psycopg connection string for pytest                     |
| `RABBITMQ_URL`  | Docker + local       | AMQP URL (e.g. `amqp://guest:guest@rabbitmq:5672/`)           |
| `FLASK_SECRET`  | Docker               | Flask session secret key                                      |
| `FLASK_ENV`     | Docker               | `development` or `production`                                 |
| `DATA_DIR`      | Docker               | Path to data volume inside container (set to `/data` in Compose) |

---

## Running Tests Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests with coverage
pytest tests/ --cov=src --cov-report=term-missing
```

100% test coverage is enforced (`--cov-fail-under=100`). Database-backed tests
require `DATABASE_URL` to be set in `.env`; they skip automatically if it is
not present.

## Linting

```bash
pylint src/
```

Target score: 10.00/10.

---

## Project Structure

```
module_6/
    docker-compose.yml       # defines all 4 services, health checks, named volume
    setup.py
    README.md
    .env.example             # template — copy to .env and fill in values
    pytest.ini
    .coveragerc
    docs/
    tests/
        conftest.py
        test_flask_page.py
        test_buttons.py
        test_analysis_format.py
        test_db_insert.py
        test_load_data.py
        test_integration_end_to_end.py
        test_publisher.py
        test_consumer.py
    src/
        web/
            Dockerfile           # non-root, python:3.11-slim
            requirements.txt
            run.py               # Flask entrypoint — binds 0.0.0.0:8080
            publisher.py         # RabbitMQ publisher (_open_channel, publish_task)
            webapp/
                app.py           # Flask application factory + routes
                query_data.py    # SQL queries against applicants table
        worker/
            Dockerfile           # non-root, build-essential + LLM model pre-download
            requirements.txt
            consumer.py          # RabbitMQ consumer (acks, prefetch=1, task map)
            etl/
                web_scraper/     # GradCafe scraper + LLM enrichment pipeline
        db/
            load_data.py         # JSON → PostgreSQL loader, watermark table
        shared/
            configuration.py     # shared env var reader + JSON loader
        data/
            applicant_data.json  # seed data (LLM-cleaned applicant records)
```

---

## Docker Hub Registry

Public repository: https://hub.docker.com/r/stefanthomas26/module_6

```bash
# Pull images
docker pull stefanthomas26/module_6:web-v1
docker pull stefanthomas26/module_6:worker-v1
```

To run the web image standalone (for testing only — requires a running DB and
RabbitMQ):

```bash
docker run -p 8080:8080 --env-file .env stefanthomas26/module_6:web-v1
```

---

## Notes

- Both containers run as a non-root user (`USER 1000`) for security.
- The worker pre-downloads the TinyLlama GGUF model at build time so runtime
  LLM inference does not require a network download.
- `Pull Data` scraping is incremental and idempotent — the `ingestion_watermarks`
  table tracks the last-seen record so duplicate rows are never inserted.
- All SQL uses parameterized queries (`%s` placeholders via psycopg) —
  no string interpolation in SQL.