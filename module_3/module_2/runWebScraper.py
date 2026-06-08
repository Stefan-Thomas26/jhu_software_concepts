from concurrent.futures import ThreadPoolExecutor
from webScraper import confirmRobot, scrapeData, cleanData, saveData, loadData
import time
from pathlib import Path
from llm_hosting.app import enrich_row


# ================
# Define Constants
# ================
start = time.time()
BASE_URL = "https://www.thegradcafe.com"
totalPages = 2000

# ======================
# Verify robots.txt file 
# ======================
confirmRobot.confirm_robot(BASE_URL)


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

allGradApplicants = []
numScrapeWorkers = 10
# run thread pool
with ThreadPoolExecutor(max_workers = numScrapeWorkers) as executor:
    results = executor.map(process_page, range(1, totalPages+1))
    
    for page_applicants in results:
        allGradApplicants.extend(page_applicants)


for ii, applicant in enumerate(allGradApplicants, start=1):
    applicant.applicantNumber = ii 

# Create filename to store applicant data PRE LLM
applicantDataFilename = "applicant_data.json"

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
numLlmWorkers = 1 # Never figured out how to parallelize this

# Load Data using default .json file viewer on machine
applicantDataRows = loadData.load_data(applicantDataFilePath.resolve())

# run thread pool
with ThreadPoolExecutor(max_workers = numLlmWorkers) as executor:
    enriched_rows = list(executor.map(enrich_row, applicantDataRows))

outputLLMfilename = "llm_extended_applicant_data.json"
saveData.save_data(enriched_rows, outputLLMfilename)

# Find absolute path to .json file on local machine
applicantDataFilePath_LLM = Path(outputLLMfilename)

# Open File
loadData.view_file(applicantDataFilePath_LLM)


# ==============================
# Loop through multiple webpages
# ==============================
# allGradApplicants = []
# count = 0
# for pageNum in range(1, totalPages+1):

#     # Scrape webpage for html data
#     html_data = scrape.scrape(BASE_URL, pageNum)
#     # Collect and organize Grad Applicant data
#     applicantsFromCurrentPage, count = cleanData.clean_data(html_data, BASE_URL, count)

#     # Add applicants from current page to the larger list of all applicants
#     allGradApplicants = allGradApplicants + applicantsFromCurrentPage

# # Save this data to a .json file
# saveData.save_data(allGradApplicants)
