import subprocess
import sys
import os

def pull_and_load():
    # Step 1: Run the scraper
    print("Scraping new data...")
    scraper_path = os.path.join(os.path.dirname(__file__), "module_2", "runWebScraper.py")
    subprocess.run([sys.executable, scraper_path], check=True)

    # Step 2: Load new data into the database
    print("Loading new data into database...")
    import load_data
    load_data.load_data_to_database("module_2/applicant_data.json", "applicantdata")
    print("Done!")

if __name__ == "__main__":
    pull_and_load()