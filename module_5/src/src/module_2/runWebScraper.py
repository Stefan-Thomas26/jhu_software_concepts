# Python Packages
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import time
from pathlib import Path
import sys
import os
import argparse
import psycopg

# Add module_3 to path so configuration.py can be found when run as subprocess
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# My Packages
from llm_hosting.app import enrich_row
from webScraper import confirmRobot, scrape_data, clean_data, save_data, load_data
import configuration


# ================
# Define Constants
# ================
BASE_URL = "https://www.thegradcafe.com"
TOTAL_PAGES = 20
# Full scrape outputs (initial load — never overwritten after first run)
SCRAPE_OUTPUT = "module_2/applicant_data.json"
LLM_OUTPUT = "module_2/llm_extended_applicant_data.json"
# Update scrape outputs (overwritten each update run)
NEW_SCRAPE_OUTPUT = "module_2/new_applicant_data.json"
NEW_LLM_OUTPUT = "module_2/new_llm_extended_applicant_data.json"
# Leave at least 1–2 cores free for the OS.
NUM_LLM_WORKERS = max(1, os.cpu_count() - 2)



# ===============
# Parallelization 
# ===============
def process_page(page_num):
    try:
        html_data = scrape_data.scrape_data(BASE_URL, page_num)
        applicants = cleanData.clean_data(html_data, BASE_URL)
        print(f"Finished reading page {page_num}")
        return applicants
    
    except Exception as e:
        print(f"Failed page {page_num}: {e}")
        return []
    # process_page FUNCTION END



# ================
# URL Watermarking
# ================
def get_known_urls():
    """Fetch all URLs already stored in the database. Returns empty set if DB unavailable."""
    
    try:
        USERNAME, PASSWORD, HOST = configuration.load_configuration_file()
        conn = psycopg.connect(
            dbname   = "applicantdata",
            user     = USERNAME,
            password = PASSWORD,
            host     = HOST
        )
        cursor = conn.cursor()
        cursor.execute("SELECT url FROM applicants;")
        urls = {row[0] for row in cursor.fetchall()}
        cursor.close()
        conn.close()
        print(f"Loaded {len(urls)} known URLs from DB.")
        
        return urls
    except Exception as e:
        print(f"Could not load known URLs (DB may not exist yet): {e}")
        return set()



# =========================
# Get Next Applicant Number
# =========================
def get_next_applicant_number():
    """
    Returns the next available applicant number based on how many
    rows are already in the DB. Ensures p_id stays unique across runs.
    """
    try:
        USERNAME, PASSWORD, HOST = configuration.load_configuration_file()
        conn = psycopg.connect(
            dbname   = "applicantdata",
            user     = USERNAME,
            password = PASSWORD,
            host     = HOST
        )
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM applicants;")
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        print(f"DB has {count} existing rows. Next applicantNumber starts at {count + 1}.")
        return count + 1
    
    except Exception as e:
        print(f"Could not get row count (DB may not exist yet): {e}")
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
    confirmRobot.confirm_robot(BASE_URL)

    # Initializations
    start = time.time()
    allGradApplicants = []
    numScrapeWorkers = 10
    
    # run thread pool
    with ThreadPoolExecutor(max_workers = numScrapeWorkers) as executor:
        results = executor.map(process_page, range(1, TOTAL_PAGES+1))
        
        for page_applicants in results:
            allGradApplicants.extend(page_applicants)


    for ii, applicant in enumerate(allGradApplicants, start=1):
        applicant.applicantNumber = ii 

    save_data.save_data(allGradApplicants, SCRAPE_OUTPUT)
    print(f"Full scrape complete — {len(allGradApplicants)} entries saved to {SCRAPE_OUTPUT}.")
    print(f"!!! Elapsed time = {(time.time() - start)/60:.2f} minutes !!!")
    # open file
    # load_data.view_file(Path(SCRAPE_OUTPUT))



# =================================================================
# PART I (b) - Update Scrape
# Scrapes pages sequentially, stopping as soon as a full page of
# already-seen URLs is found. Used for incremental database updates.
# =================================================================
def run_scraper_update():
    """
    Sequential update scrape. Checks each page against known URLs in the DB.
    - Loads all known URLs from the DB before scraping.
    - Checks each page against known URLs.
    - Stops early once an entire page has already been seen.
    - Assigns applicantNumbers continuing from the last DB row count
      so applicantNumber values never clash with existing entries.
    - Saves only new entries to new_applicant_data.json.
    Use this when pulling new data into an existing database.
    """
    
    # Confirm robots.txt
    confirmRobot.confirm_robot(BASE_URL)

    # Load all known URLs from the DB before scraping
    known_urls       = get_known_urls()
    next_num         = get_next_applicant_number() #get number of existing entries in database
    start            = time.time()
    allNewApplicants = []

    for page_num in range(1, TOTAL_PAGES + 1):
        page_applicants = process_page(page_num)

        if not page_applicants:
            continue

        # Filter to only entries not already in the DB
        new_on_page = [a for a in page_applicants if a.url not in known_urls]

        print(f"Page {page_num}: {len(new_on_page)}/{len(page_applicants)} new entries")
        allNewApplicants.extend(new_on_page)
 
        # Early stop — if nothing on this page was new, we've hit old data
        if len(new_on_page) == 0:
            print(f"Page {page_num} fully seen before — stopping early.")
            break

    if not allNewApplicants:
        print("No new entries found.")
        return

    # Assign row numbers to new entries only
    for ii, applicant in enumerate(allNewApplicants, start = next_num):
        applicant.applicantNumber = ii

    save_data.save_data(allNewApplicants, NEW_SCRAPE_OUTPUT)
    print(f"Update scrape complete — {len(allNewApplicants)} new entries saved to {NEW_SCRAPE_OUTPUT}.")
    print(f"!!! Elapsed time = {(time.time() - start)/60:.2f} minutes !!!")
   
    # open file
    # load_data.view_file(Path(NEW_SCRAPE_OUTPUT))



# ========================================
# PART II - run applicant data through LLM
# ========================================

def run_llm(input_file = SCRAPE_OUTPUT, output_file = LLM_OUTPUT, num_workers = NUM_LLM_WORKERS):
    """
        Part II — enrich scraped rows with LLM and save to JSON.
        Enriches scraped rows with LLM-generated university and program fields.
        For a full scrape: reads SCRAPE_OUTPUT, writes to LLM_OUTPUT.
        For an update run: reads NEW_SCRAPE_OUTPUT, writes to NEW_LLM_OUTPUT.
    """

    start = time.time()

    # Load Data using default .json file viewer on machine
    applicantDataRows = load_data.load_data(Path(input_file).resolve())
    print(f"Loaded {len(applicantDataRows)} rows from {input_file}")
    print(f"Running LLM enrichment with {NUM_LLM_WORKERS} worker processes...")


    # IMPORTANT: ProcessPoolExecutor must be inside if __name__ == "__main__"
    # to avoid recursive spawning on Windows/macOS
    with ProcessPoolExecutor(max_workers = num_workers) as executor:
        enriched_rows = list(executor.map(enrich_row, applicantDataRows, chunksize=10))

    # Save the output LLM JSON file
    save_data.save_data(enriched_rows, output_file)
    print(f"LLM enrichment done — saved to {LLM_OUTPUT}")
    print(f"!!! Total elapsed time = {(time.time() - start)/60} minutes !!!")
    # load_data.view_file(Path(outputLLMfilename))



# ===========
# ENTRY POINT
# ===========
# Include arguments for better indepedent testing
if __name__ == "__main__":
 
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        choices = ["full", "update"],
        default = "full",
        help = "Scraping mode: 'full' (parallel, all pages) or 'update' (sequential, early stop)"
    )
    parser.add_argument(
        "--part",
        choices = ["1", "2", "both"],
        default = "both",
        help = "Which part to run: 1 (scrape), 2 (LLM), or both"
    )
    parser.add_argument(
        "--workers",
        type = int,
        default = 2,
        help = "Number of LLM worker processes (default: 2)"
    )
    parser.add_argument(
        "--input",
        default = SCRAPE_OUTPUT,
        help = "Input JSON file for Part II (default: applicant_data.json)"
    )
    args = parser.parse_args()


    # Select correct input/output files based on mode
    is_update   = args.mode == "update"
    scrape_file = NEW_SCRAPE_OUTPUT if is_update else SCRAPE_OUTPUT
    llm_file    = NEW_LLM_OUTPUT    if is_update else LLM_OUTPUT
    input_file  = args.input or scrape_file
 
    def run_part_1():
        if is_update:
            run_scraper_update()
        else:
            run_scraper_full()
 
    if args.part == "1":
        run_part_1()
    elif args.part == "2":
        run_llm(input_file = input_file, output_file = llm_file, num_workers = args.workers)
    else:
        run_part_1()
        run_llm(input_file = scrape_file, output_file = llm_file, num_workers = args.workers)

