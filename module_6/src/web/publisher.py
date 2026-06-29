"""
publisher.py
============
RabbitMQ publisher for the GradCafe web service.

Publishes tasks to the 'tasks' exchange so the worker can process them
asynchronously. Flask routes call publish_task() and immediately return
HTTP 202 without waiting for the work to complete.
"""
import json
import os
from datetime import datetime

import pika

# AMQP entity names — must match consumer.py exactly
EXCHANGE = "tasks"
QUEUE = "tasks_q"
ROUTING_KEY = "tasks"


def _open_channel():
    """
    Open a RabbitMQ connection and declare durable AMQP entities.

    Returns
    -------
    tuple
        (connection, channel) — caller is responsible for closing connection.
    """
    url = os.environ["RABBITMQ_URL"]
    params = pika.URLParameters(url)
    conn = pika.BlockingConnection(params)
    ch = conn.channel()

    # Idempotent declarations — safe to call on every publish
    ch.exchange_declare(exchange=EXCHANGE, exchange_type="direct", durable=True)
    ch.queue_declare(queue=QUEUE, durable=True)
    ch.queue_bind(exchange=EXCHANGE, queue=QUEUE, routing_key=ROUTING_KEY)

    return conn, ch


def publish_task(kind: str, payload: dict | None=None, headers: dict | None=None) -> None:
    """
    Publish a task message to RabbitMQ.

    Parameters
    ----------
    kind : str
        Task type, e.g. ``'scrape_new_data'`` or ``'recompute_analytics'``.
    payload : dict, optional
        Extra data for the worker. Defaults to ``{}``.
    headers : dict, optional
        AMQP message headers. Defaults to ``{}``.

    Raises
    ------
    Exception
        Re-raises any connection or publish error so Flask can return 503.
    """
    body = json.dumps(
        {
            "kind": kind,
            "ts": datetime.utcnow().isoformat(),
            "payload": payload or {},
        },
        separators=(",", ":"),
    ).encode("utf-8")

    conn, ch = _open_channel()
    try:
        ch.basic_publish(
            exchange=EXCHANGE,
            routing_key=ROUTING_KEY,
            body=body,
            properties=pika.BasicProperties(
                delivery_mode=2,
                headers=headers or {},
            ),
            mandatory=False,
        )
    finally:
        conn.close()
