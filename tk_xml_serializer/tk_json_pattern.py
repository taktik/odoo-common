# -*- coding: utf-8 -*-
##############################################################################
#
# Authors: Lefever David
# Copyright (c) 2015 Taktik SA/NV (http://www.taktik.be)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import orm, fields
import logging
import simplejson

logger = logging.getLogger(__name__)


class PatternModel(orm.Model):
    _name = 'tk.json.pattern'

    def validate_json(self, cr, uid, ids, context=None):
        if not ids:
            return

        if not isinstance(ids, list):
            ids = [ids]

        for pattern in self.browse(cr, uid, ids):
            try:
                simplejson.loads(pattern.json_pattern)
            except Exception, e:
                logger.error(e)
                return False

        return True

    _columns = {
        'name': fields.char('Name', size=128, required=False),
        'model_id': fields.many2one('ir.model', 'Model', required=False),
        'json_pattern': fields.text('JSON Pattern')
    }
