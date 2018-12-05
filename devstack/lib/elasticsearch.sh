#!/bin/bash

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

_XTRACE_ELASTICSEARCH=$(set +o | grep xtrace)
set +o xtrace

function is_elasticsearch_enabled {
    is_service_enabled monasca-elasticsearch && return 0
    return 1
}

function configure_elasticsearch {
    if is_elasticsearch_enabled; then
        echo_summary "Configuring Elasticsearch for events handling"
        local service_file="/etc/systemd/system/devstack@elasticsearch.service"
        # This property disable elasticsearch check for dots in filed name,
        # Some event use dot in field name.
        local es_java_opts="ES_JAVA_OPTS=-Dmapper.allow_dots_in_name=true"
        iniset -sudo "$service_file" "Service" "Environment" "$es_java_opts"
        restart_process "elasticsearch" || true
    fi
}

$_XTRACE_ELASTICSEARCH
