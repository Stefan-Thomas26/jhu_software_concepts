"""
tests/test_publisher.py
=======================
Unit tests for the RabbitMQ publisher.

Markers: publisher
"""
import pytest
from unittest.mock import MagicMock, patch
import publisher


# ====================
# _open_channel() tests
# ====================
@pytest.mark.publisher
def test_open_channel_declares_exchange(monkeypatch):
    """_open_channel declares a durable direct exchange named 'tasks'."""
    mock_conn = MagicMock()
    mock_ch = MagicMock()
    mock_conn.channel.return_value = mock_ch

    with patch("publisher.pika.BlockingConnection", return_value=mock_conn), \
         patch("publisher.pika.URLParameters"), \
         patch.dict("os.environ", {"RABBITMQ_URL": "amqp://guest:guest@localhost/"}):

        conn, ch = publisher._open_channel()

    ch.exchange_declare.assert_called_once_with(
        exchange="tasks", exchange_type="direct", durable=True
    )


@pytest.mark.publisher
def test_open_channel_declares_queue(monkeypatch):
    """_open_channel declares a durable queue named 'tasks_q'."""
    mock_conn = MagicMock()
    mock_ch = MagicMock()
    mock_conn.channel.return_value = mock_ch

    with patch("publisher.pika.BlockingConnection", return_value=mock_conn), \
         patch("publisher.pika.URLParameters"), \
         patch.dict("os.environ", {"RABBITMQ_URL": "amqp://guest:guest@localhost/"}):

        conn, ch = publisher._open_channel()

    ch.queue_declare.assert_called_once_with(queue="tasks_q", durable=True)


@pytest.mark.publisher
def test_open_channel_binds_queue(monkeypatch):
    """_open_channel binds the queue to the exchange with routing key 'tasks'."""
    mock_conn = MagicMock()
    mock_ch = MagicMock()
    mock_conn.channel.return_value = mock_ch

    with patch("publisher.pika.BlockingConnection", return_value=mock_conn), \
         patch("publisher.pika.URLParameters"), \
         patch.dict("os.environ", {"RABBITMQ_URL": "amqp://guest:guest@localhost/"}):

        conn, ch = publisher._open_channel()

    ch.queue_bind.assert_called_once_with(
        exchange="tasks", queue="tasks_q", routing_key="tasks"
    )


@pytest.mark.publisher
def test_open_channel_returns_conn_and_channel():
    """_open_channel returns a (connection, channel) tuple."""
    mock_conn = MagicMock()
    mock_ch = MagicMock()
    mock_conn.channel.return_value = mock_ch

    with patch("publisher.pika.BlockingConnection", return_value=mock_conn), \
         patch("publisher.pika.URLParameters"), \
         patch.dict("os.environ", {"RABBITMQ_URL": "amqp://guest:guest@localhost/"}):

        conn, ch = publisher._open_channel()

    assert conn is mock_conn
    assert ch is mock_ch


# =====================
# publish_task() tests
# =====================
@pytest.mark.publisher
def test_publish_task_calls_basic_publish():
    """publish_task calls basic_publish on the channel."""
    mock_conn = MagicMock()
    mock_ch = MagicMock()
    mock_conn.channel.return_value = mock_ch

    with patch("publisher.pika.BlockingConnection", return_value=mock_conn), \
         patch("publisher.pika.URLParameters"), \
         patch.dict("os.environ", {"RABBITMQ_URL": "amqp://guest:guest@localhost/"}):

        publisher.publish_task("scrape_new_data")

    assert mock_ch.basic_publish.called


@pytest.mark.publisher
def test_publish_task_uses_correct_exchange():
    """publish_task publishes to the 'tasks' exchange."""
    mock_conn = MagicMock()
    mock_ch = MagicMock()
    mock_conn.channel.return_value = mock_ch

    with patch("publisher.pika.BlockingConnection", return_value=mock_conn), \
         patch("publisher.pika.URLParameters"), \
         patch.dict("os.environ", {"RABBITMQ_URL": "amqp://guest:guest@localhost/"}):

        publisher.publish_task("scrape_new_data")

    _, kwargs = mock_ch.basic_publish.call_args
    assert kwargs["exchange"] == "tasks"


@pytest.mark.publisher
def test_publish_task_uses_correct_routing_key():
    """publish_task uses routing key 'tasks'."""
    mock_conn = MagicMock()
    mock_ch = MagicMock()
    mock_conn.channel.return_value = mock_ch

    with patch("publisher.pika.BlockingConnection", return_value=mock_conn), \
         patch("publisher.pika.URLParameters"), \
         patch.dict("os.environ", {"RABBITMQ_URL": "amqp://guest:guest@localhost/"}):

        publisher.publish_task("recompute_analytics")

    _, kwargs = mock_ch.basic_publish.call_args
    assert kwargs["routing_key"] == "tasks"


@pytest.mark.publisher
def test_publish_task_closes_connection_on_success():
    """publish_task closes the connection after publishing."""
    mock_conn = MagicMock()
    mock_ch = MagicMock()
    mock_conn.channel.return_value = mock_ch

    with patch("publisher.pika.BlockingConnection", return_value=mock_conn), \
         patch("publisher.pika.URLParameters"), \
         patch.dict("os.environ", {"RABBITMQ_URL": "amqp://guest:guest@localhost/"}):

        publisher.publish_task("scrape_new_data")

    mock_conn.close.assert_called_once()


@pytest.mark.publisher
def test_publish_task_closes_connection_on_error():
    """publish_task closes connection even when basic_publish raises."""
    mock_conn = MagicMock()
    mock_ch = MagicMock()
    mock_ch.basic_publish.side_effect = RuntimeError("publish failed")
    mock_conn.channel.return_value = mock_ch

    with patch("publisher.pika.BlockingConnection", return_value=mock_conn), \
         patch("publisher.pika.URLParameters"), \
         patch.dict("os.environ", {"RABBITMQ_URL": "amqp://guest:guest@localhost/"}):

        with pytest.raises(RuntimeError):
            publisher.publish_task("scrape_new_data")

    mock_conn.close.assert_called_once()


@pytest.mark.publisher
def test_publish_task_message_contains_kind():
    """publish_task body JSON contains the task kind."""
    import json
    mock_conn = MagicMock()
    mock_ch = MagicMock()
    mock_conn.channel.return_value = mock_ch

    with patch("publisher.pika.BlockingConnection", return_value=mock_conn), \
         patch("publisher.pika.URLParameters"), \
         patch.dict("os.environ", {"RABBITMQ_URL": "amqp://guest:guest@localhost/"}):

        publisher.publish_task("scrape_new_data", payload={"since": "2025-01-01"})

    _, kwargs = mock_ch.basic_publish.call_args
    body = json.loads(kwargs["body"])
    assert body["kind"] == "scrape_new_data"
    assert body["payload"] == {"since": "2025-01-01"}
