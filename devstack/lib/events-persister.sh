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


_XTRACE_EVENTS_PERSISTER=$(set +o | grep xtrace)
set +o xtrace

function is_events_persister_enabled {
    is_service_enabled monasca-events-persister && return 0
    return 1
}

function install_events_persister {
    if is_events_persister_enabled; then
        echo_summary "Installing Events Persister dependencies"
        pip_install "elasticsearch>=2.0.0,<3.0.0"
    fi
}

function configure_events_persister {
    if is_events_persister_enabled; then
        echo_summary "Configuring Events Persister"
        # Put config files in ``$MONASCA_EVENTS_PERSISTER_CONF_DIR`` for everyone to find
        sudo install -d -o $STACK_USER $MONASCA_EVENTS_PERSISTER_CONF_DIR

        # ensure fresh installation of configuration files
        rm -rf $MONASCA_EVENTS_PERSISTER_CONF $MONASCA_EVENTS_PERSISTER_LOGGING_CONF

        oslo-config-generator \
            --config-file $MONASCA_EVENTS_PERSISTER_DIR/config-generator/persister.conf \
            --output-file $MONASCA_EVENTS_PERSISTER_CONF

        iniset "$MONASCA_EVENTS_PERSISTER_CONF" DEFAULT log_config_append $MONASCA_EVENTS_PERSISTER_LOGGING_CONF
        iniset "$MONASCA_EVENTS_PERSISTER_CONF" zookeeper uri 127.0.0.1:2181
        iniset "$MONASCA_EVENTS_PERSISTER_CONF" zookeeper partition_interval_recheck_seconds 15
        iniset "$MONASCA_EVENTS_PERSISTER_CONF" kafka num_processors 0
        iniset "$MONASCA_EVENTS_PERSISTER_CONF" kafka_events num_processors 1
        iniset "$MONASCA_EVENTS_PERSISTER_CONF" kafka_events enabled True
        iniset "$MONASCA_EVENTS_PERSISTER_CONF" kafka_events uri $SERVICE_HOST:9092
        iniset "$MONASCA_EVENTS_PERSISTER_CONF" elasticsearch hosts ${ELASTICSEARCH_BIND_HOST}:${ELASTICSEARCH_BIND_PORT}

        sudo cp -f "${MONASCA_EVENTS_DEVSTACK_DIR}"/files/monasca-events-persister/events-persister-logging.conf \
                    "${MONASCA_EVENTS_PERSISTER_LOGGING_CONF}"

        sudo sed -e "
            s|%MONASCA_EVENTS_LOG_DIR%|$MONASCA_EVENTS_LOG_DIR|g;
        " -i ${MONASCA_EVENTS_PERSISTER_LOGGING_CONF}
    fi
}

function start_events_persister {
    if is_events_persister_enabled; then
        echo_summary "Starting Events Persister"
        run_process "monasca-events-persister" "/usr/local/bin/monasca-persister --config-file $MONASCA_EVENTS_PERSISTER_CONF"
    fi
}

function stop_events_persister {
    if is_events_persister_enabled; then
        echo_summary "Stopping Events Persister"
        stop_process "monasca-events-persister" || true
    fi
}

function clean_events_persister {
    if is_events_persister_enabled; then
        echo_summary "Cleaning Events Persister"
        sudo rm -f $MONASCA_EVENTS_PERSISTER_CONF || true
        sudo rm -f $MONASCA_EVENTS_PERSISTER_LOGGING_CONF  || true

        sudo rm -rf $MONASCA_EVENTS_PERSISTER_DIR || true
    fi
}

$_XTRACE_EVENTS_PERSISTER
