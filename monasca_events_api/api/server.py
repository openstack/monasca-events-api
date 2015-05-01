# Copyright 2015 Hewlett-Packard
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.


import os
from wsgiref import simple_server

from oslo.config import cfg
import paste.deploy

import falcon
import simport

from monasca_events_api.openstack.common import log

dispatcher_opts = [cfg.StrOpt('stream_definitions', default=None,
                              help='Stream definition endpoint'),
                   cfg.StrOpt('events', default=None,
                              help='Events endpoint'),
                   cfg.StrOpt('transforms', default=None,
                              help='Transforms endpoint')]

dispatcher_group = cfg.OptGroup(name='dispatcher', title='dispatcher')
cfg.CONF.register_group(dispatcher_group)
cfg.CONF.register_opts(dispatcher_opts, dispatcher_group)

LOG = log.getLogger(__name__)


def launch(conf, config_file="/etc/monasca/events_api.conf"):
    cfg.CONF(args=[],
             project='monasca_events_api',
             default_config_files=[config_file])
    log_levels = (cfg.CONF.default_log_levels)
    cfg.set_defaults(log.log_opts, default_log_levels=log_levels)
    log.setup('monasca_events_api')

    app = falcon.API()

    events = simport.load(cfg.CONF.dispatcher.events)()
    app.add_route("/v2.0/events", events)
    app.add_route("/v2.0/events/{event_id}", events)

    streams = simport.load(cfg.CONF.dispatcher.stream_definitions)()
    app.add_route("/v2.0/stream-definitions/", streams)
    app.add_route("/v2.0/stream-definitions/{stream_id}", streams)

    transforms = simport.load(cfg.CONF.dispatcher.transforms)()
    app.add_route("/v2.0/transforms", transforms)
    app.add_route("/v2.0/transforms/{transform_id}", transforms)

    LOG.debug('Dispatcher drivers have been added to the routes!')
    return app


if __name__ == '__main__':
    wsgi_app = (
        paste.deploy.loadapp('config:etc/events_api.ini',
                             relative_to=os.getcwd()))
    httpd = simple_server.make_server('127.0.0.1', 8080, wsgi_app)
    httpd.serve_forever()
