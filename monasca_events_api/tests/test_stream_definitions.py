# Copyright 2014 Hewlett-Packard
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.


import falcon
import json

from monasca_events_api.common.repositories.mysql.streams_repository import StreamsRepository
from monasca_events_api.v2.stream_definitions import StreamDefinitions

import mock
from monasca_events_api.common.repositories.exceptions import AlreadyExistsException
from monasca_events_api.common.repositories.exceptions import RepositoryException


import unittest


class StreamDefinitionsSubClass(StreamDefinitions):

    def __init__(self):
        self._default_authorized_roles = ['user', 'domainuser',
                                          'domainadmin', 'monasca-user']
        self._post_events_authorized_roles = [
            'user',
            'domainuser',
            'domainadmin',
            'monasca-user',
            'monasca-agent']
        self._stream_definitions_repo = None
        self.stream_definition_event_message_queue = None
        self._region = 'useast'


class Test_StreamDefinitions(unittest.TestCase):

    def _generate_req(self):
        """Generate a mock HTTP request"""
        req = mock.MagicMock()
        req.get_param.return_value = None

        req.headers = {
            'X-Auth-User': 'mini-mon',
            'X-Auth-Token': 'ABCD',
            'X-Auth-Key': 'password',
            'X-TENANT-ID': '0ab1ac0a-2867-402d',
            'X-ROLES': 'user, domainuser, domainadmin, monasca-user, monasca-agent',
            'Accept': 'application/json',
            'User-Agent': 'python-monascaclient',
            'Content-Type': 'application/json'}

        req.body = {}
        req.uri = "/v2.0/stream-definitions/{stream_id}"
        req.content_type = 'application/json'
        return req

    @mock.patch('monasca_events_api.v2.common.helpers.add_links_to_resource')
    @mock.patch(
        'monasca_events_api.common.repositories.mysql.mysql_repository.mdb')
    @mock.patch('monasca_events_api.v2.common.helpers.normalize_offset')
    @mock.patch('monasca_events_api.v2.common.helpers.get_query_name')
    @mock.patch(
        'monasca_events_api.common.repositories.mysql.mysql_repository.mdb')
    @mock.patch('monasca_events_api.v2.common.helpers.validate_authorization')
    @mock.patch('monasca_events_api.v2.common.helpers.get_tenant_id')
    def test_on_get_stream_fail_db_down(
            self,
            tenant_id,
            validate,
            mysqlRepo,
            qname,
            normalize,
            repo,
            getlinks):
        """GET Method FAIL Single Stream"""
        repo.connect.side_effect = RepositoryException(
            "Database Connection Error")
        validate.return_value = True
        normalize.return_value = 5
        qname.return_value = "Test"
        tenant_id.return_value = '0ab1ac0a-2867-402d'

        stream_id = "1"
        streamsObj = StreamDefinitionsSubClass()
        streamsObj._stream_definitions_repo = StreamsRepository()
        res = mock.MagicMock()
        res.body = {}
        res.status = 0
        try:
            streamsObj.on_get(self._generate_req(), res, stream_id)
            self.assertFalse(
                1,
                msg="Database Down, GET should fail but succeeded")
        except Exception as e:
            self.assertRaises(falcon.HTTPInternalServerError)
            self.assertEqual(e.status, '500 Internal Server Error')

    @mock.patch(
        'monasca_events_api.common.repositories.mysql.mysql_repository.mdb')
    @mock.patch(
        'monasca_events_api.v2.stream_definitions.StreamDefinitions._stream_definition_show')
    @mock.patch('monasca_events_api.v2.common.helpers.add_links_to_resource')
    @mock.patch('monasca_events_api.v2.common.helpers.get_tenant_id')
    @mock.patch('monasca_events_api.v2.common.helpers.validate_authorization')
    def test_on_get_streamid_pass(
            self,
            validate,
            tenant_id,
            getlinks,
            definitionshow,
            mysqlRepo):
        """GET Method SUCCESS Single Stream"""

        validate.return_value = True
        tenant_id.return_value = '0ab1ac0a-2867-402d'
        returnStream = [{"region": "useast", "tenantId": "0ab1ac0a-2867-402d",
                         "creation_time": "1434331190", "stream": "1"}]
        definitionshow.return_value = returnStream
        getlinks.return_value = "/v2.0/stream-definitions/{stream_id}"
        mysqlRepo.connect.return_value = True
        stream_id = "1"
        streamsObj = StreamDefinitionsSubClass()
        streamsObj._stream_definitions_repo = StreamsRepository()
        res = mock.MagicMock()
        res.body = {}
        res.status = 0
        streamsObj.on_get(self._generate_req(), res, stream_id)
        self.assertEqual(returnStream, json.loads(res.body))
        self.assertEqual(res.status, '200 OK')

    @mock.patch('monasca_events_api.v2.common.helpers.normalize_offset')
    @mock.patch(
        'monasca_events_api.common.repositories.mysql.mysql_repository.mdb')
    @mock.patch('monasca_events_api.v2.common.helpers.validate_authorization')
    @mock.patch('monasca_events_api.v2.common.helpers.get_tenant_id')
    def test_on_get_streams_fail_db_down(
            self,
            tenant_id,
            validate,
            mysqlRepo,
            normalize):
        """GET Method FAILS Multiple Streams"""
        mysqlRepo.connect.side_effect = RepositoryException(
            "Database Connection Error")
        validate.return_value = True
        tenant_id.return_value = '0ab1ac0a-2867-402d'
        normalize.return_value = 5
        streamsObj = StreamDefinitionsSubClass()
        streamsObj._stream_definitions_repo = StreamsRepository()
        res = mock.MagicMock()
        res.body = {}
        res.status = 0
        try:
            streamsObj.on_get(self._generate_req(), res, None)
            self.assertFalse(
                1,
                msg="Database Down, GET should fail but succeeded")
        except Exception as e:
            self.assertRaises(falcon.HTTPInternalServerError)
            self.assertEqual(e.status, '500 Internal Server Error')

    @mock.patch('monasca_events_api.v2.common.helpers.normalize_offset')
    @mock.patch(
        'monasca_events_api.common.repositories.mysql.mysql_repository.mdb')
    @mock.patch(
        'monasca_events_api.v2.stream_definitions.StreamDefinitions._stream_definition_list')
    @mock.patch('monasca_events_api.v2.common.helpers.add_links_to_resource')
    @mock.patch('monasca_events_api.v2.common.helpers.get_tenant_id')
    @mock.patch('monasca_events_api.v2.common.helpers.validate_authorization')
    def test_on_get_streams_pass(
            self,
            validate,
            tenant_id,
            getlinks,
            definitionlist,
            mysqlRepo,
            normalize):
        """GET Method SUCCESS Streams List"""

        validate.return_value = True
        tenant_id.return_value = '0ab1ac0a-2867-402d'
        returnStreams = [{"region": "useast", "tenantId": "0ab1ac0a-2867-402d",
                          "creation_time": "1434331190", "stream": "1"},
                         {"region": "useast", "tenantId": "0ab1ac0a-2866-403d",
                          "creation_time": "1234567890", "stream": "2"}]
        definitionlist.return_value = returnStreams
        normalize.return_value = 5
        getlinks.return_value = "/v2.0/stream-definitions/"
        mysqlRepo.connect.return_value = True

        streamsObj = StreamDefinitionsSubClass()
        streamsObj._stream_definitions_repo = StreamsRepository()
        res = mock.MagicMock()
        res.body = {}
        res.status = 0
        streamsObj.on_get(self._generate_req(), res, None)
        self.assertEqual(returnStreams, json.loads(res.body))
        self.assertEqual(res.status, '200 OK')

    @mock.patch(
        'monasca_events_api.common.repositories.mysql.mysql_repository.mdb')
    @mock.patch(
        'monasca_events_api.v2.stream_definitions.get_query_stream_definition_expire_actions')
    @mock.patch(
        'monasca_events_api.v2.stream_definitions.get_query_stream_definition_fire_actions')
    @mock.patch(
        'monasca_events_api.v2.stream_definitions.get_query_stream_definition_description')
    @mock.patch(
        'monasca_events_api.v2.stream_definitions.get_query_stream_definition_name')
    @mock.patch(
        'monasca_events_api.v2.stream_definitions.StreamDefinitions._validate_stream_definition')
    @mock.patch('monasca_events_api.v2.common.helpers.read_json_msg_body')
    @mock.patch(
        'monasca_events_api.v2.common.helpers.validate_json_content_type')
    @mock.patch('monasca_events_api.v2.common.helpers.get_tenant_id')
    @mock.patch('monasca_events_api.v2.common.helpers.validate_authorization')
    def test_on_post_integrity_error(
            self,
            validate,
            tenantid,
            json,
            readjson,
            streamvalid,
            getname,
            desc,
            fireactions,
            expire,
            repo):
        """POST method  failed due to integrity error"""
        validate.return_value = True
        repo.connect.side_effect = AlreadyExistsException()
        fireactions.return_value = "fire_actions"
        getname.return_value = "Test"
        expire.return_value = "expire_actions"
        desc.return_value = "Stream_Description"
        readjson.return_value = {
            u'fire_criteria': [
                {
                    u'event_type': u'compute.instance.create.start'},
                {
                    u'event_type': u'compute.instance.create.end'}],
            u'description': u'provisioning duration',
            u'group_by': [u'instance_id'],
            u'expiration': 90000,
            u'select': [
                {
                    u'event_type': u'compute.instance.create.*'}],
            u'name': u'buzz'}

        tenantid.return_value = '0ab1ac0a-2867-402d'
        streamvalid.return_value = True

        streamsObj = StreamDefinitionsSubClass()
        streamsObj._stream_definitions_repo = StreamsRepository()
        res = mock.MagicMock()
        res.body = {}
        res.status = 0
        try:
            streamsObj.on_post(self._generate_req(), res)
            self.assertFalse(
                1,
                msg="DB Integrity Error, should fail but passed")
        except Exception as e:
            self.assertRaises(falcon.HTTPConflict)
            self.assertEqual(e.status, '409 Conflict')

    @mock.patch('monasca_events_api.v2.common.helpers.add_links_to_resource')
    @mock.patch(
        'monasca_events_api.common.messaging.kafka_publisher.KafkaPublisher')
    @mock.patch(
        'monasca_events_api.v2.stream_definitions.StreamDefinitions._stream_definition_create')
    @mock.patch(
        'monasca_events_api.v2.stream_definitions.get_query_stream_definition_expire_actions')
    @mock.patch(
        'monasca_events_api.v2.stream_definitions.get_query_stream_definition_fire_actions')
    @mock.patch(
        'monasca_events_api.v2.stream_definitions.get_query_stream_definition_description')
    @mock.patch(
        'monasca_events_api.v2.stream_definitions.get_query_stream_definition_name')
    @mock.patch(
        'monasca_events_api.v2.stream_definitions.StreamDefinitions._validate_stream_definition')
    @mock.patch('monasca_events_api.v2.common.helpers.read_json_msg_body')
    @mock.patch('monasca_events_api.v2.common.helpers.get_tenant_id')
    @mock.patch('monasca_events_api.v2.common.helpers.validate_authorization')
    def test_on_post_pass__validate_stream_definition(
            self,
            validate,
            tenantid,
            readjson,
            streamvalid,
            getname,
            desc,
            fireactions,
            expire,
            streamsrepo,
            kafka,
            addlink):
        """POST method successful"""
        validate.return_value = True
        fireactions.return_value = "fire_actions"
        getname.return_value = "Test"
        addlink.return_value = "/v2.0/stream-definitions/{stream_id}"
        expire.return_value = "expire_actions"
        desc.return_value = "Stream_Description"
        responseObj = {u'fire_criteria': [{u'event_type': u'compute.instance.create.start'},
                                          {u'event_type': u'compute.instance.create.end'}],
                       u'description': u'provisioning duration',
                       u'group_by': [u'instance_id'],
                       u'expiration': 90000,
                       u'select': [{u'event_type': u'compute.instance.create.*'}],
                       u'name': u'buzz'}

        readjson.return_value = responseObj
        streamsrepo.return_value = responseObj
        tenantid.return_value = '0ab1ac0a-2867-402d'

        streamsObj = StreamDefinitionsSubClass()
        streamsObj._stream_definitions_repo = StreamsRepository()
        streamsObj.stream_definition_event_message_queue = kafka
        res = mock.MagicMock()
        res.body = {}
        res.status = 0
        streamsObj.on_post(self._generate_req(), res)
        self.assertEqual(falcon.HTTP_201, res.status)
        self.assertEqual(responseObj, json.loads(res.body))

    @mock.patch('monasca_events_api.v2.common.helpers.validate_authorization')
    @mock.patch('monasca_events_api.v2.common.helpers.read_http_resource')
    @mock.patch('monasca_events_api.v2.common.helpers.add_links_to_resource')
    @mock.patch(
        'monasca_events_api.common.messaging.kafka_publisher.KafkaPublisher')
    @mock.patch(
        'monasca_events_api.v2.stream_definitions.get_query_stream_definition_expire_actions')
    @mock.patch(
        'monasca_events_api.v2.stream_definitions.get_query_stream_definition_fire_actions')
    @mock.patch(
        'monasca_events_api.v2.stream_definitions.get_query_stream_definition_description')
    @mock.patch('monasca_events_api.v2.common.helpers.read_json_msg_body')
    @mock.patch(
        'monasca_events_api.v2.stream_definitions.get_query_stream_definition_name')
    @mock.patch('monasca_events_api.v2.common.helpers.get_tenant_id')
    def test_on_post_fail__validate_stream_definition(
            self,
            tenantid,
            getname,
            readjson,
            desc,
            fireactions,
            expire,
            kafka,
            addlink,
            httpRes,
            authorization):
        """POST method failed due to invalid body"""
        fireactions.return_value = "fire_actions"
        getname.return_value = "Test"
        addlink.return_value = "/v2.0/stream-definitions/{stream_id}"
        expire.return_value = "expire_actions"
        desc.return_value = "Stream_Description"
        """name removed from body"""
        responseObj = {u'fire_criteria': [{u'event_type': u'compute.instance.create.start'},
                                          {u'event_type': u'compute.instance.create.end'}],
                       u'description': u'provisioning duration',
                       u'group_by': [u'instance_id'],
                       u'expiration': 90000,
                       u'name': u'buzz'}
        tenantid.return_value = '0ab1ac0a-2867-402d'
        readjson.return_value = responseObj
        streamsObj = StreamDefinitionsSubClass()
        streamsObj._stream_definitions_repo = StreamsRepository()
        streamsObj.stream_definition_event_message_queue = kafka
        res = mock.MagicMock()
        res.body = {}
        res.status = 0
        try:
            streamsObj.on_post(self._generate_req(), res)
            self.assertFalse(1, msg="Bad Request Sent, should fail but passed")
        except Exception as e:
            self.assertRaises(falcon.HTTPBadRequest)
            self.assertEqual(e.status, '400 Bad Request')

    @mock.patch('monasca_events_api.v2.common.helpers.read_json_msg_body')
    @mock.patch('monasca_events_api.v2.common.helpers.validate_authorization')
    def test_on_post_badrequest(self, validate, readjson):
        """POST method Fail Due to bad request"""
        validate.return_value = True
        readjson.side_effect = falcon.HTTPBadRequest(
            'Bad request',
            'Request body is not valid JSON')
        streamsObj = StreamDefinitionsSubClass()
        res = mock.MagicMock()
        res.body = {}
        res.status = 0
        try:
            streamsObj.on_post(self._generate_req(), res)
            self.assertFalse(1, msg="Bad Request Sent, should fail but passed")
        except Exception as e:
            self.assertRaises(falcon.HTTPBadRequest)
            self.assertEqual(e.status, '400 Bad Request')

    @mock.patch(
        'monasca_events_api.common.repositories.mysql.streams_repository.StreamsRepository.delete_stream_definition')
    @mock.patch('monasca_events_api.v2.common.helpers.get_tenant_id')
    @mock.patch('monasca_events_api.v2.common.helpers.validate_authorization')
    def test_on_delete_fail(self, validate, tenantid, deleteStream):
        """DELETEE method failed due to database down  """
        validate.return_value = True
        tenantid.return_value = '0ab1ac0a-2867-402d'
        deleteStream.side_effect = RepositoryException(
            "Database Connection Error")
        stream_id = "1"
        streamsObj = StreamDefinitionsSubClass()
        res = mock.MagicMock()
        res.body = {}
        res.status = 0
        try:
            streamsObj.on_delete(self._generate_req(), res, stream_id)
            self.assertFalse(1, msg="Database Down, should fail but passed")
        except Exception as e:
            self.assertRaises(falcon.HTTPInternalServerError)
            self.assertEqual(e.status, '500 Internal Server Error')

    @mock.patch(
        'monasca_events_api.v2.stream_definitions.StreamDefinitions._stream_definition_delete')
    @mock.patch(
        'monasca_events_api.common.repositories.mysql.mysql_repository.mdb')
    @mock.patch('monasca_events_api.v2.common.helpers.get_tenant_id')
    @mock.patch('monasca_events_api.v2.common.helpers.validate_authorization')
    def test_on_delete_pass(self, validate, tenantid, mysql, deleteStream):
        """DELETE method successful """
        validate.return_value = True
        tenantid.return_value = '0ab1ac0a-2867-402d'

        deleteStream.return_value = True
        stream_id = "1"

        streamsObj = StreamDefinitionsSubClass()
        streamsObj._stream_definitions_repo = StreamsRepository()
        res = mock.MagicMock()
        res.body = {}
        res.status = 0
        streamsObj.on_delete(self._generate_req(), res, stream_id)
        self.assertEqual("204 No Content", res.status)
