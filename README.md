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

``` bash
python -m pip install -r requirements.txt
```

``` bash
docker compose up
```

``` bash
python createDB.py
```

``` bash
python clientsim.py
```

``` bash
deactivate
```


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
