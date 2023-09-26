from clickhouse_driver import Client
import time
import datetime


while True:
    print(datetime.datetime.now())
    ip = '10.0.2.15'
    try:
        # client = Client('0.0.0.0')
        client = Client(ip) # ip add  --> "2: enp0s3 ..."  '10.0.2.15'
        result = client.execute("SHOW DATABASES")
        print(result)
    except Exception as e:
        print(f"""ERROR - {ip} is not valid.
              Or clickhouse_driver error, restart service.
              ERR MSG --> {e} <--""")
    time.sleep(10)