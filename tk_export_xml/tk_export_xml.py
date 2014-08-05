# -*- coding: utf-8 -*-
# #############################################################################
#
# OpenERP, Open Source Management Solution
# Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
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
from lxml import etree
from operator import itemgetter
from collections import OrderedDict
import base64

logger = logging.getLogger(__name__)

FORMAT_ID = '__export__%s_%s'

class tk_export_xml(orm.Model):
    _name = 'tk.export.xml'

    def _generate_dico(self, cr, uid, ids, document={}, context=None):
        # Objects
        field_obj = self.pool.get('ir.model.fields')
        record_obj = self.pool.get('tk.field.record')

        for export in self.browse(cr, uid, ids, context=context):
            data_ids = self.pool.get(export.model_id.model).search(cr, uid, [], context=context)

            field_names = []
            for record in export.field_record_ids:
                if record.action in ['run_classic', 'run_recursive']:
                    field_names.append(record.field_id.name)



            for data_record in self.pool.get(export.model_id.model).read(cr, uid, data_ids, field_names, context=context):
                export_id = FORMAT_ID % (export.model_id.model.replace('.', '_'), '%s,%s' %(data_record.get('id'), export.model_id.model))
                if export_id in document.keys():
                    continue
                document[export_id]= {}
                for field_name in field_names:
                    value = data_record.get(field_name)

                    # Get info on relation
                    field_id = field_obj.search(cr, uid, [('name', '=', field_name), ('model_id', '=', export.model_id.id)], limit=1)[0]
                    field_relation = field_obj.read(cr, uid, field_id, ['relation']).get('relation')

                    if type(value).__name__ == 'tuple':
                        document[export_id][field_name] = FORMAT_ID % (field_relation.replace('.', '_'), value[0])
                    elif type(value).__name__ == 'list':
                        document[export_id][field_name] = '[' + ','.join(map(lambda x: '(4, ref(\'__export__%s_%s\'))' % (field_relation.replace('.', '_'), x), value)) + ']'
                    elif type(value).__name__ == 'bool':
                        document[export_id][field_name] = 'bool,%s' % value
                    else:
                        document[export_id][field_name] = value

                    if field_relation:
                        record_ids = record_obj.search(cr, uid, [('export_id', '=', export.id), ('field_id', '=', field_id)])
                        record = record_obj.browse(cr, uid, record_ids[0])
                        if field_relation != export.model_id.model and record.action == 'run_recursive':
                            other_export_ids = self.search(cr, uid, [('model_id', '=', record.field_id.model_id.id)])
                            if other_export_ids:
                                document.update(self._generate_dico(cr, uid, other_export_ids, document=document, context=context))


        return document

    def export_xml(self, cr, uid, ids, context=None):
        dico = self._generate_dico(cr, uid, ids, context=context)

        openerp = etree.Element('openerp')
        data = etree.Element('data', noupdate="0")

        for key in dico.keys():
            record = etree.Element('record', id=key.split(',')[0], model=key.split(',')[1])
            for field_key in dico[key]:
                if not dico[key][field_key]:
                    continue
                print '----------'
                print key
                print field_key
                print dico[key][field_key]
                print '----------'
                value = u'' + dico[key][field_key]
                if 'ref(\'__export__' in value:
                    field = etree.Element('field', name=field_key, eval=value)
                elif '__export__' in value:
                    field = etree.Element('field', name=field_key, ref=value)
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
            'filename': 'last_export.xml',
        })


        print '-----------------------------------------'
        import pprint; pp = pprint.PrettyPrinter(indent=4);pp.pprint(dico)
        print xml
        print '-----------------------------------------'
        return True

    def set_all_to_ignore(self, cr, uid, ids, context=None):
        query = '''
            UPDATE tk_field_record SET action = 'ignore' where export_id = any(%s)
        '''
        cr.execute(query, (ids, ))
        cr.commit()
        return True

    def set_all_to_run(self, cr, uid, ids, context=None):
        query = '''
            UPDATE tk_field_record SET action = 'run_classic' where export_id = any(%s)
        '''
        cr.execute(query, (ids, ))
        cr.commit()
        return True

    def onchange_model_id(self, cr, uid, ids, name, model_id, context=None):



        if model_id:
            # Objects
            record_obj = self.pool.get('tk.field.record')
            field_obj = self.pool.get('ir.model.fields')



            # Get record associated to current export
            record_ids = record_obj.search(cr, uid, [('export_id', 'in', ids)])

            # Unlink records
            record_obj.unlink(cr, uid, record_ids)

            # Create record with the selected model_id
            field_ids = field_obj.search(cr, uid, [('model_id', '=', model_id)])

            # Create new records
            field_record_ids = []

            for field_id in field_ids:
                field_record_ids.append(
                    record_obj.create(cr, uid, {
                        'model_id': model_id,
                        'field_id': field_id}))

            return {
                'value': {
                    'field_record_ids': field_record_ids
                }
            }

    def create(self, cr, uid, values, context=None):
        # Object
        field_obj = self.pool.get('tk.field.record')
        model_obj = self.pool.get('ir.model')

        # Get all lines
        all_field_ids = field_obj.search(cr, uid, [])
        all_fields = field_obj.browse(cr, uid, all_field_ids, context=context)



        fields_to_update_ids = []
        for field in all_fields:
            if field.field_id.ttype in ['many2one', 'one2many', 'many2many']:
                model_rel_ids = model_obj.search(cr, uid, [('model', '=', field.field_id.relation)])

                if values['model_id'] in model_rel_ids:
                    fields_to_update_ids.append(field.id)
        if fields_to_update_ids:
            query = '''
                UPDATE tk_field_record SET action = 'run_recursive' where id = any(%s)
            '''
            cr.execute(query, (fields_to_update_ids, ))
            cr.commit()

        return super(tk_export_xml, self).create(cr, uid, values, context=context)


    def unlink(self, cr, uid, ids, context=None):
        # Object
        field_obj = self.pool.get('tk.field.record')
        model_obj = self.pool.get('ir.model')

        # Delete line attached to exports
        line_to_delete_ids = field_obj.search(cr, uid, [('export_id', 'in', ids)])
        field_obj.unlink(cr, uid, line_to_delete_ids)

        # Get all lines
        all_field_ids = field_obj.search(cr, uid, [])
        all_fields = field_obj.browse(cr, uid, all_field_ids, context=context)



        for export_config in self.browse(cr, uid, ids, context):
            fields_to_update_ids = []
            for field in all_fields:
                if field.field_id.ttype in ['many2one', 'one2many', 'many2many']:
                    model_rel_ids = model_obj.search(cr, uid, [('model', '=', field.field_id.relation)])

                    if export_config.model_id.id in model_rel_ids:
                        fields_to_update_ids.append(field.id)

            if fields_to_update_ids:
                query = '''
                    UPDATE tk_field_record SET action = 'run_classic' where id = any(%s)
                '''
                cr.execute(query, (fields_to_update_ids, ))
                cr.commit()

        return super(tk_export_xml, self).unlink(cr, uid, ids, context=context)


    _columns = {
        'name': fields.char('Name', size=255, required=True),
        'model_id': fields.many2one('ir.model', string='Model'),
        'field_record_ids': fields.one2many('tk.field.record', 'export_id', string='Records'),
        'file': fields.binary('File'),
        'filename': fields.char('Filename', size=128),
    }

    _defaults = {
    }


tk_export_xml()


class tk_field_record(orm.Model):
    _name = 'tk.field.record'

    _actions = (
        ('ignore', 'Ignore'),
        ('run_classic', 'Run'),
        ('run_recursive', 'Run with children')
    )

    def _get_default_action(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for record in self.browse(cr, uid, ids, context=context):
            if not record.action:
                # If relation type we check if there is export configuration for the model associated
                if record.field_id.name in ['id', 'write_date', 'create_date']:
                    res[record.id] = 'ignore'
                elif record.field_type in ['one2many', 'many2one', 'many2many']:
                    rel_model_name = record.field_id.relation
                    model_ids = self.pool.get('ir.model').search(cr, uid, [('model', '=', rel_model_name)])
                    export_ids = self.pool.get('tk.export.xml').search(cr, uid, [('model_id', 'in', model_ids)])
                    if export_ids:
                        res[record.id] = 'run_recursive'
                    else:
                        res[record.id] = 'run_classic'
                else:
                    res[record.id] = 'run_classic'
            else:
                res[record.id] = record.action

        return res


    def _set_action(self, cr, uid, ids, name, value, arg, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        if value:
            print str(value) + '----' + str(ids)
            query = '''
                UPDATE tk_field_record set action = %s where id = any(%s)
            '''
            cr.execute(query, (value, ids))
            cr.commit()

            return True
        else:
            return False

    _columns = {
        'export_id': fields.many2one('tk.export.xml', string='Export', required=False),
        'model_id': fields.many2one('ir.model', string='Model',),
        'field_id': fields.many2one('ir.model.fields', string='Field'),
        'field_name': fields.related('field_id', 'name', string='Name', type='char'),
        'field_relation': fields.related('field_id', 'relation', string='Relation', type='char'),
        'field_type': fields.related('field_id', 'ttype', string='Type', type='char'),
        'field_required': fields.related('field_id', 'required', string='Required', type='boolean'),
        'action': fields.function(_get_default_action, store=True, string='Action', method=True, type='selection', selection=_actions, fnct_inv=_set_action),
    }




tk_field_record()
