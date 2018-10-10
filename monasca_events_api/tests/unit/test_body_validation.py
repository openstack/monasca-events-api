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

from falcon.errors import HTTPUnprocessableEntity

from monasca_events_api.app.controller.v1.body_validation import validate_body
from monasca_events_api.tests.unit import base


class TestBodyValidation(base.BaseTestCase):

    def test_missing_events_filed(self):
        body = {'timestamp': '2012-10-29T13:42:11Z+0200'}
        self.assertRaises(HTTPUnprocessableEntity, validate_body, body)

    def test_missing_timestamp_field(self):
        body = {'events': [{'event': {'payload': 'test'}}]}
        self.assertRaises(HTTPUnprocessableEntity, validate_body, body)

    def test_empty_events_as_list(self):
        body = {'events': [], 'timestamp': u'2012-10-29T13:42:11Z+0200'}
        self.assertRaises(HTTPUnprocessableEntity, validate_body, body)

    def test_empty_events_as_dict(self):
        body = {'events': {}, 'timestamp': u'2012-10-29T13:42:11Z+0200'}
        self.assertRaises(HTTPUnprocessableEntity, validate_body, body)

    def test_empty_body(self):
        body = {}
        self.assertRaises(HTTPUnprocessableEntity, validate_body, body)

    def test_incorrect_timestamp_type(self):
        body = {'events': [], 'timestamp': 9000}
        self.assertRaises(HTTPUnprocessableEntity, validate_body, body)

    def test_incorrect_events_type(self):
        body = {'events': 'over9000', 'timestamp': '2012-10-29T13:42:11Z+0200'}
        self.assertRaises(HTTPUnprocessableEntity, validate_body, body)

    def test_correct_body(self):
        body = [{'events': [{'event': {'payload': 'test'}}],
                 'timestamp': u'2012-10-29T13:42:11Z+0200'},
                {'events': {'event': {'payload': 'test'}},
                 'timestamp': u'2012-10-29T13:42:11Z+0200'}]
        for b in body:
            validate_body(b)
