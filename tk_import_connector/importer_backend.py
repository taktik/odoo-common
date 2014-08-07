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


    _defaults = {
        'version': '1.0.0',
        'quoting': '"',
        'delimiter': ',',
        'encoding': 'utf-8',
    }

    _columns = {
        'version': fields.selection(_select_versions, string='Version', required=True),
        'model_id': fields.many2one('ir.model', 'Model', required=True),
        'key': fields.many2many('ir.model.fields', 'model_fields_backend_importer_rel', 'importer_backend_id', 'ir_model_fields_id', 'Key'),
        'file': fields.binary('File'),
        'quoting': fields.char('Quoting', size=1, required=True),
        'delimiter': fields.selection(_delimiter, string='Delimiter', required=True),
        'encoding': fields.char('Encoding', size=10, required=True),
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

    def _scheduler_import_rows(self, cr, uid, domain=None, context=None):
        if domain is None:
            domain = []
        ids = self.search(cr, uid, domain, context=context)
        if ids:
            self.import_rows(cr, uid, ids, context=context)
        return True