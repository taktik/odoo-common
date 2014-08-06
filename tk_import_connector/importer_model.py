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

from .backend import taktik_importer_backend
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
    _name = 'taktik.importer.model'
    _description = 'Taktik Importer model'

    _columns = {
        'res_model': fields.many2one('ir.model', string='Model'),
    }

    def __get_fields(self, cr, uid, model, context=None, depth=FIELDS_RECURSION_LIMIT):

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
            if field.get('readonly'):
                states = field.get('states')
                if not states:
                    continue
                # states = {state: [(attr, value), (attr2, value2)], state2:...}
                if not any(attr == 'readonly' and value is False
                           for attr, value in itertools.chain.from_iterable(
                        states.itervalues())):
                    continue

            f = {
                'id': name,
                'name': name,
                'string': field['string'],
                'required': bool(field.get('required')),
                'fields': [],
            }

            if field.get('relation', False):
                f['relation'] = field['relation']

            if field['type'] in ('many2many', 'many2one'):
                f['fields'] = [
                    dict(f, name='id', string="External ID"),
                    dict(f, name='.id', string="Database ID"),
                ]
            elif field['type'] == 'one2many' and depth:
                f['fields'] = self.__get_fields(cr, uid, field['relation'], context=context, depth=depth - 1)

            fields[f.get('id')] = f

        return fields

    def __get_data(self, cr, uid, fields, columns, row, context=None):
        to_save = {}
        for index, _r in enumerate(fields):
            if '/' in _r:
                col = _r.split('/')
                ids = self.pool.get(columns.get(col[0]).get('relation')).search(cr, uid, [(col[1], '=', row[index])])
                if len(ids):
                    to_save[col[0]] = ids[0]
                else:
                    to_save[col[0]] = False
            else:
                to_save[_r] = row[index]
        return to_save

    def import_data(self, cr, uid, data):
        model = data[0]
        # TODO Check key composite
        keys = data[1][0]
        fields = data[2]
        row = data[3]
        columns = self.__get_fields(cr, uid, model)

        to_save = self.__get_data(cr, uid, fields, columns, row)

        ids = self.pool.get(model).search(cr, uid, [(keys, '=', to_save.get(keys, False))])
        if len(ids):
            return self.pool.get(model).write(cr, uid, ids[0], to_save)
        else:
            return self.pool.get(model).create(cr, uid, to_save)


@taktik_importer_backend
class TomraBatchImport(DelayedBatchImport):
    _model_name = ['taktik.importer.model']

    def __parse_file(self):
        record = self.environment.backend_record
        data = StringIO(base64.b64decode(u'' + record.file))
        csv_iterator = csv.reader(data, quotechar=str(record.quoting), delimiter=str(record.delimiter))
        csv_nonempty = itertools.ifilter(None, csv_iterator)
        encoding = record.encoding
        return itertools.imap(lambda row: [item.decode(encoding) for item in row], csv_nonempty)

    def __check_key(self):
        key_domain = []
        keys = self.environment.backend_record.key
        for key in keys:
            key_domain.append(key.name)
        return key_domain


    def _run(self, data=None):
        """ Run the synchronization """

        # cr = self.session.cr
        # uid = self.session.uid
        # model = self.environment.backend_record.model_id.model

        self.rows = self.__parse_file()
        self.keys = self.__check_key()
        # self.columns = self.__get_fields(cr, uid, model)

        fields = []
        _list = []
        for index, row in enumerate(self.rows):
            if index == 0:
                fields = row
            else:
                # model
                _list.append(self.environment.backend_record.model_id.model)

                # keys
                _list.append(self.keys)

                # fields
                _list.append(fields)

                # row
                _list.append(row)

                self._import_row(_list)

                _list = []


@taktik_importer_backend
class TomraFileImport(TaktikImport):
    _model_name = ['taktik.importer.model']

    def _run(self, data):
        self.session.pool.get('taktik.importer.model').import_data(self.session.cr, self.session.uid, data)