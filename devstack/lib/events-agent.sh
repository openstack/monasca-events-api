#!/bin/bash

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


_XTRACE_EVENTS_AGENT=$(set +o | grep xtrace)
set +o xtrace

function is_events_agent_enabled {
    is_service_enabled monasca-events-agent && return 0
    return 1
}

function install_events_agent {
    if is_events_agent_enabled; then
        echo_summary "Installing Events Agent"
        # TODO implement this
    fi
}

function configure_events_agent {
    if is_events_agent_enabled; then
        echo_summary "Configuring Events Agent"
        # TODO implement this
    fi
}

function start_events_agent {
    if is_events_agent_enabled; then
        echo_summary "Starting Events Agent"
        # TODO implement this
    fi
}

function stop_events_agent {
    if is_events_agent_enabled; then
        echo_summary "Stopping Events Agent"
        # TODO implement this
    fi
}

function clean_events_agent {
    if is_events_agent_enabled; then
        echo_summary "Cleaning Events Agent"
        # TODO implement this
    fi
}

$_XTRACE_EVENTS_AGENT
