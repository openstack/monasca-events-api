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


def prepare_message_to_sent(body):
    """prepare_message_to_sent convert message to proper format,

    :param dict body: original request body
    :return dict: prepared message for publish to kafka
    """
    timestamp = body['timestamp']
    final_body = []
    for events in body['events']:
        ev = events['event'].copy()
        ev.update({'timestamp': timestamp})
        ev.update({'dimensions': events.get('dimensions')})
        final_body.append(ev)
    return final_body
