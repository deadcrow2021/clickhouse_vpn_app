# Tutorial for set up app

## Download app

- Clone repository

```
git clone https://github.com/deadcrow2021/rv_test.git
```

- Move to directory

```
cd Desktop/rv_test/
```

## Run app 

- Run server

```
docker-compose up
```

## Run Issues 
### Pass if run was OK

- EOFError, ConnectionResetError.

App failed to connect to ClickHouse DB.
Just restart app.

```
docker-compose down
docker-compose up
```

---

- TimeoutError, ConnectionRefusedError.

IP in main.py is not valid.

In this case, run only database in container.

```
docker-compose -f no-app-compose.yml up
```

And then run app on your host machine.
```
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
---


## Results

- To see results, connect to service.

Copy and paste to browser input the following URL address:
```
http://0.0.0.0:8000
```

---
---

# Tips

- To insert your data into table, follow next example:

Use datetime between '2023-01-01 00:00:00' and '2023-01-31 23:59:59'

Use latitude = [-90, 90] and longitude = [-180, 180]
```
INSERT INTO logs_db.logs VALUES (generateUUIDv4(), 'Sanya', '10.10.0.1', -10.123, 100.321, '2023-01-20 10:10:10')
```

- To get anomalies, write

```
SELECT * FROM logs_db.anomalies
ORDER BY username ASC
```

## Features

### How does it works under the hood

- Connect to DB

db.py
```py
def connect_db(db_ip: str) -> Client:
    try:
        client = Client(db_ip)
        print(f'Database has been connected. IP - {db_ip}')
        break
    except Exception as e:
        print(f"""ERROR - {db_ip} address is not valid
                or clickhouse_driver error, restart service.
                ERR MSG --> {e} <--""")
```

- Initialize database and tables

db.py
```py
def init_db(client: Client) -> None:
    # create database
    client.execute("CREATE DATABASE IF NOT EXISTS logs_db COMMENT 'Database for logs and anomalies'")

    # create tables
    client.execute("""CREATE TABLE IF NOT EXISTS logs_db.logs
                        (
                        id            UUID,
                        username       String,
                        ip              String,
                        latitude      Float32,
                        longitude        Float32,
                        datetime    DateTime('Etc/GMT')
                        ) ENGINE = Log;""")

    client.execute("""CREATE TABLE IF NOT EXISTS logs_db.anomalies
                        (
                        id            UUID,
                        user_id       UUID,
                        username       String
                        ) ENGINE = Log;""")
```

- Generate test data and insert it into table

db.py
```py
def insert_data(client: Client) -> None:
    data = []
    # generate data
    for i in range(1000): # insert 1000 records
        data.append([str(uuid.uuid4()),
                    f'{random.choice(first_names)}_{random.choice(last_names)}',
                    generate_ip(),
                    random.uniform(-90, 90),
                    random.uniform(-180, 180),
                    datetime.datetime.strptime(
                                                str(random_datetime("2023-01-01 00:00:00",
                                                                "2023-01-31 23:59:59",
                                                                random.random())),
                                                '%Y-%m-%d %H:%M:%S'
                                                )
                    ])
    # insert data
    client.execute('INSERT INTO logs_db.logs VALUES', data)
```

- Every 1 minute anomalies would be found in table logs

main.py
```py
@app.on_event("startup")
@repeat_every(seconds=60)
async def check_anomalies() -> None:
    new_anomaly_records = []

    # all anomaly records that
    # was found in logs table
    anomalies = find_anomalies(client)

    # all exist anomalies from anomaly table
    queried_anomalies = select_records_from_anomalies(client)

    # find new anomalies
    for anom in anomalies:
        if not any(anom[1] in q for q in queried_anomalies):
            new_anomaly_records.append(anom)

    # insert new anomalies to anomaly table
    client.execute('INSERT INTO logs_db.anomalies VALUES', new_anomaly_records)
```

- Get data by chanks from logs table

anomalies.py
```py
def find_anomalies(client: Client) -> list:
    anomalies = []
        settings = {'max_block_size': 100}
    rows_gen = client.execute_iter(
        """SELECT * FROM logs_db.logs
            ORDER BY username ASC""",
            settings=settings)
    get_sorted_chunks(client, rows_gen, anomalies)
```

- Append records with distinct username to the list and sort it by datetime 

anomalies.py
```py
def get_sorted_chunks(client: Client, rows_gen: list, anomalies: list) -> None:
    username_chunk = [] # list of records for distinct username
    current_name = None

    # separate records by username and append to username_chunk list
    for row in rows_gen:
        if username_chunk == []:
            username_chunk.append(row)
            current_name = row[1]
        elif current_name == row[1]:
            username_chunk.append(row)
        else:
            sorted_chunk = sorted(username_chunk, key=operator.itemgetter(5))
            append_anomalies(client, sorted_chunk, anomalies)
            username_chunk = []
```

- Calculate speed between two logs and append second log if it is an anomaly

anomalies.py
```py
def append_anomalies(client: Client, chunk: list, anomalies: list) -> None:
    for i in range(len(chunk) - 1):
        # find time (hours) between two dates
        hours = (chunk[i+1][5] - chunk[i][5]).total_seconds() / 60 / 60

        # find distance between two coordinates
        distance = calculate_distance(
                                    chunk[i][3], chunk[i][4],
                                    chunk[i+1][3], chunk[i+1][4]
                                    )
        # find speed
        speed = distance / hours

        # if user speed was faster then average plane speed (926 km/h) 
        if speed > 926:
            anomaly_record = chunk[i+1]
            anomalies.append([
                str(uuid.uuid4()),
                str(anomaly_record[0]),
                anomaly_record[1]
            ])
```

- Distance between two coordinates on Earth
* [Distance](https://ru.wikipedia.org/wiki/%D0%9E%D1%80%D1%82%D0%BE%D0%B4%D1%80%D0%BE%D0%BC%D0%B8%D1%8F) between coordinates

anomalies.py
```py
def to_rads(deg: float) -> float:
    if deg == 0:
        return 0.0
    else:
        return pi / (180 / deg)

def calculate_distance(lat1, long1, lat2, long2: float) -> float:
    # calculates distance between two coordinates
    deg_length = acos(
                      sin(to_rads(lat1)) * sin(to_rads(lat2)) +
                      cos(to_rads(lat1)) * cos(to_rads(lat2)) * cos(to_rads(long2-long1))
                      )
    r = 6371 # Earth radius
    distance = r * deg_length
    return distance
```

- Every 10 sec JS fetches records from anomaly table

script.js
```js
function make_fetch() {
    fetch('http://0.0.0.0:8000/anomalies/', {
      method: 'GET',
    }).then(
      response => response.json()
    ).then(result => {
      table_block.innerHTML =`
          <tr>
              <th>UUID</th>
              <th>User UUID</th>
              <th>Username</th>
          </tr>`
      Object.entries(result).forEach(element => {
        table_block.innerHTML += `
          <tr>
              <td>${element[0]}</td>
              <td>${element[1][0]}</td>
              <td>${element[1][1]}</td>
          </tr>`
      });
    })
}
```

- API with records from anomaly table

main.py
```py
# API to get records from anomaly table
@app.get("/anomalies")
async def anomalies():
    query = select_records_from_anomalies(client)
    res = {str(x[0]): [x[1], x[2]] for x in query}
    return res
```