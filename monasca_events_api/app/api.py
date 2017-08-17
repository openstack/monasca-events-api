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

"""Module initializes various applications of monasca-events-api."""


import falcon
from oslo_config import cfg
from oslo_log import log


LOG = log.getLogger(__name__)
CONF = cfg.CONF

_CONF_LOADED = False


class Versions(object):
    """Versions API.

    Versions returns information about API itself.

    """

    def __init__(self):
        """Init the Version App."""
        LOG.info('Initializing VersionsAPI!')

    def on_get(self, req, res):
        """On get method."""
        res.status = falcon.HTTP_200
        res.body = '{"version": "v1.0"}'


def create_version_app(global_conf, **local_conf):
    """Create Version application."""
    ctrl = Versions()
    controllers = {
        '/': ctrl,   # redirect http://host:port/ down to Version app
                     # avoid conflicts with actual pipelines and 404 error
        '/version': ctrl,  # list all the versions
    }

    wsgi_app = falcon.API()
    for route, ctrl in controllers.items():
        wsgi_app.add_route(route, ctrl)
    return wsgi_app
