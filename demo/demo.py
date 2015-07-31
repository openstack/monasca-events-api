#!/opt/monasca/bin/python
# Copyright (c) 2015 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# This script is designed to demo the entire Monasca Events package.
# It will post a stream defintion and transform defintion,
# and then it'll generate events at 5 per minute


import datetime
import json
import kafka
import sys
import time

import notigen
import requests
import yaml

from monascaclient import ksclient

events_url = "http://192.168.10.4:8082/v2.0"

def token():
    keystone = {
        'username': 'mini-mon',
        'password': 'password',
        'project': 'test',
        'auth_url': 'http://192.168.10.5:35357/v3'
    }
    ks_client = ksclient.KSClient(**keystone)
    return ks_client.token

headers = {
    'X-Auth-User': 'mini-mon',
    'X-Auth-Key': 'password',
    'X-Auth-Token': token(),
    'Accept': 'application/json',
    'User-Agent': 'python-monascaclient',
    'Content-Type': 'application/json'}

def stream_definition_post():
    body = {}

    notif_resp = requests.get(
        url="http://192.168.10.4:8080/v2.0/notification-methods",
        data=json.dumps(body), headers=headers)
    notif_dict = json.loads(notif_resp.text)
    action_id = str(notif_dict['elements'][0]['id'])

    body = {"fire_criteria": [{"event_type": "compute.instance.create.start"},
                              {"event_type": "compute.instance.create.end"}],
            "description": "provisioning duration",
            "name": "Example Stream Definition",
            "group_by": ["instance_id"],
            "expiration": 3000,
            "select": [{"traits": {"tenant_id": "406904"},
                        "event_type": "compute.instance.create.*"}],
            "fire_actions": [action_id],
            "expire_actions": [action_id]}

    response = requests.post(
	    url=events_url + "/stream-definitions",
	    data=json.dumps(body),
	    headers=headers)


def transform_definition_post():

    # Open example yaml file and post to DB
    fh = open('files/transform_definition.yaml', 'r')
    specification_data = yaml.load(fh)

    body = {
        "name": 'Example Transform Definition',
        "description": 'an example description',
        "specification": str(specification_data)
    }

    response = requests.post(
	    url=events_url + "/transforms",
	    data=json.dumps(body),
	    headers=headers)

def event_generator():
    
    # generate 5 events per minute
    g = notigen.EventGenerator("files/event_templates", operations_per_hour=300)
    now = datetime.datetime.utcnow()
    start = now
    nevents = 0

    length = 0

    while nevents < 300:
        e = g.generate(now)
        if e:
            nevents += len(e)
            key = time.time() * 1000

            msg = e

            if len(msg) > length:
                length = len(msg)
                print("Max notification size: {}".format(length))

            response = requests.post(
                url=events_url + "/events",
                data=json.dumps(msg),
                headers=headers)

        now = datetime.datetime.utcnow()
        time.sleep(0.01)



def main():

    stream_definition_post()
    transform_definition_post()
    event_generator()


if __name__ == "__main__":
    sys.exit(main())




