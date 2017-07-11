.. -*- rst -*-
..
      Copyright 2017 Fujitsu LIMITED

      Licensed under the Apache License, Version 2.0 (the "License"); you may
      not use this file except in compliance with the License. You may obtain
      a copy of the License at

          http://www.apache.org/licenses/LICENSE-2.0

      Unless required by applicable law or agreed to in writing, software
      distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
      WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
      License for the specific language governing permissions and limitations
      under the License.

======
Events
======

Accept events send from e.g. monasca-events-agent. Events are JSON objects collected from
the OpenStack message bus. Events, also called notifications, are emitted by the OpenStack Cloud core components.
Monasca-events-api accepts versioned notifications according to the `OpenStack
documentation <https://docs.openstack.org/nova/latest/notifications.html#versioned-notifications>`_.

Send Events
===========

.. rest_method:: POST /v1.0/events

Accepts multiple events (i.e. bulk mode). Each event can be enriched with a set of dimensions
with information about the notification service source (Nova, Glance, etc.), or the message bus source
(topic name). A single event in bulk mode must also contain the project_id field which is required.
Each event can be enriched with a set of dimensions. Dimensions can contain additional information,
for example, about the topic from which the event was read or the hostname from which it was
generated.

.. rest_status_code:: success http_codes.yaml

    - 204

.. rest_status_code:: error http_codes.yaml

    - 400
    - 401
    - 411
    - 413
    - 422: event_no_project
    - 422: event_no_event
    - 422: bad_envelope
    - 503

Request
-------

 .. rest_parameters:: parameters.yaml

    - events: events

**Example 1: Request with a single event**

.. literalinclude:: ../../doc/api-samples/v1/req_simple_event.json
   :language: javascript

**Example 2:Request with multiple events**

.. literalinclude:: ../../doc/api-samples/v1/req_multiple_events.json
   :language: javascript

Response
========

No body content is returned on successful POST.