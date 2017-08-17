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


_XTRACE_ELASTICSEARCH=$(set +o | grep xtrace)
set +o xtrace

function is_elasticsearch_enabled {
    is_service_enabled monasca-elasticsearch && return 0
    return 1
}

function install_elasticsearch {
    if is_elasticsearch_enabled; then
        echo_summary "Installing ElasticSearch ${ELASTICSEARCH_VERSION}"

        local es_tarball=elasticsearch-${ELASTICSEARCH_VERSION}.tar.gz
        local es_url=http://download.elasticsearch.org/elasticsearch/elasticsearch/${es_tarball}
        local es_dest=${FILES}/${es_tarball}

        download_file ${es_url} ${es_dest}
        tar xzf ${es_dest} -C $DEST

        sudo chown -R $STACK_USER $DEST/elasticsearch-${ELASTICSEARCH_VERSION}
        ln -sf $DEST/elasticsearch-${ELASTICSEARCH_VERSION} $ELASTICSEARCH_DIR
    fi
}

function configure_elasticsearch {
    if is_elasticsearch_enabled; then
        echo_summary "Configuring ElasticSearch ${ELASTICSEARCH_VERSION}"

        local templateDir=$ELASTICSEARCH_CFG_DIR/templates

        for dir in $ELASTICSEARCH_LOG_DIR $templateDir $ELASTICSEARCH_DATA_DIR; do
            sudo install -m 755 -d -o $STACK_USER $dir
        done

        sudo cp -f "${PLUGIN_FILES}"/elasticsearch/elasticsearch.yml $ELASTICSEARCH_CFG_DIR/elasticsearch.yml
        sudo chown -R $STACK_USER $ELASTICSEARCH_CFG_DIR/elasticsearch.yml
        sudo chmod 0644 $ELASTICSEARCH_CFG_DIR/elasticsearch.yml

        sudo sed -e "
            s|%ELASTICSEARCH_BIND_HOST%|$ELASTICSEARCH_BIND_HOST|g;
            s|%ELASTICSEARCH_BIND_PORT%|$ELASTICSEARCH_BIND_PORT|g;
            s|%ELASTICSEARCH_PUBLISH_HOST%|$ELASTICSEARCH_PUBLISH_HOST|g;
            s|%ELASTICSEARCH_PUBLISH_PORT%|$ELASTICSEARCH_PUBLISH_PORT|g;
            s|%ELASTICSEARCH_DATA_DIR%|$ELASTICSEARCH_DATA_DIR|g;
            s|%ELASTICSEARCH_LOG_DIR%|$ELASTICSEARCH_LOG_DIR|g;
        " -i $ELASTICSEARCH_CFG_DIR/elasticsearch.yml
    fi
}

function start_elasticsearch {
    if is_elasticsearch_enabled; then
        echo_summary "Starting ElasticSearch ${ELASTICSEARCH_VERSION}"
        # TODO(jwachowski) find some nicer solution for setting env variable
        local service_file="/etc/systemd/system/devstack@elasticsearch.service"
        local es_java_opts="ES_JAVA_OPTS=-Dmapper.allow_dots_in_name=true"
        iniset -sudo "$service_file" "Service" "Environment" "$es_java_opts"
        run_process "elasticsearch" "$ELASTICSEARCH_DIR/bin/elasticsearch"
    fi
}

function stop_elasticsearch {
    if is_elasticsearch_enabled; then
        echo_summary "Stopping ElasticSearch ${ELASTICSEARCH_VERSION}"
        stop_process "elasticsearch" || true
    fi
}

function clean_elasticsearch {
    if is_elasticsearch_enabled; then
        echo_summary "Cleaning Elasticsearch ${ELASTICSEARCH_VERSION}"

        sudo rm -rf ELASTICSEARCH_DIR || true
        sudo rm -rf ELASTICSEARCH_CFG_DIR || true
        sudo rm -rf ELASTICSEARCH_LOG_DIR || true
        sudo rm -rf ELASTICSEARCH_DATA_DIR || true
        sudo rm -rf $FILES/elasticsearch-${ELASTICSEARCH_VERSION}.tar.gz || true
        sudo rm -rf $DEST/elasticsearch-${ELASTICSEARCH_VERSION} || true
    fi
}

$_XTRACE_ELASTICSEARCH
