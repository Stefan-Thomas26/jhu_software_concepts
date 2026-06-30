"""Module for loading applicant data into a PostgreSQL database."""

from datetime import datetime
from pathlib import Path
import os
import psycopg
from psycopg import sql as pg_sql
from shared import configuration


# Constants
DATABASE_NAME = "applicantdata"


def create_new_database(new_database_name):
    """Create a new PostgreSQL database if one does not already exist."""
    username, password, host = configuration.load_configuration_file()

    default_connection = psycopg.connect(
        dbname="postgres",
        user=username,
        password=password,
        host=host
    )
    default_connection.autocommit = True

    with default_connection.cursor() as default_cur:
        try:
            default_cur.execute(f"CREATE DATABASE {new_database_name}")
            print(f"Created database called {new_database_name}!")  # pragma: no cover
        except psycopg.errors.DuplicateDatabase:
            print(f"A database called {new_database_name} already exists!")

    default_connection.close()


def _create_table_sql():
    """Return the SQL string for creating the applicants table."""
    create_table_sql = """
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
    return create_table_sql


def _insert_sql():
    """Return the SQL string for inserting a row into the applicants table."""
    insert_sql = """
    INSERT INTO applicants (
        p_id, program, degreeType, datePosted, status, statusDate, semester,
        citizenship, gpa, gre, gre_v, gre_aw, comment, url, llm_generated_program, llm_generated_university )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (p_id) DO NOTHING;
    """
    return insert_sql


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


def load_into_db(applicants, database_name):
    """Insert a list of applicant dicts into the specified PostgreSQL database."""
    username, password, host = configuration.load_configuration_file()

    conn = psycopg.connect(
        dbname=database_name,
        user=username,
        password=password,
        host=host
    )
    cursor = conn.cursor()

    create_table_sql = _create_table_sql()
    cursor.execute(create_table_sql)
    conn.commit()

    inserted = 0
    skipped = 0

    for a in applicants:
        row = (
            a.get("applicantNumber"),
            combine_uni_program(a.get("university"), a.get("program")),
            a.get("degreeType"),
            parse_date(a.get("datePosted")),
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

        insert_sql = _insert_sql()
        try:
            cursor.execute(insert_sql, row)
            if cursor.rowcount > 0:
                inserted += 1
            else:
                skipped += 1
        except psycopg.Error as e:
            print(f"  Insert error for p_id {a.get('applicant_number')}: {e}")
            conn.rollback()

    conn.commit()
    cursor.close()
    conn.close()

    print(f"Done — {inserted} inserted in table, {skipped} skipped (duplicates).")


def load_data_into_database(filename=None):
    """Load applicant data from a JSON file into the PostgreSQL database."""
    create_new_database(DATABASE_NAME)

    if filename is None:
        data_dir = os.environ.get("DATA_DIR", "src/data")
        filename = os.environ.get(
            "DATA_FILE",
            os.path.join(data_dir, "llm_extended_applicant_data.json")
        )

    applicant_data_file_path = Path(filename)
    print(applicant_data_file_path.resolve())  # pragma: no cover
    applicants = configuration.load_json(applicant_data_file_path.resolve())

    load_into_db(applicants, DATABASE_NAME)


def reset_database(database_name, table_name):  # pragma: no cover
    """Drop the specified table from the given database."""
    username, password, host = configuration.load_configuration_file()

    conn = psycopg.connect(
        dbname=database_name,
        user=username,
        password=password,
        host=host
    )
    cursor = conn.cursor()
    stmt = pg_sql.SQL("DROP TABLE IF EXISTS {table}").format(
        table=pg_sql.Identifier(table_name)
    )
    cursor.execute(stmt)
    conn.commit()
    print(f"The table {table_name} in the {database_name} database has been cleared!")


def delete_database(database_name):  # pragma: no cover
    """Terminate all connections and drop the specified database."""
    username, password, host = configuration.load_configuration_file()

    conn = psycopg.connect(
        dbname="postgres",
        user=username,
        password=password,
        host=host
    )
    conn.autocommit = True
    cursor = conn.cursor()

    stmt = pg_sql.SQL("""
        SELECT pg_terminate_backend(pid)
        FROM pg_stat_activity
        WHERE datname = %s
          AND pid <> pg_backend_pid()
    """)
    cursor.execute(stmt, (database_name,))

    drop_stmt = pg_sql.SQL("DROP DATABASE IF EXISTS {db}").format(
        db=pg_sql.Identifier(database_name)
    )
    cursor.execute(drop_stmt)
    cursor.close()
    conn.close()
    print(f"Database {database_name} has been deleted!")


def main():  # pragma: no cover
    """Entry point for loading data into the database."""
    load_data_into_database()


if __name__ == "__main__":  # pragma: no cover
    main()
