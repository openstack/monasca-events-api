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


_XTRACE_UTILS=$(set +o | grep xtrace)
set +o xtrace

# download_file
#  $1 - url to download
#  $2 - location where to save url to
#
# Download file only when it not exists or there is newer version of it.
#
#  Uses global variables:
#  - OFFLINE
#  - DOWNLOAD_FILE_TIMEOUT
function download_file {
    local url=$1
    local file=$2

    # If in OFFLINE mode check if file already exists
    if [[ ${OFFLINE} == "True" ]] && [[ ! -f ${file} ]]; then
        die $LINENO "You are running in OFFLINE mode but
                        the target file \"$file\" was not found"
    fi

    local curl_z_flag=""
    if [[ -f "${file}" ]]; then
        # If the file exists tell cURL to download only if newer version
        # is available
        curl_z_flag="-z $file"
    fi

    # yeah...downloading...devstack...hungry..om, om, om
    local timeout=0

    if [[ -n "${DOWNLOAD_FILE_TIMEOUT}" ]]; then
        timeout=${DOWNLOAD_FILE_TIMEOUT}
    fi

    time_start "download_file"
    _safe_permission_operation ${CURL_GET} -L $url --connect-timeout $timeout --retry 3 --retry-delay 5 -o $file $curl_z_flag
    time_stop "download_file"
}

function configure_log_dir {
    local logdir=$1

    sudo mkdir -p $logdir
    sudo chmod -R 0777 $logdir
}

$_XTRACE_UTILS
