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

import falcon

from monasca_events_api.middleware import validation_middleware as vm
from monasca_events_api.tests.unit import base


class FakeRequest(object):
    def __init__(self, content=None, length=0):
        self.content_type = content if content else None
        self.content_length = (length if length is not None and length > 0
                               else None)


class TestValidation(base.BaseTestCase):

    def setUp(self):
        super(TestValidation, self).setUp()

    def test_should_validate_right_content_type(self):
        req = FakeRequest('application/json')
        vm._validate_content_type(req)

    def test_should_fail_missing_content_type(self):
        req = FakeRequest()
        self.assertRaises(falcon.HTTPMissingHeader,
                          vm._validate_content_type,
                          req)

    def test_should_fail_unsupported_content_type(self):
        req = FakeRequest('test/plain')
        self.assertRaises(falcon.HTTPUnsupportedMediaType,
                          vm._validate_content_type,
                          req)
