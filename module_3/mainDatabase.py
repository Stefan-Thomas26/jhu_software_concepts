import load_json
import load_data
import query_data
from pathlib import Path

from flask import Flask, render_template

def main():
    # Find absolute path to .json file on local machine
    applicantDataFilename = "module_2/applicant_data.json"
    applicantDataFilePath = Path(applicantDataFilename)

    # Load JSON file
    applicants = load_json._load_json(applicantDataFilePath.resolve())
    
    # Create datapath with applicant data
    load_data.load_into_db(applicants)
    
    # applicants = enrich_with_llm(applicants)
    # load_into_db(applicants)

    # ================
    # Answer Questions
    # ================
    conn = query_data.get_connection()
    cursor = conn.cursor()

    print("=" * 60)
    print("GRAD CAFÉ DATA ANALYSIS")
    print("=" * 60)

    query_data.q1_fall2026_count(cursor)
    query_data.q2_international_percent(cursor)
    query_data.q3_average_scores(cursor)
    query_data.q4_american_fall2026_gpa(cursor)
    query_data.q5_fall2026_acceptance_pct(cursor)
    query_data.q6_fall2026_accepted_gpa(cursor)
    query_data.q7_jhu_masters_cs(cursor)
    query_data.q8_top_schools_phd_cs_2026(cursor)
    
    # !!!!!!!!!!STEFAN TODO - FIX LLM STUFF!!!!!!!!!!!!
    # query_data.q9_llm_fields(cursor)


    query_data.q10_phd_rejection_rate_by_year(cursor)
    query_data.q11_phd_gpa_accepted_vs_rejected(cursor)
    
    print("=" * 60)

    cursor.close()
    conn.close()
    # ================== 
    # Make flask webpage
    # ==================
    # Run the application at port 8080 and local host 0.0.0.0
    # app.run(host = '0.0.0.0', port = 8080, debug=True)

if __name__ == "__main__":
    main()