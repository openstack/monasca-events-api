# Copyright 2014 Hewlett-Packard
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

import json

from oslo_utils import timeutils


def transform(events, tenant_id, region):
    event_template = {'event': {},
                      '_tenant_id': tenant_id,
                      'meta': {'tenantId': tenant_id, 'region': region},
                      'creation_time': timeutils.utcnow_ts()}

    if isinstance(events, list):
        transformed_events = []
        for event in events:
            event_template['event'] = event
            transformed_events.append(json.dumps(event_template))
        return transformed_events
    else:
        transformed_event = event_template['event']
        transformed_event['event'] = events
        return [json.dumps(transformed_event)]
