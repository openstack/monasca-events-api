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


_XTRACE_KAFKA=$(set +o | grep xtrace)
set +o xtrace

function is_kafka_enabled {
    is_service_enabled monasca-kafka && return 0
    return 1
}

function install_kafka {
    if is_kafka_enabled; then
        echo_summary "Installing kafka"

        local kafka_tarball=kafka_${KAFKA_VERSION}.tgz
        local kafka_tarball_url=${APACHE_ARCHIVES}kafka/${BASE_KAFKA_VERSION}/${kafka_tarball}
        local kafka_tarball_dest=${FILES}/${kafka_tarball}

        download_file ${kafka_tarball_url} ${kafka_tarball_dest}

        sudo groupadd --system kafka || true
        sudo useradd --system -g kafka kafka || true
        sudo tar -xzf ${kafka_tarball_dest} -C /opt
        sudo ln -sf /opt/kafka_${KAFKA_VERSION} /opt/kafka
        sudo cp -f "${MONASCA_EVENTS_API_DIR}"/devstack/files/kafka/kafka-server-start.sh /opt/kafka_${KAFKA_VERSION}/bin/kafka-server-start.sh
    fi
}

function configure_kafka {
    if is_kafka_enabled; then
        echo_summary "Configuring kafka"
        sudo mkdir -p /var/kafka || true
        sudo chown kafka:kafka /var/kafka
        sudo chmod 755 /var/kafka
        sudo rm -rf /var/kafka/lost+found
        sudo mkdir -p /var/log/kafka || true
        sudo chown kafka:kafka /var/log/kafka
        sudo chmod 755 /var/log/kafka
        sudo ln -sf /opt/kafka/config /etc/kafka
        sudo ln -sf /var/log/kafka /opt/kafka/logs

        sudo cp -f "${MONASCA_EVENTS_DEVSTACK_DIR}"/files/kafka/log4j.properties /etc/kafka/log4j.properties
        sudo cp -f "${MONASCA_EVENTS_DEVSTACK_DIR}"/files/kafka/server.properties /etc/kafka/server.properties
        sudo chown kafka:kafka /etc/kafka/*
        sudo chmod 644 /etc/kafka/*
    fi
}

function start_kafka {
    if is_kafka_enabled; then
        echo_summary "Starting Monasca Kafka"
        run_process "kafka" "/opt/kafka/bin/kafka-server-start.sh /etc/kafka/server.properties" "kafka" "kafka"
    fi
}

function stop_kafka {
    if is_kafka_enabled; then
        echo_summary "Stopping Monasca Kafka"
        stop_process "kafka" || true
    fi
}

function clean_kafka {
    if is_kafka_enabled; then
        echo_summary "Clean Monasca Kafka"
        sudo rm -rf /var/kafka
        sudo rm -rf /var/log/kafka
        sudo rm -rf /etc/kafka
        sudo rm -rf /opt/kafka
        sudo userdel kafka || true
        sudo groupdel kafka || true
        sudo rm -rf /opt/kafka_${KAFKA_VERSION}
        sudo rm -rf ${FILES}/kafka_${KAFKA_VERSION}.tgz
    fi
}

function create_kafka_topic {
    if is_kafka_enabled; then
        /opt/kafka/bin/kafka-topics.sh --create --zookeeper localhost:2181 --replication-factor 1 --partitions 4 --topic $1
    fi
}

$_XTRACE_KAFKA
