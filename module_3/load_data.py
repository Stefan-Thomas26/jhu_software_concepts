import psycopg
import json
import get_credentials
import load_json


# ==================================================================

# get credentials
USERNAME, PASSWORD, HOST = get_credentials._get_credentials()

# Connect to an already-existing database in order to create a new database
defaultConnection = psycopg.connect(
    dbname = "postgres",
    user = USERNAME,
    password = PASSWORD,
    host = HOST
    )

defaultConnection.autocommit = True


# Create a new database
with defaultConnection.cursor() as default_cur:

    # Execute out select all command
    try:
        default_cur.execute("CREATE DATABASE applicantdata")
        print("Created database applicantdata!")
    except psycopg.errors.DuplicateDatabase:
        print("applicantdata database already exists!")



# Close default connections
default_cur.close()
defaultConnection.close()


conn = psycopg.connect(
    dbname = "applicantdata",
    user = USERNAME,
    password = PASSWORD,
    host = HOST
    )



# Create table sql string
def _create_table_sql():
    CREATE_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS applicants (
        p_id                    INTEGER PRIMARY KEY,
        program                 TEXT,
        comments                TEXT,
        date_added              DATE,
        url                     TEXT,
        status                  TEXT,
        term                    TEXT,
        us_or_international     TEXT,
        gpa                     FLOAT,
        gre                     FLOAT,
        gre_v                   FLOAT,
        gre_aw                  FLOAT,
        degree                  TEXT,
        llm_generated_program   TEXT,
        llm_generated_university TEXT
    );
    """

    return CREATE_TABLE_SQL






# # Open a cursor to perform database operations
# with defaultConnection.cursor() as def_cur:

#     # Execute out select all command
#     def_cur.execute("""
#                     select * from student;
                
#                     """)
    

# # ================================================================
# # ================================================================




INSERT_SQL = """
INSERT INTO applicants (
    p_id, program, comments, date_added, url, status, term,
    us_or_international, gpa, gre, gre_v, gre_aw, degree,
    llm_generated_program, llm_generated_university
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (p_id) DO NOTHING;
"""

# def load_into_db(applicants):
#     """Insert all applicants into PostgreSQL. Skips duplicates via ON CONFLICT."""
#     conn = psycopg2.connect(**DB_CONFIG)
#     cur  = conn.cursor()
 
#     # Create table if it doesn't exist yet
#     cur.execute(CREATE_TABLE_SQL)
#     conn.commit()
 
#     inserted = 0
#     skipped  = 0
 
#     for a in applicants:
#         row = (
#             a.get("applicantNumber"),
#             build_program(a.get("university"), a.get("program")),
#             a.get("comment"),
#             parse_date(a.get("date_posted")),
#             a.get("url"),
#             parse_status(a.get("decision")),
#             a.get("semester"),
#             a.get("citizenship"),
#             a.get("gpa"),
#             a.get("gre_q"),
#             a.get("gre_v"),
#             a.get("gre_aw"),
#             a.get("degreeType"),
#             a.get("llm_generated_program"),
#             a.get("llm_generated_university"),
#         )
#         try:
#             cur.execute(INSERT_SQL, row)
#             if cur.rowcount > 0:
#                 inserted += 1
#             else:
#                 skipped += 1
#         except Exception as e:
#             print(f"  Insert error for p_id {a.get('applicantNumber')}: {e}")
#             conn.rollback()
#             continue
 
#     conn.commit()
#     cur.close()
#     conn.close()
 
#     print(f"Done — {inserted} inserted, {skipped} skipped (duplicates).")