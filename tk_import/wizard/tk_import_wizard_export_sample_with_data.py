from openerp.tools.translate import _
from openerp.osv import fields, osv
from openerp.addons.tk_import import exporter
import cPickle

class tk_import_wizard_export_sample_with_data(osv.osv_memory):
    _name = 'tk_import.export_sample_with_data'
    
    def __get_available_languages(self, cr, uid, context=None):
        res_lang_obj = self.pool.get('res.lang')
        lang_ids = res_lang_obj.search(cr, uid, [])
        lang_data = res_lang_obj.read(cr, uid, lang_ids, ['name','code'], context)
        return [(lang_info['code'], lang_info['name']) for lang_info in lang_data]
    
    _columns = {
            'name':             fields.char('File name', size=128),
            'import_model_id':  fields.many2one('tk_import.model', 'Import Model'),
            'model_id':         fields.many2one('ir.model', 'Model'),
            'column_ids':       fields.many2many('tk_import.column', 'tk_import_column_to_wizard_with_data', 'wizard_id', 'column_id', 'Columns'),
            'key_ids':          fields.many2many('tk_import.column', 'tk_import_key_to_wizard_with_data', 'wizard_id', 'key_id', 'Columns'),
            'csv':              fields.binary('CSV File'),
            'current_model':    fields.many2one('ir.model', 'Model'),
            'column':           fields.char('Column', size=256),
            'use_id':           fields.boolean('Use database ID to identify the record'),
            'from_other_export':fields.boolean('From Other Export'),
            'import_lang':      fields.selection(__get_available_languages, 'Language'),
            'separator':        fields.char('Separator', size=1),
            'quote_delimiter':  fields.char('Quote Delimiter', size=1)
                }
    
    views = {
        'default':  'export.sample.with.data.view.form',
        'step2':    'export.sample.with.data.view.form.step2',
        'success':  'export.sample.with.data.view.form.success',
        }
    
    relation = ['one2many','many2many','many2one','related']
    
    def get_view_dict(self, cr, uid, ids, view_name, context=None):
        view_name = self.views[view_name]
        message_view_id = self.pool.get('ir.ui.view').search(cr, uid,
            [('name','=', view_name)])
        result_message = {
            'view_type'      : 'form',
            'view_mode'      : 'form',
            'res_model'      : self._name,
            'type'           : 'ir.actions.act_window',
            'context'        : context,
            'view_id'        : message_view_id,
            'target'         : 'new',
            'res_id'         : ids[0],
            }
        return result_message
    
    def get_columns(self, cr, uid, model_obj_name, context=None):
        model_obj = self.pool.get(model_obj_name)
        
        columns = {}
        for column in model_obj._columns:
            columns[column] = model_obj._columns[column]
            
        if model_obj._inherits:
            for parent_model_name in model_obj._inherits.keys():
                columns.update(self.get_columns(cr, uid, parent_model_name))
        return columns
    
    def finish(self, cr, uid, ids, context={}):
        return {
            'type': 'ir.actions.act_window_close'
        }
        
    def make_row(self, cr, uid, ids, context, tree):
        model_name = tree['model']
        column = tree['column']
        fields = tree['fields']
        model_columns = self.get_columns(cr, uid, model_name, context)
        row = {}
        header = []
        for field_name in fields.keys():
            field = fields[field_name]
            if isinstance(field, dict):
                new_row, new_header = self.make_row(cr, uid, ids, context, field)
                row.update(new_row)
                header.extend(new_header)
                continue
            if field_name == '.id':
                header.append(column and (column + '.id') or '.id')
                row[column and (column + '.id') or '.id'] = 'Database ID'
                continue
            else:
                header.append((column and (column + '/') or '') + field_name)                                
            row[column and ((column + '/') + field_name) or field_name] = model_columns[field_name].string
        return row, header
        
    def get_key_values(self, cr, uid, ids, context, tree):
        model_name = tree['model']
        column = tree['column']
        fields = tree['fields']
        model_columns = self.get_columns(cr, uid, model_name, context)
        model_obj = self.pool.get('ir.model')
        keys = []
        for field_name in fields.keys():
            field = fields[field_name]
            if isinstance(field, dict):
                keys.extend(self.get_key_values(cr, uid, ids, context, field))
                continue
            if field:
                model_id = model_obj.search(cr, uid, [('model','=', model_name)])[0]
                key_values = {
                            'column':   column,
                            'model_id': model_id,
                            'name':     field_name,
                              }
                keys.append((0,0,key_values))
        
        return keys
    
    def create_file(self, cr, uid, ids, context=None):
        wizard = self.browse(cr, uid, ids[0])
        file_obj = self.pool.get('tk_import.export_file')
        tree = self.entity_tree[ids[0]]
        
        file_id = file_obj.create(cr, uid, {
                                        'name':             wizard.name + '.csv',
                                        'import_model_id':  wizard.import_model_id.id,
                                        'export_name':      wizard.name,
                                            })
        template_obj = self.pool.get('tk_import.template')
        template_value = {
                        'name':             wizard.name,
                        'import_model_id':  wizard.import_model_id.id,
                        'type':             'export',
                          }
        cr.commit()
        template_value['key_ids'] = self.get_key_values(cr, uid, ids, context, tree)
        template_obj.create(cr, uid, template_value)
        if self.row and self.header:
            row = self.row
            header = self.header
        else:
            row, header = self.make_row(cr, uid, ids, context, tree)
        serialized_data = cPickle.dumps((tree, row, header))
        file_obj.write(cr, uid, [file_id], {'export_params': serialized_data})
        
        exp = exporter.data_exporter(cr.dbname, tree, file_id, row, header, self.id, wizard.import_lang, wizard.separator, wizard.quote_delimiter)
        exp.start()
        return self.get_view_dict(cr, uid, ids, 'success', context)
    
    
    def generate_in_memory_columns(self, cr, uid, id, columns, model_id, context, parent_column=''):
        column_obj = self.pool.get('tk_import.column')
        for column_name in columns.keys():
            column = columns[column_name]
            if isinstance(column, fields.function):
                continue
            existing_columns = column_obj.search(cr, uid, [('name','=',column_name),('model_id','=',model_id),('wizard_id','=',id),('column','=',parent_column)])
            if existing_columns and len(existing_columns)>0 :
                continue

            values = {
                    'name':         column_name,
                    'label':        column.string,
                    'type':         column._type,
                    'required':     column.required and True or False,
                    'readonly':     column.readonly and True or False,
                    'model_id':     model_id,
                    'column':       parent_column,
                    'wizard_id':    id,
                      }
            column_id = column_obj.create(cr, uid, values)
    
    def iterate(self, cr, uid, ids, context=None):
        tree = self.list[ids[0]].pop(0)
        wizard = self.browse(cr, uid, ids[0])
        use_id = wizard.use_id
        model_obj = self.pool.get(tree['model'])
        model_columns = self.get_columns(cr, uid, model_obj._name, context)
        
        #Get the columns
        for column in wizard.column_ids:
            column_info = model_columns[column.name]
            tree['fields'][column.name] = column in wizard.key_ids and not use_id and True or False
            if column_info._type in self.relation:
                subtree = {
                        'model':    column_info._obj,
                        'fields':   {},
                        'column':   (tree['column'] and (tree['column'] + '/') or '') + column.name
                           }
                self.list[ids[0]].insert(0, subtree)
                tree['fields'][column.name] = subtree
        if use_id:
            tree['fields']['.id'] = True
    
        if not self.list[ids[0]]:
            return self.create_file(cr, uid, ids, context)
        
        ir_model_obj = self.pool.get('ir.model')
        new_tree = self.list[ids[0]][0]
        new_columns = self.get_columns(cr, uid, new_tree['model'], context)
        new_model_id = ir_model_obj.search(cr, uid, [('model','=', new_tree['model'])])[0]
        self.generate_in_memory_columns(cr, uid, ids[0], new_columns, new_model_id, context, new_tree['column'])
        self.write(cr, uid, ids, {
                                'current_model':    new_model_id,
                                'column':           new_tree['column'],
                                'column_ids':       [(6, 0, [])],
                                'key_ids':          [(6, 0, [])],
                                'use_id':           False,
                                  })
        return self.get_view_dict(cr, uid, ids, 'step2', context)
    
    
    def prepare_values(self, cr, uid, ids, context=None):
        if self.skip_all:
            self.entity_tree[ids[0]] = self.imported_entity_tree
            return self.create_file(cr, uid, ids, context)
        wizard = self.browse(cr, uid, ids[0])
        ir_model_obj = self.pool.get('ir.model')
        model = wizard.model_id
        model_obj = self.pool.get(model.model)
       
        self.entity_tree[ids[0]] = {
                                    'model':    model_obj._name,
                                    'fields':   {},
                                    'column':   '',
                                    }
        
        self.list[ids[0]] = [self.entity_tree[ids[0]]]
        
        return self.iterate(cr, uid, ids, context)
           

    def prepare_wizard(self, cr, uid, ids, context):
        wizard = self.browse(cr, uid, ids[0])
        columns = self.get_columns(cr, uid, wizard.model_id.model, context)
        self.generate_in_memory_columns(cr, uid, ids[0], columns, wizard.model_id.id, context)
        return self.get_view_dict(cr, uid, ids, 'default', context)
    
    def default_get(self, cr, uid, field_list, context=None):
        res = {}
        if not context:
            return res
        self.entity_tree = {}
        self.id = False
        self.row = False
        self.header = False
        self.skip_all = False
        self.imported_entity_tree = False
        import_model_obj = self.pool.get('tk_import.model')
        model_obj = self.pool.get('ir.model')
        
        if context.get('active_model') == 'tk_import.template':
            model_id = model_obj.search(cr, uid, [('model','=','tk_import.template')])[0]
            import_model_ids = import_model_obj.search(cr, uid, [('model_id','=',model_id)])
            if not import_model_ids:
                import_model_id = import_model_obj.create(cr, uid, {
                                                  'model_id': model_id,
                                                  })
            else:
                import_model_id = import_model_ids[0]
            import_model = import_model_obj.browse(cr, uid, import_model_id, context)
            self.id = context.get('active_id')
        elif context.get('active_model') == 'tk_import.export_file':
            file_obj = self.pool.get('tk_import.export_file')
            file = file_obj.browse(cr, uid, context.get('active_id'))
            import_model_id = file.import_model_id.id
            import_model = file.import_model_id
            self.imported_entity_tree, self.row, self.header = cPickle.loads(str(file.export_params))
            res['from_other_export'] = True
            self.skip_all = True
        else:
            
            ir_model_obj = self.pool.get('ir.model')
            import_model_id = context['active_id']
        
        import_model = import_model_obj.browse(cr, uid, import_model_id, context)
        self.list = {}
        res.update({
                'import_model_id':  import_model_id,
                'model_id':         import_model.model_id.id,
                'current_model':    import_model.model_id.id,
                'column':           '',
                'separator': ',',
                'quote_delimiter': '"'
                    })
        return res
    
tk_import_wizard_export_sample_with_data()