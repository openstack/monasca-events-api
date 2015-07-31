import json
import requests
import time
import random

address = "http://192.168.10.4:8765/events.php"

while True:
    t = random.uniform(100, 10000)
    body = {'VM Create time': '{}'.format(t),
            'units': 'ms'}
    headers = {'content-type': 'application/json'}

    try:
        requests.post(url=address,
                      data=json.dumps(body),
                      headers=headers)
    except Exception as e:
        print("unable to post")
        print e

    time.sleep(3)
