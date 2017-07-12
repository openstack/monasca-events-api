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

from falcon import testing

from monasca_events_api.app.core import request
from monasca_events_api.tests.unit import base


class TestRequest(base.BaseTestCase):

    def setUp(self):
        super(TestRequest, self).setUp()

    def test_use_context_from_request(self):
        req = request.Request(
            testing.create_environ(
                path='/',
                headers={
                    'X_AUTH_TOKEN': '1111',
                    'X_USER_ID': '2222',
                    'X_PROJECT_ID': '3333',
                    'X_ROLES': 'goku,vegeta'
                }
            )
        )
        self.assertEqual('1111', req.context.auth_token)
        self.assertEqual('2222', req.context.user_id)
        self.assertEqual('3333', req.context.project_id)
        self.assertItemsEqual(['goku', 'vegeta'], req.context.roles)

    def test_check_is_admin_from_request(self):
        req = request.Request(
            testing.create_environ(
                path='/',
                headers={
                    'X_USER_ID': '2222',
                    'X_PROJECT_ID': '3333',
                    'X_ROLES': 'admin,burger'
                }
            ),

        )
        self.assertTrue(req.is_admin)

    def test_request_context_admin_uppercase(self):
        req = request.Request(
            testing.create_environ(
                path='/',
                headers={
                    'X_USER_ID': '1111',
                    'X_PROJECT_ID': '2222',
                    'X_ROLES': 'Admin,bob'
                }
            )
        )
        self.assertTrue(req.is_admin)
