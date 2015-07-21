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

import falcon
from oslo_config import cfg
from oslo_log import log
import paste.deploy
import simport


dispatcher_opts = [cfg.StrOpt('versions', default=None,
                              help='Versions endpoint'),
                   cfg.StrOpt('stream_definitions', default=None,
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
    log.register_options(cfg.CONF)
    log.set_defaults()
    cfg.CONF(args=[],
             project='monasca_events_api',
             default_config_files=[config_file])
    log.setup(cfg.CONF, 'monasca_events_api')

    app = falcon.API()

    versions = simport.load(cfg.CONF.dispatcher.versions)()
    app.add_route("/", versions)
    app.add_route("/{version_id}", versions)

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
    httpd = simple_server.make_server('127.0.0.1', 8082, wsgi_app)
    httpd.serve_forever()
