"""
worker/consumer.py
==================
RabbitMQ consumer for the GradCafe worker service.

Listens on the 'tasks_q' queue and routes messages to handlers:
  - scrape_new_data      → handle_scrape_new_data
  - recompute_analytics  → handle_recompute_analytics
"""
import json
import logging
import os

import pika
import psycopg

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# AMQP entity names — must match publisher.py exactly
EXCHANGE = "tasks"
QUEUE = "tasks_q"
ROUTING_KEY = "tasks"

DATABASE_URL = os.environ.get("DATABASE_URL", "")


# ==============
# DB Connection
# ==============
def get_db_conn():
    """Open and return a psycopg connection using DATABASE_URL."""
    return psycopg.connect(DATABASE_URL)


# ========
# Handlers
# ========
def handle_scrape_new_data(_conn, _payload):
    """
    Scrape new entries from GradCafe and insert into the database.

    Runs the incremental scraper, enriches with LLM, and inserts
    idempotently into the database.
    """
    import sys  # pylint: disable=import-outside-toplevel
    from pathlib import Path  # pylint: disable=import-outside-toplevel
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "etl", "web_scraper"))
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "web", "webapp"))
    import run_web_scraper  # pylint: disable=import-outside-toplevel
    import load_data  # pylint: disable=import-outside-toplevel
    import configuration  # pylint: disable=import-outside-toplevel

    log.info("Handling scrape_new_data task...")
    run_web_scraper.run_scraper_update()

    new_llm_output = run_web_scraper.NEW_LLM_OUTPUT
    run_web_scraper.run_llm(
        input_file=run_web_scraper.NEW_SCRAPE_OUTPUT,
        output_file=new_llm_output,
        num_workers=2
    )

    applicants = configuration.load_json(Path(new_llm_output).resolve())
    load_data.load_into_db(applicants, "applicantdata")
    log.info("scrape_new_data complete.")


def handle_recompute_analytics(conn, _payload):
    """
    Recompute analytics summaries used by the UI.

    Refreshes any materialized views or summary tables within
    the current transaction.
    """
    log.info("Handling recompute_analytics task...")

    with conn.cursor() as cur:
        cur.execute("""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM pg_matviews WHERE matviewname = 'applicant_summary'
                ) THEN
                    REFRESH MATERIALIZED VIEW applicant_summary;
                END IF;
            END $$;
        """)

    log.info("recompute_analytics complete.")


# ========
# Task map
# ========
TASK_MAP = {
    "scrape_new_data":     handle_scrape_new_data,
    "recompute_analytics": handle_recompute_analytics,
}


# ================
# Message callback
# ================
def on_message(ch, method, _properties, body):
    """Parse and route each incoming RabbitMQ message."""
    try:
        msg = json.loads(body)
        kind = msg.get("kind", "")
        payload = msg.get("payload", {})
        log.info("Received task: %s", kind)

        handler = TASK_MAP.get(kind)
        if not handler:
            log.warning("Unknown task kind: %s — nacking", kind)
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return

        conn = get_db_conn()
        try:
            handler(conn, payload)
            conn.commit()
            ch.basic_ack(delivery_tag=method.delivery_tag)
            log.info("Task %s completed and acked.", kind)
        except Exception as e:  # pylint: disable=broad-exception-caught
            conn.rollback()
            log.error("Handler error for %s: %s — nacking", kind, e)
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        finally:
            conn.close()

    except json.JSONDecodeError as e:
        log.error("Malformed message body: %s — nacking", e)
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


# ===========
# Entry point
# ===========
def main():  # pragma: no cover
    """Connect to RabbitMQ and start consuming tasks."""
    url = os.environ["RABBITMQ_URL"]
    params = pika.URLParameters(url)
    conn = pika.BlockingConnection(params)
    ch = conn.channel()

    ch.exchange_declare(exchange=EXCHANGE, exchange_type="direct", durable=True)
    ch.queue_declare(queue=QUEUE, durable=True)
    ch.queue_bind(exchange=EXCHANGE, queue=QUEUE, routing_key=ROUTING_KEY)

    ch.basic_qos(prefetch_count=1)
    ch.basic_consume(queue=QUEUE, on_message_callback=on_message)

    log.info("Worker ready — waiting for tasks on '%s'...", QUEUE)
    ch.start_consuming()


if __name__ == "__main__":  # pragma: no cover
    main()
