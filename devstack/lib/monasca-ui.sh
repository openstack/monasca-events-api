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


_XTRACE_MONASCA_UI=$(set +o | grep xtrace)
set +o xtrace

function configure_monasca-ui {
    if is_service_enabled horizon && is_service_enabled kibana; then
        local localSettings=${DEST}/horizon/monitoring/config/local_settings.py
        sudo sed -e "
            s|'ENABLE_EVENT_MANAGEMENT_BUTTON', False|'ENABLE_EVENT_MANAGEMENT_BUTTON', True|g;
        " -i ${localSettings}
        restart_apache_server
    fi
}


$_XTRACE_MONASCA_UI
