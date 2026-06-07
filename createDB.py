from itertools import combinations
import mysql.connector
from datetime import datetime
import random
import time

from config import DB_CONFIG

# ----- CONFIGURATION -----
# Do NOT change this configuration
CONFIG = {
    'photos': 1_000_000,
    'nachrichten': 500_000,
    'personmultiplier': 5,
    'istabgebildet': 10,
    'istingruppe': 10,
    'friendratio': 5,
}

EMAIL_DOMAINS = [
    'gmail.com', 'yahoo.com', 'gmx.net', 'aon.at', 'sms.at', 'aau.at',
    'uni-klu.ac.at', 'web.de', 'live.at', 'outlook.com', 'edu.auu.at', 'me.com'
]

def load_lines(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]

def chunked_insert(cursor, query, data, chunk_size=1000, showlogs = True):
    total = len(data)
    if total == 0:
        print("[chunked_insert] No data to insert.")
        return

    print(f"[chunked_insert] Starting insert of {total:,} rows with chunk size {chunk_size}...")
    start_time = time.time()

    successful = 0
    failed_chunks = 0

    for i in range(0, total, chunk_size):
        chunk = data[i:i + chunk_size]
        try:
            cursor.executemany(query, chunk)
            successful += len(chunk)
            print(f"  Inserted chunk {i // chunk_size + 1} ({len(chunk)} rows) "
                  f"[{i + len(chunk):,}/{total:,}]")
        except Exception as e:
            failed_chunks += 1
            if showlogs == "true":
                print(f"\n  Failed to insert chunk {i // chunk_size + 1} ({len(chunk)} rows)")
                print("     → Error:", e)
                print("     → Query:", query[:80].replace('\n', ' ') + "...")
                print("     → First bad row:", chunk[0] if chunk else "N/A")
                print("     → Skipping this chunk and continuing...\n")
                # Uncomment the following to debug deeper:
                # traceback.print_exc()

    duration = time.time() - start_time
    print(f"\n[chunked_insert] Finished in {duration:.2f} seconds.")
    print(f"  → Rows inserted: {successful:,}")
    print(f"  → Chunks failed: {failed_chunks}\n")

def reset_schema(cursor):
    print("RESET SCHEMA")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
    cursor.execute("SHOW TABLES;")
    tables = [row[0] for row in cursor.fetchall()]
    for table in tables:
        try:
            cursor.execute(f"DROP TABLE IF EXISTS `{table}`;")
        except Exception as e:
            print(f"Error dropping {table}: {e}")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")

    cursor.execute("""
        CREATE TABLE person (
            email VARCHAR(60) PRIMARY KEY NOT NULL,
            vorname VARCHAR(255),
            nachname VARCHAR(255),
            geburtsdatum DATE,
            geschlecht TEXT
        );
    """)
    cursor.execute("""
        CREATE TABLE gruppe (
            name VARCHAR(30) PRIMARY KEY NOT NULL,
            beschreibung VARCHAR(255),
            emailowner VARCHAR(60),
            FOREIGN KEY (emailowner) REFERENCES person(email)
        );
    """)
    cursor.execute("""
        CREATE TABLE photo (
            URL VARCHAR(255) PRIMARY KEY NOT NULL,
            titel VARCHAR(60),
            beschreibung VARCHAR(1000),
            personemail TEXT
        );
    """)
    cursor.execute("""
        CREATE TABLE nachricht (
            id INTEGER PRIMARY KEY AUTO_INCREMENT,
            vonemail VARCHAR(60),
            anemail VARCHAR(60),
            betreff TEXT,
            datum DATE,
            messagetext VARCHAR(10000)
        );
    """)
    cursor.execute("""
        CREATE TABLE hatfreund (
            email VARCHAR(60),
            emailfreund VARCHAR(60),
            PRIMARY KEY(email, emailfreund)
        );
    """)
    cursor.execute("""
        CREATE TABLE istingruppe (
            gruppename VARCHAR(30),
            email VARCHAR(60),
            PRIMARY KEY(gruppename, email)
        );
    """)
    cursor.execute("""
        CREATE TABLE istabgebildet (
            photourl VARCHAR(255),
            personemail VARCHAR(60),
            PRIMARY KEY(photourl, personemail)
        );
    """)

def main():
    try:
        vornamen = load_lines('data/vornamen.txt')
        nachnamen = load_lines('data/nachnamen.txt')
        groups = load_lines('data/groups.txt')

        conn = mysql.connector.connect(**DB_CONFIG)
        conn.autocommit = False
        cursor = conn.cursor()

        reset_schema(cursor)
        conn.commit()

        user_keys = []
        email_counter = {}
        persons = []

        print("ADDING USERS")
        person_counter = 0
        for nachname in nachnamen:
            for _ in range(random.randint(1, CONFIG['personmultiplier'])):
                for v_entry in vornamen:
                    vorname, geschl = (v_entry.split("\t") + ["m"])[:2]
                    email = f"{vorname.lower()}.{nachname.lower()}@{random.choice(EMAIL_DOMAINS)}"
                    email = email.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
                    if email in email_counter:
                        email_counter[email] += 1
                        email = f"{email_counter[email]}{email}"
                    else:
                        email_counter[email] = 1
                    dob = datetime(1980 + random.randint(0, 20), random.randint(1, 12), random.randint(1, 28)).date()
                    persons.append((email, vorname, nachname, dob, geschl))
                    user_keys.append(email)
                    person_counter += 1
                    if person_counter % 1000 == 0:
                        print(f"Generated {person_counter} users")
        print("Start Insert")
        chunked_insert(cursor, """
            INSERT INTO person (email, vorname, nachname, geburtsdatum, geschlecht)
            VALUES (%s, %s, %s, %s, %s)
        """, persons)
        conn.commit()

        print("ADDING GROUPS")
        group_owners = {}
        group_values = []
        for i, group in enumerate(groups):
            owner = random.choice(user_keys)
            group_owners[group] = owner
            group_values.append((group, f"What should I say: just {group}!", owner))
            if i % 1000 == 0 and i != 0:
                print(f"Generated {i} groups")
        print("Start Insert")
        chunked_insert(cursor, """
            INSERT INTO gruppe (name, beschreibung, emailowner)
            VALUES (%s, %s, %s)
        """, group_values)
        conn.commit()

        print("ADDING PHOTOS")
        photo_values = []
        photo_urls = []
        for i in range(CONFIG['photos']):
            person = random.choice(user_keys)
            url = f"http://flickr.com/{person.split('@')[0]}/{i}.jpg"
            title = f"Photo Number {i}"
            desc = f"This is a very nice picture taken by {person}"
            photo_values.append((url, title, desc, person))
            photo_urls.append(url)
            if i % 1000 == 0 and i != 0:
                print(f"Generated {i} photos")
        print("Start Insert")
        chunked_insert(cursor, """
            INSERT INTO photo (URL, titel, beschreibung, personemail)
            VALUES (%s, %s, %s, %s)
        """, photo_values, 5000)
        conn.commit()

        print("ADDING NACHRICHTEN")
        message_values = []
        subjects = ['RE', 'Good morning', 'Did you know?', 'Happy Birthday!', 'FWD', 'Good luck!', 'Bad news', 'Good news']
        for i in range(CONFIG['nachrichten']):
            sender = random.choice(user_keys)
            receiver = random.choice(user_keys)
            if sender == receiver:
                continue
            subject = random.choice(subjects)
            date = datetime(2000 + random.randint(0, 25), random.randint(1, 12), random.randint(1, 28)).date()
            message = f"some message about {subject}"
            message_values.append((sender, receiver, subject, date, message))
            if i % 1000 == 0 and i != 0:
                print(f"Generated {i} nachrichten")
        print("Start Insert")
        chunked_insert(cursor, """
            INSERT INTO nachricht (vonemail, anemail, betreff, datum, messagetext)
            VALUES (%s, %s, %s, %s, %s)
        """, message_values, 5000)
        conn.commit()

        print("FILLING HATFREUND")
        friends = 0
        CHUNK_SIZE = 100000
        buffer = []

        total_combinations = len(user_keys) * (len(user_keys) - 1) // 2
        progress_interval = 100000
        checked = 0

        for person, friend in combinations(user_keys, 2):
            checked += 1
            if checked % progress_interval == 0:
                print(f"Checked {checked:,} of {total_combinations:,} combinations "
                      f"({checked / total_combinations:.2%}) — Friends so far: {friends:,}")

            if random.randint(1, 100) <= CONFIG['friendratio']:
                buffer.extend([(person, friend), (friend, person)])
                friends += 1

            if len(buffer) >= 10*CHUNK_SIZE:
                chunked_insert(cursor, """
                    INSERT IGNORE INTO hatfreund (email, emailfreund) VALUES (%s, %s)
                """, buffer, CHUNK_SIZE, False)
                conn.commit()
                buffer.clear()

        if buffer:
            chunked_insert(cursor, """
                INSERT IGNORE INTO hatfreund (email, emailfreund) VALUES (%s, %s)
            """, buffer, CHUNK_SIZE)
            conn.commit()

        print(f"Done. Checked {checked:,} pairs. Inserted {friends * 2:,} hatfreund rows.")



        print("FILLING ISTINGRUPPE")
        group_member_values = []
        for i, person in enumerate(user_keys):
            for _ in range(random.randint(0, CONFIG['istingruppe'])):
                group = random.choice(groups)
                if group_owners[group] != person:
                    group_member_values.append((group, person))
            if i % 1000 == 0 and i != 0:
                print(f"Processed {i} users for istingruppe")
        print("Start Insert")
        chunked_insert(cursor, """
            INSERT IGNORE INTO istingruppe (gruppename, email) VALUES (%s, %s)
        """, group_member_values)
        conn.commit()
        print(f"Inserted {len(group_member_values)} istingruppe rows.")

        print("FILLING ISTABGEBILDET")
        abgebildet = set()
        abgebildet_values = []
        count = 0
        for idx, photo in enumerate(photo_urls):
            for _ in range(random.randint(0, CONFIG['istabgebildet'])):
                person = random.choice(user_keys)
                key = (photo, person)
                if key not in abgebildet:
                    abgebildet.add(key)
                    abgebildet_values.append(key)
                    count += 1
                    if count % 1000 == 0:
                        print(f"Generated {count} istabgebildet entries")
        print("Start Insert")
        chunked_insert(cursor, """
            INSERT IGNORE INTO istabgebildet (photourl, personemail) VALUES (%s, %s)
        """, abgebildet_values, 5000)
        conn.commit()
        print(f"Inserted {len(abgebildet_values)} istabgebildet rows.")

        # ----- WRITE EMAILS TO FILE -----
        emails_output_path = "data/emails.txt"
        with open(emails_output_path, "w", encoding="utf-8") as f:
            for email in user_keys:
               f.write(email + "\n")
        print(f"Saved {len(user_keys):,} emails to {emails_output_path}")

        cursor.execute("""
            CREATE TABLE freundecount AS
            SELECT p.email, p.vorname, p.nachname, COUNT(h.emailfreund) as anzahl
            FROM person p
            JOIN hatfreund h ON p.email = h.email
            GROUP BY p.email, p.vorname, p.nachname;
        """)
        conn.commit()

        print("\nTABLE ROW COUNTS:")
        table_names = [
            'person', 'gruppe', 'photo', 'nachricht', 'hatfreund',
            'istingruppe', 'istabgebildet', 'freundecount'
        ]
        for table in table_names:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"{table}: {count} rows")

        print("Data generation complete.")
        cursor.close()
        conn.close()

    except KeyboardInterrupt:
        print("Interrupted! Rolling back.")
        if conn:
            conn.rollback()

    except Exception as e:
        print("Exception occurred:", e)
        if conn:
            conn.rollback()

    finally:
        print("Releasing DB resources")
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        print("Connection closed.")

if __name__ == "__main__":
    main()
