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
from oslo_log import log
from oslo_middleware import base

from monasca_events_api import config

CONF = config.CONF
LOG = log.getLogger(__name__)

SUPPORTED_CONTENT_TYPES = ('application/json',)


def _validate_content_type(req):
    """Validate content type.

    Function validates request against correct content type.

    If Content-Type cannot be established (i.e. header is missing),
    :py:class:`falcon.HTTPMissingHeader` is thrown.
    If Content-Type is not **application/json**(supported contents

    types are define in SUPPORTED_CONTENT_TYPES variable),
    :py:class:`falcon.HTTPUnsupportedMediaType` is thrown.

    :param falcon.Request req: current request

    :exception: :py:class:`falcon.HTTPMissingHeader`
    :exception: :py:class:`falcon.HTTPUnsupportedMediaType`
    """
    content_type = req.content_type
    LOG.debug('Content-type is {0}'.format(content_type))

    if content_type is None or len(content_type) == 0:
        raise falcon.HTTPMissingHeader('Content-Type')

    if content_type not in SUPPORTED_CONTENT_TYPES:
        types = ','.join(SUPPORTED_CONTENT_TYPES)
        details = ('Only [{0}] are accepted as events representation'.
                   format(types))
        raise falcon.HTTPUnsupportedMediaType(description=details)


class ValidationMiddleware(base.ConfigurableMiddleware):
    """Middleware that validates request content.

    """

    @staticmethod
    def process_request(req):

        _validate_content_type(req)

        return
