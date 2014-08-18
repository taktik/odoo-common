# -*- coding: utf-8 -*-
# #############################################################################
#
# OpenERP, Open Source Management Solution
# Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
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
from lxml import etree
from operator import itemgetter
from collections import OrderedDict
import base64
from ast import literal_eval

logger = logging.getLogger(__name__)

FORMAT_ID = '__export__%s_%s'


class tk_export_xml(orm.Model):
    _name = 'tk.export.xml'

    def _generate_dico(self, cr, uid, ids, context=None):
        # Objects
        field_obj = self.pool.get('ir.model.fields')
        data_obj = self.pool.get('ir.model.data')
        model_obj = self.pool.get('ir.model')

        document = OrderedDict()

        export = self.browse(cr, uid, ids[0], context=context)



        domain = literal_eval(export.domain_custom) or []

        query = '''
            select name from ir_model_fields f, tk_field_record r
            where f.id = r.field_id
            and r.action = 'enabled'
            and export_id = %s
        '''
        cr.execute(query, (export.id, ))
        field_names = map(lambda x: x[0], cr.fetchall())

        if 'parent_id' in field_names:
            if export.limit > 0:
                data_ids = self.pool.get(export.model_id.model).search(cr, uid, domain, context=context, order='parent_id DESC', limit=export.limit)
            else:
                data_ids = self.pool.get(export.model_id.model).search(cr, uid, domain, context=context, order='parent_id DESC')
        else:
            if export.limit > 0:
                data_ids = self.pool.get(export.model_id.model).search(cr, uid, domain, context=context, limit=export.limit)
            else:
                data_ids = self.pool.get(export.model_id.model).search(cr, uid, domain, context=context)

        logger.debug(str(field_names))

        for data_record in self.pool.get(export.model_id.model).read(cr, uid, data_ids, field_names, context=context):
            # Check if present in xml data
            xml_ids = data_obj.search(cr, uid, [('model', '=', export.model_id.model), ('res_id', '=', data_record.get('id'))], limit=1)
            if xml_ids:
                if export.fetch_existant:
                    xml_data = data_obj.browse(cr, uid, xml_ids[0])
                    export_id = '%s.%s,%s' % (xml_data.module, xml_data.name, export.model_id.model)
                else:
                    continue
            else:
                export_id = FORMAT_ID % (export.model_id.model.replace('.', '_'), '%s,%s' % (data_record.get('id'), export.model_id.model))

            logger.debug('Try to export %s' % export_id)
            if export_id in document.keys():
                continue
            document[export_id] = {}
            for field_name in field_names:
                value = data_record.get(field_name)

                # Get info on relation
                if export.model_id.model == 'product.product':
                    field_id = field_obj.search(cr, uid, [('name', '=', field_name), ('model_id', 'in', [export.model_id.id, model_obj.search(cr, uid, [('model', '=', 'product.template')])[0]])], limit=1)[0]
                else:
                    field_id = field_obj.search(cr, uid, [('name', '=', field_name), ('model_id', '=', export.model_id.id)], limit=1)[0]
                field_relation = field_obj.read(cr, uid, field_id, ['relation']).get('relation')

                if type(value).__name__ == 'tuple':
                    res_id = value[0]
                    data_ids = data_obj.search(cr, uid, [('model', '=', field_relation), ('res_id', '=', res_id)], limit=1)
                    if data_ids:
                        data = data_obj.browse(cr, uid, data_ids[0])
                        value = '__xml_data__%s.%s' % (data.module, data.name)
                    else:
                        value = FORMAT_ID % (field_relation.replace('.', '_'), value[0])
                    document[export_id][field_name] = value

                elif type(value).__name__ == 'list':
                    result = '['
                    for res_id in value:
                        data_ids = data_obj.search(cr, uid, [('model', '=', field_relation), ('res_id', '=', res_id)], limit=1)
                        if data_ids:
                            data = data_obj.browse(cr, uid, data_ids[0])
                            ref = 'ref(\'__xml_data__%s.%s\')' % (data.module, data.name)
                        else:
                            ref = 'ref(\'__export__%s_%s\')' % (field_relation.replace('.', '_'), res_id)

                        result += '(4, %s)' % ref

                    result += ']'
                    document[export_id][field_name] = result
                elif type(value).__name__ == 'bool':
                    document[export_id][field_name] = 'bool,%s' % value
                elif type(value).__name__ in ['int', 'float']:
                    document[export_id][field_name] = str(value)
                else:
                    document[export_id][field_name] = value
        return document

    @staticmethod
    def getItemLevel(item):
        return item.getElementsByTagName("parent_id")[0].data

    def export_xml(self, cr, uid, ids, context=None):
        dico = self._generate_dico(cr, uid, ids, context=context)

        openerp = etree.Element('openerp')
        data = etree.Element('data', noupdate="1")
        data_keys = []

        for key in dico.keys():
            record = etree.Element('record', id=key.split(',')[0], model=key.split(',')[1])
            for field_key in dico[key]:
                if not dico[key][field_key]:
                    continue
                value = u'' + dico[key][field_key]
                if 'ref(\'__export__' in value or 'ref(\'__xml_data__' in value:
                    field = etree.Element('field', name=field_key, eval=value.replace('__xml_data__', ''))
                elif '__export__' in value:
                    field = etree.Element('field', name=field_key, ref=value)
                    data_keys.append((value, field))
                elif '__xml_data__' in value:
                    field = etree.Element('field', name=field_key, ref=value.replace('__xml_data__', ''))
                elif 'bool,' in value:
                    value = value.split(',')[1]
                    if value == 'True':
                        field = etree.Element('field', name=field_key, eval=value)
                    else:
                        continue
                else:
                    field = etree.Element('field', name=field_key)
                    field.text = value or ''
                record.append(field)
            data.append(record)
        openerp.append(data)

        xml = etree.tostring(openerp, encoding='UTF-8', xml_declaration=True, pretty_print=True)
        data = base64.encodestring(xml)
        self.write(cr, uid, ids, {
            'file': data,
            'filename': '%s_%s_(%s record(s)).xml' % (self.browse(cr, uid, ids[0]).model_id.model.replace('.', '_'), datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT), len(dico.keys()))
        })

        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'tk.export.xml',
            'res_id': ids[0],
            'type': 'ir.actions.act_window',
            'target': 'current',
        }

    def set_all_to_disabled(self, cr, uid, ids, context=None):
        query = '''
            UPDATE tk_field_record SET action = 'disabled' where export_id = any(%s)
        '''
        cr.execute(query, (ids, ))
        cr.commit()
        return True

    def set_all_to_enabled(self, cr, uid, ids, context=None):
        query = '''
            UPDATE tk_field_record SET action = 'enabled' where export_id = any(%s)
        '''
        cr.execute(query, (ids, ))
        cr.commit()
        return True

    def onchange_model_id(self, cr, uid, ids, name, model_id, context=None):


        if model_id:
            # Objects
            record_obj = self.pool.get('tk.field.record')
            field_obj = self.pool.get('ir.model.fields')
            model_obj = self.pool.get('ir.model')

            fields_to_ignore = ['id', 'create_date', 'write_date', 'create_uid', 'write_uid']

            # Get record associated to current export
            record_ids = record_obj.search(cr, uid, [('export_id', 'in', ids)])

            # Unlink records
            record_obj.unlink(cr, uid, record_ids)

            # Create record with the selected model_id
            field_ids = field_obj.search(cr, uid, [('model_id', '=', model_id)])

            # Create new records
            field_record_ids = []

            for field in field_obj.browse(cr, uid, field_ids):
                if field.name not in fields_to_ignore:
                    field_record_ids.append(
                        record_obj.create(cr, uid, {
                            'model_id': model_id,
                            'field_id': field.id,
                        }))

            if model_id == model_obj.search(cr, uid, [('model', '=', 'product.product')])[0]:
                product_template_model_id = model_obj.search(cr, uid, [('model', '=', 'product.template')])[0]
                field_ids = field_obj.search(cr, uid, [('model_id', '=', product_template_model_id)])
                for field in field_obj.browse(cr, uid, field_ids):
                    if field.name not in fields_to_ignore:
                        field_record_ids.append(
                            record_obj.create(cr, uid, {
                                'model_id': product_template_model_id,
                                'field_id': field.id}))

            return {
                'value': {
                    'field_record_ids': field_record_ids,
                    'model_name': model_obj.read(cr, uid, model_id, ['model'])['model']
                }
            }

    _columns = {
        'name': fields.char('Name', size=255, required=True),
        'model_id': fields.many2one('ir.model', string='Model'),
        'field_record_ids': fields.one2many('tk.field.record', 'export_id', string='Records'),
        'file': fields.binary('File'),
        'filename': fields.char('Filename', size=255),
        'domain_custom': fields.char('Domain', size=255, required=True),
        'fetch_existant': fields.boolean('Get ID from database'),
        'limit': fields.integer('Limit'),
        'model_name': fields.char('Model Name', type='char', size=255)
    }

    _defaults = {
        'domain_custom': "['|', ('active', '=', False), ('active', '=', True)]"
    }


tk_export_xml()


class tk_field_record(orm.Model):
    _name = 'tk.field.record'

    _actions = (
        ('disabled', 'Disabled'),
        ('enabled', 'Enabled'),
    )

    _columns = {
        'export_id': fields.many2one('tk.export.xml', string='Export', required=False),
        'model_id': fields.many2one('ir.model', string='Model', ),
        'field_id': fields.many2one('ir.model.fields', string='Field'),
        'field_name': fields.related('field_id', 'name', string='Name', type='char'),
        'field_relation': fields.related('field_id', 'relation', string='Relation', type='char'),
        'field_type': fields.related('field_id', 'ttype', string='Type', type='char'),
        'field_required': fields.related('field_id', 'required', string='Required', type='boolean'),
        'action': fields.selection(_actions, string='Action', required=True),
    }

    _defaults = {
        'action': 'enabled'
    }


tk_field_record()
