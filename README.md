# Database-Tuning

``` bash
python -m pip install venv
```


``` bash
python -m venv .venv
```


``` bash
source .venv/bin/activate
```
or
``` bash
./.venv/Scripts/activate
```
> installs a new virtual environment in the current dir and activates it


``` bash
python -m pip install -r requirements.txt
```
> installs required python libraries


``` bash
docker compose up
```
> starts and runs the MySQL Docker container with socialnet DB


``` bash
setx DB_PASSWORD "userpass"
```
or on Linux (current session only)
``` bash
export DB_PASSWORD "userpass"
```
> sets the environment vars for DB password in config.py


``` bash
setx DB_ROOT_PASSWORD "my-secret-pw"
```
or on Linux (current session only)
``` bash
export DB_ROOT_PASSWORD "my-secret-pw"
```
> sets the environment vars for DB root password in config.py


``` bash
python createDB.py
```
> executes the python script for creating tables


``` bash
python clientsim.py
```
> executes the python script for simulating client operations


``` bash
deactivate
```
> deactivates the virtual environment


## Introduction

### Database Tuning (definition, principles, etc.)

### Database-specific performance issues

### Tuning methods (monitoring) / techniques (concurrency control, table design, query tuning, etc.)

## Part 1: Query speedup without changing queries and server config
>no creation or removal of attributes or tables

### Sub-problem 1: Workload analysis and query pattern identification

### Sub-problem 2: Indexing strategy

### Sub-problem 3: Index type optimization

### Sub-problem 4: Clustering and fill factor optimization

### Sub-problem 5: Constraints optimization

### Sub-problem 6: Statistics optimization

### Sub-problem 7: Materialized views

## Part 2: Performance optimization with hardware upgrades and changing server config

### Sub-problem 1: RAM requirements

### Sub-problem 2: Storage requirements

### Sub-problem 3: CPU requirements

### Sub-problem 4: Network requirements

### Sub-problem 5: Server architecture

### Sub-problem 6: Backup and disaster recovery

### Sub-problem 7: Monitoring and alerting

## Part 3: Rewriting of queries
>Query result must not change
