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
import time

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

    event_id = json_data[0]['id']

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


def test_events_get_all():
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

    assert response.status_code == 200
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

    notif_resp = requests.get(
        url="http://192.168.10.4:8080/v2.0/notification-methods",
        data=json.dumps(body), headers=headers)
    notif_dict = json.loads(notif_resp.text)
    action_id = str(notif_dict['elements'][0]['id'])

    body = {"fire_criteria": [{"event_type": "compute.instance.create.start"},
                              {"event_type": "compute.instance.create.end"}],
            "description": "provisioning duration",
            "name": str(time.time()),
            "group_by": ["instance_id"],
            "expiration": 3000,
            "select": [{"traits": {"tenant_id": "406904"},
                        "event_type": "compute.instance.create.*"}],
            "fire_actions": [action_id],
            "expire_actions": [action_id]}

    response = requests.post(
        url=events_url + "/v2.0/stream-definitions",
        data=json.dumps(body),
        headers=headers)
    assert response.status_code == 201
    print("POST /stream-definitions success")


def test_stream_definition_get():
    headers = {
        'X-Auth-User': 'mini-mon',
        'X-Auth-Key': 'password',
        'X-Auth-Token': token(),
        'Accept': 'application/json',
        'User-Agent': 'python-monascaclient',
        'Content-Type': 'application/json'}

    body = {}

    response = requests.get(
        url=events_url + "/v2.0/stream-definitions/",
        data=json.dumps(body),
        headers=headers)
    assert response.status_code == 200
    print("GET /stream-definitions success")


def test_stream_definition_delete():
    headers = {
        'X-Auth-User': 'mini-mon',
        'X-Auth-Token': token(),
        'X-Auth-Key': 'password',
        'Accept': 'application/json',
        'User-Agent': 'python-monascaclient',
        'Content-Type': 'application/json'}

    body = {}

    stream_resp = requests.get(
        url=events_url + "/v2.0/stream-definitions/",
        data=json.dumps(body),
        headers=headers)
    stream_dict = json.loads(stream_resp.text)
    stream_id = str(stream_dict[0]['id'])
    response = requests.delete(
        url=events_url + "/v2.0/stream-definitions/{}".format(
            stream_id),
        data=json.dumps(body),
        headers=headers)
    assert response.status_code == 204
    print("DELETE /stream-definitions success")

test_stream_definition_post()
test_stream_definition_get()
test_stream_definition_delete()
test_events_get_all()
