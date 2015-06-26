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
from monasca_events_api.common.messaging import exceptions
from monasca_events_api.common.repositories.mysql.events_repository import EventsRepository
from monasca_events_api.v2.events import Events

import mock
from monasca_events_api.common.repositories.exceptions import RepositoryException

from oslo_utils import timeutils

import unittest


class EventsSubClass(Events):

    def __init__(self):
        self._default_authorized_roles = ['user', 'domainuser',
                                          'domainadmin', 'monasca-user']
        self._post_events_authorized_roles = [
            'user',
            'domainuser',
            'domainadmin',
            'monasca-user',
            'monasca-agent']
        self._events_repo = None
        self._message_queue = None
        self._region = 'useast'

    def _event_transform(self, event, tenant_id, _region):
        return dict(
            event=1,
            meta=dict(
                tenantId='0ab1ac0a-2867-402d',
                region='useast'),
            creation_time=timeutils.utcnow_ts())


class Test_Events(unittest.TestCase):

    def _generate_req(self):
        """Generate a mock HTTP request"""
        req = mock.MagicMock()
        req.get_param.return_value = None

        req.headers = {
            'X-Auth-User': 'mini-mon',
            'X-Auth-Token': "ABCD",
            'X-Auth-Key': 'password',
            'X-TENANT-ID': '0ab1ac0a-2867-402d',
            'X-ROLES': 'user, domainuser, domainadmin, monasca-user, monasca-agent',
            'Accept': 'application/json',
            'User-Agent': 'python-monascaclient',
            'Content-Type': 'application/json'}

        req.body = {}
        req.content_type = 'application/json'
        return req

    @mock.patch('monasca_events_api.v2.events.Events._list_event')
    @mock.patch(
        'monasca_events_api.common.repositories.mysql.mysql_repository.mdb')
    @mock.patch('monasca_events_api.v2.common.helpers.validate_authorization')
    @mock.patch('monasca_events_api.v2.common.helpers.get_tenant_id')
    def test_on_get_pass_singleevent(
            self,
            helper_tenant_id,
            helpers_validate,
            mysqlRepo,
            listev):
        """GET Method success Single Event"""
        helpers_validate.validate_authorization.return_value = True
        returnEvent = [{"region": "useast", "tenantId": "0ab1ac0a-2867-402d",
                        "creation_time": "1434331190", "event": "1"}]
        listev.return_value = returnEvent

        mysqlRepo.connect.return_value = True
        helper_tenant_id.get_tenant_id.return_value = '0ab1ac0a-2867-402d'
        event_id = "1"
        eventsObj = EventsSubClass()
        eventsObj._events_repo = EventsRepository()
        res = mock.MagicMock()
        res.body = {}
        res.status = 0
        eventsObj.on_get(self._generate_req(), res, event_id)
        self.assertEqual(returnEvent, json.loads(res.body))

    @mock.patch('monasca_events_api.v2.events.Events._list_events')
    @mock.patch(
        'monasca_events_api.common.repositories.mysql.mysql_repository.mdb')
    @mock.patch('monasca_events_api.v2.common.helpers.validate_authorization')
    @mock.patch('monasca_events_api.v2.common.helpers.get_tenant_id')
    def test_on_get_pass_events(
            self,
            helper_tenant_id,
            helpers_validate,
            mysqlRepo,
            listev):
        """GET Method success Multiple Events"""
        helpers_validate.validate_authorization.return_value = True
        returnEvent = [{"region": "useast", "tenantId": "0ab1ac0a-2867-402d",
                        "creation_time": "1434331190", "event": "1"},
                       {"region": "useast", "tenantId": "0ab1ac0a-2866-403d",
                        "creation_time": "1234567890", "event": "2"}]
        listev.return_value = returnEvent

        mysqlRepo.connect.return_value = True
        helper_tenant_id.get_tenant_id.return_value = '0ab1ac0a-2867-402d'
        eventsObj = EventsSubClass()
        eventsObj._events_repo = EventsRepository()
        res = mock.MagicMock()
        res.body = {}
        res.status = 0
        eventsObj.on_get(self._generate_req(), res)
        self.assertEqual(returnEvent, json.loads(res.body))

    @mock.patch(
        'monasca_events_api.common.repositories.mysql.mysql_repository.mdb')
    @mock.patch('monasca_events_api.v2.common.helpers.validate_authorization')
    @mock.patch('monasca_events_api.v2.common.helpers.get_tenant_id')
    def test_on_get_with_eventid_dbdown(
            self,
            helper_tenant_id,
            helpers_validate,
            mysqlRepo):
        """GET method when DB Down with event_ID"""
        mysqlRepo.connect.side_effect = RepositoryException("Database\
                                                             Connection Error")
        helpers_validate.validate_authorization.return_value = True

        helper_tenant_id.get_tenant_id.return_value = '0ab1ac0a-2867-402d'
        event_id = "0ab1ac0a-2867-402d-83c7-d7087262470c"

        eventsObj = EventsSubClass()
        eventsObj._events_repo = EventsRepository()
        res = mock.MagicMock()
        res.body = {}
        res.status = 0
        try:
            eventsObj.on_get(self._generate_req(), res, event_id)
            self.assertFalse(
                1,
                msg="Database Down, GET should fail but succeeded")
        except Exception as e:
            self.assertRaises(falcon.HTTPInternalServerError)
            self.assertEqual(e.status, '500 Internal Server Error')

    @mock.patch(
        'monasca_events_api.common.repositories.mysql.mysql_repository.mdb')
    @mock.patch('monasca_events_api.v2.common.helpers.validate_authorization')
    @mock.patch('monasca_events_api.v2.common.helpers.get_tenant_id')
    def test_on_get_mysql_down(
            self,
            helper_tenant_id,
            helpers_validate,
            mysqlRepo):
        """GET METHOD without event ID DB DOWN"""
        mysqlRepo.connect.side_effect = RepositoryException("Database\
                                                             Connection Error")
        helpers_validate.return_value = True
        helper_tenant_id.return_value = '0ab1ac0a-2867-402d'
        eventsObj = EventsSubClass()
        eventsObj._events_repo = EventsRepository()
        res = mock.MagicMock(spec='status')
        res.body = {}
        try:
            eventsObj.on_get(self._generate_req(), res, None)
            self.assertFalse(
                1,
                msg="Database Down, GET should fail but succeeded")
        except Exception as e:
            self.assertRaises(falcon.HTTPInternalServerError)
            self.assertEqual(e.status, '500 Internal Server Error')

    @mock.patch(
        'monasca_events_api.common.messaging.kafka_publisher.KafkaPublisher')
    @mock.patch('monasca_events_api.v2.common.helpers.validate_authorization')
    @mock.patch('monasca_events_api.v2.events.Events._validate_event')
    @mock.patch('monasca_events_api.v2.common.helpers.read_http_resource')
    @mock.patch(
        'monasca_events_api.v2.common.helpers.validate_json_content_type')
    @mock.patch('monasca_events_api.v2.common.helpers.get_tenant_id')
    def test_on_post_unauthorized(
            self,
            tenantid,
            json,
            http,
            event,
            validate,
            kafka):
        """POST method unauthorized  """
        json.return_value = None
        validate.side_effect = falcon.HTTPUnauthorized('Forbidden',
                                                       'Tenant ID is missing a'
                                                       'required role to '
                                                       'access this service')
        http.return_value = self._generate_req()
        tenantid.return_value = '0ab1ac0a-2867-402d'
        event.return_value = True

        eventsObj = EventsSubClass()
        eventsObj._message_queue = kafka
        res = mock.MagicMock()
        res.body = {}
        res.status = 0
        try:
            eventsObj.on_post(self._generate_req(), res)
            self.assertFalse(
                1,
                msg="Unauthorized Access, should fail but passed")
        except Exception as e:
            self.assertRaises(falcon.HTTPUnauthorized)
            self.assertEqual(e.status, '401 Unauthorized')

    @mock.patch(
        'monasca_events_api.common.messaging.kafka_publisher.KafkaPublisher')
    @mock.patch('monasca_events_api.v2.common.helpers.validate_authorization')
    @mock.patch('monasca_events_api.v2.events.Events._validate_event')
    @mock.patch('monasca_events_api.v2.common.helpers.read_http_resource')
    @mock.patch(
        'monasca_events_api.v2.common.helpers.validate_json_content_type')
    @mock.patch('monasca_events_api.v2.common.helpers.get_tenant_id')
    def test_on_post_bad_request(
            self,
            tenantid,
            json,
            readHttpRes,
            event,
            validate,
            kafka):
        """POST method with bad request body"""
        json.return_value = None
        validate.return_value = True
        readHttpRes.side_effect = falcon.HTTPBadRequest('Bad request',
                                                        'Request body is'
                                                        'not valid JSON')
        tenantid.return_value = '0ab1ac0a-2867-402d'
        event.return_value = True

        eventsObj = EventsSubClass()
        eventsObj._message_queue = kafka
        res = mock.MagicMock()
        res.body = {}
        res.status = 0
        try:
            eventsObj.on_post(self._generate_req(), res)
            self.assertFalse(
                1,
                msg="Get Method should fail but succeeded, bad request sent")
        except Exception as e:
            self.assertRaises(falcon.HTTPBadRequest)
            self.assertEqual(e.status, '400 Bad Request')

    @mock.patch(
        'monasca_events_api.common.messaging.kafka_publisher.KafkaPublisher')
    @mock.patch('monasca_events_api.v2.common.helpers.validate_authorization')
    @mock.patch('monasca_events_api.v2.events.Events._validate_event')
    @mock.patch('monasca_events_api.v2.common.helpers.read_http_resource')
    @mock.patch(
        'monasca_events_api.v2.common.helpers.validate_json_content_type')
    @mock.patch('monasca_events_api.v2.common.helpers.get_tenant_id')
    def test_on_post_kafka_down(
            self,
            tenantid,
            json,
            readHttpRes,
            event,
            validate,
            kafka):
        """POST method with Kafka Down"""
        kafka.send_message_batch.side_effect = exceptions.MessageQueueException()

        json.return_value = None
        validate.return_value = True
        readHttpRes.return_value = {
            'event_type': 'compute.instance.create.start',
            'timestamp': '2015-06-17T21:57:03.493436',
            'message_id': '1f4609b5-f01d-11e4-81ac-20c9d0b84f8b'
        }

        tenantid.return_value = '0ab1ac0a-2867-402d'
        event.return_value = True

        eventsObj = EventsSubClass()
        eventsObj._message_queue = kafka
        res = mock.MagicMock()
        res.body = {}
        try:
            eventsObj.on_post(self._generate_req(), res)
            self.assertFalse(
                1,
                msg="Kakfa Server Down, Post should fail but succeeded")
        except Exception as e:
            self.assertRaises(falcon.HTTPInternalServerError)
            self.assertEqual(e.status, '500 Internal Server Error')

    @mock.patch(
        'monasca_events_api.common.messaging.kafka_publisher.KafkaPublisher')
    @mock.patch('monasca_events_api.v2.common.helpers.validate_authorization')
    @mock.patch('monasca_events_api.v2.common.helpers.read_http_resource')
    @mock.patch(
        'monasca_events_api.v2.common.helpers.validate_json_content_type')
    @mock.patch('monasca_events_api.v2.common.helpers.get_tenant_id')
    def test_on_post_pass_validate_event(self, tenantid, json, readHttpRes, validate, kafka):
        """POST method passed due to validate event """
        jsonObj = {
            'event_type': 'compute.instance.create.start',
            'timestamp': '2015-06-17T21:57:03.493436',
            'message_id': '1f4609b5-f01d-11e4-81ac-20c9d0b84f8b'
        }

        json.return_value = True
        validate.return_value = True
        readHttpRes.return_value = jsonObj
        tenantid.return_value = '0ab1ac0a-2867-402d'
        eventsObj = EventsSubClass()
        eventsObj._message_queue = kafka
        res = mock.MagicMock()
        res.body = {}
        res.status = 0
        eventsObj.on_post(self._generate_req(), res)
        self.assertEqual(falcon.HTTP_204, res.status)
        self.assertEqual({}, res.body)

    @mock.patch(
        'monasca_events_api.common.messaging.kafka_publisher.KafkaPublisher')
    @mock.patch('monasca_events_api.v2.common.helpers.validate_authorization')
    @mock.patch('monasca_events_api.v2.common.helpers.read_http_resource')
    @mock.patch(
        'monasca_events_api.v2.common.helpers.validate_json_content_type')
    @mock.patch('monasca_events_api.v2.common.helpers.get_tenant_id')
    def test_on_post_fail_on_validate_event(self, tenantid, json, readHttpRes, validate, kafka):
        """POST method failed due to validate event """
        """_tenant_id is a reserved word that cannot be used"""
        jsonObj = {
            'event_type': 'compute.instance.create.start',
            'timestamp': '2015-06-17T21:57:03.493436',
            'message_id': '1f4609b5-f01d-11e4-81ac-20c9d0b84f8b',
            '_tenant_id': '0ab1ac0a-2867-402d'
        }

        json.return_value = True
        validate.return_value = True
        readHttpRes.return_value = jsonObj
        tenantid.return_value = '0ab1ac0a-2867-402d'
        eventsObj = EventsSubClass()
        eventsObj._message_queue = kafka
        res = mock.MagicMock()
        res.body = {}
        res.status = 0
        try:
            eventsObj.on_post(self._generate_req(), res)
            self.assertFalse(
                1,
                msg="Post Method should fail but succeeded, bad request sent")
        except Exception as e:
            self.assertRaises(falcon.HTTPBadRequest)
            self.assertEqual(e.status, '400 Bad Request')
            self.assertEqual({}, res.body)
