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


_XTRACE_EVENTS_API=$(set +o | grep xtrace)
set +o xtrace

function is_events_api_enabled {
    is_service_enabled monasca-events-api && return 0
    return 1
}

function install_events_api {
    if is_events_api_enabled; then
        echo_summary "Installing Events Api"
        git_clone $MONASCA_EVENTS_API_REPO $MONASCA_EVENTS_API_DIR $MONASCA_EVENTS_API_BRANCH
        setup_develop $MONASCA_EVENTS_API_DIR
        install_monasca_common
        install_keystonemiddleware
        pip_install uwsgi
    fi
}

function install_monasca_common {
    if use_library_from_git "monasca-common"; then
        git_clone_by_name "monasca-common"
        setup_dev_lib "monasca-common"
    fi
}

function create_monasca_events_cache_dir {
    sudo install -m 700 -d -o $STACK_USER $MONASCA_EVENTS_API_CACHE_DIR
}

function configure_events_api {
    if is_events_api_enabled; then
        echo_summary "Configuring Events Api"

        # Put config files in ``$MONASCA_EVENTS_API_CONF_DIR`` for everyone to find
        sudo install -d -o $STACK_USER $MONASCA_EVENTS_API_CONF_DIR
        sudo install -d -o $STACK_USER $MONASCA_EVENTS_LOG_DIR

        create_monasca_events_cache_dir

        # ensure fresh installation of configuration files
        rm -rf $MONASCA_EVENTS_API_CONF $MONASCA_EVENTS_API_PASTE $MONASCA_EVENTS_API_LOGGING_CONF

        if [[ "$MONASCA_EVENTS_API_CONF_DIR" != "$MONASCA_EVENTS_API_DIR/etc/monasca" ]]; then
            install -m 600 $MONASCA_EVENTS_API_DIR/etc/monasca/events-api-paste.ini $MONASCA_EVENTS_API_PASTE
            install -m 600 $MONASCA_EVENTS_API_DIR/etc/monasca/events-api-logging.conf $MONASCA_EVENTS_API_LOGGING_CONF
        fi

        oslo-config-generator \
            --config-file $MONASCA_EVENTS_API_DIR/config-generator/config.conf \
            --output-file $MONASCA_EVENTS_API_CONF

        iniset "$MONASCA_EVENTS_API_CONF" DEFAULT log_config_append $MONASCA_EVENTS_API_LOGGING_CONF

        # configure events_publisher
        iniset "$MONASCA_EVENTS_API_CONF" events_publisher kafka_url "$SERVICE_HOST:9092"

        # configure keystone middleware
        configure_auth_token_middleware "$MONASCA_EVENTS_API_CONF" "admin" $MONASCA_EVENTS_API_CACHE_DIR
        iniset "$MONASCA_EVENTS_API_CONF" keystone_authtoken region_name $REGION_NAME
        iniset "$MONASCA_EVENTS_API_CONF" keystone_authtoken project_name "admin"
        iniset "$MONASCA_EVENTS_API_CONF" keystone_authtoken password $ADMIN_PASSWORD

        # configure events-api-paste.ini
        iniset "$MONASCA_EVENTS_API_PASTE" server:main bind $MONASCA_EVENTS_API_SERVICE_HOST:$MONASCA_EVENTS_API_SERVICE_PORT
        iniset "$MONASCA_EVENTS_API_PASTE" server:main chdir $MONASCA_EVENTS_API_DIR
        iniset "$MONASCA_EVENTS_API_PASTE" server:main workers $API_WORKERS

        rm -rf $MONASCA_EVENTS_API_UWSGI_CONF
        MONASCA_EVENTS_API_WSGI=/usr/local/bin/monasca-events-api-wsgi
        install -m 600 $MONASCA_EVENTS_API_DIR/etc/monasca/events-api-uwsgi.ini $MONASCA_EVENTS_API_UWSGI_CONF
        write_uwsgi_config "$MONASCA_EVENTS_API_UWSGI_CONF" "$MONASCA_EVENTS_API_WSGI" "/events"

    fi
}


function start_events_api {
    if is_events_api_enabled; then
        echo_summary "Starting Events Api"
        run_process "monasca-events-api" "/usr/local/bin/uwsgi --ini $MONASCA_EVENTS_API_UWSGI_CONF"
    fi
}

function stop_events_api {
    if is_events_api_enabled; then
        echo_summary "Stopping Events Api"
        stop_process "monasca-events-api"
    fi
}

function clean_events_api {
    if is_events_api_enabled; then
        echo_summary "Cleaning Events Api"
        sudo rm -f $MONASCA_EVENTS_API_CONF || true
        sudo rm -f $MONASCA_EVENTS_API_PASTE  || true
        sudo rm -f $MONASCA_EVENTS_API_LOGGING_CONF || true
        sudo rm -rf $MONASCA_EVENTS_API_CACHE_DIR || true

        sudo rm -rf $MONASCA_EVENTS_API_DIR || true
    fi
}

$_XTRACE_EVENTS_API
