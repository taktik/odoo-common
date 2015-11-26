# coding=utf-8
import csv
import threading
import time
import copy
import types
import logging

from openerp.tools.translate import _
import openerp.pooler as pooler
from openerp.osv import fields, osv

logger = logging.getLogger(__name__)


class data_importer():

    def check_required(self, model_obj, entity, parent, fullname=False):
        if 'id' in entity.keys():
            return
        errors = ''
        model_columns = {}
        inherit_obj = []
        model_columns.update(model_obj._columns)
        for inherit_model_name in model_obj._inherits.keys():
            inherit_model_obj = self.pool.get(inherit_model_name)
            model_columns.update(inherit_model_obj._columns)
            inherit_obj.append(inherit_model_name)
        for field in model_columns.keys():
            if model_columns[field].required:
                parent_objs = []
                if parent:
                    parent_objs.append(parent._name)
                    parent_objs.extend(parent._inherits.keys())
                if model_columns[field]._obj in parent_objs:
                    continue
                if model_columns[field]._obj in inherit_obj:
                    continue
                if field not in entity.keys():
                    if field in model_obj.default_get(self.cr, self.uid, [field]):
                        continue
                    errors += 'Required field "%s" of "%s" is not fill %s !' % (field, model_obj._name, fullname and (', Parent field : ' + fullname) or '')
        if errors:
            self.import_error = True
            raise Exception(errors)

    def get_relation_field(self, field_info, c_id):
        type = field_info._type
        if type == 'many2one':
            return c_id
        elif type == 'related':
            return '%s, %d' % (c_id, field_info._obj)
        elif type == 'one2many':
            return [(4, c_id)]
        elif type == 'many2many':
            return [(4, c_id)]

    def get_new_relation_field(self, field_info, values):
        type = field_info._type
        model_obj = self.pool.get(field_info._obj)
        c_id = model_obj.create(self.cr, self.uid, values, {'import': True, 'lang': self.lang})
        if type == 'many2one':
            return c_id
        elif type == 'one2many':
            return [(4, c_id)]
        elif type == 'many2many':
            return [(4, c_id)]

    def convert_value(self, model_obj, field_info, value):
        converted_value = value
        field_type = field_info._type
        if field_type == 'float':
            converted_value = float(value)
        elif field_type == 'integer':
            converted_value = int(value)
        elif field_type == 'boolean':
            if value in ['true', 'True', 1]:
                converted_value = True
            elif value in ['false', 'False', 0]:
                converted_value = False
        elif field_type == 'selection':
            selection = field_info.selection
            if isinstance(selection, types.FunctionType):
                selection = field_info.selection.__call__(model_obj, self.cr, self.uid, {})
            for selection_item in selection:
                if value == selection_item[1]:
                    converted_value = selection_item[0]

        return converted_value

    def make_human_readable_domain(self, domain):
        if not len(domain):
            return ''
        readable_domain = '%s %s %s' % (domain[0][0], domain[0][1], domain[0][2])
        for condition in domain[1:]:
            readable_domain += ' AND %s %s %s' % (condition[0], condition[1], condition[2])
        return readable_domain

    def treat_subtree(self, tree, model_obj, fullname, row, line_number, parent=False):
        model_columns = {}
        model_columns.update(model_obj._columns)
        parent_field = fullname
        model_id = self.pool.get('ir.model').search(self.cr, self.uid, [
            ('model', '=', model_obj._name)])[0]
        if fullname.count('/'):
            parent_fields = fullname.split('/')
            parent_field = parent_fields[len(parent_fields) - 1:][0]
        if model_obj._inherits and model_obj._inherits.keys():
            for key in model_obj._inherits.keys():
                other_model_obj = self.pool.get(key)
                model_columns.update(other_model_obj._columns)
        entity = {}

        tree = copy.deepcopy(tree)

        error = False
        error_message = ''
        for field in tree.keys():
            if field == '.id':
                field = 'id'
            separator = field == 'id' and '.' or '/'
            new_fullname = fullname and (fullname + separator + field) or (field == 'id' and '.id' or field)
            if tree.get(field, False):
                try:
                    new_model_obj = self.pool.get(model_columns[field]._obj)
                    sub_entity = self.treat_subtree(tree[field], new_model_obj, new_fullname, row, line_number, model_obj)
                    if isinstance(sub_entity, bool) and sub_entity is False:
                        continue
                    elif isinstance(sub_entity, int) or isinstance(sub_entity, long):
                        entity[field] = self.get_relation_field(model_columns[field], sub_entity)
                    else:
                        entity[field] = self.get_new_relation_field(model_columns[field], sub_entity)
                except Exception, message:
                    logger.debug(message)
                    error_message = '%s, %s' % (error_message, message)
                    error = True
            else:
                if not row[new_fullname]:
                    continue
                field_info = model_columns.get(field, False)
                if field == 'id':
                    entity[field] = row[new_fullname]
                else:
                    entity[field] = self.convert_value(model_obj, field_info, row[new_fullname])
        if not entity:
            return False
        if error:
            self.import_error = True
            raise Exception(error_message)
        
        # update avec id
        if '.id' in tree.keys():
            del tree['.id']
            c_id = False
            for key in row.keys():
                if fullname and '.id' in key and fullname in key:
                    c_id = row['.id' in fullname and fullname or (fullname + '.id')]
                    break
            if not c_id:
                c_id = row['.id']
            ids = model_obj.search(self.cr, self.uid, [('id', '=', c_id)])
            if not ids or len(ids) > 1:
                self.import_error = True
                raise Exception("Il n'existe pas de %s avec l'id %s" % (model_obj._name, c_id))
            self.entities_to_update.setdefault(model_id, {}).setdefault(c_id,
                                                                        []).append(
                entity)
            return int(c_id)
        # update
        elif (self.update or self.update_strict) and model_id in self.keys and fullname in self.keys[model_id]:
            keys = self.keys[model_id][fullname]
            domain = []
            active_clause = ('active', 'in', ['True', 'False'])
            for key in keys:
                field_info = model_columns[key]
                field = key
                new_fullname = fullname and (fullname + '/' + field) or field
                domain.append((field, '=', self.convert_value(model_obj, field_info, row[new_fullname])))
            if 'active' in model_columns:
                domain.append(active_clause)
            ids = model_obj.search(self.cr, self.uid, domain)
            if len(ids) > 1:
                self.import_error = True
                raise Exception('The system was not able to find a unique "%s" with the selected keys. Domain was : %s' % (model_obj._name, self.make_human_readable_domain(domain)))
            elif not len(ids):
                if self.update_strict:
                    self.log_error(line_number, 'The system was not able to find a %s to update' % model_obj._name)
                try:
                    self.check_required(model_obj, entity, parent, fullname)
                except Exception, message:
                    self.import_error = True
                    raise Exception(message)
                return entity
            else:
                self.entities_to_update.setdefault(model_id, {}).setdefault(
                    ids[0], []).append(entity)
                return int(ids[0])
        # create
        else:
            try:
                self.check_required(model_obj, entity, parent)
            except Exception, message:
                self.errors = True
                raise Exception(message)
            return entity

    def import_row(self, row, line_number):
        domain = []
        for key in self.keys.get(self.model_id, {}).get('', {}):
            value = row[key]
            if key == '.id':
                key = 'id'
            domain.append((key, '=', value))
        self.import_error = False
        entity = self.treat_subtree(self.tree, self.model_obj, '', row, line_number)
        if isinstance(entity, int) or isinstance(entity, long):
            return
        if self.import_error:
            self.errors = True
        if domain:
            ids = self.model_obj.search(self.cr, self.uid, domain)
            if len(ids) > 1:
                self.log_error(line_number, 'Unable to identify formally %s' % self.model_obj._name)
            elif len(ids) == 1:
                return
            else:
                if not self.update_strict:
                    if not self.import_error:
                        self.model_obj.create(self.cr, self.uid, entity,
                                              {'import': True,
                                               'lang': self.lang})
                else:
                    self.log_error(line_number, 'The system was not able to find a %s to update' % self.model_obj._name)
        else:
            if not self.import_error:
                self.model_obj.create(self.cr, self.uid, entity,
                                      {'import': True, 'lang': self.lang})

    def print_tree(self, tree, rank=0):
        for key in tree.keys():
            print '%s%s' % (rank * '\t', key)
            if tree[key]:
                self.print_tree(tree[key], rank+1)

    def log_error(self, line_number, message):
        self.log.append('Line % 5d : %s' % (line_number, message))

    def write_errors(self, logical_file):
        ir_config_parameter_obj = self.pool.get('ir.config_parameter')
        import_path = ir_config_parameter_obj.get_param(self.cr, self.uid, 'tk_import_path_parameter', False)
        if not import_path:
            logger.error("No import_path defined (config_parameter tk_import_path_parameter)")
            return False
        error_file_path = import_path + '/' + logical_file.file + '_error.txt'
        error_file = open(error_file_path, 'wb')
        for error in self.log:
            error_file.write(error + '\n')
        error_file.flush()
        error_file.close()

    def update_records(self):
        if self.errors and not self.ignore_errors:
            return False
        model_obj = self.pool.get('ir.model')
        progress = self.progress
        progress_to_go = 100 - self.progress
        percent_per_entities = float(progress_to_go) / float(self.number_of_entities)
        for model_id in self.entities_to_update.keys():
            current_model = model_obj.browse(self.cr, self.uid, model_id)
            current_model_obj = self.pool.get(current_model.model)
            for c_id in self.entities_to_update[model_id].keys():
                progress = progress + percent_per_entities
                while progress >= self.progress and self.progress < 100:
                    self.progress += 1
                    self.log_progress(self.progress)
                for values in self.entities_to_update[model_id][c_id]:
                    try:
                        current_model_obj.write(self.cr, self.uid, [int(c_id)], values, {'lang': self.lang})
                    except Exception, e:
                        self.errors = True
                        self.log_error(self.i, "Error : %s / Model : %s / Values : %s" % (e, current_model_obj._name, values))
        return self.errors

    def finish(self, logical_file):
        file_obj = self.pool.get('tk_import.file')
        if not self.errors:
            file_obj.write(self.progress_cr, self.uid, self.logical_file_id, {'state':  'processed', 'errors': 0})
            self.progress_cr.commit()
            self.cr.commit()
        else:
            if not self.ignore_errors:
                self.cr.rollback()
            self.write_errors(logical_file)
            file_obj.write(self.progress_cr, self.uid, self.logical_file_id, {'state':  'error', 'errors': len(self.log), 'name': logical_file.import_name + '_error.txt'})
            self.progress_cr.commit()
            self.cr.commit()
        self.cr.close()
        self.progress_cr.close()

    # log progress has to be done in a separated thread because of the transaction
    def log_progress(self, progress):
        file_obj = self.progress_pool.get('tk_import.file')
        file_obj.write(self.progress_cr, self.uid, self.logical_file_id, {'progress': progress})
        logger.info("Importing %s%%" % self.progress)
        self.progress_cr.commit()

    def start_import(self):
        time.sleep(3)
        self.db, self.pool = pooler.get_db_and_pool(self.db_name)
        self.cr = self.db.cursor()
        self.errors = False
        self.log = []

        self.progress_db, self.progress_pool = pooler.get_db_and_pool(self.db_name)
        self.progress_cr = self.progress_db.cursor()

        user_obj = self.pool.get('res.users')
        ir_config_parameter_obj = self.pool.get('ir.config_parameter')
        import_path = ir_config_parameter_obj.get_param(self.cr, self.uid, 'tk_import_path_parameter', False)
        if not import_path:
            logger.error("No import_path defined (config_parameter tk_import_path_parameter)")
            return False

        file_obj = self.pool.get('tk_import.file')
        logical_file = file_obj.browse(self.cr, self.uid, self.logical_file_id)
        number_of_record = logical_file.lines

        self.model_obj = self.pool.get(logical_file.model_id.model)
        self.model_id = logical_file.model_id.id
        # self.product_tmpl_columns = self.pool.get('product.template')._columns.keys()
        file_path = import_path + '/' + logical_file.file

        file = open(file_path, 'rb')
        dict_reader = csv.DictReader(file, delimiter=self.separator, quotechar=self.quote_delimiter)

        self.cr.autocommit(False)

        if self.ignore_errors:
            self.cr.autocommit(True)

        file_obj.write(self.cr, self.uid, self.logical_file_id, {'state':  'processing'})
        self.cr.commit()

        self.i = 0
        self.progress = 0
        # Compute the number of steps possible
        # Round to the superior multiple of 20
        steps = number_of_record / 20
        if steps * 20 < number_of_record:
            steps += 1
        for row in dict_reader:
            try:
                self.i += 1
                if self.i % steps == 0:
                    self.progress += 5
                    self.log_progress(self.progress)
                self.import_row(row, self.i)
            except Exception, e:
                self.errors = True
                self.log_error(self.i, e)

        if self.entities_to_update:
            self.number_of_entities = reduce(lambda x, y: x+y, [len(self.entities_to_update[entity]) for entity in self.entities_to_update.keys()])
            self.number_of_records = number_of_record + self.number_of_entities
        else:
            self.number_of_entities = 1
            self.number_of_records = number_of_record
        # compute new progress
        self.steps = self.number_of_records / 20
        if self.steps * 20 != self.number_of_records:
            self.steps += 1
        self.progress = (float(self.i) / float(self.number_of_records)) * 100
        self.progress = int(self.progress)
        # if progress is not a multiple of 5, set to the superior multiple of 5
        if self.progress % 5 != 0:
            self.progress = ((self.progress / 5) + 1) * 5
        self.log_progress(self.progress)
        self.update_records()
        self.finish(logical_file)

        return

    def __init__(self, db_name, uid, logical_file_id, keys, tree, update, update_strict, ignore_errors=None, import_lang='en_US', separator=',', quote_delimiter='\''):
        self.logical_file_id = logical_file_id
        self.db_name = db_name
        self.uid = uid
        self.keys = keys
        self.entities_to_update = {}
        self.tree = tree
        self.new_entities = {}
        self.update = update
        self.update_strict = update_strict
        self.ignore_errors = ignore_errors or False
        self.thread = threading.Thread(target=self.start_import, name='importer', args=[], kwargs={})
        self.lang = import_lang
        self.separator = separator.encode('UTF-8')
        self.quote_delimiter = quote_delimiter.encode('UTF-8')

    def start(self):
        self.thread.start()
