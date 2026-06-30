"""Flask application factory and route definitions for the GradCafe analysis app."""
import os
from flask import Flask, jsonify, render_template
import pika
import psycopg
from dotenv import load_dotenv
load_dotenv()


import query_data


# ===========
# APP FACTORY
# ===========
def _reset_state():
    """Reset state — used in tests to get a clean slate."""


def create_app(test_config=None):
    """
    Flask application factory.

    Parameters
    ----------
    test_config : dict, optional
        Overrides applied to ``app.config`` during testing.

        * ``TESTING``        : set ``True`` for Flask test mode.
        * ``QUERY_FUNC``     : callable ``() -> dict``.
        * ``PUBLISH_FUNC``   : callable ``(kind, payload) -> None``.

    Returns
    -------
    flask.Flask
    """
    templates_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
    static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
    app = Flask(__name__,
                template_folder=os.path.abspath(templates_dir),
                static_folder=os.path.abspath(static_dir))
    app.secret_key = "gradcafe_setup_key"

    # Import publisher here so tests can override PUBLISH_FUNC without
    # needing a real RabbitMQ connection at import time
    import publisher  # pylint: disable=import-outside-toplevel

    app.config["QUERY_FUNC"] = query_data.run_all_queries
    app.config["PUBLISH_FUNC"] = publisher.publish_task

    if test_config:
        app.config.update(test_config)

    # --------
    # ROUTES
    # --------
    @app.route("/")
    def index():
        """Render the main index page with current query results."""
        try:
            results = app.config["QUERY_FUNC"]()
        except (psycopg.Error, OSError, RuntimeError) as e:
            print(f"Could not load query results: {e}")
            results = None
        return render_template("index.html", results=results,
                    scraper={"running": False, "message": ""},
                    db_init={"running": False, "message": ""})

    @app.route("/analysis")
    def analysis():
        """Main analysis page."""
        try:
            results = app.config["QUERY_FUNC"]()
        except (psycopg.Error, OSError, RuntimeError) as e:
            print(f"Could not load query results: {e}")
            results = None
        return render_template("index.html", results=results,
                       scraper={"running": False, "message": ""},
                       db_init={"running": False, "message": ""})

    @app.route("/pull-data", methods=["POST"])
    def pull_data():
        """
        Enqueue a scrape_new_data task via RabbitMQ.

        Returns 202 with queued status, or 503 if broker is unreachable.
        """
        try:
            app.config["PUBLISH_FUNC"]("scrape_new_data")
        except (pika.exceptions.AMQPError, OSError, RuntimeError) as e:
            return jsonify({"status": "error",
                            "message": f"Could not queue task: {e}"}), 503
        return jsonify({"status": "queued",
                        "message": "Scrape task queued!"}), 202

    @app.route("/create-database", methods=["POST"])
    def create_database():
        """
        Enqueue a recompute_analytics task via RabbitMQ.

        Returns 202 with queued status, or 503 if broker is unreachable.
        """
        try:
            app.config["PUBLISH_FUNC"]("recompute_analytics")
        except (pika.exceptions.AMQPError, OSError, RuntimeError) as e:
            return jsonify({"status": "error",
                            "message": f"Could not queue task: {e}"}), 503
        return jsonify({"status": "queued",
                        "message": "Analytics recompute queued!"}), 202

    @app.route("/scraper-status")
    def scraper_status():
        """Return current scraper state as JSON."""
        return jsonify({"running": False, "message": ""})

    @app.route("/db-init-status")
    def db_init_status():
        """Return current database initialisation state as JSON."""
        return jsonify({"running": False, "message": ""})

    @app.route("/update-analysis", methods=["GET", "POST"])
    def update_analysis():
        """Re-run all queries and return JSON results."""
        try:
            results = app.config["QUERY_FUNC"]()
        except (psycopg.Error, OSError, RuntimeError) as e:
            return jsonify({"status": "error",
                            "message": f"Query error: {e}"}), 500

        serialisable = {}
        for key, val in results.items():
            if val is None:
                serialisable[key] = None
            elif isinstance(val, list):
                serialisable[key] = [list(row) for row in val]
            else:
                serialisable[key] = val

        return jsonify({"status": "ok", "results": serialisable}), 200

    return app
