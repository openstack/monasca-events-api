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

import json

import requests

from monascaclient import ksclient


events_url = "http://127.0.0.1:8082"


def token():
    keystone = {
        'username': 'mini-mon',
        'password': 'password',
        'project': 'test',
        'auth_url': 'http://192.168.10.5:35357/v3'
    }
    ks_client = ksclient.KSClient(**keystone)
    return ks_client.token


def test_events_get():
    headers = {
        'X-Auth-User': 'mini-mon',
        'X-Auth-Token': token(),
        'X-Auth-Key': 'password',
        'Accept': 'application/json',
        'User-Agent': 'python-monascaclient',
        'Content-Type': 'application/json'}

    body = {}

    response = requests.get(url=events_url + "/v2.0/events",
                            data=json.dumps(body),
                            headers=headers)

    json_data = json.loads(response.text)

    event_id = json_data[3]['id']

    assert response.status_code == 200

    response = requests.get(
        url=events_url + "/v2.0/events/{}".format(event_id),
        data=json.dumps(body),
        headers=headers)

    json_data = json.loads(response.text)

    new_event_id = json_data[0]['id']

    assert response.status_code == 200
    assert event_id == new_event_id
    print("GET /events success")


def test_stream_definition_post():
    headers = {
        'X-Auth-User': 'mini-mon',
        'X-Auth-Key': 'password',
        'X-Auth-Token': token(),
        'Accept': 'application/json',
        'User-Agent': 'python-monascaclient',
        'Content-Tye': 'application/json'}

    body = {}

    body = {"fire_criteria": [{"event_type": "compute.instance.create.start"},
                              {"event_type": "compute.instance.create.end"}],
            "description": "provisioning duration",
            "name": "panda",
            "group_by": ["instance_id"],
            "expiration": 3,
            "select": [{"traits": {"tenant_id": "406904"},
                        "event_type": "compute.instance.create.*"}],
            "fire_actions": ["ed469bb9-2b4a-457a-9926-9da9f6ac75da"],
            "expire_actions": ["ed469bb9-2b4a-457a-9926-9da9f6ac75da"]}

    response = requests.post(url=events_url + "/v2.0/stream-definitions",
                             data=json.dumps(body),
                             headers=headers)
    print(response.status_code)
    print(response.text)


def test_stream_definition_get():
    headers = {
        'X-Auth-User': 'mini-mon',
        'X-Auth-Key': 'password',
        'X-Auth-Token': token(),
        'Accept': 'application/json',
        'User-Agent': 'python-monascaclient',
        'Content-Type': 'application/json'}

    body = {}

    response = requests.post(url=events_url + "/v2.0/stream-definitions",
                             data=json.dumps(body),
                             headers=headers)
    print(response.status_code)
    print(response.text)


def test_stream_definition_delete():
    headers = {
        'X-Auth-User': 'mini-mon',
        'X-Auth-Token': token(),
        'X-Auth-Key': 'password',
        'Accept': 'application/json',
        'User-Agent': 'python-monascaclient',
        'Content-Type': 'application/json'}

    body = {}

    response = requests.delete(
        url=events_url + "/v2.0/stream-definitions/86177f0e-f811-4c42-a91a-1813251bf93f",
        data=json.dumps(body),
        headers=headers)

    print(response.status_code)
    print(response.text)

test_stream_definition_post()
test_stream_definition_get()
test_stream_definition_delete()
test_events_get()
