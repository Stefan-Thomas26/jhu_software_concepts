# Python Packages
import psycopg
from datetime import datetime
from pathlib import Path
# My Packages
import configuration



def create_new_database(new_database_name):
    # =========================================================================
    # CONNECT TO PostgreSQL
    # Insert all applicants into PostgreSQL. Skips duplicates via ON CONFLICT.
    # =========================================================================
    
    # get user credentials 
    USERNAME, PASSWORD, HOST = configuration.load_configuration_file()

    # Connect to an already-existing database in order to create a new database
    defaultConnection = psycopg.connect(
        dbname      = "postgres",
        user        = USERNAME,
        password    = PASSWORD,
        host        = HOST
        )

    defaultConnection.autocommit = True

    # Create a new database
    with defaultConnection.cursor() as default_cur:

        # Try to create a new database if it does not exist already
        try:
            default_cur.execute(f"CREATE DATABASE {new_database_name}")
            print(f"Created database called {new_database_name}!") # pragma: no cover
        except psycopg.errors.DuplicateDatabase:
            print(f"A database called {new_database_name} already exists!")


    # Close default connections
    default_cur.close()
    defaultConnection.close()



# Create table sql string
def _create_table_sql():
    CREATE_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS applicants (
        p_id                        INTEGER PRIMARY KEY,
        program                     TEXT,
        degreeType                  TEXT,
        datePosted                  DATE,
        status                      TEXT,
        statusDate                  TEXT,
        semester                    TEXT,
        citizenship                 TEXT,
        gpa                         FLOAT,
        gre                         FLOAT,
        gre_v                       FLOAT,
        gre_aw                      FLOAT,
        comment                     TEXT,
        url                         TEXT,
        llm_generated_program       TEXT,
        llm_generated_university    TEXT
    );
    """

    return CREATE_TABLE_SQL



def _insert_sql():
    INSERT_SQL = """
    INSERT INTO applicants (
        p_id, program, degreeType, datePosted, status, statusDate, semester,
        citizenship, gpa, gre, gre_v, gre_aw, comment, url, llm_generated_program, llm_generated_university )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (p_id) DO NOTHING;
    """
    
    return INSERT_SQL



def parse_date(date_str):
    """Convert 'Mar 12, 2025' to datetime.date object. Returns None if blank."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str.strip(), "%b %d, %Y").date()
    except ValueError:
        return None



def combine_uni_program(university, program):
    """Combine university + program into one string as the assignment requires."""
    if university and program:
        return f"{university} - {program}"
    return university or program or None



def load_into_db(applicants, databaseName):
    
    # get user credentials 
    USERNAME, PASSWORD, HOST = configuration.load_configuration_file()

    # Make new connection to  database that we made
    conn = psycopg.connect(
        dbname      = databaseName,
        user        = USERNAME,
        password    = PASSWORD,
        host        = HOST
        )
    cursor = conn.cursor()


    # ========================
    # Create table in database      
    # ========================
    createTableSql = _create_table_sql()

    cursor.execute(createTableSql)
    conn.commit()

    inserted = 0
    skipped  = 0
 
    for a in applicants:
        row = (
            a.get("applicantNumber"),
            combine_uni_program(a.get("university"), a.get("program")),
            # a.get("university"),
            # a.get("program"),
            a.get("degreeType"),
            parse_date(a.get("datePosted")),
            # a.get("datePosted"),
            a.get("status"),
            a.get("statusDate"),
            a.get("semester"),
            a.get("citizenship"),
            a.get("gpa"),
            a.get("gre"),
            a.get("gre_v"),
            a.get("gre_aw"),
            a.get("comment"),
            a.get("url"),
            a.get("llm_generated_program"),
            a.get("llm_generated_university"),
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

    print(f"Done — {inserted} inserted in table, {skipped} skipped (duplicates).")



def load_data_into_database(filename=None):
    # Create new database called "applicantdata" if one does not already exist
    databaseName = "applicantdata"
    create_new_database(databaseName)


    if filename is None:
        try:
            config_path = configuration.get_configuration_filepath()
            config      = configuration.load_json(config_path)
            filename    = config[0].get("dataFile", "module_2/llm_extended_applicant_data.json")
        
        except Exception:
            filename = "module_2/llm_extended_applicant_data.json"


    # Find absolute path to .json file on local machine
    applicantDataFilePath = Path(filename)
    print(applicantDataFilePath.resolve()) # pragma: no cover
    # Load JSON file
    applicants = configuration.load_json(applicantDataFilePath.resolve())
    
    # Load applicant data into the database
    load_into_db(applicants, databaseName)


# Clear database
def reset_database(databaseName, tableName): # pragma: no cover
    
    # get user credentials 
    USERNAME, PASSWORD, HOST = configuration.load_configuration_file()

    # Make new connection to  database that we made
    conn = psycopg.connect(
    dbname      = databaseName,
    user        = USERNAME,
    password    = PASSWORD,
    host        = HOST
    )
    
    cursor = conn.cursor()
    cursor.execute(f"DROP TABLE IF EXISTS {tableName}")
    conn.commit()

    print(f"The table {tableName} in the {databaseName} database has been cleared!")



def delete_database(databaseName): # pragma: no cover
    
    USERNAME, PASSWORD, HOST = configuration.load_configuration_file()

    conn = psycopg.connect(
        dbname   = "postgres",
        user     = USERNAME,
        password = PASSWORD,
        host     = HOST
    )
    conn.autocommit = True
    cursor = conn.cursor()

    # Terminate all other connections to the database first
    cursor.execute(f"""
        SELECT pg_terminate_backend(pid)
        FROM pg_stat_activity
        WHERE datname = '{databaseName}'
          AND pid <> pg_backend_pid();
    """)

    # Now safe to drop
    cursor.execute(f"DROP DATABASE IF EXISTS {databaseName}")
    cursor.close()
    conn.close()

    print(f"Database {databaseName} has been deleted!")



def main(): # pragma: no cover
    # reset_database("applicantdata", "applicantable")
    # delete_database("applicantdata")
    load_data_into_database()


if __name__ == "__main__": # pragma: no cover
    main()