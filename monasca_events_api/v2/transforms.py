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

import re
import datetime
import json
from time import mktime
import yaml

import falcon
from oslo_config import cfg
from oslo_log import log
from oslo_utils import uuidutils

import simport

from monasca_events_api.api import transforms_api_v2
from monasca_events_api.common.messaging import exceptions as message_queue_exceptions
from monasca_events_api.common.messaging.message_formats import (
    transforms as message_formats_transforms)
from monasca_events_api.common.repositories import exceptions as repository_exceptions
from monasca_events_api.v2.common import helpers
from monasca_events_api.v2.common.schemas import (exceptions as schemas_exceptions)
from monasca_events_api.v2.common.schemas import (
    transforms_request_body_schema as schemas_transforms)


LOG = log.getLogger(__name__)


class MyEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return int(mktime(obj.timetuple()))

        return json.JSONEncoder.default(self, obj)


class Transforms(transforms_api_v2.TransformsV2API):
    def __init__(self):
        self._region = cfg.CONF.region
        self._default_authorized_roles = (
            cfg.CONF.security.default_authorized_roles)
        self._message_queue = (
            simport.load(cfg.CONF.messaging.driver)("transform-definitions"))
        self._transforms_repo = (
            simport.load(cfg.CONF.repositories.transforms)())

    def on_post(self, req, res):
        helpers.validate_json_content_type(req)
        helpers.validate_authorization(req, self._default_authorized_roles)
        transform = helpers.read_http_resource(req)
        self._validate_transform(transform)
        transform_id = uuidutils.generate_uuid()
        tenant_id = helpers.get_tenant_id(req)
        self._create_transform(transform_id, tenant_id, transform)
        transformed_event = message_formats_transforms.transform(
            transform_id, tenant_id, transform)
        self._send_event(transformed_event)
        res.body = self._create_transform_response(transform_id, transform)
        res.status = falcon.HTTP_200

    def on_get(self, req, res, transform_id=None):
        if transform_id:
            helpers.validate_authorization(req, self._default_authorized_roles)
            tenant_id = helpers.get_tenant_id(req)
            result = self._list_transform(tenant_id, transform_id, req.uri)
            helpers.add_links_to_resource(
                result, re.sub('/' + transform_id, '', req.uri))
            res.body = json.dumps(result, cls=MyEncoder)
            res.status = falcon.HTTP_200
        else:
            helpers.validate_authorization(req, self._default_authorized_roles)
            tenant_id = helpers.get_tenant_id(req)
            limit = helpers.get_query_param(req, 'limit')
            offset = helpers.normalize_offset(helpers.get_query_param(
                req,
                'offset'))
            result = self._list_transforms(tenant_id, limit, offset, req.uri)
            res.body = json.dumps(result, cls=MyEncoder)
            res.status = falcon.HTTP_200

    def on_delete(self, req, res, transform_id):
        helpers.validate_authorization(req, self._default_authorized_roles)
        tenant_id = helpers.get_tenant_id(req)
        self._delete_transform(tenant_id, transform_id)
        transformed_event = message_formats_transforms.transform(transform_id,
                                                                 tenant_id,
                                                                 [])
        self._send_event(transformed_event)
        res.status = falcon.HTTP_204

    def _send_event(self, event):
        """Send the event using the message queue.

        :param metrics: An event object.
        :raises: falcon.HTTPServiceUnavailable
        """
        try:
            str_msg = json.dumps(event, cls=MyEncoder,
                                 ensure_ascii=False).encode('utf8')
            self._message_queue.send_message(str_msg)
        except message_queue_exceptions.MessageQueueException as ex:
            LOG.exception(ex)
            raise falcon.HTTPInternalServerError('Service unavailable',
                                                 ex.message)

    def _validate_transform(self, transform):
        """Validates the transform

        :param transform: An event object.
        :raises falcon.HTTPBadRequest
        """
        try:
            schemas_transforms.validate(transform)
        except schemas_exceptions.ValidationException as ex:
            LOG.debug(ex)
            raise falcon.HTTPBadRequest('Bad request', ex.message)

    def _create_transform(self, transform_id, tenant_id, transform):
        """Store the transform using the repository.

        :param transform: A transform object.
        :raises: falcon.HTTPServiceUnavailable
        """
        try:
            name = transform['name']
            description = transform['description']
            specification = str(yaml.load(transform['specification']))
            if 'enabled' in transform:
                enabled = transform['enabled']
            else:
                enabled = False
            self._transforms_repo.create_transforms(transform_id, tenant_id,
                                                    name, description,
                                                    specification, enabled)
        except repository_exceptions.RepositoryException as ex:
            LOG.error(ex)
            raise falcon.HTTPInternalServerError('Service unavailable',
                                                 ex.message)

    def _create_transform_response(self, transform_id, transform):
        name = transform['name']
        description = transform['description']
        specification = transform['specification']
        if 'enabled' in transform:
            enabled = transform['enabled']
        else:
            enabled = False
        response = {'id': transform_id, 'name': name, 'description': description,
                    'specification': specification, 'enabled': enabled}
        return json.dumps(response)

    def _list_transforms(self, tenant_id, limit, offset, uri):
        try:
            transforms = self._transforms_repo.list_transforms(tenant_id,
                                                               limit, offset)
            transforms = helpers.paginate(transforms, uri)
            return transforms
        except repository_exceptions.RepositoryException as ex:
            LOG.error(ex)
            raise falcon.HTTPInternalServerError('Service unavailable',
                                                 ex.message)

    def _list_transform(self, tenant_id, transform_id, uri):
        try:
            transform = self._transforms_repo.list_transform(tenant_id,
                                                             transform_id)[0]
            transform['specification'] = yaml.safe_dump(
                transform['specification'])
            return transform
        except repository_exceptions.RepositoryException as ex:
            LOG.error(ex)
            raise falcon.HTTPInternalServerError('Service unavailable',
                                                 ex.message)

    def _delete_transform(self, tenant_id, transform_id):
        try:
            self._transforms_repo.delete_transform(tenant_id, transform_id)
        except repository_exceptions.DoesNotExistException:
            raise falcon.HTTPNotFound()
        except repository_exceptions.RepositoryException as ex:
            LOG.error(ex)
            raise falcon.HTTPInternalServerError('Service unavailable',
                                                 ex.message)
