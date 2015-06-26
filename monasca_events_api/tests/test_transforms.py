# Copyright 2014 Hewlett-Packard
#
# Licensed under the Apache License,  Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,  software
# distributed under the License is distributed on an "AS IS" BASIS,  WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND,  either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import falcon
import json
from monasca_events_api.common.repositories.mysql.transforms_repository import TransformsRepository
from monasca_events_api.v2.transforms import Transforms

import mock
from monasca_events_api.common.repositories import exceptions as repository_exceptions

import unittest


class TransformsSubClass(Transforms):

    def __init__(self):
        self._default_authorized_roles = ['user', 'domainuser',
                                          'domainadmin', 'monasca-user']
        self._transforms_repo = None
        self._region = 'useast'
        self._message_queue = None


class Test_Transforms(unittest.TestCase):

    def _generate_req(self):
        """Generate a mock HTTP request"""
        req = mock.MagicMock()
        req.get_param.return_value = None

        req.headers = {
            'X-Auth-User': 'mini-mon',
            'X-Auth-Token': "ABCD",
            'X-Auth-Key': 'password',
            'X-TENANT-ID': '0ab1ac0a-2867-402d',
            'X-ROLES': 'user,  domainuser,  domainadmin,  monasca-user,  monasca-agent',
            'Accept': 'application/json',
            'User-Agent': 'python-monascaclient',
            'Content-Type': 'application/json'}

        req.body = {}
        req.content_type = 'application/json'
        return req

    @mock.patch(
        'monasca_events_api.common.repositories.mysql.mysql_repository.mdb')
    @mock.patch('monasca_events_api.v2.common.helpers.validate_authorization')
    @mock.patch('monasca_events_api.v2.common.helpers.get_tenant_id')
    def test_on_get_fail_db_down(
            self,
            helper_tenant_id,
            helpers_validate,
            mysqlRepo):
        """GET Method fail due to db down"""
        mysqlRepo.connect.side_effect = repository_exceptions.RepositoryException(
            "Database Connection Error")
        helpers_validate.return_value = True
        mysqlRepo.connect.return_value = True
        helper_tenant_id.return_value = '0ab1ac0a-2867-402d'

        transObj = TransformsSubClass()
        transObj._transforms_repo = TransformsRepository()
        res = mock.MagicMock()
        res.body = {}
        res.status = 0
        try:
            transObj.on_get(self._generate_req(), res)
            self.assertFalse(
                1,
                msg="Database Down,  GET should fail but succeeded")
        except Exception as e:
            self.assertRaises(falcon.HTTPInternalServerError)
            self.assertEqual(e.status, '500 Internal Server Error')

    @mock.patch('monasca_events_api.v2.common.helpers.validate_authorization')
    def test_on_get_fail_validate_authorization(self, _validate_authorization):
        """GET Method fail due to validate authorization"""
        _validate_authorization.side_effect = falcon.HTTPUnauthorized(
            'Forbidden',
            'Tenant does not have any roles')
        transObj = TransformsSubClass()
        transObj._transforms_repo = TransformsRepository()
        res = mock.MagicMock()
        res.body = {}
        res.status = 0
        try:
            transObj.on_get(self._generate_req(), res)
            self.assertFalse(
                1,
                msg="Validate Authorization failed, GET should fail but succeeded")
        except Exception as e:
            self.assertRaises(falcon.HTTPUnauthorized)
            self.assertEqual(e.status, '401 Unauthorized')

    @mock.patch('monasca_events_api.v2.transforms.Transforms._list_transforms')
    @mock.patch('monasca_events_api.v2.common.helpers.validate_authorization')
    @mock.patch('monasca_events_api.v2.common.helpers.get_tenant_id')
    def test_on_get_pass(
            self,
            helper_tenant_id,
            helpers_validate,
            list_transforms):
        """GET Method success Single Event"""
        helpers_validate.return_value = True
        helper_tenant_id.return_value = '0ab1ac0a-2867-402d'
        returnTransform = [{"id": "1",
                            "name": "Trans1",
                            "description": "Desc1",
                            "specification": "AutoSpec1",
                            "enabled": "True"},
                           {"id": "2",
                            "name": "Trans2",
                            "description": "Desc2",
                            "specification": "AutoSpec2",
                            "enabled": "False"}]

        list_transforms.return_value = returnTransform
        transObj = TransformsSubClass()
        transObj._transforms_repo = TransformsRepository()
        res = mock.MagicMock()
        res.body = {}
        res.status = 0
        transObj.on_get(self._generate_req(), res)
        self.assertEqual(res.status, '200 OK')
        self.assertEqual(returnTransform, json.loads(json.dumps(res.body)))

    @mock.patch(
        'monasca_events_api.common.repositories.mysql.mysql_repository.mdb')
    @mock.patch('monasca_events_api.v2.common.helpers.validate_authorization')
    @mock.patch('monasca_events_api.v2.common.helpers.get_tenant_id')
    def test_on_delete_fail(
            self,
            helper_tenant_id,
            helpers_validate,
            mysqlRepo):
        """DELETE Method fail due to db down"""
        mysqlRepo.connect.side_effect = repository_exceptions.RepositoryException(
            "Database Connection Error")
        helpers_validate.return_value = True
        helper_tenant_id.return_value = '0ab1ac0a-2867-402d'
        transform_id = "0ab1ac0a"

        transObj = TransformsSubClass()
        transObj._transforms_repo = TransformsRepository()
        res = mock.MagicMock()
        res.body = {}
        res.status = 0
        try:
            transObj.on_delete(self._generate_req(), res, transform_id)
            self.assertFalse(
                1,
                msg="Database Down,  delete should fail but succeeded")
        except Exception as e:
            self.assertRaises(falcon.HTTPInternalServerError)
            self.assertEqual(e.status, '500 Internal Server Error')

    @mock.patch('monasca_events_api.v2.common.helpers.validate_authorization')
    def test_on_delete_fail_validate_authorization(
            self,
            _validate_authorization):
        """Post Method fail due to validate authorization"""
        _validate_authorization.side_effect = falcon.HTTPUnauthorized(
            'Forbidden',
            'Tenant does not have any roles')
        transform_id = "0ab1ac0a"
        transObj = TransformsSubClass()
        transObj._transforms_repo = TransformsRepository()
        res = mock.MagicMock()
        res.body = {}
        res.status = 0
        try:
            transObj.on_delete(self._generate_req(), res, transform_id)
            self.assertFalse(
                1,
                msg="Validate Authorization failed, delete should fail but succeeded")

        except Exception as e:
            self.assertRaises(falcon.HTTPUnauthorized)
            self.assertEqual(e.status, '401 Unauthorized')

    @mock.patch(
        'monasca_events_api.common.messaging.kafka_publisher.KafkaPublisher')
    @mock.patch(
        'monasca_events_api.v2.transforms.Transforms._delete_transform')
    @mock.patch('monasca_events_api.v2.common.helpers.validate_authorization')
    @mock.patch('monasca_events_api.v2.common.helpers.get_tenant_id')
    def test_on_delete_pass(
            self,
            helper_tenant_id,
            helpers_validate,
            deleteTransform,
            kafka):
        """DELETE Method pass"""
        helpers_validate.return_value = True
        helper_tenant_id.return_value = '0ab1ac0a-2867-402d'
        transform_id = "0ab1ac0a"
        deleteTransform.return_value = True

        transObj = TransformsSubClass()
        transObj._message_queue = kafka
        transObj._transforms_repo = TransformsRepository()
        res = mock.MagicMock()
        res.body = {}
        res.status = 0
        transObj.on_delete(self._generate_req(), res, transform_id)
        self.assertEqual(res.status, '204 No Content')

    @mock.patch(
        'monasca_events_api.common.repositories.mysql.mysql_repository.mdb')
    @mock.patch(
        'monasca_events_api.v2.transforms.Transforms._validate_transform')
    @mock.patch(
        'monasca_events_api.v2.common.helpers.validate_json_content_type')
    @mock.patch(
        'monasca_events_api.v2.transforms.Transforms._delete_transform')
    @mock.patch('monasca_events_api.v2.common.helpers.validate_authorization')
    @mock.patch('monasca_events_api.v2.common.helpers.get_tenant_id')
    @mock.patch('monasca_events_api.v2.common.helpers.read_http_resource')
    def test_on_post_fail_db_down(
            self,
            readhttp,
            helper_tenant_id,
            helpers_validate,
            deleteTransform,
            validjson,
            validateTransform,
            mysqlRepo):
        """Post Method fail due to db down"""
        mysqlRepo.connect.side_effect = repository_exceptions.RepositoryException(
            "Database Connection Error")
        helpers_validate.return_value = True
        validjson.return_value = True
        validateTransform.return_value = True
        readhttp.return_value = {
            'name': 'Foo',
            'description': 'transform def',
            'specification': 'transform spec'}

        helper_tenant_id.return_value = '0ab1ac0a-2867-402d'

        transObj = TransformsSubClass()
        transObj._transforms_repo = TransformsRepository()
        res = mock.MagicMock()
        res.body = {}
        res.status = 0
        try:
            transObj.on_post(self._generate_req(), res)
            self.assertFalse(
                1,
                msg="Database Down, POST should fail but succeeded")
        except Exception as e:
            self.assertRaises(falcon.HTTPInternalServerError)
            self.assertEqual(e.status, '500 Internal Server Error')

    @mock.patch(
        'monasca_events_api.v2.transforms.Transforms._validate_transform')
    @mock.patch(
        'monasca_events_api.v2.common.helpers.validate_json_content_type')
    @mock.patch('monasca_events_api.v2.common.helpers.validate_authorization')
    @mock.patch('monasca_events_api.v2.common.helpers.read_http_resource')
    def test_on_post_fail_validate_transform(
            self,
            readhttp,
            helpers_validate,
            validjson,
            _validate_transform):
        """Post Method fail due to validate transform"""
        helpers_validate.return_value = True
        validjson.return_value = True
        _validate_transform.side_effect = falcon.HTTPBadRequest(
            'Bad request',
            'Error')
        readhttp.return_value = self._generate_req()

        transObj = TransformsSubClass()
        transObj._transforms_repo = TransformsRepository()
        res = mock.MagicMock()
        res.body = {}
        res.status = 0
        try:
            transObj.on_post(self._generate_req(), res)
            self.assertFalse(
                1,
                msg="Validate Trasnform failed, POST should fail but succeeded")
        except Exception as e:
            self.assertRaises(falcon.HTTPBadRequest)
            self.assertEqual(e.status, '400 Bad Request')

    @mock.patch('monasca_events_api.v2.common.helpers.validate_authorization')
    def test_on_post_fail_validate_authorization(
            self,
            _validate_authorization):
        """Post Method fail due to validate authorization"""
        _validate_authorization.side_effect = falcon.HTTPUnauthorized(
            'Forbidden',
            'Tenant does not have any roles')

        transObj = TransformsSubClass()
        transObj._transforms_repo = TransformsRepository()
        res = mock.MagicMock()
        res.body = {}
        res.status = 0
        try:
            transObj.on_post(self._generate_req(), res)
            self.assertFalse(
                1,
                msg="Validate Authorization failed, POST should fail but succeeded")
        except Exception as e:
            self.assertRaises(falcon.HTTPUnauthorized)
            self.assertEqual(e.status, '401 Unauthorized')

    @mock.patch(
        'monasca_events_api.common.messaging.kafka_publisher.KafkaPublisher')
    @mock.patch(
        'monasca_events_api.v2.transforms.Transforms._create_transform_response')
    @mock.patch(
        'monasca_events_api.common.repositories.mysql.mysql_repository.mdb')
    @mock.patch(
        'monasca_events_api.v2.transforms.Transforms._validate_transform')
    @mock.patch(
        'monasca_events_api.v2.common.helpers.validate_json_content_type')
    @mock.patch(
        'monasca_events_api.v2.transforms.Transforms._delete_transform')
    @mock.patch('monasca_events_api.v2.common.helpers.validate_authorization')
    @mock.patch('monasca_events_api.v2.common.helpers.get_tenant_id')
    @mock.patch('monasca_events_api.v2.common.helpers.read_http_resource')
    def test_on_post_pass_valid_request(
            self,
            readhttp,
            helper_tenant_id,
            helpers_validate,
            deleteTransform,
            validjson,
            validateTransform,
            mysqlRepo,
            createRes,
            kafka):
        """Post Method pass due to valid request"""
        helpers_validate.return_value = True
        validjson.return_value = True
        returnTransform = {'name': 'Trans1',
                           'description': 'Desc1',
                           'specification': 'AutoSpec1'
                           }
        createRes.return_value = returnTransform
        readhttp.return_value = returnTransform
        helper_tenant_id.return_value = '0ab1ac0a-2867-402d'

        transObj = TransformsSubClass()
        transObj._message_queue = kafka
        transObj._transforms_repo = TransformsRepository()
        res = mock.MagicMock()
        res.body = {}
        res.status = 0
        transObj.on_post(self._generate_req(), res)
        self.assertEqual(falcon.HTTP_200, "200 OK")
        self.assertEqual(returnTransform, json.loads(json.dumps(res.body)))

    @mock.patch(
        'monasca_events_api.common.messaging.kafka_publisher.KafkaPublisher')
    @mock.patch(
        'monasca_events_api.v2.transforms.Transforms._create_transform_response')
    @mock.patch(
        'monasca_events_api.common.repositories.mysql.mysql_repository.mdb')
    @mock.patch(
        'monasca_events_api.v2.common.helpers.validate_json_content_type')
    @mock.patch(
        'monasca_events_api.v2.transforms.Transforms._delete_transform')
    @mock.patch('monasca_events_api.v2.common.helpers.validate_authorization')
    @mock.patch('monasca_events_api.v2.common.helpers.get_tenant_id')
    @mock.patch('monasca_events_api.v2.common.helpers.read_http_resource')
    def test_on_post_pass_fail_invalid_request(
            self,
            readhttp,
            helper_tenant_id,
            helpers_validate,
            deleteTransform,
            validjson,
            mysqlRepo,
            createRes,
            kafka):
        """Post Method fails due to invalid request"""
        helpers_validate.return_value = True
        validjson.return_value = True
        returnTransform = {
            'description': 'Desc1',
            'specification': 'AutoSpec1'
        }
        createRes.return_value = returnTransform
        readhttp.return_value = returnTransform
        helper_tenant_id.return_value = '0ab1ac0a-2867-402d'

        transObj = TransformsSubClass()
        transObj._message_queue = kafka
        transObj._transforms_repo = TransformsRepository()
        res = mock.MagicMock()
        res.body = {}
        res.status = 0
        try:
            transObj.on_post(self._generate_req(), res)
            self.assertFalse(
                1,
                msg="Validate transform failed, POST should fail but succeeded")
        except Exception as e:
            self.assertRaises(falcon.HTTPBadRequest)
            self.assertEqual(e.status, '400 Bad Request')
