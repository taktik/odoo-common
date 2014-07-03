import csv
import threading
import cStringIO
import codecs
import copy
import logging

import openerp.pooler as pooler

logger = logging.getLogger(__name__)

class DictUnicodeWriter(object):

    def __init__(self, f, fieldnames, dialect=csv.excel, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.queue = cStringIO.StringIO()
        self.writer = csv.DictWriter(self.queue, fieldnames, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, D):
        def treat_encoding(key, value):
            encoded_string = "?"
            try :
                encoded_string = value.encode('utf-8',errors='replace')
            except Exception, e:
                encoded_string = value
                print e
                print "key: %s, value: %s" % (key, value)
            return encoded_string
            
        self.writer.writerow({k:isinstance(v, basestring) and treat_encoding(k, v) or v for k,v in D.items()})
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for D in rows:
            self.writerow(D)

    def writeheader(self):
        self.writer.writeheader()


class data_exporter():
    
    def get_data(self, id, tree):
        row = {}
        model_obj_name = tree['model']
        column = tree['column']
        model_obj = self.pool.get(model_obj_name)
        values = model_obj.read(self.cr, 1, [id], tree['fields'].keys(), {'lang': self.lang})[0]
        is_row = False
        for field in tree['fields']:
            searched_field = field
            separator = '/'
            if field == '.id':
                is_row = True
                searched_field = 'id'
                separator = ''
            field_info = field in model_obj._columns and model_obj._columns[field] or False
            if not field_info:
                field_info = field in model_obj._inherit_fields and model_obj._inherit_fields[field][2] or False
            if not field_info and searched_field != 'id':
                continue
            field_value = field_info and (field_info._type == 'boolean' and (values[searched_field] or 'False') or (values[searched_field] or '')) or values[searched_field] 
            #This is a subfield
            if isinstance(field_value, tuple):
                scope_ids = [field_value[0]]
                subrow = self.make_row(scope_ids, tree['fields'][field])
                if not subrow:
                    continue
                is_row = True
                row[(column and (column + separator) or '') + field] = subrow 
            elif isinstance(field_value, list):
                scope_ids = field_value
                subrow = self.make_row(scope_ids, tree['fields'][field])
                if not subrow:
                    continue
                is_row = True
                row[(column and (column + separator) or '') + field] = subrow
            else:
                if field_value:
                    is_row = True
                    row[(column and (column + separator) or '') + field] = field_value
        if not is_row:
            return {}
        return row
    
    def decompose_row(self, row):
        rows = []
        first_row = {}
        rows.append(first_row)
        for field in row:
            field_value = row[field]
            
            if isinstance(field_value, list):
                subrows = []
                for subfield in field_value:
                    subrows.extend(self.decompose_row(subfield))
                for i in range(0, len(subrows)):
                    if len(rows) < i + 1:
                        rows.append(copy.copy(first_row))
                    rows[i].update(subrows[i])
            else:
                first_row[field] = field_value
        return rows
    
    def create_csv(self, rows):
        print 'CREATE CSV'
        output_string = cStringIO.StringIO()
        codecs.EncodedFile(output_string, 'UTF8', 'UTF8', 'replace')
        if not rows:
            return
        csv.register_dialect('used_for_export', delimiter=self.separator, quotechar=self.quote_delimiter)
        dict_writer = DictUnicodeWriter(output_string, self.header, dialect='used_for_export')
        dict_writer.writeheader()
        dict_writer.writerow(self.row)
        #As we could possibly have something like this
        #{'element1': [{'element2': Value}, {'element3': Value2}], 'element4':Value3},
        #We have to remember that a record can lies on multiple lines
        print rows
        for row in rows:
            #We make the first row
            real_rows = self.decompose_row(row)
            if real_rows:
                first_row = real_rows[0]
                dict_writer.writerow(first_row)
            for real_row in real_rows[1:]:
                actualized_row = copy.copy(first_row)
                actualized_row.update(real_row)
                dict_writer.writerow(actualized_row)
                
        file = self.pool.get('tk_import.export_file').browse(self.cr, 1, self.file_id)

        ir_config_parameter_obj = self.pool.get('ir.config_parameter')
        export_path = ir_config_parameter_obj.get_param(self.cr, 1, 'tk_export_path_parameter', False)
        if not export_path:
            logger.error("No export_path defined (config_parameter tk_export_path_parameter)")
            return False

        file_path = export_path + '/' + file.name
        f = open(file_path, 'wb')
        print output_string.getvalue()
        f.write(output_string.getvalue())
        f.flush()
        f.close()
        
        output_string.close()
    
    def make_row(self, ids, tree):
        rows = []
        for id in ids:
            row = self.get_data(id, tree)
            if row:
                rows.append(row)
        return rows
    
    def start_export(self):
        base_model_obj = self.pool.get(self.base_model_name)
        domain = []
        if base_model_obj._columns.get('active', False) :
            domain.append(('active','in',['True','False']))
        ids = self.id and self.id or base_model_obj.search(self.cr, 1, domain)
        rows = self.make_row(ids, self.entity)
        self.create_csv(rows)
        self.cr.commit()
        self.cr.close()
    
    def __init__(self, db_name, entity_to_export, file_id, row, header, id=False, lang='en_US', separator=',', quote_delimiter='\''):
        self.entity = entity_to_export
        self.base_model_name = self.entity['model']
        self.db_name = db_name
        self.file_id = file_id
        self.header = header
        self.row = row
        self.thread = threading.Thread(target=self.start_export, name='exporter', args=[], kwargs={})
        self.id = id
        self.lang = lang
        self.separator = separator.encode('UTF-8')
        self.quote_delimiter = quote_delimiter.encode('UTF-8')
        
    def start(self):
        self.db, self.pool = pooler.get_db_and_pool(self.db_name)
        self.cr = self.db.cursor()
        self.thread.start()