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
from falcon import testing

from monasca_common.policy import policy_engine as policy
from oslo_context import context
from oslo_policy import policy as os_policy

from monasca_events_api.app.core import request
from monasca_events_api.tests.unit import base


class TestPolicyFileCase(base.BaseTestCase):
    def setUp(self):
        super(TestPolicyFileCase, self).setUp()
        self.context = context.RequestContext(user='fake',
                                              tenant='fake',
                                              is_admin=False)
        self.target = {'tenant_id': 'fake'}

    def test_modified_policy_reloads(self):
        tmp_file = \
            self.create_tempfiles(files=[('policies', '{}')], ext='.yaml')[0]
        base.BaseTestCase.conf_override(policy_file=tmp_file,
                                        group='oslo_policy')

        policy.reset()
        policy.init()

        action = 'example:test'
        rule = os_policy.RuleDefault(action, '')
        policy._ENFORCER.register_defaults([rule])

        with open(tmp_file, 'w') as policy_file:
            policy_file.write('{"example:test": ""}')
        policy.authorize(self.context, action, self.target)

        with open(tmp_file, 'w') as policy_file:
            policy_file.write('{"example:test": "!"}')
        policy._ENFORCER.load_rules(True)
        self.assertRaises(os_policy.PolicyNotAuthorized, policy.authorize,
                          self.context, action, self.target)


class TestPolicyCase(base.BaseTestCase):
    def setUp(self):
        super(TestPolicyCase, self).setUp()
        rules = [
            os_policy.RuleDefault("true", "@"),
            os_policy.RuleDefault("example:allowed", "@"),
            os_policy.RuleDefault("example:denied", "!"),
            os_policy.RuleDefault("example:lowercase_admin",
                                  "role:admin or role:sysadmin"),
            os_policy.RuleDefault("example:uppercase_admin",
                                  "role:ADMIN or role:sysadmin"),
        ]
        policy.reset()
        policy.init()
        policy._ENFORCER.register_defaults(rules)

    def test_authorize_nonexist_action_throws(self):
        action = "example:noexist"
        ctx = request.Request(
            testing.create_environ(
                path="/",
                headers={
                    "X_USER_ID": "fake",
                    "X_PROJECT_ID": "fake",
                    "X_ROLES": "member"
                }
            )
        )
        self.assertRaises(os_policy.PolicyNotRegistered, policy.authorize,
                          ctx.context, action, {})

    def test_authorize_bad_action_throws(self):
        action = "example:denied"
        ctx = request.Request(
            testing.create_environ(
                path="/",
                headers={
                    "X_USER_ID": "fake",
                    "X_PROJECT_ID": "fake",
                    "X_ROLES": "member"
                }
            )
        )
        self.assertRaises(os_policy.PolicyNotAuthorized, policy.authorize,
                          ctx.context, action, {})

    def test_authorize_bad_action_no_exception(self):
        action = "example:denied"
        ctx = request.Request(
            testing.create_environ(
                path="/",
                headers={
                    "X_USER_ID": "fake",
                    "X_PROJECT_ID": "fake",
                    "X_ROLES": "member"
                }
            )
        )
        result = policy.authorize(ctx.context, action, {}, False)
        self.assertFalse(result)

    def test_authorize_good_action(self):
        action = "example:allowed"
        ctx = request.Request(
            testing.create_environ(
                path="/",
                headers={
                    "X_USER_ID": "fake",
                    "X_PROJECT_ID": "fake",
                    "X_ROLES": "member"
                }
            )
        )
        result = policy.authorize(ctx.context, action, False)
        self.assertTrue(result)

    def test_ignore_case_role_check(self):
        lowercase_action = "example:lowercase_admin"
        uppercase_action = "example:uppercase_admin"

        admin_context = request.Request(
            testing.create_environ(
                path="/",
                headers={
                    "X_USER_ID": "admin",
                    "X_PROJECT_ID": "fake",
                    "X_ROLES": "AdMiN"
                }
            )
        )
        self.assertTrue(policy.authorize(admin_context.context,
                                         lowercase_action,
                                         {}))
        self.assertTrue(policy.authorize(admin_context.context,
                                         uppercase_action,
                                         {}))
