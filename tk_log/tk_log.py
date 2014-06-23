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
import datetime
import logging


logger = logging.getLogger(__name__)

class tk_log(orm.Model):
    _name = 'tk_log.log'

    _rec_name = 'label'

    _order = "date desc"

    levels_order = {
        'debug': 0,
        'info': 1,
        'warn': 2,
        'error': 3,
        'fatal': 4,
    }

    @staticmethod
    def create_log(self, cr, uid, message, log_erp=False, model=False, name=False, log_level_console='debug', log_level_erp='info'):
        if log_erp and model and name:
            self.log(cr, uid, 0, message, model=model, name=name, level=log_level_erp)
        if log_level_console == 'debug':
            logger.debug(message)
        elif log_level_console == 'info':
            logger.info(message)
        elif log_level_console == 'warning':
            logger.warning(message)
        elif log_level_console == 'error':
            logger.error(message)



    def _get_source_model(self, cr, uid, context=None):
        return None

    def get_trimmed_message(self, cr, uid, ids, field_name, arg, context=None):
        res = {}

        logs = self.browse(cr, uid, ids, context)

        for log in logs:
            if len(log.message) > 100:
                res[log.id] = log.message[0:100] + '...'
            else:
                res[log.id] = log.message[0:len(log.message)]

        return res

    _columns = {
        'message': fields.text('Message'),
        'date': fields.datetime('Date'),
        'level': fields.selection([
                                      ('debug', 'Debug'),
                                      ('info', 'Information'),
                                      ('warn', 'Warning'),
                                      ('error', 'Error'),
                                      ('fatal', 'Fatal'),
                                  ], 'Level'),
        'model': fields.char('Model', size=64, required=True, select=1),
        'model_name': fields.char('Model Name', size=64),
        'model_id': fields.integer('Record ID', select=1, help="ID of the target record in the database"),
        'source': fields.function(_get_source_model, string="Entity concern", type='many2one', relation='ir.model'),
        'label': fields.function(get_trimmed_message, method=True, type='char', size=100, string='Label'),
        'user': fields.many2one('res.users', 'User'),
    }

    _defaults = {
        'date': lambda *a: fields.datetime.now()
    }

    def create(self, cr, uid, value, context=None):
        db, pool = pooler.get_db_and_pool(cr.dbname)
        cursor = db.cursor(serialized=False)
        cursor.autocommit(True)

        log_level = self.pool.get('ir.model.data').get_object(cr, uid, 'tk_log', 'log_level')
        if self.levels_order.get((value.get('level', 'info'))) >= self.levels_order.get(log_level.value, 1):
            id = super(tk_log, self).create(cursor, uid, value, context)
        else:
            id = False

        cursor.commit()
        cursor.close()
        return id

    def remove_old_logs(self, cr, uid):
        config_parameter_obj = self.pool.get('ir.config_parameter')
        param = config_parameter_obj.get_param(cr, uid, 'tk_log_deletion_in_days')
        if not param:
            return True
        try:
            nb_days = int(param)
            now = datetime.datetime.now()
            past = now - datetime.timedelta(days=nb_days)
            old_log_ids = self.search(cr, uid, [('date', '<', tkdt.datetime_to_string(past, '%Y-%m-%d %H:%M:%S'))])
            if old_log_ids:
                self.unlink(cr, uid, old_log_ids)
        except Exception, e:
            print e
            return True

    def see_entity(self, cr, uid, ids, context):
        log = self.browse(cr, uid, ids)[0]

        return {'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': log.model,
                'context': {'init': True},
                'res_id': log.model_id,
        }


tk_log()


class mail_thread(orm.TransientModel):
    _name = 'mail.thread'
    _inherit = 'mail.thread'

    def log(self, cr, uid, id, message, level='debug', name='', model=None, user=None, context=None):
        data = {
            'message': message,
            'model_id': id,
            'model': model or self._name,
            'level': level,
            'user': user or uid,
            'model_name': name,
        }
        self.pool.get('tk_log.log').create(cr, uid, data, context)

