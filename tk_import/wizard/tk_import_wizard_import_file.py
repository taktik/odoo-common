# coding=utf-8
from openerp.tools.translate import _
from openerp.osv import fields, osv
from openerp.addons.tk_import import importer

import threading
import base64
import csv
import cStringIO
import copy
import logging

logger = logging.getLogger(__name__)


class import_field(osv.osv_memory):
    _name = 'tk_import.field'
    
    _rec_name = 'label'

    _columns = {
        'name':             fields.char('Name', size=64),
        'model_id':         fields.many2one('ir.model', 'Model'),
        'label':            fields.char('Label', size=256),
        'column':           fields.char('Column', size=1024),
    }

import_field()


class import_file(osv.osv_memory):
    _name = 'tk_import.import_file'

    __types = [('csv', 'CSV File'), ('txt', 'Text File'), ('unknown', 'Unknown')]
    
    def __get_available_languages(self, cr, uid, context=None):
        res_lang_obj = self.pool.get('res.lang')
        lang_ids = res_lang_obj.search(cr, uid, [])
        lang_data = res_lang_obj.read(cr, uid, lang_ids, ['name', 'code'], context)
        return [(lang_info['code'], lang_info['name']) for lang_info in lang_data]
    
    _columns = {
        'file':             fields.binary('File to import', required=True),
        'model_id':         fields.many2one('ir.model', 'Model', required=True),
        'import_name':      fields.char('Filename', size=128, required=True),
        'error_report':     fields.binary(string='Error Report', readonly=True),
        'name':             fields.char('Report Name', size=64),
        'update':           fields.boolean('Update', help='If "Update" is chosen, the system will update the already existing records and create the others. If not, the system will only create new record even if there is existing ones'),
        'update_strict':    fields.boolean('Update Strict'),
        'current_model':    fields.many2one('ir.model', 'Current Model'),
        'current_column':   fields.char('Column', size=1024),
        'available_keys':   fields.many2many('tk_import.field', 'tk_import_field_av_to_wizard', 'wizard_id', 'field_id', string='Available Keys'),
        'selected_keys':    fields.many2many('tk_import.field', 'tk_import_field_sel_to_wizard', 'wizard_id', 'field_id', string='Selected Keys'),
        'progress':         fields.integer('%'),
        'type':             fields.selection(__types, 'Type'),
        'import_model_id':  fields.many2one('tk_import.model', 'Import Model'),
        'template_id':      fields.many2one('tk_import.template', 'Template', help='You can use a predefined binding or define a new one at the end of the wizard.'),
        'save_template':    fields.boolean('Save template'),
        'template_name':    fields.char('Name', size=128),
        'import_file_id':   fields.many2one('tk_import.file', 'Import File'),
        'import_from_file': fields.boolean('Import from file'),
        'ignore_errors':    fields.boolean('Ignore errors (Import anyway)'),
        'import_lang':      fields.selection(__get_available_languages, 'Language'),
        'separator':        fields.char('Separator', size=1),
        'quote_delimiter':  fields.char('Quote Delimiter', size=1)
        }

    error_types = {
        'rel':      'Relational Field not precisely defined : ',
        'required': 'Required fields missing : ',
        'fct':      'Function fields with no way to set value :',
        'notin':    'Fields not existing :'
    }

    views = {
        'default':  'file.importer.view',
        'step2':    'file.importer.view_step2',
        'success':  'file.importer.view_success',
        'failure':  'file.importer.view_failure',
        'resume':   'file.importer.view_resume',
        }

    def default_get(self, cr, uid, field_list, context={}):
        res = {
            'update': True,
            'progress': 0,
            'separator': ',',
            'quote_delimiter': '"'
        }
        if not context:
            return res
        active_model = context.get('active_model')
        if active_model == 'tk_import.file':
            file_id = context.get('active_id')
            file = self.pool.get(active_model).browse(cr, uid, file_id)
            res.update({
                'model_id': file.model_id.id,
                'import_model_id': file.import_model_id.id,
                'template_id': file.template_id.id,
                'import_from_file': True,
                'update': file.update,
                'update_strict': file.update_strict,
            })
            
        elif active_model == 'tk_import.model':
            # Get the model_id from context using active_model and active_id$
            import_model = self.pool.get(context['active_model']).browse(cr, uid, context['active_id'])
            res['model_id'] = import_model.model_id.id
            res['import_model_id'] = import_model.id
        return res
    
    def on_change_file(self, cr, uid, ids, file, context=None):
        value = {}
        warning = {}
        file_name = file
        extension = file[file.rfind('.'):]
        if extension == '.csv':
            file_name = file[:-4]
            type = 'csv'
        else:
            type = 'unknown'
            warning['title'] = 'File format not supported'
            warning['message'] = 'The file format you choose seems not to be supported (%s). Please note that this check is based on the file extension.' % extension
            
        value['import_name'] = file_name
        value['type'] = type

        return {
            'value': value,
            'warning': warning
        }

    def get_view_dict(self, cr, uid, ids, view_name, context=None):
        message_view_id = self.pool.get('ir.ui.view').search(cr, uid,
                                                             [('name', '=',
                                                               view_name), (
                                                              'model', '=',
                                                              self._name)])
        result_message = {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': self._name,
            'type': 'ir.actions.act_window',
            'context': context,
            'view_id': message_view_id,
            'target': 'new',
            'res_id': ids[0],
        }
        return result_message

    def write_errors(self, cr, uid, ids):
        log = ''
        for entity in self.errors.keys():
            log += '%s\n' % entity
            for error_type in self.errors[entity]:
                log += '\t%s\n' % self.error_types[error_type]
                for error in self.errors[entity][error_type]:
                    log += '\t\t%s\n' % error
        log_error = base64.encodestring(log)
        self.write(cr, uid, ids, {'error_report': log_error, 'name': self.name + '_error.txt'})

    def write_file_and_record(self, cr, uid, wizard):
        file_obj = self.pool.get('tk_import.file')
        user_obj = self.pool.get('res.users')
        values = {
            'import_name':      wizard.import_name,
            'import_model_id':  wizard.import_model_id.id,
            'size':             len(self.file_content),
            'lines':            len(self.file_content.splitlines()) - 1,
            'template_id':      wizard.template_id and wizard.template_id.id or False,
            'update':           wizard.update,
            'update_strict':    wizard.update_strict,
            }
        logical_file_id = file_obj.create(cr, uid, values)
        if not logical_file_id:
            raise osv.except_osv(_('Error!'),
                                 _(
                                     'There was a problem while creating '
                                     'the import, please try again.'))

        logical_file = file_obj.browse(cr, uid, logical_file_id)
        ir_config_parameter_obj = self.pool.get('ir.config_parameter')
        import_path = ir_config_parameter_obj.get_param(cr, uid, 'tk_import_path_parameter', False)
        if not import_path:
            logger.error("No import_path defined (config_parameter tk_import_path_parameter)")
            return False

        file_path = import_path + '/' + logical_file.file

        f = open(file_path, 'wb')
        f.write(self.file_content)
        f.flush()
        f.close()

        self.write(cr, uid, [wizard.id], {
            'import_file_id': logical_file_id
        })

    def log(self, entity, type, error_message):
        if entity not in self.errors:
            self.errors[entity] = {}
        if type not in self.errors[entity]:
            self.errors[entity][type] = []
        self.errors[entity][type].append(error_message)

    def decompose_column(self, tree, columns):
        field = columns[0]
        if field != '.id' and field.count('.id'):
            field = field[:len(field)-3]
            columns.append('.id')
        if field not in tree:
            tree[field] = {}
        if len(columns) <= 1:
            tree[field] = False
            return
        self.decompose_column(tree[field], columns[1:])

    def create_entity_tree(self, file_column_names):
        tree = {}
        for column in file_column_names:
            if column == 'id':
                tree['.id'] = False
            elif column.count('/'):
                subcolumns = column.split('/')
                self.decompose_column(tree, subcolumns)
            elif column.count('.id'):
                self.decompose_column(tree, [column])
            else:
                tree[column] = False
        return tree
    
    def check_field_existence(self, cr, uid, tree, field, model_columns, model_columns_names, model_obj, hierarchy):
        relations = ['many2one', 'many2many', 'one2many', 'related']
        res = False
        if field == '.id':
            pass
        elif field not in model_columns_names:
            self.log(model_obj._name, 'notin', field)
            pass
        elif tree[field]:
            submodel_obj = self.pool.get(model_columns[field]._obj)
            res = {}
            res['model'] = submodel_obj
            res['value'] = self.validate_tree(cr, uid, submodel_obj, tree[field], hierarchy)
            pass
        elif model_columns[field]._type in relations and not tree[field]:
            self.log(model_obj._name, 'rel', field)
            pass
        return res
    
    def get_model_columns(self, cr, uid, model_obj):
        model_columns = {}
        model_columns.update(model_obj._columns)
        if model_obj._inherits and model_obj._inherits.keys():
            for key in model_obj._inherits.keys():
                other_model_obj = self.pool.get(key)
                model_columns.update(other_model_obj._columns)
        return model_columns
    
    def validate_tree(self, cr, uid, model_obj, tree, hierarchy=[]):
        entities = {}
        model_columns = self.get_model_columns(cr, uid, model_obj)
                
        model_columns_names = model_columns.keys()
        
        field_obj = self.pool.get('tk_import.field')
        
        model_id = self.pool.get('ir.model').search(cr, uid, [('model', '=', model_obj._name)])[0]
        
        # Validate fields existence
        for field in tree.keys():
            new_hierarchy = copy.copy(hierarchy)
            new_hierarchy.append(model_obj)
            field_info = self.check_field_existence(cr, uid, tree, field, model_columns, model_columns_names, model_obj, new_hierarchy)
            entities[field] = field_info

        # Validate required constraint
        tree_columns = tree.keys()
        for field in model_columns_names:
            field_info = model_columns[field]
            if not field_info.required or field_info._obj in hierarchy or self.update:
                continue
            if field not in tree_columns:
                self.log(model_obj._name, 'required', field)
                continue
        return entities

    def check_file(self, cr, uid, ids):
        wizard = self.browse(cr, uid, ids[0])
        file = cStringIO.StringIO(self.file_content)
        csv.register_dialect('used_for_import', delimiter=wizard.separator.encode('UTF-8'), quotechar=wizard.quote_delimiter.encode('UTF-8'))
        reader = csv.DictReader(file, dialect='used_for_import')
        # first next() to get columns
        reader.next()

        file_column_names = reader.fieldnames
        self.errors = {}

        self.tree = self.create_entity_tree(file_column_names)
        root = {}
        root['model'] = self.model
        root['value'] = self.validate_tree(cr, uid, self.model, self.tree)
        self.entities = {'': root}
    
    def generate_fields_and_flat_tree(self, cr, uid, ids, tree, path=''):
        field_obj = self.pool.get('tk_import.field')
        base_model_obj = self.pool.get('ir.model')
        model_columns = {}
        model_obj = tree.get('model')
        if not model_obj:
            self.log(model_obj, '', ' %s not found.' % path)
            return
        model_columns = self.get_model_columns(cr, uid, model_obj)
        entity_values = tree.get('value', {})
        for key in entity_values.keys():
            entity = entity_values[key]
            # is a relation, so make a field for each son if it is not a relation too
            if entity and entity.get('model', False):
                new_path = path and path + '/' + key or key
                model_id = base_model_obj.search(cr, uid, [('model', '=', entity_values[key]['model']._name)])[0]
                self.list.append((model_id, new_path))
                isId = '.id' in entity['value']
                if isId:
                    self.generate_fields_and_flat_tree(cr, uid, ids, {'.id': False}, new_path)
                else:
                    self.generate_fields_and_flat_tree(cr, uid, ids, entity_values[key], new_path, )
            # is a simple field
            else:
                model_id = base_model_obj.search(cr, uid, [('model', '=', model_obj._name)])[0]
                label = (key != '.id') and hasattr(model_columns[key], 'string') and model_columns[key].string or ''
                values = {
                    'name': key,
                    'label': label,
                    'column': path or '/',
                    'model_id': model_id
                }
                field_obj.create(cr, uid, values)
                self.flat_tree.setdefault(model_id, {}).setdefault(path, []).append(values)
                
    def apply_template(self, cr, uid, ids):
        wizard = self.browse(cr, uid, ids[0])
        
        template = wizard.template_id
        
        field_obj = self.pool.get('tk_import.field')
        
        keys = []
        
        for key in template.key_ids:
            model_id = key.model_id and key.model_id.id
            column = key.column
            name = key.name

            field_ids = field_obj.search(cr, uid, [('model_id', '=', model_id),
                                                   ('column', '=', column),
                                                   ('name', '=', name)])
            if field_ids and len(field_ids) == 1:
                keys.append(field_ids[0])
            elif field_ids and len(field_ids) > 1:
                keys.extend(field_ids)

        self.write(cr, uid, [wizard.id], {
            'selected_keys': [(6, 0, keys)]
        })

    def import_file(self, cr, uid, ids, context={}):
        for thread in threading.enumerate():
            if thread.getName() == 'importer':
                raise osv.except_osv(_('Error!'), _('There is already an import job running. Please wait for it to terminate before trying to import again.'))
                return
        ids_to_erase = self.pool.get('tk_import.field').search(cr, uid, [])
        self.pool.get('tk_import.field').unlink(cr, uid, ids_to_erase)
        wizard = self.browse(cr, uid, ids[0])
        self.update = wizard.update
        self.update_strict = wizard.update_strict
        self.ignore_errors = wizard.ignore_errors
        self.file_content = base64.decodestring(wizard.file)
        self.name = wizard.import_name
        self.model = self.pool.get(wizard.model_id.model)
        self.model_id = wizard.model_id.id
        self.keys = {}
        self.position = 0
        self.check_file(cr, uid, ids)
        self.flat_tree = {}
        self.list = []
        if self.errors.keys():
            self.write_errors(cr, uid, ids)
            view = self.views['failure']
            return self.get_view_dict(cr, uid, ids, view, context)
        self.list.append((self.model_id, ''))
        self.generate_fields_and_flat_tree(cr, uid, ids, self.entities[''])
        if not wizard.template_id:
            field_obj = self.pool.get('tk_import.field')
            keys = []
            not_selected_entities = []
            for entity in self.list:
                model_id = entity[0]
                model_name = entity[1]
                if model_id in self.flat_tree:
                    key_added = False
                    # TODO : verify that generate_fields_and_flat_tree was successful
                    for column_dico in self.flat_tree[model_id][model_name]:
                        if column_dico['name'] == '.id':
                            column = column_dico['column']
                            name = column_dico['name']
                            field_ids = field_obj.search(cr, uid, [
                                ('model_id', '=', model_id),
                                ('column', '=', column), ('name', '=', name)])
                            if field_ids and len(field_ids) == 1:
                                keys.append(field_ids[0])
                            elif field_ids and len(field_ids) > 1:
                                keys.extend(field_ids)
                            key_added = True
                    if not key_added:
                        not_selected_entities.append(entity)
            self.list = not_selected_entities

            self.write(cr, uid, [wizard.id], {
                'selected_keys': [(6, 0, keys)]
            })
                        
        view = self.views['step2']
        progress = round(100 / ((len(self.list) - self.position) or 1))
        if self.list:
            self.write(cr, uid, ids, {'current_model': self.list[self.position][0], 'progress': progress, 'current_column': self.list[self.position][1] or '/'})
        else:
            self.write(cr, uid, ids, {'progress': progress})
        if wizard.template_id:
            self.apply_template(cr, uid, ids)
            self.position = len(self.list)
            progress = 100
            self.write(cr, uid, ids, {'current_model': self.list[-1][0], 'progress': progress, 'current_column': self.list[-1][1]})
        if progress >= 100 and (wizard.template_id or not self.list):
            view = self.views['resume']
        
        return self.get_view_dict(cr, uid, ids, view, context)

    def start_thread(self, cr, uid, ids):
        wizard = self.browse(cr, uid, ids[0])
        data_importer = importer.data_importer(cr.dbname, uid, wizard.import_file_id.id, self.keys, self.tree, self.update, self.update_strict, self.ignore_errors, wizard.import_lang, wizard.separator, wizard.quote_delimiter)
        data_importer.start()
        return

    def iterate(self, cr, uid, ids, context=None):
        wizard = self.browse(cr, uid, ids[0])
        field_obj = self.pool.get('tk_import.field')
        current_model_id, column = self.list[self.position]
        label = self.flat_tree[current_model_id][column]
        if not column:
            column = '/'
        # Retrieve keys if they already exists
        previous_keys = []
        for field in wizard.selected_keys:
            if field.column == column and field.model_id.id == current_model_id:
                previous_keys.append(field.id)
            
        new_model_name = self.pool.get('ir.model').browse(cr, uid, current_model_id).model

        values = {
            'current_model': current_model_id,
            'current_column': column,
            'progress': (self.position + 1) * (100 / (len(self.list)) or 1),
        }
        
        if previous_keys:
            values['available_keys'] = [(6, 0, previous_keys)]
        
        new_model_obj = self.pool.get(new_model_name)
        related_fields = field_obj.search
        self.write(cr, uid, ids, values)

        return self.get_view_dict(cr, uid, ids, self.views['step2'], context)

    def previous_step(self, cr, uid, ids, context={}):
        if not self.list:
            raise Exception("Sorry, the id's are already specified as keys so you can not chose another key.")
        self.position -= 1
        return self.iterate(cr, uid, ids, context)

    def save_template(self, cr, uid, ids):
        wizard = self.browse(cr, uid, ids[0])
        template_name = wizard.template_name
        template_import = wizard.import_model_id.id
        
        import_model_obj = self.pool.get('tk_import.model')

        template_value = {
            'name': template_name,
            'import_id': template_import
        }
        keys = []
        for key in wizard.selected_keys:
            key_value = {
                'name': key.name,
                'model_id': key.model_id and key.model_id.id,
                'column': key.column
            }
            keys.append((0, 0, key_value))
        template_value.update({
            'key_ids': keys
        })
        import_model_obj.write(cr, uid, [template_import], {
            'template_ids': [(0, 0, template_value)],
        })
    
    def generate_keys(self, cr, uid, wizard):
        keys = {}
        for key in wizard.selected_keys:
            column = key.column
            if key.column == '/':
                column = ''
            keys.setdefault(key.model_id.id, {}).setdefault(column, []).append(
                key.name)
        return keys
            
    def next_step(self, cr, uid, ids, context=None):
        wizard = self.browse(cr, uid, ids[0])
        self.write_file_and_record(cr, uid, wizard)
        if wizard.save_template:
            self.save_template(cr, uid, ids)
            
        self.keys = self.generate_keys(cr, uid, wizard)
            
        return self.get_view_dict(cr, uid, ids, self.views['success'], context)
            
    def refresh_list(self, cr, uid, ids):
        wizard = self.browse(cr, uid, ids[0])
        
        keys = []
        
        model_id = wizard.current_model.id
        column = wizard.current_column
        
        for field in wizard.available_keys:
            keys.append(field.id)
        
        keys_to_remove = []
        for field in wizard.selected_keys:
            if field.model_id.id == model_id and field.column == column:
                keys_to_remove.append(field.id)
        
        all_keys = [key.id for key in wizard.selected_keys]

        self.write(cr, uid, [wizard.id], {
            'available_keys': [(6, 0, [])],
        })
        all_keys.extend(keys)
        for id in keys_to_remove:
            all_keys.remove(id)
        self.write(cr, uid, [wizard.id], {
            'selected_keys': [(6, 0, all_keys)],
        })
        
    # Increment the position in the entity list.
    # At the end, compute the resume
    def next(self, cr, uid, ids, context={}):
        self.refresh_list(cr, uid, ids)
        if self.position < len(self.list) - 1:
            self.position += 1
            return self.iterate(cr, uid, ids, context)
        return self.get_view_dict(cr, uid, ids, self.views['resume'], context)
    
    def previous(self, cr, uid, ids, context={}):
        self.refresh_list(cr, uid, ids)
        if self.position > 0:
            self.position -= 1
        return self.iterate(cr, uid, ids, context)

    def finish(self, cr, uid, ids, context={}):
        self.start_thread(cr, uid, ids)
        return {
            'type': 'ir.actions.act_window_close'
        }

import_file()
