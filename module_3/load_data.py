import psycopg
import credentials


# Create table sql string
def _create_table_sql():
    CREATE_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS applicants (
        p_id            INTEGER PRIMARY KEY,
        university                 TEXT,
        program                    TEXT,
        degreeType                 TEXT,
        datePosted                 TEXT,
        status                     TEXT,
        semester                   TEXT,
        citizenship                TEXT,
        gpa                        FLOAT,
        gre                        FLOAT,
        gre_v                      FLOAT,
        gre_aw                     FLOAT,
        comment                    TEXT,
        url                        TEXT
    );
    """
    
    # CREATE_TABLE_SQL = """
    # CREATE TABLE IF NOT EXISTS applicants (
    #     p_id                    INTEGER PRIMARY KEY,
    #     program                 TEXT,
    #     comments                TEXT,
    #     date_added              DATE,
    #     url                     TEXT,
    #     status                  TEXT,
    #     term                    TEXT,
    #     us_or_international     TEXT,
    #     gpa                     FLOAT,
    #     gre                     FLOAT,
    #     gre_v                   FLOAT,
    #     gre_aw                  FLOAT,
    #     degree                  TEXT,
    #     llm_generated_program   TEXT,
    #     llm_generated_university TEXT
    # );
    # """

    return CREATE_TABLE_SQL

def _insert_sql():

    INSERT_SQL = """
    INSERT INTO applicants (
        p_id, university, program, degreeType, datePosted, status, semester,
        citizenship, gpa, gre, gre_v, gre_aw, comment, url)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (p_id) DO NOTHING;
    """

    # INSERT_SQL = """
    # INSERT INTO applicants (
    #     p_id, program, comments, date_added, url, status, term,
    #     us_or_international, gpa, gre, gre_v, gre_aw, degree,
    #     llm_generated_program, llm_generated_university
    # ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    # ON CONFLICT (p_id) DO NOTHING;
    # """

    return INSERT_SQL

# ==================================================================


def load_into_db(applicants):
    # =========================================================================
    # CONNECT TO PostgreSQL
    # Insert all applicants into PostgreSQL. Skips duplicates via ON CONFLICT.
    # =========================================================================
    
    # get user credentials 
    USERNAME, PASSWORD, HOST = credentials._get_credentials()

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

        # Try to create a new database if it does not exist already
        try:
            default_cur.execute("CREATE DATABASE applicantdata")
            print("Created database applicantdata!")
        except psycopg.errors.DuplicateDatabase:
            print("applicantdata database already exists!")


    # Close default connections
    default_cur.close()
    defaultConnection.close()

    # Make new connection to applicantdata database
    conn = psycopg.connect(
        dbname = "applicantdata",
        user = USERNAME,
        password = PASSWORD,
        host = HOST
        )
    cursor = conn.cursor()


    # ========================
    # Create table in database      
    # ========================
    
    createTableSql = _create_table_sql()

    # Delete table if it already exists and make new one
    cursor.execute("DROP TABLE IF EXISTS applicants")
    conn.commit()
    cursor.execute(createTableSql)
    conn.commit()

    inserted = 0
    skipped  = 0
 
    for a in applicants:
        row = (
            a.get("applicantNumber"),
            a.get("university"),
            a.get("program"),
            a.get("degreeType"),
            # build_program(a.get("university"), a.get("program")),
            # parse_date(a.get("datePosted")),
            a.get("datePosted"),
            
            # parse_status(a.get("status")),
            a.get("status"),
            a.get("semester"),
            a.get("citizenship"),
            a.get("gpa"),
            a.get("gre"),
            a.get("gre_v"),
            a.get("gre_aw"),
            a.get("comment"),
            a.get("url"),
            
            # a.get("llm_generated_program"),
            # a.get("llm_generated_university"),
        )

        insertSql = _insert_sql()
        try:
            cursor.execute(insertSql, row)
            if cursor.rowcount > 0:
                inserted += 1
            else:
                skipped += 1
        except Exception as e:
            print(f"  Insert error for p_id {a.get('applicantNumber')}: {e}")
            conn.rollback()
            continue


    conn.commit()
    cursor.close()
    conn.close()

    print(f"Done — {inserted} inserted, {skipped} skipped (duplicates).")
