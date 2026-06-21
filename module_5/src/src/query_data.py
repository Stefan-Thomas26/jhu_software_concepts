# Python Packages
import psycopg
# My Packages
import configuration



# ========================================
# Get connection to applicantdata database
# ========================================
def get_connection(): # pragma: no cover
    USERNAME, PASSWORD, HOST = configuration.load_configuration_file()
    return psycopg.connect(
        dbname="applicantdata",
        user=USERNAME,
        password=PASSWORD,
        host=HOST
    )



# ===========
# Run a query
# ===========
def run_query(cursor, sql, params=None):
    """Executes a query and returns all results."""
    cursor.execute(sql, params or ())
    return cursor.fetchall()



# =========
# QUESTIONS
# =========
def q1_fall2026_count(cursor):
    """Q1: How many entries applied for Fall 2026?"""
    
    sql = """
        SELECT COUNT(*)
        FROM applicants
        WHERE semester = 'Fall 2026';
    """
    result = run_query(cursor, sql)
    count = result[0][0]
    print(f"Q1: Entries for Fall 2026: {count}")
    return count
 
 

def q2_international_percent(cursor):
    """Q2: What percentage of entries are from international students?"""
    
    sql = """
        SELECT
            ROUND(
                100.0 * COUNT(*) FILTER (WHERE citizenship = 'International')
                / COUNT(*),
                2
            ) AS international_pct
        FROM applicants;
    """
    result = run_query(cursor, sql)
    pct = result[0][0]
    print(f"Q2: Percentage international students: {pct}%")
    return pct
 
 
 
def q3_average_scores(cursor):
    """Q3: Average GPA, GRE, GRE_V, GRE_AW of applicants who provided these metrics."""
    
    sql = """
        SELECT
            ROUND(AVG(gpa)::numeric,   2) AS avg_gpa,
            ROUND(AVG(gre)::numeric,   2) AS avg_gre,
            ROUND(AVG(gre_v)::numeric, 2) AS avg_gre_v,
            ROUND(AVG(gre_aw)::numeric,2) AS avg_gre_aw
        FROM applicants
        WHERE gpa   IS NOT NULL
           OR gre   IS NOT NULL
           OR gre_v IS NOT NULL
           OR gre_aw IS NOT NULL;
    """
    result = run_query(cursor, sql)
    avg_gpa, avg_gre, avg_gre_v, avg_gre_aw = result[0]
    print(f"Q3: Avg GPA: {avg_gpa}, Avg GRE: {avg_gre}, Avg GRE_V: {avg_gre_v}, Avg GRE_AW: {avg_gre_aw}")
    return result[0]
 
 

def q4_american_fall2026_gpa(cursor):
    """Q4: Average GPA of American students in Fall 2026."""
    
    sql = """
        SELECT ROUND(AVG(gpa)::numeric, 2)
        FROM applicants
        WHERE citizenship = 'American'
          AND semester    = 'Fall 2026'
          AND gpa IS NOT NULL;
    """
    result = run_query(cursor, sql)
    avg = result[0][0]
    print(f"Q4: Average GPA of American students in Fall 2026: {avg}")
    return avg
 
 

def q5_fall2026_acceptance_pct(cursor):
    """Q5: What percent of Fall 2026 entries are Acceptances?"""
    
    sql = """
        SELECT
            ROUND(
                100.0 * COUNT(*) FILTER (WHERE status = 'Accepted')
                / COUNT(*),
                2
            ) AS acceptance_pct
        FROM applicants
        WHERE semester = 'Fall 2026';
    """
    result = run_query(cursor, sql)
    pct = result[0][0]
    print(f"Q5: Acceptance rate for Fall 2026: {pct}%")
    return pct
 

 
def q6_fall2026_accepted_gpa(cursor):
    """Q6: Average GPA of Fall 2026 acceptances."""
    
    sql = """
        SELECT ROUND(AVG(gpa)::numeric, 2)
        FROM applicants
        WHERE semester = 'Fall 2026'
          AND status   = 'Accepted'
          AND gpa IS NOT NULL;
    """
    result = run_query(cursor, sql)
    avg = result[0][0]
    print(f"Q6: Average GPA of Fall 2026 acceptances: {avg}")
    return avg
 

 
def q7_jhu_masters_cs(cursor):
    """Q7: How many entries applied to JHU for a Masters in Computer Science?"""
    
    sql = """
        SELECT COUNT(*)
        FROM applicants
        WHERE program    ILIKE '%%Johns Hopkins%%'
          AND program    ILIKE '%%Computer Science%%'
          AND degreeType ILIKE '%%Master%%';
    """
    result = run_query(cursor, sql)
    count = result[0][0]
    print(f"Q7: JHU Masters CS applicants: {count}")
    return count
 
 

def q8_top_schools_phd_cs_2026(cursor):
    """Q8: How many 2026 acceptances from Georgetown, MIT, Stanford, or CMU for PhD CS?"""
    
    sql = """
        SELECT COUNT(*)
        FROM applicants
        WHERE program ILIKE ANY(ARRAY[
                '%%Georgetown%%',
                '%%Massachusetts Institute of Technology%%',
                '%%MIT%%',
                '%%Stanford%%',
                '%%Carnegie Mellon%%'
              ])
          AND program    ILIKE '%%Computer Science%%'
          AND degreeType ILIKE '%%PhD%%'
          AND status     = 'Accepted'
          AND semester   LIKE '%%2026%%';
    """
    result = run_query(cursor, sql)
    count = result[0][0]
    print(f"Q8: # Acceptances from  Georgetown, MIT, Stanford, or CMU for PhD CS in 2026: {count}")
    return count
 
 

def q9_llm_fields(cursor):
    """
    Q9: Do numbers for Q8 change using LLM generated fields?
    """

    # # Check if LLM columns exist first
    # check_sql = """
    #     SELECT column_name 
    #     FROM information_schema.columns 
    #     WHERE table_name = 'applicants' 
    #       AND column_name IN ('llm_generated_university', 'llm_generated_program');
    # """
    # cols = run_query(cursor, check_sql)
 
    # if len(cols) < 2:
    #     print("Q9: LLM generated fields not yet in database — skipping.")
    #     print("    Re-run load_data.py with LLM enrichment enabled to populate these fields.")
    #     return None
 
    sql = """
        SELECT COUNT(*)
        FROM applicants
        WHERE llm_generated_university ILIKE ANY(ARRAY[
                '%%Georgetown%%',
                '%%Massachusetts Institute of Technology%%',
                '%%MIT%%',
                '%%Stanford%%',
                '%%Carnegie Mellon%%'
              ])
          AND llm_generated_program ILIKE '%%Computer Science%%'
          AND degreeType ILIKE '%%PhD%%'
          AND status     = 'Accepted'
          AND semester   LIKE '%%2026%%';
    """
    result = run_query(cursor, sql)
    count = result[0][0]

    print(f"Q9: Top school PhD CS 2026 acceptances (LLM fields): {count}")
    return count
 
 

def q10_phd_rejection_rate_by_year(cursor):
    """
    Q10: What is the rejection rate of PhD applicants in 2025 vs 2026?
    Curious whether PhD rejection rates have changed year over year.
    """
    
    sql = """
        SELECT
            semester,
            COUNT(*) AS total,
            COUNT(*) FILTER (WHERE status = 'Rejected') AS rejections,
            ROUND(
                100.0 * COUNT(*) FILTER (WHERE status = 'Rejected') / COUNT(*),
                2
            ) AS rejection_pct
        FROM applicants
        WHERE degreeType ILIKE '%%PhD%%'
          AND (semester LIKE '%%2026%%' OR semester LIKE '%%2025%%')
        GROUP BY semester
        ORDER BY semester DESC;
    """
    results = run_query(cursor, sql)

    print("\nQ10: PhD rejection rate by year (2025 vs 2026):")
    for row in results:
        print(f"  {row[0]}: {row[3]}% rejected ({row[2]}/{row[1]} applicants)")
    return results
 


def q11_phd_gpa_accepted_vs_rejected(cursor):
    """
    Q11: What is the average GPA of PhD students who were accepted
    vs rejected in 2026? Curious whether GPA is a strong differentiator.
    """
    
    sql = """
        SELECT
            status,
            COUNT(*) AS total,
            ROUND(AVG(gpa)::numeric, 2) AS avg_gpa
        FROM applicants
        WHERE degreeType ILIKE '%%PhD%%'
          AND semester LIKE '%%2026%%'
          AND status IN ('Accepted', 'Rejected')
          AND gpa IS NOT NULL
        GROUP BY status
        ORDER BY status;
    """
    results = run_query(cursor, sql)
    print("\nQ11: Average GPA of PhD applicants accepted vs rejected in 2026:")
    for row in results:
        print(f"  {row[0]}: avg GPA = {row[2]} ({row[1]} applicants with GPA reported)")
    return results



# ===============
# Run all queries
# ===============
def run_all_queries():
    """Run all queries and return results as a dictionary."""
    
    conn   = get_connection()
    cursor = conn.cursor()
    results = {}

    print("=" * 60)
    print("GRAD CAFÉ DATA ANALYSIS")
    print("=" * 60)
 
    try:
        results["q1"]  = q1_fall2026_count(cursor)
        results["q2"]  = q2_international_percent(cursor)
        results["q3"]  = q3_average_scores(cursor)
        results["q4"]  = q4_american_fall2026_gpa(cursor)
        results["q5"]  = q5_fall2026_acceptance_pct(cursor)
        results["q6"]  = q6_fall2026_accepted_gpa(cursor)
        results["q7"]  = q7_jhu_masters_cs(cursor)
        results["q8"]  = q8_top_schools_phd_cs_2026(cursor)
        results["q9"]  = q9_llm_fields(cursor)
        results["q10"] = q10_phd_rejection_rate_by_year(cursor)
        results["q11"] = q11_phd_gpa_accepted_vs_rejected(cursor)
    
    except Exception as e:
        print(f"Query error: {e}")
        print("=" * 60)
    
    finally:
        cursor.close()
        conn.close()
 
    return results