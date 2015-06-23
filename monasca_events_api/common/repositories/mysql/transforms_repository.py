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
from oslo_utils import timeutils

from monasca_events_api.common.repositories import transforms_repository
from monasca_events_api.common.repositories.mysql import mysql_repository
from monasca_events_api.openstack.common import log


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
            except MySQLdb.IntegrityError, e:
                code, msg = e
                if code == 1062:
                    MySQLdb.AlreadyExistsException(
                        'Transform definition already '
                        'exists for tenant_id: {}'.format(tenant_id))
                else:
                    raise e

    def list_transforms(self, tenant_id, limit=None, offset=None):
        cnxn, cursor = self._get_cnxn_cursor_tuple()
        with cnxn:
            if limit:
                if offset:
                    query = ("""select * from event_transform
                        where tenant_id = "{}" and id > "{}" and deleted_at
                        IS NULL order by id limit {}"""
                             .format(tenant_id, offset, limit))
                else:
                    query = ("""select * from event_transform
                        where tenant_id = "{}" and deleted_at
                        IS NULL order by id limit {}"""
                             .format(tenant_id, limit))
                cursor.execute(query)
            elif offset:
                query = ("""select * from event_transform
                        where tenant_id = "{}" and id > "{}" and deleted_at
                        IS NULL order by id"""
                         .format(tenant_id, offset))
                cursor.execute(query)
            else:
                cursor.execute("""select * from event_transform
                    where tenant_id = %s and deleted_at IS NULL order by id""",
                               [tenant_id])
            return cursor.fetchall()

    def list_transform(self, tenant_id, transform_id):
        cnxn, cursor = self._get_cnxn_cursor_tuple()
        with cnxn:
            cursor.execute("""select * from event_transform
            where tenant_id = %s and id = %s and deleted_at
            IS NULL order by id """,(tenant_id, transform_id))
            return cursor.fetchall()

    def delete_transform(self, tenant_id, transform_id):
        cnxn, cursor = self._get_cnxn_cursor_tuple()
        with cnxn:
            cursor.execute("""delete from event_transform
            where id = %s and tenant_id = %s""", (transform_id, tenant_id))
