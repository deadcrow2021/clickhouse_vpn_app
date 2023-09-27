from fastapi.templating import Jinja2Templates
from fastapi_utils.tasks import repeat_every
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, Request

import os

from .anomalies import find_anomalies, select_records_from_anomalies
from .db import connect_db, init_db, insert_data


# connect to database
ip = '172.25.0.1'

print('Connect to DB')
client = connect_db(ip)

# if can't connect with docker bridge ip
# try to connect with localhost ip
if not client: 
    client = connect_db('0.0.0.0')

# create database and tables: logs, anomalies
print('Create DB and tables')
try:
    init_db(client)
except Exception as e:
    print(f"""ERROR - Initialize db error.
                    Restart service or choose valid ip.
                    ERR MSG --> {e} <--""")

# insert data into table logs
print('Inserting data')
insert_data(client)

# Initialize app, connect tempates and static files 
abs_path = os.path.dirname(__file__)
templ_path = os.path.join(abs_path, "templates/")

templates = Jinja2Templates(directory=templ_path)
app = FastAPI()

static_path = os.path.join(abs_path, "static/")
app.mount("/static", StaticFiles(directory=static_path), name="static")


# Routes

# main page to demonstrate a table with anomalies 
@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse('home.html', context={'request': request})


# API to get records from anomaly table
@app.get("/anomalies")
async def anomalies():
    query = select_records_from_anomalies(client)
    res = {str(x[0]): [x[1], x[2]] for x in query}
    return res


# function that runs every 1 minute
@app.on_event("startup")
@repeat_every(seconds=60)
async def check_anomalies() -> None:
    """
    Function runs every 1 minute.

    Every minute function makes
    query to the database to find
    new anomalies.
    """
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
    print(f'{len(new_anomaly_records)} anomalies were inserted')