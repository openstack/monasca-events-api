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

"""
Module contains factories to initializes various applications
of monasca-events-api.
"""

import falcon
from oslo_log import log
import six

from monasca_events_api.app.controller import healthchecks
from monasca_events_api.app.controller.v1 import events as v1_events
from monasca_events_api.app.controller import versions
from monasca_events_api.app.core import error_handlers
from monasca_events_api.app.core import request
from monasca_events_api import config


def error_trap(app_name):
    """Decorator trapping any error during application boot time.

    :param app_name: Application name
    :type app_name: str
    :return: _wrapper function
    """
    @six.wraps(error_trap)
    def _wrapper(func):

        @six.wraps(_wrapper)
        def _inner_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception:
                logger = log.getLogger(__name__)
                logger.exception(
                    'Failed to load application: \'{}\''.format(app_name))
                raise
        return _inner_wrapper
    return _wrapper


def singleton_config(func):
    """Decorator ensuring that configuration is loaded only once.

    :param func: Function to execute
    :return: _wrapper
    """
    @six.wraps(singleton_config)
    def _wrapper(global_conf, **local_conf):
        config.parse_args()
        return func(global_conf, **local_conf)
    return _wrapper


@error_trap('version')
def create_version_app(global_conf, **local_conf):
    """Creates Version application"""

    ctrl = versions.Versions()
    controllers = {
        '/': ctrl,   # redirect http://host:port/ down to Version app
                     # avoid conflicts with actual pipelines and 404 error
        '/version': ctrl,  # list all the versions
        '/version/{version_id}': ctrl  # display details of the version
    }

    wsgi_app = falcon.API()
    for route, ctrl in controllers.items():
        wsgi_app.add_route(route, ctrl)
    return wsgi_app


@error_trap('healthcheck')
def create_healthcheck_app(global_conf, **local_conf):
    """Create Healthcheck application"""

    controllers = {
        '/': healthchecks.HealthChecks(),
    }

    wsgi_app = falcon.API()
    for route, ctrl in controllers.items():
        wsgi_app.add_route(route, ctrl)
    return wsgi_app


@error_trap('api')
@singleton_config
def create_api_app(global_conf, **local_conf):
    """Create Main Events Api application.

    :param global_conf: Global config
    :param local_conf: Local config
    :return: falcon.API
    """
    controllers = {}
    controllers.update({
        '/events': v1_events.Events()
    })

    wsgi_app = falcon.API(
        request_type=request.Request
    )

    for route, ctrl in controllers.items():
        wsgi_app.add_route(route, ctrl)

    error_handlers.register_error_handler(wsgi_app)

    return wsgi_app
