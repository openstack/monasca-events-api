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

from oslo_context import context

from monasca_events_api import policy


class Request(falcon.Request):
    """Variation of falcon. Request with context.

    Following class enhances :py:class:`falcon.Request` with
    :py:class:`context.RequestContext`
    """

    def __init__(self, env, options=None):
        """Init an Request class."""
        super(Request, self).__init__(env, options)
        self.is_admin = None
        self.context = context.RequestContext.from_environ(self.env)

        if self.is_admin is None:
            self.is_admin = policy.check_is_admin(self)

    def to_policy_values(self):
        policy = self.context.to_policy_values()
        policy['is_admin'] = self.is_admin
        return policy
