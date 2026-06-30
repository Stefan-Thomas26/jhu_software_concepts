"""Run Web Scraper - the top level file that is parallelized and will scrape GradCafe."""

# Python Packages
import os
import sys
import time
import argparse
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from pathlib import Path

import psycopg

# Add parent directory to path so configuration.py can be found when run as subprocess
sys.path.insert(0, os.path.dirname(__file__))  # web_scraper/ first
sys.path.insert(1, os.path.join(os.path.dirname(__file__), ".."))  # etl/ second
sys.path.insert(2, os.path.join(os.path.dirname(__file__), "..", "..", ".."))  # /app third

# My Packages
from llm_hosting.app import enrich_row
import scrape_data
import clean_data
import save_data
import confirm_robots
import load_data
from shared import configuration


# ================
# Define Constants
# ================
BASE_URL = "https://www.thegradcafe.com"
TOTAL_PAGES = 20
# General Pathing
_HERE = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.environ.get("DATA_DIR", os.path.join(_HERE, "..", "..", "..", "data"))
# Full scrape outputs (initial load — never overwritten after first run)
SCRAPE_OUTPUT = os.path.join(_DATA_DIR, "applicant_data.json")
LLM_OUTPUT = os.path.join(_DATA_DIR, "llm_extended_applicant_data.json")
# Update scrape outputs (overwritten each update run)
NEW_SCRAPE_OUTPUT = os.path.join(_HERE, "new_applicant_data.json")
NEW_LLM_OUTPUT = os.path.join(_HERE, "new_llm_extended_applicant_data.json")
# Leave at least 1–2 cores free for the OS
NUM_SCRAPE_WORKERS = 10
NUM_LLM_WORKERS = max(1, os.cpu_count() - 2)

# ===============
# Parallelization
# ===============
def process_page(page_num):
    """Scrape and parse a single page, returning a list of GradApplicant objects."""
    try:
        html_data = scrape_data.scrape_data(BASE_URL, page_num)
        applicants = clean_data.clean_data(html_data, BASE_URL)
        print(f"Finished reading page {page_num}")
        return applicants
    except (RuntimeError, ValueError) as e:
        print(f"Failed page {page_num}: {e}")
        return []


# ================
# URL Watermarking
# ================
def get_known_urls():
    """Fetch all URLs already stored in the database. Returns empty set if DB unavailable."""
    try:
        username, password, host = configuration.load_configuration_file()
        conn = psycopg.connect(
            dbname="applicantdata",
            user=username,
            password=password,
            host=host
        )
        cursor = conn.cursor()
        cursor.execute("SELECT url FROM applicants;")
        urls = {row[0] for row in cursor.fetchall()}
        cursor.close()
        conn.close()
        print(f"Loaded {len(urls)} known URLs from DB.")
        return urls
    except (psycopg.OperationalError, psycopg.errors.UndefinedTable) as e:
        print(f"Could not load known URLs (table may not exist yet): {e}")
        return set()


# =========================
# Get Next Applicant Number
# =========================
def get_next_applicant_number():
    """
    Return the next available applicant number based on how many
    rows are already in the DB. Ensures applicant_number stays unique across runs.
    """
    try:
        username, password, host = configuration.load_configuration_file()
        conn = psycopg.connect(
            dbname="applicantdata",
            user=username,
            password=password,
            host=host
        )
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM applicants;")
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        print(f"DB has {count} existing rows. Next applicant_number starts at {count + 1}.")
        return count + 1
    except (psycopg.OperationalError, psycopg.errors.UndefinedTable) as e:
        print(f"Could not load known URLs (table may not exist yet): {e}")
        return 1


# ==================================================================
# PART I (a) - Create a .json with all applicant data
# Scrapes all pages in parallel. Used for the initial database load.
# ==================================================================
def run_scraper_full():
    """
    Part I — scrape all pages and save to JSON.
    Full parallel scrape of all pages. Use this for the initial database load.
    """
    # Verify robots.txt file
    confirm_robots.confirm_robot(BASE_URL)

    # Initializations
    start = time.time()
    all_grad_applicants = []

    # Run thread pool
    with ThreadPoolExecutor(max_workers=NUM_SCRAPE_WORKERS) as executor:
        results = executor.map(process_page, range(1, TOTAL_PAGES + 1))

        for page_applicants in results:
            all_grad_applicants.extend(page_applicants)

    for ii, applicant in enumerate(all_grad_applicants, start=1):
        applicant.applicant_number = ii

    save_data.save_data(all_grad_applicants, SCRAPE_OUTPUT)
    print(f"Full scrape complete — {len(all_grad_applicants)} entries saved to {SCRAPE_OUTPUT}.")
    print(f"!!! Elapsed time = {(time.time() - start)/60:.2f} minutes !!!")


# =================================================================
# PART I (b) - Update Scrape
# Scrapes pages sequentially, stopping as soon as a full page of
# already-seen URLs is found. Used for incremental database updates.
# =================================================================
def run_scraper_update():
    """
    Sequential update scrape. Checks each page against known URLs in the DB.
    - Loads all known URLs from the DB before scraping.
    - Stops early once an entire page has already been seen.
    - Assigns applicant_numbers continuing from the last DB row count.
    - Saves only new entries to new_applicant_data.json.
    Use this when pulling new data into an existing database.
    """
    # Confirm robots.txt
    confirm_robots.confirm_robot(BASE_URL)

    # Load all known URLs from the DB before scraping
    known_urls = get_known_urls()
    next_num = get_next_applicant_number()
    start = time.time()
    all_new_applicants = []

    for page_num in range(1, TOTAL_PAGES + 1):
        page_applicants = process_page(page_num)

        if not page_applicants:
            continue

        # Filter to only entries not already in the DB
        new_on_page = [a for a in page_applicants if a.url not in known_urls]
        print(f"Page {page_num}: {len(new_on_page)}/{len(page_applicants)} new entries")
        all_new_applicants.extend(new_on_page)

        # Early stop — if nothing on this page was new, we've hit old data
        if not new_on_page:
            print(f"Page {page_num} fully seen before — stopping early.")
            break

    if not all_new_applicants:
        print("No new entries found.")
        return

    # Assign row numbers to new entries only
    for ii, applicant in enumerate(all_new_applicants, start=next_num):
        applicant.applicant_number = ii

    save_data.save_data(all_new_applicants, NEW_SCRAPE_OUTPUT)
    print(f"Update scrape complete — {len(all_new_applicants)} new entries saved to {NEW_SCRAPE_OUTPUT}.")
    print(f"!!! Elapsed time = {(time.time() - start)/60:.2f} minutes !!!")


# ========================================
# PART II - run applicant data through LLM
# ========================================
def run_llm(input_file=SCRAPE_OUTPUT, output_file=LLM_OUTPUT, num_workers=NUM_LLM_WORKERS):
    """
    Part II — enrich scraped rows with LLM and save to JSON.
    Enriches scraped rows with LLM-generated university and program fields.
    For a full scrape: reads SCRAPE_OUTPUT, writes to LLM_OUTPUT.
    For an update run: reads NEW_SCRAPE_OUTPUT, writes to NEW_LLM_OUTPUT.
    """
    start = time.time()

    # Load data from JSON file
    applicant_data_rows = load_data.load_data(Path(input_file).resolve())
    print(f"Loaded {len(applicant_data_rows)} rows from {input_file}")
    print(f"Running LLM enrichment with {num_workers} worker processes...")

    # IMPORTANT: ProcessPoolExecutor must be inside if __name__ == "__main__"
    # to avoid recursive spawning on Windows/macOS
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        enriched_rows = list(executor.map(enrich_row, applicant_data_rows, chunksize=10))

    # Save the output LLM JSON file
    save_data.save_data(enriched_rows, output_file)
    print(f"LLM enrichment done — saved to {output_file}")
    print(f"!!! Total elapsed time = {(time.time() - start)/60} minutes !!!")


# ===========
# ENTRY POINT
# ===========
if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        choices=["full", "update"],
        default="full",
        help="Scraping mode: 'full' (parallel, all pages) or 'update' (sequential, early stop)"
    )
    parser.add_argument(
        "--part",
        choices=["1", "2", "both"],
        default="both",
        help="Which part to run: 1 (scrape), 2 (LLM), or both"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=2,
        help="Number of LLM worker processes (default: 2)"
    )
    parser.add_argument(
        "--input",
        default=SCRAPE_OUTPUT,
        help="Input JSON file for Part II (default: applicant_data.json)"
    )
    args = parser.parse_args()

    # Select correct input/output files based on mode
    is_update = args.mode == "update"
    SCRAPE_FILE = NEW_SCRAPE_OUTPUT if is_update else SCRAPE_OUTPUT
    LLM_FILE = NEW_LLM_OUTPUT if is_update else LLM_OUTPUT
    scrape_input_file = args.input or SCRAPE_FILE

    def run_part_1():
        """Run only Part 1 of the scraping pipeline."""
        if is_update:
            run_scraper_update()
        else:
            run_scraper_full()

    if args.part == "1":
        run_part_1()
    elif args.part == "2":
        run_llm(input_file=scrape_input_file, output_file=LLM_FILE, num_workers=args.workers)
    else:
        run_part_1()
        run_llm(input_file=SCRAPE_FILE, output_file=LLM_FILE, num_workers=args.workers)
