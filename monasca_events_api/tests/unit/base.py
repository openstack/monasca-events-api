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

import os

import falcon
from falcon import testing
import fixtures
from monasca_common.policy import policy_engine as policy
from oslo_config import cfg
from oslo_config import fixture as config_fixture
from oslo_context import fixture as oc_fixture
from oslo_log.fixture import logging_error as log_fixture
from oslo_serialization import jsonutils
from oslotest import base

from monasca_events_api.app.core import request
from monasca_events_api import config
from monasca_events_api import policies


CONF = cfg.CONF
policy.POLICIES = policies


class ConfigFixture(config_fixture.Config):

    def setUp(self):
        super(ConfigFixture, self).setUp()
        self.addCleanup(self._clean_config_loaded_flag)
        config.parse_args()

    @staticmethod
    def _clean_config_loaded_flag():
        config._CONF_LOADED = False


class BaseTestCase(base.BaseTestCase):

    def setUp(self):
        super(BaseTestCase, self).setUp()
        self.useFixture(fixtures.NestedTempfile())
        self.useFixture(fixtures.TempHomeDir())
        self.useFixture(log_fixture.get_logging_handle_error_fixture())
        self.useFixture(ConfigFixture(CONF))
        self.useFixture(oc_fixture.ClearRequestContext())
        self.useFixture(PolicyFixture())

    @staticmethod
    def conf_override(**kw):
        """Override flag variables for a test."""
        group = kw.pop('group', None)
        for k, v in kw.items():
            CONF.set_override(k, v, group)


class PolicyFixture(fixtures.Fixture):
    """Override the policy with a completely new policy file.

    This overrides the policy with a completely fake and synthetic
    policy file.

    """

    def setUp(self):
        super(PolicyFixture, self).setUp()
        self._prepare_policy()
        policy.reset()
        policy.init()
        self.addCleanup(policy.reset)

    def _prepare_policy(self):
        policy_dir = self.useFixture(fixtures.TempDir())
        policy_file = os.path.join(policy_dir.path, 'policy.yaml')

        # load the fake_policy data and add the missing default rules.
        policy_rules = jsonutils.loads('{}')
        self.add_missing_default_rules(policy_rules)
        with open(policy_file, 'w') as f:
            jsonutils.dump(policy_rules, f)

        BaseTestCase.conf_override(policy_file=policy_file,
                                   group='oslo_policy')
        BaseTestCase.conf_override(policy_dirs=[], group='oslo_policy')

    def add_missing_default_rules(self, rules):
        for rule in policies.list_rules():
            if rule.name not in rules:
                rules[rule.name] = rule.check_str


class BaseApiTestCase(BaseTestCase, testing.TestCase):

    def setUp(self):
        super(BaseApiTestCase, self).setUp()
        self.app = falcon.API(request_type=request.Request)
        # NOTE: Falcon 2.0.0 switches the default for this from
        # True to False so we explicitly set it here to prevent the behaviour
        # changing between versions.
        self.app.req_options.strip_url_path_trailing_slash = True
