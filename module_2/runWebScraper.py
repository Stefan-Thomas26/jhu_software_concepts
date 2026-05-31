from webScraper import scrape, confirmRobot, cleanData, saveData

# ================
# Define Constants 
# ================
BASE_URL = "https://www.thegradcafe.com"
totalPages = 1


# ======================
# Verify robots.txt file 
# ======================
# confirmRobot.confirmRobot(BASE_URL)


# ==============================
# Loop through multiple webpages
# ==============================
allGradApplicants = []
count = 0
for pageNum in range(1, totalPages+1):

    # Scrape webpage for html data
    html_data = scrape.scrape(BASE_URL, pageNum)
    # Collect and organize Grad Applicant data
    applicantsFromCurrentPage, count = cleanData.clean_data(html_data, BASE_URL, count)

    # Add applicants from current page to the larger list of all applicants
    allGradApplicants = allGradApplicants + applicantsFromCurrentPage

# Save this data to a .json file
saveData.save_data(allGradApplicants)
