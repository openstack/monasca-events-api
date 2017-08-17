#!/bin/bash

#
# Copyright 2017 FUJITSU LIMITED
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Save trace setting
_EVENTS_XTRACE=$(set +o | grep xtrace)
set -o xtrace
_EVENTS_ERREXIT=$(set +o | grep errexit)
set -o errexit

# source lib/*
source ${MONASCA_EVENTS_API_DIR}/devstack/lib/utils.sh
source ${MONASCA_EVENTS_API_DIR}/devstack/lib/zookeeper.sh
source ${MONASCA_EVENTS_API_DIR}/devstack/lib/kafka.sh
source ${MONASCA_EVENTS_API_DIR}/devstack/lib/elasticsearch.sh
source ${MONASCA_EVENTS_API_DIR}/devstack/lib/events-persister.sh
source ${MONASCA_EVENTS_API_DIR}/devstack/lib/events-api.sh
source ${MONASCA_EVENTS_API_DIR}/devstack/lib/events-agent.sh

function pre_install_monasca_events {
    echo_summary "Pre-Installing Monasca Events Dependency Components"

    find_nearest_apache_mirror
    install_zookeeper
    install_kafka
    install_elasticsearch
}

function install_monasca_events {
    echo_summary "Installing Core Monasca Events Components"
    install_events_persister
    install_events_api
    install_events_agent
}

function configure_monasca_events {
    echo_summary "Configuring Monasca Events Dependency Components"
    configure_zookeeper
    configure_kafka
    configure_elasticsearch

    echo_summary "Configuring Monasca Events Core Components"
    configure_log_dir ${MONASCA_EVENTS_LOG_DIR}
    configure_events_persister
    configure_events_api
    configure_events_agent
}

function init_monasca_events {
    echo_summary "Initializing Monasca Events Components"
    start_zookeeper
    start_kafka
    start_elasticsearch
    # wait for all services to start
    sleep 10s
    create_kafka_topic monevents
}

function start_monasca_events {
    echo_summary "Starting Monasca Events Components"
    start_events_persister
    start_events_api
    start_events_agent
}

function unstack_monasca_events {
    echo_summary "Unstacking Monasca Events Components"
    stop_events_agent
    stop_events_api
    stop_events_persister
    stop_elasticsearch
    stop_kafka
    stop_zookeeper
}

function clean_monasca_events {
    echo_summary "Cleaning Monasca Events Components"
    clean_events_agent
    clean_events_api
    clean_events_persister
    clean_elasticsearch
    clean_kafka
    clean_zookeeper
}

# check for service enabled
if is_service_enabled monasca-events; then

    if [[ "$1" == "stack" && "$2" == "pre-install" ]]; then
        # Set up system services
        echo_summary "Configuring Monasca Events system services"
        pre_install_monasca_events

    elif [[ "$1" == "stack" && "$2" == "install" ]]; then
        # Perform installation of service source
        echo_summary "Installing Monasca Events"
        install_monasca_events

    elif [[ "$1" == "stack" && "$2" == "post-config" ]]; then
        # Configure after the other layer 1 and 2 services have been configured
        echo_summary "Configuring Monasca Events"
        configure_monasca_events

    elif [[ "$1" == "stack" && "$2" == "extra" ]]; then
        # Initialize and start the Monasca service
        echo_summary "Initializing Monasca Events"
        init_monasca_events
        start_monasca_events
    fi

    if [[ "$1" == "unstack" ]]; then
        # Shut down Monasca services
        echo_summary "Unstacking Monasca Events"
        unstack_monasca_events
    fi

    if [[ "$1" == "clean" ]]; then
        # Remove state and transient data
        # Remember clean.sh first calls unstack.sh
        echo_summary "Cleaning Monasca Events"
        clean_monasca_events
    fi
fi

# Restore errexit & xtrace
${_EVENTS_ERREXIT}
${_EVENTS_XTRACE}
