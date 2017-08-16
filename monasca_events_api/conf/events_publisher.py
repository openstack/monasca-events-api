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

from oslo_config import cfg

_MAX_MESSAGE_SIZE = 1048576

events_publisher_opts = [
    cfg.StrOpt('kafka_url',
               required=True,
               help='Url to kafka server',
               default="127.0.0.1:9092"),
    cfg.MultiStrOpt('topics',
                    help='Consumer topics',
                    default=['monevents'],)
]

events_publisher_group = cfg.OptGroup(name='events_publisher',
                                      title='events_publisher')


def register_opts(conf):
    conf.register_group(events_publisher_group)
    conf.register_opts(events_publisher_opts, events_publisher_group)


def list_opts():
    return events_publisher_group, events_publisher_opts
