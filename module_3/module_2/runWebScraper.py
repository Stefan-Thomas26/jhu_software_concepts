# Python Packages
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import time
from pathlib import Path
import os
import argparse

# My Packages
from llm_hosting.app import enrich_row
from webScraper import confirmRobot, scrapeData, cleanData, saveData, loadData



# ================
# Define Constants
# ================
BASE_URL = "https://www.thegradcafe.com"
TOTAL_PAGES = 1510
SCRAPE_OUTPUT = "applicant_data.json"
LLM_OUTPUT = "llm_extended_applicant_data.json"
# Leave at least 1–2 cores free for the OS.
NUM_LLM_WORKERS = max(1, os.cpu_count() - 2)



# ===============
# Parallelization 
# ===============
def process_page(page_num):
    try:
        html_data = scrapeData.scrape_data(BASE_URL, page_num)
        applicants = cleanData.clean_data(html_data, BASE_URL)
        print(f"Finished reading page {page_num}")
        return applicants
    
    except Exception as e:
        print(f"Failed page {page_num}: {e}")
        return []
    # process_page FUNCTION END



# ===============================================
# PART I - Create a .json with all applicant data
# ===============================================
def run_scraper():
    """Part I — scrape all pages and save to JSON."""

    # ======================
    # Verify robots.txt file 
    # ======================
    confirmRobot.confirm_robot(BASE_URL)

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

    # Create filename to store applicant data PRE LLM
    applicantDataFilename = SCRAPE_OUTPUT

    saveData.save_data(allGradApplicants, applicantDataFilename)
    print(f"!!! Elapsed time = {(time.time() - start)/60} minutes !!!")
    print("::::::::::::::::::::::")

    # Find absolute path to .json file on local machine
    applicantDataFilePath = Path(applicantDataFilename)

    # open file
    loadData.view_file(applicantDataFilePath)



# ========================================
# PART II - run applicant data through LLM
# ========================================

def run_llm(input_file = SCRAPE_OUTPUT, num_workers = NUM_LLM_WORKERS):
    """Part II — enrich scraped rows with LLM and save to JSON."""

    start = time.time()

    # Load Data using default .json file viewer on machine
    applicantDataRows = loadData.load_data(Path(input_file).resolve())
    print(f"Loaded {len(applicantDataRows)} rows from {input_file}")
    print(f"Running LLM enrichment with {NUM_LLM_WORKERS} worker processes...")


    # IMPORTANT: ProcessPoolExecutor must be inside if __name__ == "__main__"
    # to avoid recursive spawning on Windows/macOS
    with ProcessPoolExecutor(max_workers = num_workers) as executor:
        enriched_rows = list(executor.map(enrich_row, applicantDataRows, chunksize=10))

    # Save the output LLM JSON file
    outputLLMfilename = LLM_OUTPUT
    saveData.save_data(enriched_rows, outputLLMfilename)
    print(f"LLM enrichment done — saved to {LLM_OUTPUT}")
    print(f"!!! Total elapsed time = {(time.time() - start)/60} minutes !!!")
    loadData.view_file(Path(outputLLMfilename))


# Include arguments for better indepedent testing
if __name__ == "__main__":

    parser = argparse.ArgumentParser()
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

    if args.part == "1":
        run_scraper()
    elif args.part == "2":
        run_llm(input_file=args.input, num_workers=args.workers)
    else:
        run_scraper()
        run_llm(num_workers=args.workers)


