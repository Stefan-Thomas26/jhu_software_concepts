"""
tests/test_consumer.py
======================
Unit tests for the RabbitMQ consumer.

Markers: consumer
"""
import json
import pytest
from unittest.mock import MagicMock, patch
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src/worker")))

import consumer


# ==============
# get_db_conn()
# ==============
@pytest.mark.consumer
def test_get_db_conn_calls_psycopg_connect(monkeypatch):
    """get_db_conn calls psycopg.connect with DATABASE_URL."""
    mock_conn = MagicMock()
    with patch("consumer.psycopg.connect", return_value=mock_conn) as mock_connect:
        result = consumer.get_db_conn()
    mock_connect.assert_called_once()
    assert result is mock_conn


# ==============================
# handle_recompute_analytics()
# ==============================
@pytest.mark.consumer
def test_recompute_analytics_executes_sql():
    """handle_recompute_analytics executes SQL on the connection cursor."""
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cur)
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

    consumer.handle_recompute_analytics(mock_conn, {})

    assert mock_cur.execute.called


@pytest.mark.consumer
def test_recompute_analytics_uses_conn_cursor():
    """handle_recompute_analytics opens a cursor on the provided connection."""
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cur)
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

    consumer.handle_recompute_analytics(mock_conn, {})

    mock_conn.cursor.assert_called_once()


# ==============================
# handle_scrape_new_data()
# ==============================
@pytest.mark.consumer
@pytest.mark.consumer
def test_handle_scrape_new_data_calls_scraper(monkeypatch):
    """handle_scrape_new_data calls run_scraper_update."""
    mock_scraper = MagicMock()
    mock_scraper.NEW_SCRAPE_OUTPUT = "fake_scrape.json"
    mock_scraper.NEW_LLM_OUTPUT = "fake_llm.json"
    mock_scraper.run_scraper_update = MagicMock()
    mock_scraper.run_llm = MagicMock()

    mock_shared = MagicMock()
    mock_shared.configuration.load_json = MagicMock(return_value=[])

    mock_db = MagicMock()

    with patch.dict("sys.modules", {
        "run_web_scraper": mock_scraper,
        "shared": mock_shared,
        "db": mock_db,
    }):
        consumer.handle_scrape_new_data(MagicMock(), {})

    mock_scraper.run_scraper_update.assert_called_once()


@pytest.mark.consumer
def test_handle_scrape_new_data_calls_llm(monkeypatch):
    """handle_scrape_new_data calls run_llm after scraping."""
    mock_scraper = MagicMock()
    mock_scraper.NEW_SCRAPE_OUTPUT = "fake_scrape.json"
    mock_scraper.NEW_LLM_OUTPUT = "fake_llm.json"
    mock_scraper.run_scraper_update = MagicMock()
    mock_scraper.run_llm = MagicMock()

    mock_shared = MagicMock()
    mock_shared.configuration.load_json = MagicMock(return_value=[])

    mock_db = MagicMock()

    with patch.dict("sys.modules", {
        "run_web_scraper": mock_scraper,
        "shared": mock_shared,
        "db": mock_db,
    }):
        consumer.handle_scrape_new_data(MagicMock(), {})

    mock_scraper.run_llm.assert_called_once()


@pytest.mark.consumer
def test_handle_scrape_new_data_calls_load_into_db():
    """handle_scrape_new_data calls load_into_db with applicant data."""
    mock_scraper = MagicMock()
    mock_scraper.NEW_SCRAPE_OUTPUT = "fake_scrape.json"
    mock_scraper.NEW_LLM_OUTPUT = "fake_llm.json"
    mock_scraper.run_scraper_update = MagicMock()
    mock_scraper.run_llm = MagicMock()

    mock_shared = MagicMock()
    mock_shared.configuration.load_json = MagicMock(return_value=[{"applicantNumber": 1}])

    mock_db = MagicMock()

    with patch.dict("sys.modules", {
        "run_web_scraper": mock_scraper,
        "shared": mock_shared,
        "db": mock_db,
    }):
        consumer.handle_scrape_new_data(MagicMock(), {})

    mock_db.load_data.load_into_db.assert_called_once()


# ==============
# on_message()
# ==============
def _make_method(tag=1):
    """Create a fake AMQP method with a delivery tag."""
    method = MagicMock()
    method.delivery_tag = tag
    return method


def _body(kind, payload=None):
    """Create a JSON message body."""
    return json.dumps({"kind": kind, "payload": payload or {}}).encode()


@pytest.mark.consumer
def test_on_message_acks_on_success():
    """on_message acks the message after successful handler."""
    ch = MagicMock()
    method = _make_method()
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cur)
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

    with patch("consumer.get_db_conn", return_value=mock_conn):
        consumer.on_message(ch, method, None, _body("recompute_analytics"))

    ch.basic_ack.assert_called_once_with(delivery_tag=1)


@pytest.mark.consumer
def test_on_message_nacks_unknown_kind():
    """on_message nacks without requeue when kind is unknown."""
    ch = MagicMock()
    method = _make_method()

    consumer.on_message(ch, method, None, _body("unknown_task"))

    ch.basic_nack.assert_called_once_with(delivery_tag=1, requeue=False)


@pytest.mark.consumer
def test_on_message_nacks_on_handler_error():
    """on_message nacks without requeue when handler raises."""
    ch = MagicMock()
    method = _make_method()
    mock_conn = MagicMock()
    mock_conn.cursor.side_effect = RuntimeError("DB error")

    with patch("consumer.get_db_conn", return_value=mock_conn):
        consumer.on_message(ch, method, None, _body("recompute_analytics"))

    ch.basic_nack.assert_called_once_with(delivery_tag=1, requeue=False)


@pytest.mark.consumer
def test_on_message_rollback_on_handler_error():
    """on_message rolls back the transaction when handler raises."""
    ch = MagicMock()
    method = _make_method()
    mock_conn = MagicMock()
    mock_conn.cursor.side_effect = RuntimeError("DB error")

    with patch("consumer.get_db_conn", return_value=mock_conn):
        consumer.on_message(ch, method, None, _body("recompute_analytics"))

    mock_conn.rollback.assert_called_once()


@pytest.mark.consumer
def test_on_message_nacks_malformed_json():
    """on_message nacks without requeue when body is not valid JSON."""
    ch = MagicMock()
    method = _make_method()

    consumer.on_message(ch, method, None, b"not valid json{{{")

    ch.basic_nack.assert_called_once_with(delivery_tag=1, requeue=False)


@pytest.mark.consumer
def test_on_message_closes_conn_on_success():
    """on_message closes the DB connection after success."""
    ch = MagicMock()
    method = _make_method()
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cur)
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

    with patch("consumer.get_db_conn", return_value=mock_conn):
        consumer.on_message(ch, method, None, _body("recompute_analytics"))

    mock_conn.close.assert_called_once()


@pytest.mark.consumer
def test_on_message_closes_conn_on_error():
    """on_message closes the DB connection even when handler raises."""
    ch = MagicMock()
    method = _make_method()
    mock_conn = MagicMock()
    mock_conn.cursor.side_effect = RuntimeError("DB error")

    with patch("consumer.get_db_conn", return_value=mock_conn):
        consumer.on_message(ch, method, None, _body("recompute_analytics"))

    mock_conn.close.assert_called_once()


# ==========
# TASK_MAP
# ==========
@pytest.mark.consumer
def test_task_map_contains_scrape_new_data():
    """TASK_MAP contains scrape_new_data key."""
    assert "scrape_new_data" in consumer.TASK_MAP


@pytest.mark.consumer
def test_task_map_contains_recompute_analytics():
    """TASK_MAP contains recompute_analytics key."""
    assert "recompute_analytics" in consumer.TASK_MAP


@pytest.mark.consumer
def test_task_map_scrape_points_to_handler():
    """TASK_MAP scrape_new_data points to handle_scrape_new_data."""
    assert consumer.TASK_MAP["scrape_new_data"] is consumer.handle_scrape_new_data


@pytest.mark.consumer
def test_task_map_recompute_points_to_handler():
    """TASK_MAP recompute_analytics points to handle_recompute_analytics."""
    assert consumer.TASK_MAP["recompute_analytics"] is consumer.handle_recompute_analytics
