import mysql.connector

from config import DB_CONFIG_ROOT

# It may happen that connections are not closed properly if scripts are terminated during execution.
# This script can be used to delete all connections to the DB

def kill_all_queries():
    conn = mysql.connector.connect(**DB_CONFIG_ROOT)
    cursor = conn.cursor()

    cursor.execute("SELECT CONNECTION_ID()")
    my_id = cursor.fetchone()[0]
    cursor.execute("SHOW FULL PROCESSLIST")
    rows = cursor.fetchall()

    print(f"[INFO] Current connection ID: {my_id}")
    print("[INFO] Killing other running processes...")

    kill_count = 0
    for row in rows:
        pid = row[0]
        user = row[1]
        command = row[4]
        if pid != my_id and command != "Sleep":
            try:
                print(f"Killing PID {pid} (User: {user}, Command: {command})")
                cursor.execute(f"KILL {pid}")
                kill_count += 1
            except Exception as e:
                print(f"[ERROR] Failed to kill PID {pid}: {e}")

    conn.close()
    print(f"[DONE] Killed {kill_count} processes.")

if __name__ == "__main__":
    kill_all_queries()
