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

import copy

from oslo_config import cfg
from oslo_log import log
from oslo_policy import policy

from monasca_events_api import policies

CONF = cfg.CONF
LOG = log.getLogger(__name__)

_ENFORCER = None
# oslo_policy will read the policy configuration file again when the file
# is changed in runtime so the old policy rules will be saved to
# saved_file_rules and used to compare with new rules to determine the
# rules whether were updated.
saved_file_rules = []


def reset():
    """Reset Enforcer class."""
    global _ENFORCER
    if _ENFORCER:
        _ENFORCER.clear()
        _ENFORCER = None


def init(policy_file=None, rules=None, default_rule=None, use_conf=True):
    """Init an Enforcer class."""
    global _ENFORCER
    global saved_file_rules

    if not _ENFORCER:
        _ENFORCER = policy.Enforcer(CONF,
                                    policy_file=policy_file,
                                    rules=rules,
                                    default_rule=default_rule,
                                    use_conf=use_conf
                                    )
        register_rules(_ENFORCER)
        _ENFORCER.load_rules()
    # Only the rules which are loaded from file may be changed
    current_file_rules = _ENFORCER.file_rules
    current_file_rules = _serialize_rules(current_file_rules)

    if saved_file_rules != current_file_rules:
        saved_file_rules = copy.deepcopy(current_file_rules)


def _serialize_rules(rules):
    """Serialize all the Rule object as string.

    New string is used to compare the rules list.
    """
    result = [(rule_name, str(rule)) for rule_name, rule in rules.items()]
    return sorted(result, key=lambda rule: rule[0])


def register_rules(enforcer):
    """Register default policy rules."""
    rules = policies.list_rules()
    enforcer.register_defaults(rules)


def authorize(context, action, target, do_raise=True):
    """Verify that the action is valid on the target in this context.

    :param context: monasca-events-api context
    :param action: String representing the action to be checked. This
                   should be colon separated for clarity.
    :param target: Dictionary representing the object of the action for
                   object creation. This should be a dictionary representing
                   the location of the object e.g.
                   ``{'project_id': 'context.project_id'}``
    :param do_raise: if True (the default), raises PolicyNotAuthorized,
                     if False returns False
    :type context: object
    :type action: str
    :type target: dict
    :type do_raise: bool
    :return: returns a non-False value (not necessarily True) if authorized,
             and the False if not authorized and do_raise if False

    :raises oslo_policy.policy.PolicyNotAuthorized: if verification fails
    """
    init()
    credentials = context.to_policy_values()

    try:
        result = _ENFORCER.authorize(action, target, credentials,
                                     do_raise=do_raise, action=action)
        return result
    except policy.PolicyNotRegistered:
        LOG.exception('Policy not registered')
        raise
    except Exception:
        LOG.debug('Policy check for %(action)s failed with credentials '
                  '%(credentials)s',
                  {'action': action, 'credentials': credentials})
        raise


def check_is_admin(context):
    """Check if roles contains 'admin' role according to policy settings."""
    init()
    credentials = context.to_policy_values()
    target = credentials
    return _ENFORCER.authorize('admin_required', target, credentials)


def set_rules(rules, overwrite=True, use_conf=False):  # pragma: no cover
    """Set rules based on the provided dict of rules.

    Note:
        Used in tests only.

    :param rules: New rules to use. It should be an instance of dict
    :param overwrite: Whether to overwrite current rules or update them
                      with the new rules.
    :param use_conf: Whether to reload rules from config file.
    """
    init(use_conf=False)
    _ENFORCER.set_rules(rules, overwrite, use_conf)


def get_rules():  # pragma: no cover
    """Get policy rules.

    Note:
        Used in tests only.

    """
    if _ENFORCER:
        return _ENFORCER.rules
