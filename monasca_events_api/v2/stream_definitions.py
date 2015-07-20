# Copyright 2015 Hewlett-Packard
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

import json
import re

import falcon
from oslo_config import cfg
from oslo_log import log

import simport

from monasca_events_api.api import stream_definitions_api_v2
from monasca_events_api.common.messaging import exceptions \
    as message_queue_exceptions
from monasca_events_api.common.repositories import exceptions
from monasca_events_api.v2.common import helpers
from monasca_events_api.v2.common import resource
from monasca_events_api.v2.common.schemas import \
    (stream_definition_request_body_schema as schema_streams)
from monasca_events_api.v2.common.schemas import exceptions \
    as schemas_exceptions


LOG = log.getLogger(__name__)


class StreamDefinitions(stream_definitions_api_v2.StreamDefinitionsV2API):

    def __init__(self):

        try:
            self._region = cfg.CONF.region

            self._default_authorized_roles = (
                cfg.CONF.security.default_authorized_roles)
            self._delegate_authorized_roles = (
                cfg.CONF.security.delegate_authorized_roles)
            self._post_authorized_roles = (
                cfg.CONF.security.default_authorized_roles +
                cfg.CONF.security.agent_authorized_roles)

            self._stream_definitions_repo = (
                simport.load(cfg.CONF.repositories.streams)())
            self.stream_definition_event_message_queue = (
                simport.load(cfg.CONF.messaging.driver)('stream-definitions'))

        except Exception as ex:
            LOG.exception(ex)
            raise exceptions.RepositoryException(ex)

    def on_post(self, req, res):
        helpers.validate_authorization(req, self._default_authorized_roles)

        stream_definition = helpers.read_json_msg_body(req)

        self._validate_stream_definition(stream_definition)

        tenant_id = helpers.get_tenant_id(req)
        name = get_query_stream_definition_name(stream_definition)
        description = get_query_stream_definition_description(
            stream_definition)
        select = stream_definition['select']
        for s in select:
            if 'traits' in s:
                s['traits']['_tenant_id'] = tenant_id
            else:
                s['traits'] = {'_tenant_id': tenant_id}

        group_by = stream_definition['group_by']
        fire_criteria = stream_definition['fire_criteria']
        expiration = stream_definition['expiration']
        fire_actions = get_query_stream_definition_fire_actions(
            stream_definition)
        expire_actions = get_query_stream_definition_expire_actions(
            stream_definition)

        result = self._stream_definition_create(tenant_id, name, description,
                                                select, group_by,
                                                fire_criteria, expiration,
                                                fire_actions, expire_actions)

        helpers.add_links_to_resource(result, req.uri)
        res.body = helpers.dumpit_utf8(result)
        res.status = falcon.HTTP_201

    def on_get(self, req, res, stream_id=None):
        if stream_id:
            helpers.validate_authorization(req, self._default_authorized_roles)
            tenant_id = helpers.get_tenant_id(req)

            result = self._stream_definition_show(tenant_id, stream_id)

            helpers.add_links_to_resource(
                result, re.sub('/' + stream_id, '', req.uri))
            res.body = helpers.dumpit_utf8(result)
            res.status = falcon.HTTP_200
        else:
            helpers.validate_authorization(req, self._default_authorized_roles)
            tenant_id = helpers.get_tenant_id(req)
            name = helpers.get_query_name(req)
            offset = helpers.normalize_offset(
                helpers.get_query_param(req, 'offset'))
            limit = helpers.get_query_param(req, 'limit')
            result = self._stream_definition_list(tenant_id, name,
                                                  req.uri, offset, limit)

            res.body = helpers.dumpit_utf8(result)
            res.status = falcon.HTTP_200

    def on_delete(self, req, res, stream_id):
        helpers.validate_authorization(req, self._default_authorized_roles)
        tenant_id = helpers.get_tenant_id(req)
        self._stream_definition_delete(tenant_id, stream_id)
        res.status = falcon.HTTP_204

    @resource.resource_try_catch_block
    def _stream_definition_delete(self, tenant_id, stream_id):

        stream_definition_row = (
            self._stream_definitions_repo.get_stream_definition(tenant_id,
                                                                stream_id))

        if not self._stream_definitions_repo.delete_stream_definition(
                tenant_id, stream_id):
            raise falcon.HTTPNotFound

        self._send_stream_definition_deleted_event(
            stream_id, tenant_id, stream_definition_row['name'])

    def _check_invalid_trait(self, stream_definition):
        select = stream_definition['select']
        for s in select:
            if 'traits' in s and '_tenant_id' in s['traits']:
                raise falcon.HTTPBadRequest(
                    'Bad request',
                    '_tenant_id is a reserved word and invalid trait.')

    def _validate_stream_definition(self, stream_definition):

        try:
            schema_streams.validate(stream_definition)
        except schemas_exceptions.ValidationException as ex:
            LOG.debug(ex)
            raise falcon.HTTPBadRequest('Bad request', ex.message)
        self._check_invalid_trait(stream_definition)

    @resource.resource_try_catch_block
    def _stream_definition_create(self, tenant_id, name,
                                  description, select, group_by,
                                  fire_criteria, expiration,
                                  fire_actions, expire_actions):

        stream_definition_id = (
            self._stream_definitions_repo.
            create_stream_definition(tenant_id,
                                     name,
                                     description,
                                     json.dumps(select),
                                     json.dumps(group_by),
                                     json.dumps(fire_criteria),
                                     expiration,
                                     fire_actions,
                                     expire_actions))

        self._send_stream_definition_created_event(tenant_id,
                                                   stream_definition_id,
                                                   name,
                                                   select,
                                                   group_by,
                                                   fire_criteria,
                                                   expiration)
        result = (
            {u'name': name,
             u'id': stream_definition_id,
             u'description': description,
             u'select': select,
             u'group_by': group_by,
             u'fire_criteria': fire_criteria,
             u'expiration': expiration,
             u'fire_actions': fire_actions,
             u'expire_actions': expire_actions,
             u'actions_enabled': u'true'}
        )

        return result

    def send_event(self, message_queue, event_msg):
        try:
            message_queue.send_message(
                helpers.dumpit_utf8(event_msg))
        except message_queue_exceptions.MessageQueueException as ex:
            LOG.exception(ex)
            raise falcon.HTTPInternalServerError(
                'Message queue service unavailable'.encode('utf8'),
                ex.message.encode('utf8'))

    @resource.resource_try_catch_block
    def _stream_definition_show(self, tenant_id, stream_id):

        stream_definition_row = (
            self._stream_definitions_repo.get_stream_definition(tenant_id,
                                                                stream_id))

        return self._build_stream_definition_show_result(stream_definition_row)

    @resource.resource_try_catch_block
    def _stream_definition_list(self, tenant_id, name, req_uri,
                                offset, limit):

        stream_definition_rows = (
            self._stream_definitions_repo.get_stream_definitions(
                tenant_id, name, offset, limit))
        result = []
        for stream_definition_row in stream_definition_rows:
            sd = self._build_stream_definition_show_result(
                stream_definition_row)
            helpers.add_links_to_resource(sd, req_uri)
            result.append(sd)

        result = helpers.paginate(result, req_uri)

        return result

    def _build_stream_definition_show_result(self, stream_definition_row):

        fire_actions_list = get_comma_separated_str_as_list(
            stream_definition_row['fire_actions'])

        expire_actions_list = get_comma_separated_str_as_list(
            stream_definition_row['expire_actions'])

        selectlist = json.loads(stream_definition_row['select_by'])
        for s in selectlist:
            if '_tenant_id' in s['traits']:
                del s['traits']['_tenant_id']
                if not s['traits']:
                    del s['traits']

        result = (
            {u'name': stream_definition_row['name'],
             u'id': stream_definition_row['id'],
             u'description': stream_definition_row['description'],
             u'select': selectlist,
             u'group_by': json.loads(stream_definition_row['group_by']),
             u'fire_criteria': json.loads(
                 stream_definition_row['fire_criteria']),
             u'expiration': stream_definition_row['expiration'],
             u'fire_actions': fire_actions_list,
             u'expire_actions': expire_actions_list,
             u'actions_enabled': stream_definition_row['actions_enabled'] == 1,
             u'created_at': stream_definition_row['created_at'].isoformat(),
             u'updated_at': stream_definition_row['updated_at'].isoformat()}
        )

        return result

    def _send_stream_definition_deleted_event(self, stream_definition_id,
                                              tenant_id, stream_name):

        stream_definition_deleted_event_msg = {
            u"stream-definition-deleted": {u'tenant_id': tenant_id,
                                           u'stream_definition_id':
                                           stream_definition_id,
                                           u'name': stream_name}}

        self.send_event(self.stream_definition_event_message_queue,
                        stream_definition_deleted_event_msg)

    def _send_stream_definition_created_event(self, tenant_id,
                                              stream_definition_id,
                                              name,
                                              select,
                                              group_by,
                                              fire_criteria,
                                              expiration):

        stream_definition_created_event_msg = {
            u'stream-definition-created': {u'tenant_id': tenant_id,
                                           u'stream_definition_id':
                                           stream_definition_id,
                                           u'name': name,
                                           u'select': select,
                                           u'group_by': group_by,
                                           u'fire_criteria': fire_criteria,
                                           u'expiration': expiration}
        }

        self.send_event(self.stream_definition_event_message_queue,
                        stream_definition_created_event_msg)


def get_query_stream_definition_name(stream_definition):
    return (stream_definition['name'])


def get_query_stream_definition_description(stream_definition,
                                            return_none=False):
    if 'description' in stream_definition:
        return stream_definition['description']
    else:
        if return_none:
            return None
        else:
            return ''


def get_query_stream_definition_fire_actions(stream_definition,
                                             return_none=False):
    if 'fire_actions' in stream_definition:
        return stream_definition['fire_actions']
    else:
        if return_none:
            return None
        else:
            return []


def get_query_stream_definition_expire_actions(stream_definition,
                                               return_none=False):
    if 'expire_actions' in stream_definition:
        return stream_definition['expire_actions']
    else:
        if return_none:
            return None
        else:
            return []


def get_query_stream_definition_actions_enabled(stream_definition,
                                                required=False,
                                                return_none=False):
    try:
        if 'actions_enabled' in stream_definition:
            return (stream_definition['actions_enabled'])
        else:
            if return_none:
                return None
            elif required:
                raise Exception("Missing actions-enabled")
            else:
                return ''
    except Exception as ex:
        LOG.debug(ex)
        raise falcon.HTTPBadRequest('Bad request', ex.message)


def get_comma_separated_str_as_list(comma_separated_str):
    if not comma_separated_str:
        return []
    else:
        return comma_separated_str.decode('utf8').split(',')
