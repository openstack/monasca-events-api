import json
import requests
import time

address = "localhost/foo"

while True:
    t = random.uniform(100, 10000)
    body = {'VM Create time': '{}'.format(t),
            'units': 'ms'}
    headers = {'content-type': 'application/json'}

    try:
        requests.post(url=address,
                      data=json.dumps(body),
                      headers=headers,
                      timeout="10")
    except Exception:
        print("unable to post")

    time.sleep(random.randint(5, 20))
