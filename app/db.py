from clickhouse_driver import Client
import random
import datetime
import time
import uuid


def connect_db(db_ip: str) -> Client:
    """
    Connects to database.

    Establishes new connection with database.
    There are 3 attempts every second to establish
    new connection. If can't connect to database, returns None.

    :param db_ip: IP that will be used to connect database

    :return clickhouse_driver Client class
    """
    client = None
    try_count = 0
    while try_count < 3:
        try:
            client = Client(db_ip)
            print(f'Database has been connected. IP - {db_ip}')
            break
        except TimeoutError as t:
            print(f"""ERROR - {db_ip} timeout.
                This ip address is not linked to any service.
                Choose another ip address.
                    ERR MSG --> {t} <--""")
        except ConnectionRefusedError as c:
            print(f"""ERROR - {db_ip} connection refused.
                This ip address is not valid or taken.
                Choose valid ip address.
                    ERR MSG --> {c} <--""")
        except Exception as e:
            print(f"""ERROR - {db_ip} address is not valid
                    or clickhouse_driver error, restart service.
                    ERR MSG --> {e} <--""")
        time.sleep(1)
        try_count += 1
    return client


def init_db(client: Client) -> None:
    """
    Creates database and tables.
    
    Create database 'logs_db' and
    tables 'logs' and 'anomaly' with SQL query.

    :param client: clickhouse_driver Client class"""

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



### generate test data ###

def generate_ip() -> str:
    """
    Generate random IP.
    
    Generate string with format 'XX.XX.XX.XX'

    :return str: return ip address.
    """
    return ".".join(str(random.randint(0, 255)) for _ in range(4))


    
def str_time_prop(start: str, end: str, time_format: str, prop: random) -> str:
    """Get a time at a proportion of a range of two formatted times.

    :param start: string specifying times formatted in the
                  given format (strftime-style), giving
                  a start for interval [start, end].
    :param end: string specifying times formatted in the
                given format (strftime-style), giving
                a end for interval [start, end].
    :param prop: specifies how a proportion of the interval
                to be taken after start. The returned time
                will be in the specified format.
    """

    stime = time.mktime(time.strptime(start, time_format))
    etime = time.mktime(time.strptime(end, time_format))
    ptime = stime + prop * (etime - stime)

    return time.strftime(time_format, time.localtime(ptime))


def random_datetime(start: str, end: str, prop: random) -> str:
    """Get random datetime.

    :param start: string specifying times formatted in the
                  given format (strftime-style), giving
                  a start for interval [start, end].
    :param end: string specifying times formatted in the
                given format (strftime-style), giving
                a end for interval [start, end].
    :param prop: specifies how a proportion of the interval
                to be taken after start. The returned time
                will be in the specified format.

    :return str: returns random datetime in string format
    """
    return str_time_prop(start, end, '%Y-%m-%d %H:%M:%S', prop)


# list of random first_names
first_names = ['Liam', 'Noah', 'Oliver', 'James', 'Elijah', 'William', 'Henry', 'Lucas',
'Benjamin', 'Theodore', 'Mateo', 'Levi', 'Sebastian', 'Daniel',
'Jack', 'Michael', 'Alexander', 'Owen', 'Asher', 'Samuel']


# list of random last names
last_names = ['Johnson', 'Williams', 'Brown', 'Jones', 'Garcia',
'Miller', 'Davis', 'Rodriguez', 'Martinez', 'Hernandez',
'Lopez', 'Gonzales', 'Wilson', 'Anderson', 'Thomas',
'Taylor', 'Moore', 'Jackson', 'Martin', 'Smith']


def insert_data(client: Client) -> None:
    """
    Insert test data into table logs.

    list of data is filling up with random data.
    Then SQL query executes to insert
    all data into table logs.

    :param client: clickhouse_driver Client class
    """
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