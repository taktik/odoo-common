# -*- coding: utf-8 -*-
import csv
import logging
import base64
import itertools
import re

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from openerp.osv import fields, orm


_logger = logging.getLogger(__name__)

from .backend import taktik_importer_backend_custom
from .unit.import_synchronizer import DelayedBatchImport, TaktikImport

FIELDS_RECURSION_LIMIT = 2


class taktik_queue_job(orm.Model):
    _inherit = 'queue.job'

    def __get_error_report(self, cr, uid, ids, field_name, args=None, context={}):
        res = {}
        list_error = [
            re.compile("except_orm: (.*?)'\)"),
            re.compile("IntegrityError: (.*?)\)")
        ]
        for job in self.browse(cr, uid, ids, context):
            res[job.id] = ''
            if job.exc_info:
                for r in list_error:
                    m = r.search(str(job.exc_info))
                    if m:
                        res[job.id] += m.group(1) + "\n\n"
        return res

    _columns = {
        'error_report': fields.function(__get_error_report, type='char', method=True, string='Error Report'),
    }


class taktik_importer_model(orm.Model):
    _name = 'taktik.importer.model.custom'
    _description = 'Taktik Custom Importer model'

    _columns = {
        'res_model': fields.many2one('ir.model', string='Model'),
    }

    def get_fields(self, cr, uid, model, context=None, depth=FIELDS_RECURSION_LIMIT):

        model_obj = self.pool[model]
        fields = {}
        fields['id'] = {
            'id': 'id',
            'name': 'id',
            'string': "External ID",
            'required': False,
            'fields': [],
        }
        fields_got = model_obj.fields_get(cr, uid, context=context)
        blacklist = orm.MAGIC_COLUMNS + [model_obj.CONCURRENCY_CHECK_FIELD]
        for name, field in fields_got.iteritems():
            if name in blacklist:
                continue
                # an empty string means the field is deprecated, @deprecated must
            # be absent or False to mean not-deprecated
            if field.get('deprecated', False) is not False:
                continue

            f = {
                'id': name,
                'name': name,
                'string': field['string'],
                'required': bool(field.get('required')),
                'fields': [],
                'type': field['type']
            }

            if field.get('relation', False):
                f['relation'] = field['relation']

            if field['type'] in ('many2many', 'many2one'):
                f['fields'] = [
                    dict(f, name='id', string="External ID"),
                    dict(f, name='.id', string="Database ID"),
                ]
            elif field['type'] == 'one2many' and depth:
                f['fields'] = self.get_fields(cr, uid, field['relation'], context=context, depth=depth - 1)

            fields[f.get('id')] = f

        return fields

    def __get_data(self, cr, uid, model, header, columns, row):
        to_save = {}
        for index, header_item in enumerate(header):
            if '/' in header_item:

                col = header_item.split('/', 1)
                entity = columns.get(col[0]).get('relation')

                if col[1] == 'id' or col[1] == '.id':
                    # If external id or database id, get it
                    # mcol = self.pool.get(model)._all_columns.get(col[0]).column # Get the column
                    mcol = self.pool.get(model)._fields.get(col[0])
                    ids, _, _ = self.pool.get('ir.fields.converter').db_id_for(cr, uid, entity, mcol, col[1], row[index])
                    if not hasattr(ids, '__iter__'):
                        ids = [ids]

                else:
                    domain_search = []
                    if '[' in col[1] and ']' in col[1]:
                        key_composite = col[1]
                        key_composite = key_composite[key_composite.index('[') + 1:len(key_composite) - 1]
                        key_composite = key_composite.split('|')
                        value_composite = row[index].split('|')
                        for _i, _k in enumerate(key_composite):
                            if '/' in _k:
                                _k_composite = _k.split('/')
                                _k_fields = self.pool.get('taktik.importer.model.custom').get_fields(cr, uid, entity)
                                _id = self.pool.get(_k_fields.get(_k_composite[0]).get('relation')).search(cr, uid, [
                                    (_k_composite[1], '=', value_composite[_i])], context={'active_test': False})[0]
                                domain_search.append((_k_composite[0], '=', _id))
                            else:
                                domain_search.append((_k, '=', value_composite[_i]))
                    else:
                        domain_search = [(col[1], '=', row[index])]

                    ids = self.pool.get(entity).search(cr, uid, domain_search, context={'active_test': False})
                if len(ids):
                    if columns.get(col[0]).get('type') in ('many2many', 'one2many'):
                        to_save[col[0]] = [(4, ids[0])]
                    else:
                        to_save[col[0]] = ids[0]
                else:
                    to_save[col[0]] = False
            else:
                to_save[header_item] = row[index] or False
        return to_save

    def __check_key(self, cr, uid, model, keys, columns, values):
        key_domain = []
        if 'id' in values:
            # If id is in the values, search the res_id in ir_model_data (as if id was the xml_id)
            # if not found, we will force the creation
            try:
                cr.execute("""
                select res_id from ir_model_data where model=%s and name=%s
                """, (model, values.get('id')))
                res = cr.fetchone()
                if res:
                    res_id = res[0]
                    key_domain.append(('id', '=', res_id))
                else:
                    key_domain.append(('id', '=', False))  # Will force creation
            except Exception, e:
                _logger.warning(e)
                key_domain.append(('id', '=', False))  # Will force creation

        for key in keys:
            if columns.get(key).get('type') in ('many2many', 'one2many'):
                key_domain.append((key, 'in', [values.get(key)[0][1]]))
            else:
                key_domain.append((key, '=', values.get(key)))
        return key_domain

    def import_data(self, cr, uid, data):
        _logger.debug("Importing data %s" % data)
        model = data[0]
        header = data[2]
        row = data[3]
        lang = data[4]
        keys = data[1]

        columns = self.get_fields(cr, uid, model)
        to_save = self.__get_data(cr, uid, model, header, columns, row)
        domain = self.__check_key(cr, uid, model, keys, columns, to_save)

        ModelData = self.pool['ir.model.data'].clear_caches()
        mode = 'init'
        current_module = ''
        noupdate = False

        def _create():
            # No keys defined, always create
            if 'id' in to_save:
                # External id was set, import through ModelData
                xid = to_save.pop('id')
                return ModelData._update(cr, uid, model,
                                         current_module, to_save, mode=mode, xml_id=xid,
                                         noupdate=noupdate, res_id=False, context={})
            return self.pool.get(model).create(cr, uid, to_save, context={'lang': lang})

        if len(domain) == 0:
            return _create()
        else:
            ids = self.pool.get(model).search(cr, uid, domain, context={'active_test': False})
            if len(ids):
                return self.pool.get(model).write(cr, uid, ids[0], to_save, context={'lang': lang})
            else:
                return _create()


@taktik_importer_backend_custom
class TomraBatchImport(DelayedBatchImport):
    _model_name = ['taktik.importer.model.custom']

    def __parse_file(self):
        record = self.environment.backend_record
        data = StringIO(base64.b64decode(u'' + record.file))
        csv_iterator = csv.reader(data, quotechar=str(record.quoting), delimiter=str(record.delimiter))
        csv_nonempty = itertools.ifilter(None, csv_iterator)
        encoding = record.encoding
        return itertools.imap(lambda row: [item.decode(encoding) for item in row], csv_nonempty)

    def _run(self, data=None):
        """ Run the synchronization """

        self.rows = self.__parse_file()

        header = []
        _list = []
        for index, row in enumerate(self.rows):
            if index == 0:
                header = row
            else:
                # model
                _list.append(self.environment.backend_record.model_id.model)

                # keys
                keys = [x.name for x in self.environment.backend_record.key]
                _list.append(keys)

                # header
                _list.append(header)

                # row
                _list.append(row)

                # language for the context
                _list.append(self.environment.backend_record.language)

                self._import_row(_list)

                _list = []


@taktik_importer_backend_custom
class TomraFileImport(TaktikImport):
    _model_name = ['taktik.importer.model.custom']

    def _run(self, data):
        self.session.pool.get('taktik.importer.model.custom').import_data(self.session.cr, self.session.uid, data)
