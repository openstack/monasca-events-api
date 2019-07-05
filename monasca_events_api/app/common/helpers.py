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

from monasca_common.rest import exceptions


LOG = log.getLogger(__name__)


def read_json_msg_body(req):
    """Read the json_msg from the http request body and return as JSON.

    :param req: HTTP request object.
    :return: Returns the metrics as a JSON object.
    :raises falcon.HTTPBadRequest:
    """
    try:
        return req.media
    except exceptions.DataConversionException as ex:
        LOG.debug(ex)
        raise falcon.HTTPBadRequest('Bad request',
                                    'Request body is not valid JSON')
    except ValueError as ex:
        LOG.debug(ex)
        raise falcon.HTTPBadRequest('Bad request',
                                    'Request body is not valid JSON')
