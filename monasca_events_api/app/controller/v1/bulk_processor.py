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

from oslo_log import log

from monasca_events_api.app.common import events_publisher
from monasca_events_api import conf

LOG = log.getLogger(__name__)
CONF = conf.CONF


class EventsBulkProcessor(events_publisher.EventPublisher):
    """BulkProcessor for effective events processing and publishing.

    BulkProcessor is customized version of
    :py:class:`monasca_events_api.app.base.event_publisher.EventPublisher`
    that utilizes processing of bulk request inside single loop.

    """

    def send_message(self, events):
        """Sends bulk package to kafka

        :param list events: received events

        """

        num_of_msgs = len(events) if events else 0
        to_send_msgs = []

        LOG.debug('Bulk package <events=%d>',
                  num_of_msgs)

        for ev_el in events:
            try:
                t_el = self._transform_message_to_json(ev_el)
                if t_el:
                    to_send_msgs.append(t_el)
            except Exception as ex:
                LOG.error('Failed to transform message to json. '
                          'message: {} Exception {}'.format(ev_el, str(ex)))

        sent_count = len(to_send_msgs)
        try:
            self._publish(to_send_msgs)
        except Exception as ex:
            LOG.error('Failed to send bulk package <events=%d, dimensions=%s>',
                      num_of_msgs)
            LOG.exception(ex)
            raise ex
        finally:
            self._check_if_all_messages_was_publish(num_of_msgs, sent_count)
