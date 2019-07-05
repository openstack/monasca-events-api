# Copyright 2017 FUJITSU LIMITED
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import os

import falcon
import mock
import ujson as json

from monasca_events_api.app.controller.v1 import events
from monasca_events_api.tests.unit import base


ENDPOINT = '/events'


def _init_resource(test):
    resource = events.Events()
    test.app.add_route(ENDPOINT, resource)
    return resource


@mock.patch('monasca_events_api.app.controller.v1.'
            'bulk_processor.EventsBulkProcessor')
class TestEventsApi(base.BaseApiTestCase):

    def test_should_pass_simple_event(self, bulk_processor):
        events_resource = _init_resource(self)
        events_resource._processor = bulk_processor
        unit_test_patch = os.path.dirname(__file__)
        json_file_path = 'event_template_json/req_simple_event.json'
        patch_to_req_simple_event_file = os.path.join(unit_test_patch,
                                                      json_file_path)
        with open(patch_to_req_simple_event_file, 'r') as fi:
            body = fi.read()
        response = self.simulate_request(
            path=ENDPOINT,
            method='POST',
            headers={
                'Content-Type': 'application/json',
                'X_ROLES': 'monasca-user'
            },
            body=body
        )
        self.assertEqual(falcon.HTTP_200, response.status)

    def test_should_multiple_events(self, bulk_processor):
        events_resource = _init_resource(self)
        events_resource._processor = bulk_processor
        unit_test_patch = os.path.dirname(__file__)
        json_file_path = 'event_template_json/req_multiple_events.json'
        req_multiple_events_json = os.path.join(unit_test_patch,
                                                json_file_path)
        with open(req_multiple_events_json, 'r') as fi:
            body = fi.read()
        response = self.simulate_request(
            path=ENDPOINT,
            method='POST',
            headers={
                'Content-Type': 'application/json',
                'X_ROLES': 'monasca-user'
            },
            body=body
        )
        self.assertEqual(falcon.HTTP_200, response.status)

    def test_should_fail_empty_body(self, bulk_processor):
        events_resource = _init_resource(self)
        events_resource._processor = bulk_processor
        response = self.simulate_request(
            path=ENDPOINT,
            method='POST',
            headers={
                'Content-Type': 'application/json',
                'X_ROLES': 'monasca-user'
            },
            body=''
        )
        self.assertEqual(falcon.HTTP_422, response.status)

    def test_should_fail_missing_timestamp_in_body(self, bulk_processor):
        events_resource = _init_resource(self)
        events_resource._processor = bulk_processor
        unit_test_patch = os.path.dirname(__file__)
        json_file_path = 'event_template_json/req_simple_event.json'
        patch_to_req_simple_event_file = os.path.join(unit_test_patch,
                                                      json_file_path)
        with open(patch_to_req_simple_event_file, 'r') as fi:
            events = json.load(fi)['events']
        body = {'events': [events]}
        response = self.simulate_request(
            path=ENDPOINT,
            method='POST',
            headers={
                'Content-Type': 'application/json',
                'X_ROLES': 'monasca-user'
            },
            body=json.dumps(body)
        )
        self.assertEqual(falcon.HTTP_422, response.status)

    def test_should_fail_missing_events_in_body(self, bulk_processor):
        events_resource = _init_resource(self)
        events_resource._processor = bulk_processor
        body = {'timestamp': '2012-10-29T13:42:11Z+0200'}
        response = self.simulate_request(
            path=ENDPOINT,
            method='POST',
            headers={
                'Content-Type': 'application/json',
                'X_ROLES': 'monasca-user'
            },
            body=json.dumps(body)
        )
        self.assertEqual(falcon.HTTP_422, response.status)

    def test_should_fail_missing_content_type(self, bulk_processor):
        events_resource = _init_resource(self)
        events_resource._processor = bulk_processor
        body = {'timestamp': '2012-10-29T13:42:11Z+0200'}
        response = self.simulate_request(
            path=ENDPOINT,
            method='POST',
            headers={
                'X_ROLES': 'monasca-user'
            },
            body=json.dumps(body)
        )
        self.assertEqual(falcon.HTTP_400, response.status)

    def test_should_fail_wrong_content_type(self, bulk_processor):
        events_resource = _init_resource(self)
        events_resource._processor = bulk_processor
        body = {'timestamp': '2012-10-29T13:42:11Z+0200'}
        response = self.simulate_request(
            path=ENDPOINT,
            method='POST',
            headers={
                'Content-Type': 'text/plain',
                'X_ROLES': 'monasca-user'
            },
            body=json.dumps(body)
        )
        self.assertEqual(falcon.HTTP_415, response.status)


class TestApiEventsVersion(base.BaseApiTestCase):
    @mock.patch('monasca_events_api.app.controller.v1.'
                'bulk_processor.EventsBulkProcessor')
    def test_should_return_v1_as_version(self, _):
        resource = events.Events()
        self.assertEqual('v1.0', resource.version)
