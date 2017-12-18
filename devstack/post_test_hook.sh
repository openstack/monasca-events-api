#
# (C) Copyright 2015 Hewlett Packard Enterprise Development Company LP
# (C) Copyright 2017 FUJITSU LIMITED
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Sleep some time until all services are started
sleep 6

function load_devstack_utilities {
    source $BASE/new/devstack/stackrc
    source $BASE/new/devstack/functions
    source $BASE/new/devstack/openrc admin admin

    # print OS_ variables
    env | grep OS_
}
