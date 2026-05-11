import os
import mysql.connector
from config import DB_CONFIG_ROOT, DB_CONFIG

# This script can be used to import data
# set in mysql workbench under Administration --> Status and system variables --> System variables --> local_infile to ON

IMPORT_DIR = "exports"
EMAIL_EXPORT_PATH = "data/emails.txt"
TABLES = [
    'person', 'gruppe', 'photo', 'nachricht',
    'hatfreund', 'istingruppe', 'istabgebildet', 'freundecount'
]

# --- TABLE CREATION SQL ---
CREATE_STATEMENTS = {
    'person': """
        CREATE TABLE IF NOT EXISTS person (
            email VARCHAR(60) PRIMARY KEY NOT NULL,
            vorname VARCHAR(255),
            nachname VARCHAR(255),
            geburtsdatum DATE,
            geschlecht TEXT
        );
    """,
    'gruppe': """
        CREATE TABLE IF NOT EXISTS gruppe (
            name VARCHAR(30) PRIMARY KEY NOT NULL,
            beschreibung VARCHAR(255),
            emailowner VARCHAR(60),
            FOREIGN KEY (emailowner) REFERENCES person(email)
        );
    """,
    'photo': """
        CREATE TABLE IF NOT EXISTS photo (
            URL VARCHAR(255) PRIMARY KEY NOT NULL,
            titel VARCHAR(60),
            beschreibung VARCHAR(1000),
            personemail TEXT
        );
    """,
    'nachricht': """
        CREATE TABLE IF NOT EXISTS nachricht (
            id INTEGER PRIMARY KEY AUTO_INCREMENT,
            vonemail VARCHAR(60),
            anemail VARCHAR(60),
            betreff TEXT,
            datum DATE,
            messagetext VARCHAR(10000)
        );
    """,
    'hatfreund': """
        CREATE TABLE IF NOT EXISTS hatfreund (
            email VARCHAR(60),
            emailfreund VARCHAR(60),
            PRIMARY KEY(email, emailfreund)
        );
    """,
    'istingruppe': """
        CREATE TABLE IF NOT EXISTS istingruppe (
            gruppename VARCHAR(30),
            email VARCHAR(60),
            PRIMARY KEY(gruppename, email)
        );
    """,
    'istabgebildet': """
        CREATE TABLE IF NOT EXISTS istabgebildet (
            photourl VARCHAR(255),
            personemail VARCHAR(60),
            PRIMARY KEY(photourl, personemail)
        );
    """,
    'freundecount': """
        CREATE TABLE IF NOT EXISTS freundecount (
            email VARCHAR(60),
            vorname VARCHAR(255),
            nachname VARCHAR(255),
            anzahl BIGINT
        );
    """
}

def import_tables():
    conn = mysql.connector.connect(**DB_CONFIG_ROOT)
    cursor = conn.cursor()

    cursor.execute(f"USE {DB_CONFIG.get("database")};")

    for table in TABLES:
        print(f"Preparing table: {table}")
        try:
            cursor.execute(CREATE_STATEMENTS[table])
            conn.commit()
        except Exception as e:
            print(f"Failed to create table '{table}': {e}")
            continue

        path = os.path.join(IMPORT_DIR, f"{table}.csv")
        if not os.path.exists(path):
            print(f"File not found: {path}")
            continue

        abs_path = os.path.abspath(path).replace("\\", "/")

        # Allow for usage of local infile, requires root user
        cursor.execute("SET GLOBAL local_infile=1;")

        query = f"""
            LOAD DATA LOCAL INFILE '{abs_path}'
            INTO TABLE {table}
            CHARACTER SET utf8
            FIELDS TERMINATED BY ','
            ENCLOSED BY '"'
            LINES TERMINATED BY '\\n'
            IGNORE 1 LINES;
        """
        try:
            cursor.execute(query)
            print(f"Imported {table} from {path}")
        except Exception as e:
            print(f"Failed to import {table}: {e}")

    conn.commit()

    # --- Export emails from person table ---
    try:
        cursor.execute("SELECT email FROM person;")
        emails = [row[0] for row in cursor.fetchall()]

        os.makedirs(os.path.dirname(EMAIL_EXPORT_PATH), exist_ok=True)
        with open(EMAIL_EXPORT_PATH, "w", encoding="utf-8") as f:
            for email in emails:
                f.write(f"{email}\n")
        print(f"Exported {len(emails)} emails to {EMAIL_EXPORT_PATH}")
    except Exception as e:
        print(f"Failed to export emails: {e}")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    import_tables()
