from clickhouse_driver import Client
from math import pi, cos, sin, acos
import operator
import uuid


def to_rads(deg: float) -> float:
    """
    Converts degrees between [-180, 180] into radians.

    :param deg: angle as degrees
    
    :return float: degrees into radians
    """
    if deg == 0:
        return 0.0
    else:
        return pi / (180 / deg)


def calculate_distance(lat1, long1, lat2, long2: float) -> float:
    """
    Calculates distance between two coordinates.
    
    :param lat1: latitude for first coordinate
    :param long1: longitude for second coordinate
    :param lat2: latitude for first coordinate
    :param long2: longitude for second coordinate

    :return float: distance between two coordinates 
    """
    # calculates distance between two coordinates
    # https://ru.wikipedia.org/wiki/%D0%9E%D1%80%D1%82%D0%BE%D0%B4%D1%80%D0%BE%D0%BC%D0%B8%D1%8F
    deg_length = acos(
                      sin(to_rads(lat1)) * sin(to_rads(lat2)) +
                      cos(to_rads(lat1)) * cos(to_rads(lat2)) * cos(to_rads(long2-long1))
                      )
    r = 6371 # Earth radius
    distance = r * deg_length
    return distance



def append_anomalies(client: Client, chunk: list, anomalies: list) -> None:
    """
    Find anomalies from logs table. 

    Calculate speed between two logs.


    :param client: clickhouse_driver Client class.
    :param chunk: queried data from logs table
                  and separated by username.
    :return anomalies: a list of records from logs table
                       that indicates as anomalies.
    """
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


def get_sorted_chunks(client: Client, rows_gen: list, anomalies: list) -> None:
    """
    Separate records by username and append to username_chunk list.

    Some records with equal uername append
    to list and sorts by date.

    :param client: clickhouse_driver Client class.
    :param rows_gen: queried data from logs table
                     and separated by 100 records.
    :return anomalies: a list of records from logs table
                      that indicates as anomalies.
    """
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


def find_anomalies(client: Client) -> list:
    """
    Make query to get chunks of data.

    Make query to table logs to
    get data in chunks by 100 records.

    :param client: clickhouse_driver Client class

    :return list: a list of records from logs table
                      that indicates as anomalies.
    """
    anomalies = []
    settings = {'max_block_size': 100}
    rows_gen = client.execute_iter(
        """SELECT * FROM logs_db.logs
            ORDER BY username ASC""",
            settings=settings)
    get_sorted_chunks(client, rows_gen, anomalies)

    return anomalies

    

def select_records_from_anomalies(client: Client) -> None:
    """
    Make query to get chunks of data.

    Make query to table anomalies to
    get data in chunks by 100 records.

    :param client: clickhouse_driver Client class

    :return list: a list of records from anomaly table.
    """
    queried_anomalies = []
    settings = {'max_block_size': 100}
    rows_gen = client.execute_iter(
        """SELECT * FROM logs_db.anomalies
            ORDER BY username ASC""",
            settings=settings)
    for row in rows_gen:
        queried_anomalies.append([str(row[0]), str(row[1]), row[2]])

    return queried_anomalies
