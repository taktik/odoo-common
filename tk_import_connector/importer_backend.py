# -*- coding: utf-8 -*-
from openerp.osv import fields, orm
from openerp.addons.connector.session import ConnectorSession
from .unit.import_synchronizer import import_batch


class taktik_importer_backend(orm.Model):
    _name = 'taktik.importer.backend'
    _description = 'Taktik Importer Backend'
    _inherit = 'connector.backend'

    _backend_type = 'taktik_importer'

    def _select_versions(self, cr, uid, context=None):
        """ Available versions
        Can be inherited to add custom versions.
        """
        return [('1.0.0', '1.0.0')]

    def _delimiter(self, cr, uid, context=None):
        return [(',', 'Comma'),
                (';', 'Semicolon'),
                ('\t', 'Tab'),
                (' ', 'Space'),
                ]

    def _mode(self, cr, uid, context=None):
        return [('init', 'Create'),
                ('update', 'Update'),
                ]

    def __get_available_languages(self, cr, uid, context=None):
        res_lang_obj = self.pool.get('res.lang')
        lang_ids = res_lang_obj.search(cr, uid, [])
        lang_data = res_lang_obj.read(cr, uid, lang_ids, ['name', 'code'], context)
        return [(lang_info['code'], lang_info['name']) for lang_info in lang_data]

    _defaults = {
        'version': '1.0.0',
        'quoting': '"',
        'delimiter': ',',
        'encoding': 'utf-8',
        'language': 'en_US',
        'mode': 'init'
    }

    _columns = {
        'version': fields.selection(_select_versions, string='Version', required=True),
        'model_id': fields.many2one('ir.model', 'Model', required=True),
        'file': fields.binary('File'),
        'quoting': fields.char('Quoting', size=1, required=True),
        'delimiter': fields.selection(_delimiter, string='Delimiter', required=True),
        'encoding': fields.char('Encoding', size=10, required=True),
        'language': fields.selection(__get_available_languages, 'Language', required=True),
        'mode': fields.selection(_mode, string='Mode', required=True),
    }

    def onchange_model_id(self, cr, uid, ids, model_id, context=None):
        res = {
            'domain': {
                'key': False
            }
        }
        if model_id:
            field_obj = self.pool.get('ir.model.fields')
            field_ids = field_obj.search(cr, uid, [('model_id', '=', model_id)])
            res['domain']['key'] = [('id', 'in', field_ids)]
        return res

    def import_rows(self, cr, uid, ids, context=None):
        if not hasattr(ids, '__iter__'):
            ids = [ids]
        session = ConnectorSession(cr, uid, context=context)
        for backend in self.browse(cr, uid, ids, context=context):
            import_batch.delay(session, backend.id)
        return True
