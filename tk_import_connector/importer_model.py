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

_logger = logging.getLogger(__name__)

from openerp.osv import fields, orm
from .backend import taktik_importer_backend
from .unit.import_synchronizer import DelayedBatchImport, TaktikImport


class taktik_queue_job(orm.Model):
    _inherit = 'queue.job'

    def __get_error_report(self, cr, uid, ids, field_name, args=None, context={}):
        res = {}
        list_error = [
            re.compile("Exception: (.*?)'\)"),
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

    def import_data(self, cr, uid, data):
        model = data[0]
        header = data[1]
        row = [data[2]]
        lang = data[3]
        mode = data[4]

        res = self.pool.get(model).import_data(cr, uid, header, row, mode=mode, context={'lang': lang})
        if res[0] == -1:
            raise Exception('ValidateError', "%s" % res[2])
        return res


@taktik_importer_backend
class TaktikBatchImport(DelayedBatchImport):
    _model_name = ['taktik.importer.model']

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

                # header
                _list.append(header)

                # row
                _list.append(row)

                # language for the context
                _list.append(self.environment.backend_record.language)

                # mode create or update
                _list.append(self.environment.backend_record.mode)

                self._import_row(_list)

                _list = []


@taktik_importer_backend
class TaktikFileImport(TaktikImport):
    _model_name = ['taktik.importer.model']

    def _run(self, data):
        self.session.pool.get('taktik.importer.model').import_data(self.session.cr, self.session.uid, data)
