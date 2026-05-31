from concurrent.futures import ThreadPoolExecutor
from webScraper import confirmRobot, scrapeData, cleanData, saveData, loadData
import time
from pathlib import Path

# ================
# Define Constants 
# ================
start = time.time()
BASE_URL = "https://www.thegradcafe.com"
totalPages = 3000
numWorkers = 10

# ======================
# Verify robots.txt file 
# ======================
# confirmRobot.confirmRobot(BASE_URL)


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

allGradApplicants = []

with ThreadPoolExecutor(max_workers = numWorkers) as executor:
    results = executor.map(process_page, range(1, totalPages+1))
    
    for page_applicants in results:
        allGradApplicants.extend(page_applicants)


for ii, applicant in enumerate(allGradApplicants, start=1):
    applicant.applicantNumber = ii 

outputFilename = "applicant_data.json"
saveData.save_data(allGradApplicants, outputFilename)

# Find absolute path to .json file on local machine
outputFilePath = Path(outputFilename)

# Load Data using default .json file viewer on machine
loadData.load_data(outputFilePath.resolve())

print(f"!!! Elapsed time = {(time.time() - start)/60} minutes !!!")
print("::::::::::::::::::::::")

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
