# Insert here your own credentials for the DB
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'user',
    'password': 'userpass',
    'database': 'socialnet',
    'autocommit': False,
    'allow_local_infile': True
}

# Insert your root credentials for the DB here (Use a user with PROCESS + SUPER privileges)
# This is used by killAllSQLProcesses.py and import_tables.py
DB_CONFIG_ROOT = dict(DB_CONFIG)
DB_CONFIG_ROOT.update({
    'user': 'root',
    'password': 'my-secret-pw',
    'database': 'information_schema', # Don't change this, it is required to get the open connections
})

ISOLATION_LEVEL = "SERIALIZABLE" # READ UNCOMMITTED | READ COMMITTED | REPEATABLE READ | SERIALIZABLE


QUERY_DURATION_SECONDS = 90 # Query execution time
LOCK_TIMEOUT = 30 # Maximum lock wait timeout

# Now you are ready to create the DB with createDB.py and simulate traffic with clientsim.py
