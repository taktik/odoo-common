# coding=utf-8
from openerp.tools.translate import _
import openerp.pooler as pooler
from openerp.osv import fields, osv


import base64
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class import_model(osv.osv):
    _name = 'tk_import.model'
    _rec_name = 'model_id'

    _columns = {
        'model_id': fields.many2one('ir.model', 'Model', required=True),
    }
    
import_model()


class import_key(osv.osv):
    _name = 'tk_import.key'
    
    _order = 'model_id'

    _columns = {
        'column': fields.char('Column', size=1024),
        'model_id': fields.many2one('ir.model', 'Model'),
        'name': fields.char('Name', size=128),
    }
    
import_key()


class import_template(osv.osv):
    _name = 'tk_import.template'

    _columns = {
        'name': fields.char('Name', size=128),
        'import_model_id': fields.many2one('tk_import.model', 'Model'),
        'model_id': fields.related('import_model_id', 'model_id',
                                   type='many2one', obj='ir.model',
                                   string='Model'),
        'key_ids': fields.one2many('tk_import.key', 'template_id', 'Keys'),
    }

import_template()


class import_key2(osv.osv):
    _inherit = 'tk_import.key'

    _columns = {
        'template_id': fields.many2one('tk_import.template', 'Template'),
    }
import_key2()


class import_file(osv.osv):
    _name = 'tk_import.file'
    
    _order = 'date DESC'

    __states = [('processed', 'Processed'), ('error', 'Error'),
                ('processing', 'Processing'), ('header', 'Header Checked')]
    __types = [('csv', 'CSV File'), ('txt', 'Text File')]

    def __get_error_report(self, cr, uid, ids, field_name, args=None, context={}):
        res = {}
        ir_config_parameter_obj = self.pool.get('ir.config_parameter')
        import_path = ir_config_parameter_obj.get_param(cr, uid, 'tk_import_path_parameter', False)
        if not import_path:
            logger.error("No import_path defined (config_parameter tk_import_path_parameter)")
            return False

        for file in self.browse(cr, uid, ids, context):
            error_file_path = import_path + '/' + file.file + '_error.txt'
            res[file.id] = False
            if os.path.isfile(error_file_path):
                error_file = open(error_file_path, 'rb')
                file_content = error_file.read()
                res[file.id] = base64.encodestring(file_content)
        return res

    _columns = {
        'name': fields.char('Name', size=128),
        'import_name': fields.char('Import Name', size=64, required=True),
        'import_model_id': fields.many2one('tk_import.model', 'Import Model'),
        'date': fields.datetime('Import Date'),
        'model_id': fields.related('import_model_id', 'model_id',
                                   type='many2one', obj='ir.model',
                                   string='Model'),
        'file': fields.char('File', size=16),
        'state': fields.selection(__states, 'State'),
        'size': fields.integer('Size'),
        'lines': fields.integer('Lines'),
        'errors': fields.integer('Errors'),
        'error_report': fields.function(__get_error_report, type='binary',
                                        method=True, string='Error Report'),
        'progress': fields.integer('%'),
        'type': fields.selection(__types, 'Type'),
        'template_id': fields.many2one('tk_import.template', 'Template'),
        'update': fields.boolean('Update'),
        'update_strict': fields.boolean('Update Strict'),
    }

    _defaults = {
        'state': 'header',
        'date': lambda *a: datetime.today(),
    }
    
    def create(self, cr, uid, values, context={}):
        sequence = self.pool.get('ir.sequence').get(cr, uid, 'file.import')
        values.update({
            'file': cr.dbname + '_' + sequence,
        })
        return super(import_file, self).create(cr, uid, values, context)

import_file()


class export_file(osv.osv):
    _name = 'tk_import.export_file'
    
    _order = 'date DESC'
    
    def __get_export(self, cr, uid, ids, field_name, args=None, context={}):
        res = {}
        ir_config_parameter_obj = self.pool.get('ir.config_parameter')
        export_path = ir_config_parameter_obj.get_param(cr, uid, 'tk_export_path_parameter', False)
        if not export_path:
            logger.error("No export_path defined (config_parameter tk_export_path_parameter)")
            return False

        for file in self.browse(cr, uid, ids, context):
            export_file_path = export_path + '/' + file.name
            res[file.id] = False
            if os.path.isfile(export_file_path):
                export_file = open(export_file_path, 'rb')
                file_content = export_file.read()
                res[file.id] = base64.encodestring(file_content)
        return res

    _columns = {
        'name': fields.char('Name', size=256),
        'export_name': fields.char('Name', size=256),
        'import_model_id': fields.many2one('tk_import.model', 'Import Model'),
        'date': fields.datetime('Export Date'),
        'model_id': fields.related('import_model_id', 'model_id',
                                   type='many2one', obj='ir.model',
                                   string='Model'),
        'file': fields.function(__get_export, type='binary', method=True,
                                string='File'),
        'export_params': fields.text('Params'),
    }

    _defaults = {
        'date': lambda *a: datetime.today(),
    }
    
    def create(self, cr, uid, values, context={}):
        sequence = self.pool.get('ir.sequence').get(cr, uid, 'file.export')
        values.update({
            'name': cr.dbname + '_' + sequence,
        })
        return super(export_file, self).create(cr, uid, values, context)
    
export_file()


class import_model2(osv.osv):
    _inherit = 'tk_import.model'

    _columns = {
        'import_ids': fields.one2many('tk_import.file', 'import_model_id',
                                      'Imports'),
        'template_ids': fields.one2many('tk_import.template',
                                        'import_model_id', 'Templates'),
        'export_ids': fields.one2many('tk_import.export_file',
                                      'import_model_id', 'Exports'),
    }
    
    
import_model2()


class company(osv.osv):
    _inherit = 'res.company'

    _columns = {
        'import_folder': fields.char('Import Folder', size=256),
        'export_folder': fields.char('Export Folder', size=256)
    }
    
company()
