# Python Packages
import subprocess
import sys
import os
import threading
from flask import Flask, render_template, jsonify, request, redirect, url_for, session

# My Packages
import query_data
from load_data import load_data_into_database
import configuration


# =====================
# Create Flask Instance
# =====================
app = Flask(__name__)
app.secret_key = "gradcafe_setup_key"

# =============
# SCRAPER STATE
# =============
scraper_state = {"running": False, "message": ""}
scraper_lock  = threading.Lock()

# ===================
# DATABASE INIT STATE
# ===================
 
db_init_state = {"running": False, "message": ""}
db_init_lock  = threading.Lock()



# ======
# ROUTES
# ====== 
@app.route("/")
def index():
    results = query_data.run_all_queries()
    return render_template("index.html",
                           results=results,
                           scraper=scraper_state,
                           db_init=db_init_state)
 


@app.route("/create-database", methods=["POST"])
def create_database():
    """
    Runs load_data_into_database() in a background thread.
    Creates the database and loads the full initial scrape from
    llm_extended_applicant_data.json (the permanent archive).
    """
    with db_init_lock:
        if db_init_state["running"]:
            return jsonify({
                "status":  "already_running",
                "message": "Database creation already in progress. Please wait."
            })
        if scraper_state["running"]:
            return jsonify({
                "status":  "scraper_running",
                "message": "Cannot create database while data pull is running."
            })
        db_init_state["running"] = True
        db_init_state["message"] = "Creating database and loading data. This may take a few minutes..."

    def run_load():
        try:
            # Read the data filename from userConfig.json
            config_path = configuration.get_configuration_filepath()
            config      = configuration.load_json(config_path)
            filename    = config[0].get("data_file", "module_2/llm_extended_applicant_data.json") #default is module_2/llm_extended_applicant_data.json

            # Main function
            load_data_into_database(filename)
 
            with db_init_lock:
                db_init_state["message"] = "Database created! Click Update Analysis to load results."
        
        except Exception as e:
            with db_init_lock:
                db_init_state["message"] = f"Error creating database: {e}"
        
        finally:
            with db_init_lock:
                db_init_state["running"] = False
 
    threading.Thread(target=run_load, daemon=True).start()
    return jsonify({
        "status":  "started",
        "message": "Database creation started! This may take a few minutes."
    })


@app.route("/db-init-status")
def db_init_status():
    return jsonify(db_init_state)



@app.route("/pull-data", methods=["POST"])
def pull_data():
    """
    Runs the web scraper in a background thread to pull new entries.
    Flow:
      1. runWebScraper.py --mode update --part both
         a. Scrapes new entries → applicant_data.json
         b. Runs LLM enrichment → llm_extended_applicant_data.json
      2. Loads llm_extended_applicant_data.json into the DB
    The full archive files (applicant_data.json, llm_extended_applicant_data.json)
    are never touched during an update run.
    """
    scraper_path = os.path.join(os.path.dirname(__file__), "module_2", "runWebScraper.py")
    llm_file     = os.path.join(os.path.dirname(__file__), "module_2", "new_llm_extended_applicant_data.json")
 
    with scraper_lock:
        if scraper_state["running"]:
            return jsonify({
                "status":  "already_running",
                "message": "Data pull already in progress. Please wait."
            })
        if db_init_state["running"]:
            return jsonify({
                "status":  "db_running",
                "message": "Cannot pull data while database is being created."
            })
        scraper_state["running"] = True
        scraper_state["message"] = "Pulling new data from Grad Café..."
 
 
    def run_scraper():
        try:
            # Step 1 — scrape new entries and run them through the LLM
            scraper_state["message"] = "Scraping new entries from Grad Café..."
            subprocess.run(
                [sys.executable, scraper_path, "--mode", "update", "--part", "both"],
                check=True
            )
 
            # Step 2 — load the LLM-enriched results into the DB
            with scraper_lock:
                scraper_state["message"] = "Loading enriched entries into database..."
            load_data_into_database(llm_file)
 
            with scraper_lock:
                scraper_state["message"] = "Data pull complete! Click Update Analysis to refresh."
        except Exception as e:
            with scraper_lock:
                scraper_state["message"] = f"Scraper error: {e}"
        finally:
            with scraper_lock:
                scraper_state["running"] = False
 
    threading.Thread(target=run_scraper, daemon=True).start()
    return jsonify({"status": "started", "message": "Data pull started!"})



@app.route("/scraper-status")
def scraper_status():
    return jsonify(scraper_state)
 
 

@app.route("/update-analysis")
def update_analysis():
    with scraper_lock:
        if scraper_state["running"] or db_init_state["running"]:
            return jsonify({
                "status":  "busy",
                "message": "Cannot update — a background task is currently running."
            }), 409
 
    results = query_data.run_all_queries()
    serialisable = {}
    for key, val in results.items():
        if val is None:
            serialisable[key] = None
        elif isinstance(val, list):
            serialisable[key] = [list(row) for row in val]
        else:
            serialisable[key] = val
 
    return jsonify({"status": "ok", "results": serialisable})



# ===========
# ENTRY POINT
# ===========
# run the app with run.py is called from command line
if __name__ == '__main__':
    # Run the application at port 8080 and local host 0.0.0.0
    app.run(host = '0.0.0.0', port = 8080, debug=True)