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

import iso8601

from oslo_log import log
import voluptuous

from monasca_events_api.v2.common.schemas import exceptions

LOG = log.getLogger(__name__)


def DateValidator():
    return lambda v: iso8601.parse_date(v)

event_schema = {
    voluptuous.Required('event_type'): voluptuous.All(
        voluptuous.Any(str, unicode),
        voluptuous.Length(max=255)),
    voluptuous.Required('message_id'): voluptuous.All(
        voluptuous.Any(str, unicode),
        voluptuous.Length(max=50)),
    voluptuous.Required('timestamp'): DateValidator()}

event_schema = voluptuous.Schema(event_schema,
                                 required=True, extra=True)

request_body_schema = voluptuous.Schema(
    voluptuous.Any(event_schema, [event_schema]))


def validate(body):
    try:
        request_body_schema(body)
    except Exception as ex:
        LOG.debug(ex)
        raise exceptions.ValidationException(str(ex))
