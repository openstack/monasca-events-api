# Copyright 2015 kornicameister@gmail.com
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

import falcon
from monasca_common.kafka import producer
from monasca_common.kafka_lib.common import FailedPayloadsError
from monasca_common.rest import utils as rest_utils
from oslo_log import log

from monasca_events_api import conf


LOG = log.getLogger(__name__)
CONF = conf.CONF

_RETRY_AFTER = 60
_KAFKA_META_DATA_SIZE = 32
_TRUNCATION_SAFE_OFFSET = 1


class InvalidMessageException(Exception):
    pass


class EventPublisher(object):
    """Publishes events data to Kafka

    EventPublisher is able to send single message to multiple configured topic.
    It uses following configuration written in conf file ::

        [event_publisher]
        topics = 'monevents'
        kafka_url = 'localhost:8900'

    Note:
        Uses :py:class:`monasca_common.kafka.producer.KafkaProducer`
        to ship events to kafka. For more details
        see `monasca-common`_ github repository.

    .. _monasca-common: https://github.com/openstack/monasca-common

    """

    def __init__(self):

        self._topics = CONF.events_publisher.topics

        self._kafka_publisher = producer.KafkaProducer(
            url=CONF.events_publisher.kafka_url
        )

        LOG.info('Initializing EventPublisher <%s>', self)

    def send_message(self, messages):
        """Sends message to each configured topic.

        Note:
            Empty content is not shipped to kafka

        :param dict| list messages:
        """
        if not messages:
            return
        if not isinstance(messages, list):
            messages = [messages]

        sent_counter = 0
        num_of_msgs = len(messages)

        LOG.debug('About to publish %d messages to %s topics',
                  num_of_msgs, self._topics)

        send_messages = []

        for message in messages:
            try:
                msg = self._transform_message_to_json(message)
                send_messages.append(msg)
            except Exception as ex:
                LOG.exception(
                    'Failed to transform message, '
                    'this massage is dropped {} '
                    'Exception: {}'.format(message, str(ex)))
        try:
            self._publish(send_messages)
            sent_counter = len(send_messages)
        except Exception as ex:
            LOG.exception('Failure in publishing messages to kafka')
            raise ex
        finally:
            self._check_if_all_messages_was_publish(sent_counter, num_of_msgs)

    def _transform_message_to_json(self, message):
        """Transforms message into JSON.

        Method transforms message to JSON and
        encode to utf8
        :param str message: instance of message
        :return: serialized message
        :rtype: str
        """
        msg_json = rest_utils.as_json(message)
        return msg_json.encode('utf-8')

    def _create_message_for_persister_from_request_body(self, body):
        """Create message for persister from request body

        Method take original request body and them
        transform the request to proper message format
        acceptable by event-prsister
        :param body: original request body
        :return: transformed message
        """
        timestamp = body['timestamp']
        final_body = []
        for events in body['events']:
            ev = events['event'].copy()
            ev.update({'timestamp': timestamp})
            final_body.append(ev)
        return final_body

    def _ensure_type_bytes(self, message):
        """Ensures that message will have proper type.

        :param str message: instance of message

        """

        return message.encode('utf-8')

    def _publish(self, messages):
        """Publishes messages to kafka.

        :param list messages: list of messages

        """
        num_of_msg = len(messages)

        LOG.debug('Publishing %d messages', num_of_msg)

        first = True
        while True:
            try:
                for topic in self._topics:
                    self._kafka_publisher.publish(
                        topic,
                        messages
                    )
                    LOG.debug('Sent %d messages to topic %s',
                              num_of_msg, topic)
                break
            except FailedPayloadsError as ex:
                # FailedPayloadsError exception can be cause by connection
                # problem, to make sure that is not connection issue
                # message is sent again.
                LOG.error('Failed to send messages %s', ex)
                if first:
                    LOG.error('Retrying')
                    first = False
                    continue
                else:
                    raise falcon.HTTPServiceUnavailable('Service unavailable',
                                                        str(ex), 60)
            except Exception as ex:
                LOG.error('Failed to send messages %s', ex)
                raise falcon.HTTPServiceUnavailable('Service unavailable',
                                                    str(ex), 60)

    def _check_if_all_messages_was_publish(self, send_count, to_send_count):
        """Executed after publishing to sent metrics.

        :param int send_count: how many messages have been sent
        :param int to_send_count: how many messages should be sent

        """

        failed_to_send = to_send_count - send_count

        if failed_to_send == 0:
            LOG.debug('Successfully published all [%d] messages',
                      send_count)
        else:
            error_str = ('Failed to send all messages, %d '
                         'messages out of %d have not been published')
            LOG.error(error_str, failed_to_send, to_send_count)
