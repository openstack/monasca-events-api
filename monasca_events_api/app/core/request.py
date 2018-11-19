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
from monasca_common.policy import policy_engine as policy
from oslo_log import log

from monasca_events_api.app.core import request_contex
from monasca_events_api.app.core import validation
from monasca_events_api import policies

LOG = log.getLogger(__name__)
policy.POLICIES = policies


class Request(falcon.Request):
    """Variation of falcon. Request with context.

    Following class enhances :py:class:`falcon.Request` with
    :py:class:`context.CustomRequestContext`
    """

    def __init__(self, env, options=None):
        """Init an Request class."""
        super(Request, self).__init__(env, options)
        self.context = \
            request_contex.RequestContext.from_environ(self.env)
        self.is_admin = policy.check_is_admin(self.context)
        self.project_id = self.context.project_id

    def validate(self, content_types):
        """Performs common request validation

        Validation checklist (in that order):

        * :py:func:`validation.validate_content_type`

        :param content_types: allowed content-types handler supports
        :type content_types: list
        :raises Exception: if any of the validation fails

        """
        validation.validate_content_type(self, content_types)

    def can(self, action, target=None):
        return self.context.can(action, target)
