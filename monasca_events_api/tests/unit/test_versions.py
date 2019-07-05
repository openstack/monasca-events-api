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

from six.moves.urllib.parse import urlparse as urlparse

import falcon

from monasca_events_api.app.controller import versions
from monasca_events_api.tests.unit import base


def _get_versioned_url(version_id):
    return '/version/%s' % version_id


class TestVersionApi(base.BaseApiTestCase):

    def setUp(self):
        super(TestVersionApi, self).setUp()
        self.versions = versions.Versions()
        self.app.add_route("/version/", self.versions)
        self.app.add_route("/version/{version_id}", self.versions)

    def test_request_for_incorrect_version(self):
        incorrect_version = 'v2.0'
        uri = _get_versioned_url(incorrect_version)

        res = self.simulate_request(
            path=uri,
            method='GET',
            headers={
                'Content-Type': 'application/json'
            }
        )

        self.assertEqual(falcon.HTTP_400, res.status)

    def test_should_return_supported_event_api_version(self):

        def _check_global_links(current_endpoint, links):
            expected_links = {'self': current_endpoint,
                              'version': '/version',
                              'healthcheck': '/healthcheck'}
            _check_links(links, expected_links)

        def _check_links(links, expected_links):
            for link in links:
                self.assertIn('rel', link)
                self.assertIn('href', link)
                key = link.get('rel')
                href_path = urlparse(link.get('href')).path
                self.assertIn(key, expected_links.keys())
                self.assertEqual(expected_links[key], href_path)

        def _check_elements(elements, expected_versions):
            self.assertIsInstance(elements, list)
            for el in elements:
                self.assertItemsEqual([
                    u'id',
                    u'links',
                    u'status',
                    u'updated'
                ], el.keys())
                id_v = el.get('id')
                self.assertEqual(expected_versions, id_v)

        supported_versions = ['v1.0']
        version_endpoint = '/version'
        for version in supported_versions:
            endpoint = '%s/%s' % (version_endpoint, version)
            res = self.simulate_request(
                path=endpoint,
                method='GET',
                headers={
                    'Content-Type': 'application/json'
                }
            )
            self.assertEqual(falcon.HTTP_200, res.status)
            response = res.json
            self.assertIn('links', response)
            _check_global_links(endpoint, response['links'])
            self.assertIn('elements', response)
            _check_elements(response['elements'], version)
