import json
import load_json
import load_data
from pathlib import Path

def main():
    # Find absolute path to .json file on local machine
    applicantDataFilename = "applicant_data.json"
    applicantDataFilePath = Path(applicantDataFilename)
    
    # Load JSON file
    applicants = load_json._load_json(applicantDataFilePath.resolve())
    
    # Create datapath with applicant data
    load_data.load_into_db(applicants)
    
    # applicants = enrich_with_llm(applicants)
    # load_into_db(applicants)

if __name__ == "__main__":
    main()