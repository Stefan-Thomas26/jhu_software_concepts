import load_json
import load_data
from pathlib import Path

from flask import Flask, render_template

def run_all_queries():
    # Find absolute path to .json file on local machine
    applicantDataFilename = "module_2/applicant_data.json"
    applicantDataFilePath = Path(applicantDataFilename)

    # Load JSON file
    applicants = load_json._load_json(applicantDataFilePath.resolve())
    
    # Create datapath with applicant data
    load_data.load_into_db(applicants)
    
    # applicants = enrich_with_llm(applicants)
    # load_into_db(applicants)
   
    # ================== 
    # Make flask webpage
    # ==================
    # Run the application at port 8080 and local host 0.0.0.0
    # app.run(host = '0.0.0.0', port = 8080, debug=True)

if __name__ == "__main__":
    main()