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

import collections
import re

import falcon
from oslo_config import cfg
from oslo_log import log
import simport

from monasca_events_api.api import events_api_v2
from monasca_events_api.common.messaging import exceptions \
    as message_queue_exceptions
from monasca_events_api.common.messaging.message_formats import events \
    as message_format_events
from monasca_events_api.v2.common import helpers
from monasca_events_api.v2.common import resource
from monasca_events_api.v2.common.schemas import (
    events_request_body_schema as schemas_event)
from monasca_events_api.v2.common.schemas import (
    exceptions as schemas_exceptions)


LOG = log.getLogger(__name__)


class Events(events_api_v2.EventsV2API):

    def __init__(self):
        self._region = cfg.CONF.region
        self._default_authorized_roles = (
            cfg.CONF.security.default_authorized_roles)
        self._delegate_authorized_roles = (
            cfg.CONF.security.delegate_authorized_roles)
        self._post_events_authorized_roles = (
            cfg.CONF.security.default_authorized_roles +
            cfg.CONF.security.agent_authorized_roles)
        self._message_queue = (
            simport.load(cfg.CONF.messaging.driver)("raw-events"))
        self._events_repo = (
            simport.load(cfg.CONF.repositories.events)())

    def on_get(self, req, res, event_id=None):
        helpers.validate_authorization(req, self._default_authorized_roles)
        tenant_id = helpers.get_tenant_id(req)

        if event_id:
            helpers.validate_authorization(req, self._default_authorized_roles)
            tenant_id = helpers.get_tenant_id(req)
            result = self._list_event(tenant_id, event_id)
            helpers.add_links_to_resource(
                result[0], re.sub('/' + event_id, '', req.uri))
            res.body = helpers.dumpit_utf8(result)
            res.status = falcon.HTTP_200
        else:
            offset = helpers.normalize_offset(helpers.get_query_param(
                req,
                'offset'))
            limit = helpers.get_query_param(req, 'limit')

            result = self._list_events(tenant_id, req.uri, offset, limit)
            res.body = helpers.dumpit_utf8(result)
            res.status = falcon.HTTP_200

    def on_post(self, req, res):
        helpers.validate_authorization(req, self._post_events_authorized_roles)
        helpers.validate_json_content_type(req)
        event = helpers.read_http_resource(req)
        self._validate_event(event)
        tenant_id = helpers.get_tenant_id(req)
        transformed_event = message_format_events.transform(event, tenant_id,
                                                            self._region)
        self._send_event(transformed_event)
        res.status = falcon.HTTP_204

    def _validate_event(self, event):
        """Validates the event

        :param event: An event object.
        :raises falcon.HTTPBadRequest
        """
        if '_tenant_id' in event:
            raise falcon.HTTPBadRequest(
                'Bad request', 'Reserved word _tenant_id may not be used.')
        try:
            schemas_event.validate(event)
        except schemas_exceptions.ValidationException as ex:
            LOG.debug(ex)
            raise falcon.HTTPBadRequest('Bad request', ex.message)

    def _send_event(self, events):
        """Send the event using the message queue.

        :param metrics: A series of event objects.
        :raises: falcon.HTTPServiceUnavailable
        """
        try:
            self._message_queue.send_message_batch(events)
        except message_queue_exceptions.MessageQueueException as ex:
            LOG.exception(ex)
            raise falcon.HTTPInternalServerError('Service unavailable',
                                                 ex.message)

    @resource.resource_try_catch_block
    def _list_events(self, tenant_id, uri, offset, limit):
        rows = self._events_repo.list_events(tenant_id, offset, limit)
        return helpers.paginate(self._build_events(rows), uri)

    @resource.resource_try_catch_block
    def _list_event(self, tenant_id, event_id):
        rows = self._events_repo.list_event(tenant_id, event_id)
        return self._build_events(rows)

    def _build_events(self, rows):
        result = collections.OrderedDict()
        for row in rows:
            event_id, event_data = self._build_event_data(row)
            if '_tenant_id' not in event_data:
                if event_id['id'] in result:
                    result[event_id['id']]['data'].update(event_data)
                else:
                    result[event_id['id']] = {
                        'id': event_id['id'],
                        'description': event_id['desc'],
                        'generated': event_id['generated'],
                        'data': event_data}
        return result.values()

    def _build_event_data(self, event_row):
        event_data = {}
        name = event_row['name']

        if event_row['t_string']:
            event_data[name] = event_row['t_string']
        if event_row['t_int']:
            event_data[name] = event_row['t_int']
        if event_row['t_float']:
            event_data[name] = event_row['t_float']
        if event_row['t_datetime']:
            event_data[name] = float(event_row['t_datetime'])

        event_id = {'id': event_row['message_id'],
                    'desc': event_row['desc'],
                    'generated': float(event_row['generated'])}

        return event_id, event_data
