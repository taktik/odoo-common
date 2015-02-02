# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import orm, fields
import openerp.pooler as pooler
from openerp.addons.tk_tools.tk_date_tools import tk_date_tools as tkdt
from openerp.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from datetime import datetime
import logging
import threading
from openerp.modules.registry import RegistryManager

logger = logging.getLogger(__name__)


class tk_log(orm.Model):
    _name = 'tk.log'
    _rec_name = 'name'
    _order = 'date desc'

    def log(self, cr, uid, message, model_name=False, object_id=None, level='info'):
        # If no object we create a new cursor
        db_name = threading.current_thread().dbname

        new_cr = RegistryManager.get(db_name).cursor()


        if level == 'info':
            logger.info(message)
        elif level == 'debug':
            logger.debug(message)
        elif level == 'warning':
            logger.warn(message)
        elif level == 'error':
            logger.error(message)
        else:
            logger.fatal(message)

        try:
            values = {
                'message': message,
                'level': level,
                'object_id': object_id or False,
                'uid': uid,
                'model_name': model_name
            }
            log_id = self.create(new_cr, uid, values)
            new_cr.commit()

        finally:
            new_cr.close()

        return log_id



    def _get_trimmed_message(self, cr, uid, ids, field_name, arg, context=None):
        """
        Return message trimmed to max 100 characters
        """
        res = {}
        log_records = self.read(cr, uid, ids, ['message'], context)
        for log_record in log_records:
            message = log_record.get('message', '')
            log_id = log_record.get('id')
            if len(message) > 97:
                res[log_id] = message[:97] + '...'
            else:
                res[log_id] = message

        return res

    def _get_default_date(self, cr, uid, context=None):
        current_date = datetime.utcnow()
        return current_date.strftime('%Y-%m-%d %H:%M:%S.%f')

    _columns = {
        'name': fields.function(_get_trimmed_message, method=True, type='char', size=100, store=True, string='Label'),
        'message': fields.text('Message', required=True),
        'level': fields.selection([
                                      ('debug', 'Debug'),
                                      ('info', 'Information'),
                                      ('warning', 'Warning'),
                                      ('error', 'Error'),
                                      ('fatal', 'Fatal'),
                                  ], 'Level'),

        'model_name': fields.char('Model Name', size=64),
        'uid': fields.many2one('res.users', 'User'),
        'object_id': fields.integer('ID'),
        'date': fields.datetime('Date')
    }

    _defaults = {
        'date': _get_default_date,
        'uid': lambda self, cr, uid, context: uid,
        'level': 'info'
    }

    def see_entity(self, cr, uid, ids, context):
        log = self.browse(cr, uid, ids)[0]

        return {'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': log.model_name,
                'context': {'init': True},
                'res_id': log.object_id,
                'target': 'current',
        }


tk_log()