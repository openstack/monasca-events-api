import datetime
import json
import random
import requests

import kafka.client
import kafka.common
import kafka.consumer

address = "http://192.168.10.4:8765/events.php"

kc = kafka.client.KafkaClient("192.168.10.4:9092")
consumer = kafka.consumer.SimpleConsumer(kc,
                                         "Foo",
                                         "stream-notifications",
                                         auto_commit=True)

for raw_event in consumer:
    event = json.loads(raw_event.message.value)

    times = {}

    for e in event['events']:
        times[e['event_type']] = e['timestamp']

    try:
        microseconds_per_second = 1000000
        time_format = '%Y-%m-%dT%H:%M:%S.%f'
        start = datetime.datetime.strptime(times['compute.instance.create.start'],
                                           time_format)
        end = datetime.datetime.strptime(times['compute.instance.create.end'],
                                         time_format)
        duration = ((end - start).total_seconds() * microseconds_per_second)

        duration = min(100, duration)

        duration += random.uniform(5, 10)

    except Exception as e:
        continue

    body = {'VM Create time': '{}'.format(duration),
            'units': 'ms'}
    headers = {'content-type': 'application/json'}

    try:
        requests.post(url=address,
                      data=json.dumps(body),
                      headers=headers)
    except Exception as e:
        print("unable to post")
