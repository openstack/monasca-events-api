# Copyright 2014 Hewlett-Packard
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import MySQLdb
from oslo_log import log
from oslo_utils import timeutils

from monasca_events_api.common.repositories.mysql import mysql_repository
from monasca_events_api.common.repositories import transforms_repository
from monasca_events_api.common.repositories import constants

LOG = log.getLogger(__name__)


class TransformsRepository(mysql_repository.MySQLRepository,
                           transforms_repository.TransformsRepository):

    def create_transforms(self, id, tenant_id, name, description,
                          specification, enabled):

        cnxn, cursor = self._get_cnxn_cursor_tuple()
        with cnxn:
            now = timeutils.utcnow()
            try:
                cursor.execute("""insert into event_transform(
                id,
                tenant_id,
                name,
                description,
                specification,
                enabled,
                created_at,
                updated_at)
                values (%s, %s, %s, %s, %s, %s, %s, %s)""",
                               (id, tenant_id, name, description,
                                specification, enabled, now, now))
            except MySQLdb.IntegrityError as e:
                code, msg = e
                if code == 1062:
                    MySQLdb.AlreadyExistsException(
                        'Transform definition already '
                        'exists for tenant_id: {}'.format(tenant_id))
                else:
                    raise e

    def list_transforms(self, tenant_id, limit=None, offset=None):
        base_query = """select * from event_transform where deleted_at IS NULL"""
        tenant_id_clause = " and tenant_id = \"{}\"".format(tenant_id)
        order_by_clause = " order by id"

        offset_clause = ' '
        if offset:
            offset_clause = " and id > \"{}\"".format(offset)

        if not limit:
            limit = constants.PAGE_LIMIT
        limit_clause = " limit {}".format(limit)

        query = (base_query +
                 tenant_id_clause +
                 offset_clause +
                 order_by_clause +
                 limit_clause)

        rows = self._execute_query(query, [])
        return rows

    def list_transform(self, tenant_id, transform_id):
        base_query = """select * from event_transform where deleted_at IS NULL"""
        tenant_id_clause = " and tenant_id = \"{}\"".format(tenant_id)
        transform_id_clause = " and id = \"{}\"".format(transform_id)

        query = (base_query+
                 tenant_id_clause+
                 transform_id_clause)

        rows = self._execute_query(query, [])
        return rows

    def delete_transform(self, tenant_id, transform_id):
        now = timeutils.utcnow()
        base_query = "update event_transform set deleted_at = \"{}\"  where"\
            .format(now)
        tenant_id_clause = " tenant_id = \"{}\"".format(tenant_id)
        transform_id_clause = " and id = \"{}\"".format(transform_id)

        query = (base_query +
                 tenant_id_clause +
                 transform_id_clause)
        self._execute_query(query, [])
