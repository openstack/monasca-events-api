# Copyright 2018 FUJITSU LIMITED
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

LOG = log.getLogger(__name__)


def validate_content_type(req, allowed):
    """Validates content type.

    Method validates request against correct
    content type.

    If content-type cannot be established (i.e. header is missing),
    :py:class:`falcon.HTTPMissingHeader` is thrown.
    If content-type is not **application/json** or **text/plain**,
    :py:class:`falcon.HTTPUnsupportedMediaType` is thrown.


    :param falcon.Request req: current request
    :param iterable allowed: allowed content type

    :exception: :py:class:`falcon.HTTPMissingHeader`
    :exception: :py:class:`falcon.HTTPUnsupportedMediaType`
    """
    content_type = req.content_type

    LOG.debug('Content-Type is %s', content_type)

    if content_type is None or len(content_type) == 0:
        raise falcon.HTTPMissingHeader('Content-Type')

    if content_type not in allowed:
        sup_types = ', '.join(allowed)
        details = ('Only [%s] are accepted as logs representations'
                   % str(sup_types))
        raise falcon.HTTPUnsupportedMediaType(description=details)
