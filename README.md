# Overview

`monasca-events-api` is a RESTful API server that is designed with a layered architecture [layered architecture](http://en.wikipedia.org/wiki/Multilayered_architecture).

## Keystone Configuration

For secure operation of the Monasca Events API, the API must be configured to use Keystone in the configuration file under the middleware section. Monasca only works with a Keystone v3 server. The important parts of the configuration are explained below:

* serverVIP - This is the hostname or IP Address of the Keystone server
* serverPort - The port for the Keystone server
* useHttps - Whether to use https when making requests of the Keystone API
* truststore - If useHttps is true and the Keystone server is not using a certificate signed by a public CA recognized by Java, the CA certificate can be placed in a truststore so the Monasca API will trust it, otherwise it will reject the https connection. This must be a JKS truststore
* truststorePassword - The password for the above truststore
* connSSLClientAuth - If the Keystone server requires the SSL client used by the Monasca server to have a specific client certificate, this should be true, false otherwise
* keystore - The keystore holding the SSL Client certificate if connSSLClientAuth is true
* keystorePassword - The password for the keystore
* defaultAuthorizedRoles - An array of roles that authorize a user to access the complete Monasca API. User must have at least one of these roles. See below
* agentAuthorizedRoles - An array of roles that authorize only the posting of metrics.  See Keystone Roles below
* adminAuthMethod - "password" if the Monasca API should adminUser and adminPassword to login to the Keystone server to check the user's token, "token" if the Monasca API should use adminToken
* adminUser - Admin user name
* adminPassword - Admin user password
* adminProjectId - Specify the project ID the api should use to request an admin token. Defaults to the admin user's default project. The adminProjectId option takes precedence over adminProjectName.
* adminProjectName - Specify the project name the api should use to request an admin token. Defaults to the admin user's default project. The adminProjectId option takes precedence over adminProjectName.
* adminToken - A valid admin user token if adminAuthMethod is token
* timeToCacheToken - How long the Monasca API should cache the user's token before checking it again

### Installation

To install the events api, git clone the source and run the
following commands:

    sudo python setup.py install

If it installs successfully, you will need to make changes to the following
two files to reflect your system settings, especially where kafka server is
located:

    /etc/monasca/events_api.ini
    /etc/monasca/events_api.conf

Once the configurations are modified to match your environment, you can start
up the server by following the following instructions.

To start the server, run the following command:

    Running the server in foreground mode
    gunicorn -k eventlet --worker-connections=2000 --backlog=1000 --paste /etc/monasca/events_api.ini

    Running the server as daemons
    gunicorn -k eventlet --worker-connections=2000 --backlog=1000
             --paste /etc/monasca/events_api.ini -D

To check if the code follows python coding style, run the following command
from the root directory of this project

    tox -e pep8
    
To run all the unit test cases, run the following command from the root
directory of this project

    tox -e py27   (or -e py26, -e py33)

# Monasca Events API 

Stream Definition Methods
-------------------------

## POST /v2.0/stream-definitions

### Headers
* X-Auth-Token (string, required) - Keystone auth token
* Accept (string) - application/json

### Request Body
```
{
"fire_criteria": [
                {"event_type": "compute.instance.create.start"},
                {"event_type": "compute.instance.create.end"}
                ],
            "description": "provisioning duration",
            "name": "example",
            "group_by": ["instance_id"],
            "expiration": 3000,
            "select": [{
                "traits": {"tenant_id": "406904"},
                "event_type": "compute.instance.create.*"
                }],
            "fire_actions": [action_id],
            "expire_actions": [action_id]
            }
```

### Request Example
```
POST /v2.0/stream-definitions HTTP/1.1
Host: 192.168.10.4:8082
X-Auth-Token: 2b8882ba2ec44295bf300aecb2caa4f7
Accept: application/json
Cache-Control: no-cache
```

## GET /v2.0/stream-definition
### Headers
* X-Auth-Token (string, required) - Keystone auth token
* Accept (string) - application/json

### Request Body
None.

### Request Example
```
GET /v2.0/stream-definitions HTTP/1.1
Host: 192.168.10.4:8082
X-Auth-Token: 2b8882ba2ec44295bf300aecb2caa4f7
Accept: application/json
Cache-Control: no-cache
```
### Response Body
Returns a JSON object with a 'links' array of links and an 'elements' array of stream definition objects with the following fields:

* id (string)
* name (string)
* fire_actions (string)
* description (string)
* expire_actions (string)
* created_at (datetime string)
* select
    * traits
        * tenant_id (string)
    * event_type (string)
* group_by (string)
* expiration (int)
* links - links to stream-definition
* updated_at (datetime string)
* actions_enabled (bool)
* fire_criteria - JSON list of event fire criteria

### Response Body Example

```
{
  "links": [
    {
      "rel": "self",
      "href": "http://192.168.10.4:8082/v2.0/stream-definitions"
    }
  ],
  "elements": [
    {
      "id": "242dd5f4-2ef6-11e5-8945-0800273a0b5b",
      "fire_actions": [
        "56330521-92da-4a84-8239-73d880b978fa"
      ],
      "description": "provisioning duration",
      "expire_actions": [
        "56330521-92da-4a84-8239-73d880b978fa"
      ],
      "created_at": "2015-07-20T15:44:01",
      "select": [
        {
          "traits": {
            "tenant_id": "406904"
          },
          "event_type": "compute.instance.create.*"
        }
      ],
      "group_by": [
        "instance_id"
      ],
      "expiration": 3000,
      "links": [
        {
          "rel": "self",
          "href": "http://192.168.10.4:8082/v2.0/stream-definitions/242dd5f4-2ef6-11e5-8945-0800273a0b5b"
        }
      ],
      "updated_at": "2015-07-20T15:44:01",
      "actions_enabled": true,
      "name": "1437407040.8",
      "fire_criteria": [
        {
          "event_type": "compute.instance.create.start"
        },
        {
          "event_type": "compute.instance.create.end"
        }
      ]
    }
  ]
}
```

## GET /v2.0/stream-definition/{definition_id}
### Headers
* X-Auth-Token (string, required) - Keystone auth token
* Accept (string) - application/json

### Request Body
None.

### Request Example
```
GET /v2.0/stream-definitions/242dd5f4-2ef6-11e5-8945-0800273a0b5b HTTP/1.1
Host: 192.168.10.4:8082
X-Auth-Token: 2b8882ba2ec44295bf300aecb2caa4f7
Accept: application/json
Cache-Control: no-cache
```
### Response Body
Returns a JSON object with a 'links' array of links and an 'elements' array of stream definition objects with the following fields:

* id (string)
* name (string)
* fire_actions (string)
* description (string)
* expire_actions (string)
* created_at (datetime string)
* select
    * traits
        * tenant_id (string)
    * event_type (string)
* group_by (string)
* expiration (int)
* links - links to stream-definition
* updated_at (datetime string)
* actions_enabled (bool)
* fire_criteria - JSON list of event fire criteria

### Response Body Example
```
{
  "id": "242dd5f4-2ef6-11e5-8945-0800273a0b5b",
  "fire_actions": [
    "56330521-92da-4a84-8239-73d880b978fa"
  ],
  "description": "provisioning duration",
  "expire_actions": [
    "56330521-92da-4a84-8239-73d880b978fa"
  ],
  "created_at": "2015-07-20T15:44:01",
  "select": [
    {
      "traits": {
        "tenant_id": "406904"
      },
      "event_type": "compute.instance.create.*"
    }
  ],
  "group_by": [
    "instance_id"
  ],
  "expiration": 3000,
  "links": [
    {
      "rel": "self",
      "href": "http://192.168.10.4:8082/v2.0/stream-definitions/242dd5f4-2ef6-11e5-8945-0800273a0b5b"
    }
  ],
  "updated_at": "2015-07-20T15:44:01",
  "actions_enabled": true,
  "name": "1437407040.8",
  "fire_criteria": [
    {
      "event_type": "compute.instance.create.start"
    },
    {
      "event_type": "compute.instance.create.end"
    }
  ]
}
```
## DELETE /v2.0/stream-definition/{definition_id}
### Headers
* X-Auth-Token (string, required) - Keystone auth token
* Accept (string) - application/json

### Request Body
None.

### Request Example
```
DELETE /v2.0/stream-definitions/242dd5f4-2ef6-11e5-8945-0800273a0b5b HTTP/1.1
Host: 192.168.10.4:8082
X-Auth-Token: 2b8882ba2ec44295bf300aecb2caa4f7
Accept: application/json
Cache-Control: no-cache
```
### Response Body
None.

### Response Body Example
None.

## POST /v2.0/transforms/
### Headers
* X-Auth-Token (string, required) - Keystone auth token
* Accept (string) - application/json

### Request Body
```
{
    "name": 'example',
    "description": 'an example definition',
    "specification": YAML_data
}
```

### Request Example
```
POST /v2.0/transforms/ HTTP/1.1
Host: 192.168.10.4:8082
X-Auth-Token: 2b8882ba2ec44295bf300aecb2caa4f7
Accept: application/json
Cache-Control: no-cache
```
### Response Body
None.

### Response Body Example
None.

## GET /v2.0/transforms/
### Headers
* X-Auth-Token (string, required) - Keystone auth token
* Accept (string) - application/json

### Request Body
None.

### Request Example
```
GET /v2.0/transforms/ HTTP/1.1
Host: 192.168.10.4:8082
X-Auth-Token: 2b8882ba2ec44295bf300aecb2caa4f7
Accept: application/json
Cache-Control: no-cache
```
### Response Body
Returns a JSON object with a 'links' array of links and an 'elements' array of stream definition objects with the following fields:

* id (string)
* name (string)
* description (string)
* enabled (bool)
* tenant_id (string)
* deleted_at (datetime)
* specification (string YAML data)
* created_at (datetime)
* updated_at (datetime)

### Response Body Example
```
{
  "links": [
    {
      "rel": "self",
      "href": "http://192.168.10.4:8082/v2.0/transforms"
    }
  ],
  "elements": [
    {
      "enabled": 0,
      "id": "a794f22f-a231-47a0-8618-37f12b7a6f77",
      "tenant_id": "d502aac2388b43f392c302b37a401ae5",
      "deleted_at": null,
      "specification": YAML_data,
      "created_at": 1437407042,
      "updated_at": 1437407042,
      "description": "an example definition",
      "name": "func test2"
    }
  ]
}
```

## GET /v2.0/transforms/{transform_id}
### Headers
* X-Auth-Token (string, required) - Keystone auth token
* Accept (string) - application/json

### Request Body
None.

### Request Example
```
GET /v2.0/transforms/a794f22f-a231-47a0-8618-37f12b7a6f77 HTTP/1.1
Host: 192.168.10.4:8082
X-Auth-Token: 2b8882ba2ec44295bf300aecb2caa4f7
Accept: application/json
Cache-Control: no-cache
```
### Response Body
Returns a JSON object with a 'links' array of links and an 'elements' array of stream definition objects with the following fields:

* id (string)
* name (string)
* description (string)
* enabled (bool)
* tenant_id (string)
* deleted_at (datetime)
* specification (string YAML data)
* links - links to transform definition
* created_at (datetime)
* updated_at (datetime)

### Response Body Example
```
{
  "enabled": 0,
  "id": "a794f22f-a231-47a0-8618-37f12b7a6f77",
  "tenant_id": "d502aac2388b43f392c302b37a401ae5",
  "created_at": 1437407042,
  "specification": "YAML_data",
  "links": [
    {
      "rel": "self",
      "href": "http://192.168.10.4:8082/v2.0/transforms/a794f22f-a231-47a0-8618-37f12b7a6f77"
    }
  ],
  "deleted_at": null,
  "updated_at": 1437407042,
  "description": "an example definition",
  "name": "func test2"
}
```

## DELETE /v2.0/transforms/{transform_id}
### Headers
* X-Auth-Token (string, required) - Keystone auth token
* Accept (string) - application/json

### Request Body
None.

### Request Example
```
DELETE /v2.0/transforms/a794f22f-a231-47a0-8618-37f12b7a6f77 HTTP/1.1
Host: 192.168.10.4:8082
X-Auth-Token: 2b8882ba2ec44295bf300aecb2caa4f7
Accept: application/json
Cache-Control: no-cache
```
### Response Body
None.

### Response Body Example
None.






# License

Copyright (c) 2015 Hewlett-Packard Development Company, L.P.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0
    
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
implied.
See the License for the specific language governing permissions and
limitations under the License.
