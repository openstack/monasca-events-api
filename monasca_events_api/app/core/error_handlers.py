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

from monasca_events_api.app.model import envelope


def events_envelope_exception_handlet(ex, req, resp, params):
    raise falcon.HTTPUnprocessableEntity(
        title='Failed to create Envelope',
        description=ex.message
    )


def register_error_handler(app):
    app.add_error_handler(envelope.EventEnvelopeException,
                          events_envelope_exception_handlet)
