"""Flask application factory and route definitions for the GradCafe analysis app."""
import os
import subprocess
import sys
import threading
from dotenv import load_dotenv
load_dotenv()

from flask import Flask, jsonify, render_template

import query_data
from load_data import load_data_into_database


# ============
# SHARED STATE
# ============
scraper_state = {"running": False, "message": ""}
scraper_lock = threading.Lock()

db_init_state = {"running": False, "message": ""}
db_init_lock = threading.Lock()


def _reset_state():
    """Reset both state dicts — used in tests to get a clean slate."""
    with scraper_lock:
        scraper_state["running"] = False
        scraper_state["message"] = ""
    with db_init_lock:
        db_init_state["running"] = False
        db_init_state["message"] = ""


# ============
# REAL SCRAPER
# ============
def _real_scraper(scraper_path, llm_file):  # pragma: no cover
    """Run the actual subprocess scraper then load results into DB."""
    subprocess.run(
        [sys.executable, scraper_path, "--mode", "update", "--part", "both"],
        check=True
    )
    load_data_into_database(llm_file)


# ===========
# APP FACTORY
# ===========
def create_app(test_config=None):  # pylint: disable=too-many-statements
    """
    Flask application factory.

    Parameters
    ----------
    test_config : dict, optional
        Overrides applied to ``app.config`` during testing.

        * ``TESTING``      : set ``True`` for Flask test mode.
        * ``SCRAPER_FUNC`` : callable ``(path, llm_file) -> None``.
        * ``DB_LOADER_FUNC`` : callable ``(filename) -> None``.
        * ``QUERY_FUNC``   : callable ``() -> dict``.

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

    # Store default functions in app config
    # Can be overridden by passing test_config to create_app
    app.config["SCRAPER_FUNC"] = _real_scraper
    app.config["DB_LOADER_FUNC"] = load_data_into_database
    app.config["QUERY_FUNC"] = query_data.run_all_queries

    if test_config:
        app.config.update(test_config)

    # --------
    # ROUTES
    # --------
    @app.route("/")
    def index():
        """Render the main index page with current query results."""
        try:  # pylint: disable=broad-exception-caught
            results = app.config["QUERY_FUNC"]()
        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"Could not load query results: {e}")
            results = None
        return render_template("index.html",
                               results=results,
                               scraper=scraper_state,
                               db_init=db_init_state)

    @app.route("/analysis")
    def analysis():
        """Main analysis page."""
        try:
            results = app.config["QUERY_FUNC"]()
        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"Could not load query results: {e}")
            results = None
        return render_template("index.html",
                               results=results,
                               scraper=scraper_state,
                               db_init=db_init_state)

    @app.route("/create-database", methods=["POST"])
    def create_database():
        """Start background DB creation. Returns 409 if already busy."""
        with db_init_lock:
            if db_init_state["running"]:
                return jsonify({"status": "already_running",
                                "message": "Database creation already in progress."}), 409
            if scraper_state["running"]:
                return jsonify({"status": "scraper_running",
                                "message": "Cannot create database while data pull is running."}), 409
            db_init_state["running"] = True
            db_init_state["message"] = "Creating database..."

        loader_func = app.config["DB_LOADER_FUNC"]

        def run_load():
            try:
                filename = os.environ.get("DATA_FILE", "web_scraper/llm_extended_applicant_data.json")
                loader_func(filename)
                with db_init_lock:
                    db_init_state["message"] = "Database created! Click Update Analysis to load results."
            except Exception as e:  # pylint: disable=broad-exception-caught
                with db_init_lock:
                    db_init_state["message"] = f"Error creating database: {e}"
            finally:
                with db_init_lock:
                    db_init_state["running"] = False

        threading.Thread(target=run_load, daemon=True).start()
        return jsonify({"status": "started",
                        "message": "Database creation started!"}), 200

    @app.route("/db-init-status")
    def db_init_status():
        """Return current database initialisation state as JSON."""
        return jsonify(db_init_state)

    @app.route("/pull-data", methods=["POST"])
    def pull_data():
        """
        Start background scrape + load.

        Returns 409 with ``{"busy": true}`` when already running.
        Returns 200 with ``{"ok": true}`` when started successfully.
        """
        scraper_path = os.path.join(os.path.dirname(__file__), "module_2", "runWebScraper.py")
        llm_file = os.path.join(
            os.path.dirname(__file__), "module_2", "new_llm_extended_applicant_data.json")

        with scraper_lock:
            if scraper_state["running"]:
                return jsonify({"busy": True,
                                "message": "Data pull already in progress."}), 409
            if db_init_state["running"]:
                return jsonify({"busy": True,
                                "message": "Cannot pull while database is being created."}), 409
            scraper_state["running"] = True
            scraper_state["message"] = "Pulling new data from Grad Café..."

        scraper_func = app.config["SCRAPER_FUNC"]

        def run_scraper():
            try:
                scraper_func(scraper_path, llm_file)
                with scraper_lock:
                    scraper_state["message"] = "Data pull complete! Click Update Analysis to refresh."
            except Exception as e:  # pylint: disable=broad-exception-caught
                with scraper_lock:
                    scraper_state["message"] = f"Scraper error: {e}"
            finally:
                with scraper_lock:
                    scraper_state["running"] = False

        threading.Thread(target=run_scraper, daemon=True).start()
        return jsonify({"ok": True, "status": "started",
                        "message": "Data pull started!"}), 200

    @app.route("/scraper-status")
    def scraper_status():
        """Return current scraper state as JSON."""
        return jsonify(scraper_state)

    @app.route("/update-analysis", methods=["GET", "POST"])
    def update_analysis():
        """
        Re-run all queries and return JSON results.

        Returns 409 with ``{"busy": true}`` when a background task is running.
        """
        with scraper_lock:
            if scraper_state["running"] or db_init_state["running"]:
                return jsonify({"busy": True,
                                "message": "Cannot update — a background task is running."}), 409

        try:
            results = app.config["QUERY_FUNC"]()
        except Exception as e:  # pylint: disable=broad-exception-caught
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


# ===========
# ENTRY POINT
# ===========
if __name__ == "__main__":  # pragma: no cover
    application = create_app()
    application.run(host="0.0.0.0", port=8080, debug=True)
