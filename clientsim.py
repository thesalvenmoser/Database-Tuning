import random
import sys
import threading
import time
import statistics
from datetime import datetime
import os
from mysql.connector import connect
import re
import csv
import logging

from config import DB_CONFIG, QUERY_DURATION_SECONDS, ISOLATION_LEVEL, LOCK_TIMEOUT

# ----- LOGGING & FOLDER SETUP -----
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
LOG_DIR = os.path.join("logs", timestamp)
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "clientsim.log")
ERROR_LOG_FILE = os.path.join(LOG_DIR, "clientsim_errors.log")
random.seed(1234567890)

# Setup for general log file + error log file + console logging
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
log_file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
log_file_handler.setLevel(logging.DEBUG)
error_file_handler = logging.FileHandler(ERROR_LOG_FILE, encoding="utf-8")
error_file_handler.setLevel(logging.ERROR)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter(u'%(levelname)s - %(message)s')
log_file_handler.setFormatter(formatter)
error_file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)
log.addHandler(log_file_handler)
log.addHandler(error_file_handler)
log.addHandler(console_handler)


def load_lines(filename):
    with open(filename, encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def load_timed_queries(filename):
    queries = []
    with open(filename, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or line in ["\n", "\r\n"]:
                continue
            match = re.match(r"(\d+)\|(.*)", line)
            if match:
                queries.append((int(match.group(1)), match.group(2).strip()))
    return queries

def process_query(query, firstnames, lastnames, groups, emails):
    query = query.replace("[[EMAIL1]]", random.choice(emails))
    query = query.replace("[[EMAIL2]]", random.choice(emails))
    query = query.replace("[[EMAIL3]]", random.choice(emails))

    #replace lastname code, url
    query = re.sub(r"\[\[LASTNAME1TO2\]\]", lambda _: random.choice(lastnames)[:2], query)
    query = re.sub(r"\[\[URL\]\]", lambda _: f"https://example.com/photo_{random.randint(1, 1000)}.jpg", query)

    #Replace email, firstname, lastname group
    for placeholder, source in {'EMAIL': emails, 'FIRSTNAME': firstnames, 'LASTNAME': lastnames, 'GROUP': groups}.items():
        while f"[[{placeholder}]]" in query:
            query = query.replace(f"[[{placeholder}]]", random.choice(source), 1)

    #Replace year
    while "[[YEAR]]" in query:
        query = query.replace("[[YEAR]]", str(random.randint(2000, 2025)), 1)
    return query

def adaptRemainingTime(threadid, start_time, cursor):
    remaining_ms = max(1, int((start_time + QUERY_DURATION_SECONDS - time.time()) * 1000))
    log.info(f"Thread {threadid}: Adapt remaining time to {remaining_ms/1000}")
    cursor.execute(f"SET SESSION MAX_EXECUTION_TIME={remaining_ms};")


def is_pure_select(query):
    query = query.strip().lower()
    return (
        "select" in query
        and not re.search(r"\b(create|set\s+@)\b", query)
    )

def runSomeQueries(threadid, firstnames, lastnames, groups, emails, raw_queries, results):
    conn = connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute(f"SET SESSION INNODB_LOCK_WAIT_TIMEOUT = {LOCK_TIMEOUT};")
    # Disable safe updates as some queries would fail otherwise
    cursor.execute("SET SQL_SAFE_UPDATES = 0;")

    loop_index = 0
    index = threadid % len(raw_queries)
    timer, queries = raw_queries[index]
    times = []
    start_time = time.time()

    while time.time() < start_time + QUERY_DURATION_SECONDS:
        # Start transaction
        log.info(f"Thread {threadid}: Starting Transaction - ISOLATION_LEVEL: {ISOLATION_LEVEL}")
        conn.start_transaction(isolation_level=ISOLATION_LEVEL)

        query = process_query(queries, firstnames, lastnames, groups, emails)
        query_parts = [q.strip() for q in query.split(';') if q.strip()]
        adaptRemainingTime(threadid, start_time, cursor)
        log.info(f"Thread {threadid}: execute query {index} at {time.time() - start_time:.2f}")
        query_start = time.time()
        for query_part in query_parts:
            if time.time() >= start_time + QUERY_DURATION_SECONDS:
                break

            if "[[SLEEP]]" in query_part:
                coffee_break = random.random() * 5
                log.info(f"Thread {threadid}: Going for a coffee for {coffee_break} seconds.")
                time.sleep(coffee_break)
            elif "[[COMMIT]]" in query_part:
                log.info(f"Thread {threadid}: COMMIT")
                adaptRemainingTime(threadid, start_time, cursor)
                conn.commit()
            else:
                try:
                    log.info(f"Thread {threadid}: execute: {query_part}")
                    adaptRemainingTime(threadid, start_time, cursor)
                    cursor.execute(query_part)
                    cursor.fetchall()
                except Exception as e:
                    # Rollback transaction, as this one failed
                    conn.rollback()

                    if hasattr(e, 'errno') and (e.errno == 3024 or e.errno == 1051 or e.errno == 1146  or e.errno == 1050 or e.errno == 1062):
                        log.warning(f"Thread {threadid}: Query was interrupted (errno {e.errno}) - {e}")
                        continue
                    else:
                        log.error(f"Thread {threadid}: {time.time() - start_time:.2f} - {e} - Query: {query_part}")

            # Rollback transaction. This only does something if the queries did not include a commit command
            conn.rollback()

            query_duration = time.time() - query_start
            times.append(query_duration)
            loop_index += 1
            remaining_time = QUERY_DURATION_SECONDS - (time.time() - start_time)
            sleep_window = int(min(timer, remaining_time))
            if sleep_window > 0:
                sleep_time = random.random() * 5
                log.info(f"Thread {threadid}: Finished, Now I sleep a random time: {sleep_time}s")
                time.sleep(sleep_time)

        if times:
            min_time = min(times)
            max_time = max(times)
            avg_time = statistics.mean(times)
            log.info(f"Thread {threadid}: My time is up at {time.time() - start_time:.2f} - numruns: {len(times)}, min: {min_time:.4f}s, avg: {avg_time:.4f}s, max: {max_time:.4f}s")
        else:
            log.info(f"Thread {threadid}: My time is up at {time.time() - start_time:.2f}")

        results[threadid] = times

    cursor.close()
    conn.close()

def main():
    firstnames = load_lines("data/vornamen.txt")
    lastnames = load_lines("data/nachnamen.txt")
    groups = load_lines("data/groups.txt")
    emails = load_lines("data/emails.txt")
    raw_queries = load_timed_queries("data/queries.txt")

    threads = []
    results = [None] * len(raw_queries)
    for i in range(len(raw_queries)):
        t = threading.Thread(target=runSomeQueries, args=(i, firstnames, lastnames, groups, emails, raw_queries, results))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    csv_filename = os.path.join(LOG_DIR, "final_results.csv")
    with open(csv_filename, mode='w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, delimiter=';')
        writer.writerow(["Thread ID", "NumRuns", "Min (s)", "Avg (s)", "Max (s)"])

        print("\n\n\nFINAL RESULTS:")
        total_queries = []

        for i, result in enumerate(results):
            if results[i]:
                min_time = min(result)
                max_time = max(result)
                avg_time = statistics.mean(result)
                total_queries.extend(result)

                print(
                    f"Thread {i}: numruns: {len(result)}, min: {min_time:.4f}s, avg: {avg_time:.4f}s, max: {max_time:.4f}s")
                writer.writerow([i, len(result), f"{min_time:.4f}", f"{avg_time:.4f}", f"{max_time:.4f}"])

        if total_queries:
            min_time = min(total_queries)
            max_time = max(total_queries)
            avg_time = statistics.mean(total_queries)
            print(
                f"Total queries: {len(total_queries)} min: {min_time:.4f}s, avg: {avg_time:.4f}s, max: {max_time:.4f}s")
            writer.writerow(["Total", len(total_queries), f"{min_time:.4f}", f"{avg_time:.4f}", f"{max_time:.4f}"])

    # Cleanup logger
    log.removeHandler(error_file_handler)
    log.removeHandler(log_file_handler)
    log.removeHandler(console_handler)
    error_file_handler.close()
    log_file_handler.close()
    console_handler.close()

if __name__ == '__main__':
    main()