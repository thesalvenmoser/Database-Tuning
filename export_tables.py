import os
import mysql.connector
import csv

from config import DB_CONFIG

#This script can be used to export the data from your DB as importing is faster than filling.

EXPORT_DIR = "exports"
TABLES = [
    'person', 'gruppe', 'photo', 'nachricht',
    'hatfreund', 'istingruppe', 'istabgebildet', 'freundecount'
]

def export_tables():
    os.makedirs(EXPORT_DIR, exist_ok=True)

    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    for table in TABLES:
        path = os.path.join(EXPORT_DIR, f"{table}.csv")
        cursor.execute(f"SELECT * FROM {table}")
        columns = [desc[0] for desc in cursor.description]
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(columns)
            for row in cursor.fetchall():
                writer.writerow(row)
        print(f"Exported {table} → {path}")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    export_tables()
