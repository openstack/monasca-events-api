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

from oslo_policy import policy


agent_policies = [
    policy.DocumentedRuleDefault(
        name='events_api:agent_required',
        check_str='role:monasca-user or role:admin',
        description='Send events to api',
        operations=[{'path': '/v1.0/events', 'method': 'POST'}]
    )
]


def list_rules():
    """List policies rules for agent access."""
    return agent_policies
