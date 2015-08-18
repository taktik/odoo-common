# -*- coding: utf-8 -*-
##############################################################################
#
# Authors: Lefever David
# Copyright (c) 2015 Taktik SA/NV (http://www.taktik.be)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from StringIO import StringIO
import logging
from datetime import datetime
from openerp import pooler
import traceback
import re
import simplejson
from tk_exceptions import DoNotAddTagInTreeException, ModelNotFoundException, PatternNotFoundException, CriticalException

logger = logging.getLogger(__name__)

try:
    from lxml import etree

    print("running with lxml.etree")
except ImportError:
    try:
        # Python 2.5
        import xml.etree.cElementTree as etree

        print("running with cElementTree on Python 2.5+")
    except ImportError:
        try:
            # Python 2.5
            import xml.etree.ElementTree as etree

            print("running with ElementTree on Python 2.5+")
        except ImportError:
            try:
                # normal cElementTree install
                import cElementTree as etree

                print("running with cElementTree")
            except ImportError:
                try:
                    # normal ElementTree install
                    import elementtree.ElementTree as etree

                    print("running with ElementTree")
                except ImportError:
                    print("Failed to import ElementTree from any known place")


class serializer:
    def __init__(self, cr, uid, pool, pattern_id=None, xml=None, add_tag_if_empty=True, additional_values=None):
        self.cr = cr
        self.uid = uid
        self.pool = pool
        self.pattern_id = pattern_id
        self.master_json_pattern = None
        self.xml = xml
        self.model_name = None
        self.add_tag_if_empty = add_tag_if_empty

        # Additional_values is a dictionary passed as parameter containing
        # predefined values for some fields.
        # This dictionary is also completed with some hooks called before deserializing.
        self.additional_values = additional_values or {}

        # If we have declared a "multi":"True" on of of the fields of the pattern,
        # this will create multiple documents at once.
        self.multi_documents = None

        # Stack will contain the absolute paths with their xml part as we advance in the
        # deserialization.
        # It will be used to find values for xpaths located anywhere in the XML (not at the 'right' place)
        self.deserialize_stack = {}

        # Created entities ids
        self.created_ids = []

    @staticmethod
    def fill_tree(root, xml_xpath):
        # Adds the specified xml_xpath in the xml (root) if not already present
        el = root.find(xml_xpath)
        if el is None:
            for sub_path in xml_xpath.split("/"):
                if root.find(".//%s" % sub_path) is None:
                    attrs = {}
                    if '[@' in sub_path:
                        # The xpath has attributes with values, i.e
                        # line[@name='test']
                        # This will produce <line name='test'/>
                        m = re.search('(.*)(\[@.*\])(.*)', sub_path)
                        if m and m.groups() and len(m.groups()) == 3:
                            sub_path = m.groups()[0]
                            attrs_group = m.groups()[1]  # Get only [@name='test']
                            if attrs_group and len(attrs_group) > 0:
                                attrs_group = attrs_group[1:-1]  # @name='test'
                                attr_value = re.search('@(.*)=(?:\'|")(.*)(?:\'|")', attrs_group)  # ('name', 'test')
                                if attr_value and attr_value.groups() and len(attr_value.groups()) > 0:
                                    attrs[attr_value.groups()[0]] = attr_value.groups()[1]

                    logger.debug("%s not found, adding to %s" % (sub_path, root))
                    root = etree.SubElement(root, sub_path)
                    for attr, attr_value in attrs.iteritems():
                        root.set(attr, attr_value)
                else:
                    root = root.find(sub_path)

    @staticmethod
    def get_el_path(element):
        # Reconstruct the complete xml xpath of an element by concatenating the xpath of its parents
        path = element.tag
        for parent in element.iterancestors():
            path = parent.tag + '/' + path
        return path

    @staticmethod
    def strip_root_from_xpath(root, xpath):
        # Removes the root tag from the passed xpath
        if xpath.find(root.tag + '/') == 0:
            return xpath[len(root.tag) + 1:]
        if xpath.endswith('/') and len(xpath) > 0:
            xpath = xpath[:-1]  # Remove trailing /
        return xpath

    @staticmethod
    def sort_by_length(word1, word2):
        return len(word1) - len(word2)

    def _call_hook(self, model_name, hook_name, **kwargs):
        """
        Generic method to call hooks on the tk.xml.hooks (e.g. before_deserialize or before_create_entity)
        @param model_name: the name of the current model being treated
        @param hook_name: the name of the hook
        @param kwargs: the keyword args to be passed to the hook method
        @return:
        """
        try:
            self.pool.get('tk.xml.hooks').__getattribute__(hook_name)
            if callable(self.pool.get('tk.xml.hooks').__getattribute__(hook_name)):
                res = getattr(self.pool.get('tk.xml.hooks'), hook_name)(self.cr, self.uid, model_name, additional_values=self.additional_values, **kwargs)
                return res
        except DoNotAddTagInTreeException, e:
            # If it is a DoNotAddTagInTreeException, reraise it
            raise e
        except CriticalException, e:
            # CriticalException means we cannot continue what we were doing, reraise it
            raise e
        except Exception, e:
            logger.warning(e)
            traceback.print_exc()
            pass

    def _create_entity(self, model_name, entity):
        """
        Method creating an entity, specified in model_name, with the values defined in entity.
        Returns the id of the created entity or False.
        """
        model_pool = self.pool.get(model_name)
        prepared_entity = self._prepare_entity(model_name, entity)
        if not prepared_entity:
            logger.debug("Prepared entity is empty : %s model %s" % (prepared_entity, model_name))
            return False

        logger.debug("Creating entity %s\n%s" % (model_name, prepared_entity))
        new_id = model_pool.create(self.cr, self.uid, prepared_entity)

        logger.debug("Created %s, id %s" % (model_name, new_id))
        return new_id

    def _prepare_entity(self, model_name, entity, fields_id=None):
        """
        Prepares the entity values passed and return a dictionary that conforms to the ORM.
        I.e. one2many and many2many fields will be transformed :
        {'lines':[{'line1'},{'line2'}}
        will be
        {'lines':[(0,0,{'line1'}),(0,0,{'line2'})]}
        @param cr: cursor
        @param uid: user id
        @param model_name: name of the model
        @param entity: entity values as dictionary
        @param fields_id: ids of the fields used for reference between models, that will be
        ignored in the required check.
        @return: entity dictionary transformed
        """
        logger.debug("Preparing %s entity %s" % (model_name, entity))
        model_pool = self.pool.get(model_name)

        if not fields_id:
            fields_id = []

        # Before create entity hook
        entity = self._call_hook(model_name, "before_create_entity", entity=entity)
        if not entity:
            return entity  # Empty, no need to check it, return it

        # Check required
        def _check_required():
            model_columns = {}
            required_fields_not_found = []
            model_columns.update(model_pool._columns)
            for inherit_model_name in model_pool._inherits.keys():
                inherit_model_obj = self.pool.get(inherit_model_name)
                model_columns.update(inherit_model_obj._columns)
            for field in model_columns.keys():
                if model_columns[field].required and field not in fields_id:
                    if field not in entity.keys():
                        if field in model_pool.default_get(self.cr, self.uid, [field]):
                            # There is a default value, ignore
                            continue
                        required_fields_not_found.append(field)
                        logger.warn("Required field %s not found for %s" % (field, model_name))
                    else:
                        value = entity.get(field)
                        if value is None or value is False:
                            fieldType = model_pool._columns[field]._type
                            if fieldType not in ('boolean'):
                                required_fields_not_found.append(field)
                                logger.warn("Required field %s is False or None for %s" % (field, model_name))
            return required_fields_not_found

        required_fields_not_found = _check_required()
        if required_fields_not_found:
            raise Exception("Required field(s) not found")
        else:
            for field in entity.keys():
                fieldType = model_pool._columns[str(field)]._type
                if fieldType in ('one2many', 'many2many'):
                    sub_model = model_pool._columns[str(field)]._obj or False
                    values = []

                    # Put in fields_id the name of the fields used for reference between models,
                    # to be able to ignore them while checking required fields (because they will not be
                    # filled yet
                    if fieldType == 'one2many':
                        fields_id = model_pool._columns[str(field)]._fields_id or []
                    elif fieldType == 'many2many':
                        fields_id = []
                        if model_pool._columns[str(field)]._id1:
                            fields_id.append(model_pool._columns[str(field)]._id1)
                        if model_pool._columns[str(field)]._id2:
                            fields_id.append(model_pool._columns[str(field)]._id2)

                    if not isinstance(fields_id, list):
                        fields_id = [fields_id]

                    for sub_entity_dict in entity[field]:
                        if not isinstance(sub_entity_dict, dict):
                            logger.warning("Cannot verify %s/%s values, not dictionary : %s" % (model_name, field, sub_entity_dict))
                            values.append(sub_entity_dict)
                            continue
                        sub_dict = self._prepare_entity(sub_model, sub_entity_dict, fields_id=fields_id)
                        values.append((0, 0, sub_dict))
                    entity[field] = values

                elif fieldType in ('many2one'):
                    if entity[field] and isinstance(entity[field], dict):
                        sub_model = model_pool._columns[str(field)]._obj or False
                        sub_dict = self._prepare_entity(sub_model, entity[field])
                        new_id = self._create_entity(sub_model, sub_dict)
                        entity[field] = new_id

            logger.debug("Entity prepared %s entity %s" % (model_name, entity))
            return entity

    def _stack_push(self, absolute_path, xml):
        # Push the xml part at the absolute_path in the stack.
        # Remove all the previous xml whose absolute_path starts with this absolute path,
        # because they are deprecated.
        if not absolute_path:
            return
        logger.debug("Inserting %s in stack" % absolute_path)
        for key in self.deserialize_stack.keys():
            # Remove all sub elements
            if key.startswith(absolute_path):
                del self.deserialize_stack[key]
                logger.debug("%s deleted from stack" % key)
        self.deserialize_stack[absolute_path] = xml

    def serialize_object(self, res_id, context=None):
        """
        Method called to serialize a specific object. It will call the intern method _serialize_object.
        @param res_id: id of the object to be serialized
        @param context: context
        @return: the resulting XML as a string
        """
        if not self.pattern_id:
            raise PatternNotFoundException("Pattern with id %s was not found" % self.pattern_id)

        # Get model from the pattern
        pattern = self.pool.get('tk.json.pattern').browse(self.cr, self.uid, self.pattern_id)
        self.model_name = pattern and pattern.model_id and pattern.model_id.model or False

        # Load the JSON pattern
        json_pattern = simplejson.loads(pattern.json_pattern)
        self.master_json_pattern = json_pattern

        # Create the XML root
        self.xml = etree.Element(json_pattern.get('xpath', 'root'))

        # Get additional values from hook
        hook_res = self._call_hook(self.model_name, "before_serialize")
        if isinstance(hook_res, dict):
            self.additional_values.update(hook_res)
        else:
            logger.warn("before_deserialize result is not a dictionary")

        # Serialize
        xml = self._serialize_object(res_id, self.model_name, json_pattern, context=context)
        if xml is None or len(xml) == 0:
            return False

        xml = self._call_hook(self.model_name, "after_serialize", res_id=res_id, xml=xml, pattern_id=self.pattern_id, context=context)
        xml_string = etree.tostring(xml, pretty_print=True)
        self.master_json_pattern = None
        return xml_string

    def _serialize_object(self, res_id, model_name=None, json_pattern=None, current_el=None, context=None):
        """
        Internal recursive method used to serialize an object.
        @param cr: cursor
        @param uid: user id
        @param res_id: id of the object to be serialized
        @param model_name: name of the model
        @param json_pattern: the json pattern
        @param current_el: current XML element treated
        @param context: context
        @return: the resulting XML as a string
        """
        logger.debug("serialize_object for model %s, id %s, pattern %s" % (model_name or self.model_name, res_id, self.pattern_id))

        if not json_pattern:
            raise Exception("No JSON pattern")

        if not model_name:
            raise Exception("No model specified")

        model_pool = self.pool.get(model_name)
        if not model_pool:
            raise Exception("Cannot get pooler for the model %s" % model_name)

        model = False
        if res_id:
            model = model_pool.browse(self.cr, self.uid, res_id)
            if not model or not model.exists():
                logger.error("Model %s with id %s doesn't seem to exist in DB" % (model_name, res_id))
                raise ModelNotFoundException("Model %s with id %s does not exist in DB" % (model_name, res_id))

        # No current element passed, we use the root
        if current_el is None:
            current_el = self.xml

        curr_values = {}

        def add_element(root, xml_xpath, value, to_many=False):
            # Add the specified value at the specified xpath in the specified root
            logger.debug("add_element to %s xpath %s value %s" % (root, xml_xpath, value))
            try:
                value = self._call_hook(model_name, "serialize_before_add_element", xml=self.xml, pattern_id=self.pattern_id, xml_xpath=xml_xpath, value=value,
                                        res_id=res_id)
            except DoNotAddTagInTreeException, e:
                logger.debug("Not adding %s" % xml_xpath)
                return False

            attrs = {}

            if (not value or value == '') and not self.add_tag_if_empty and not to_many:
                return True

            def add_value_to_el(el):
                if value is not None and value is not False:
                    if attrs:
                        for attr, attr_value in attrs.iteritems():
                            el.set(attr, unicode(attr_value))
                    else:
                        el.text = unicode(value)  # We try to stick with unicode to avoid UnicodeEncodeError and other errors

            root_xpath = self.get_el_path(root)
            logger.debug("Current root xpath %s" % root_xpath)
            if root_xpath not in xml_xpath:
                # Add in absolute position
                xml_xpath = self.strip_root_from_xpath(self.xml, xml_xpath)
                self.fill_tree(self.xml, xml_xpath)
                el = self.xml.find(xml_xpath)
                logger.debug("Adding to absolute root xml : value of %s = %s" % (el.tag, value))
                add_value_to_el(el)
                return

            xml_xpath = xml_xpath[len(root_xpath) + 1:]
            curr_values[xml_xpath] = value

            if xml_xpath.startswith('@'):
                # Attribute on root
                root.set(xml_xpath[1:], unicode(value))
                return True
            if '/@' in xml_xpath:
                # The value must be set on an attribute, i.e
                # if the xml_xpath is line/@name, the value will be set in an attribute on line :
                # <line name='value'/>
                xpath_parts = xml_xpath.split('/@')  # First part is element name, second is attribute name
                xml_xpath = xpath_parts[0]  # Set the xml_xpath to the first part
                attrs[xpath_parts[1]] = unicode(value)  # Set the attr to the attribute name

            self.fill_tree(root, xml_xpath)  # Be sure the tag exists
            el = root.find(xml_xpath)
            if el is None:
                # Should not happen
                logger.warning("Could not found element %s in %s" % (xml_xpath, root))
                return False
            add_value_to_el(el)
            return True

        for field in json_pattern.get('fields', []):
            field_name = field.get('name', False)
            field_xpath = field.get('xpath', False)
            field_sequence = field.get('sequence', False)
            logger.debug("Field %s - seq %s" % (field_name, field_sequence))

            if field.get('multi', False):
                add_element(current_el, field_xpath, '')
                xml_xpath = field_xpath
                if xml_xpath.find(self.xml.tag + '/') == 0:
                    xml_xpath = xml_xpath[len(self.xml.tag) + 1:]
                sub_el = self.xml.find(".//%s" % xml_xpath)
                self.xml = self._serialize_object(res_id, model_name=model_name, json_pattern=field, current_el=sub_el, context=context)
                continue

            field_type = field_name and model._columns[field_name]._type or False
            logger.debug("Field type %s" % field_type)

            if not field_type or field_type not in ['one2many', 'many2many', 'many2one']:
                # Simple field, not many2many, one2many or many2one
                if not field_name or len(field_name) == 0:
                    # Add empty tag
                    add_element(current_el, field_xpath, '')
                else:
                    try:
                        value = getattr(model, field_name)
                        if field.get('date', False):
                            date_format = field.get('date_format_send', False) or json_pattern.get('date_format_send', False) or self.master_json_pattern.get('date_format_send',
                                                                                                                                                              False)
                            if date_format and value:
                                try:
                                    value_datetime = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")  # From OpenERP format to datetime
                                    value = datetime.strftime(value_datetime, date_format)  # From datetime to date_format specified
                                except Exception, e:
                                    traceback.print_exc()
                                    logger.warning(e)
                                    pass
                        add_element(current_el, field_xpath, value)
                    except Exception, e:
                        message = "Cannot get value for field %s on the model %s" % (field_name, model_name)
                        add_element(current_el, field_xpath, '')
                        logger.error(message)
                        logger.error(e)
                        traceback.print_exc()

            elif field_type in ['one2many', 'many2many']:
                try:
                    # Get the xpath without the last part, as the elements will be added under the last part, i.e
                    # Line/Lines, we get the element Line and add a SubElement Lines for each object
                    xml_xpath = field_xpath
                    current_el_xpath = self.get_el_path(current_el)
                    root_xpath = self.get_el_path(self.xml)
                    if current_el_xpath not in xml_xpath and root_xpath not in xml_xpath:
                        logger.error("Cannot add %s anywhere" % xml_xpath)

                    if current_el_xpath not in xml_xpath and root_xpath in xml_xpath:
                        current_el_xpath = root_xpath
                        current_el = self.xml

                    rel_xml_xpath = xml_xpath[len(current_el_xpath) + 1:]
                    xpath_parts = rel_xml_xpath.split('/')
                    if len(xpath_parts) <= 1:
                        anchor_el = current_el
                        new_el_xpath = rel_xml_xpath
                    else:
                        anchor_el_xpath = '/'.join(xpath_parts[:-1])
                        add_element(current_el, current_el_xpath + '/' + anchor_el_xpath, '', to_many=True)
                        anchor_el = current_el.find(".//%s" % anchor_el_xpath)
                        new_el_xpath = xpath_parts[-1]

                    sub_model_model = model._columns[field_name]._obj
                    for subModel in getattr(model, field_name):
                        logger.debug("found %s" % subModel.id)
                        if subModel:
                            sub_el = etree.SubElement(anchor_el, new_el_xpath)
                            self.xml = self._serialize_object(subModel.id, model_name=sub_model_model, json_pattern=field,
                                                              current_el=sub_el, context=context)
                except Exception, e:
                    traceback.print_exc()
                    print e

            elif field_type in ['many2one']:
                try:
                    subModel = getattr(model, field_name) if model else False
                    sub_model_model = model._columns[field_name]._obj
                    self.xml = self._serialize_object(subModel and subModel.id or False, model_name=sub_model_model, json_pattern=field,
                                                      current_el=current_el, context=context)
                    # xml = etree.XML(xml)
                except Exception, e:
                    message = "Cannot get value for field %s on the model %s (many2one)" % (field_name, model_name)
                    logger.error(message)
                    logger.error(e)
                    traceback.print_exc()

        self.xml = self._call_hook(model_name, "after_serialize_model", xml=self.xml, entity=curr_values, id=res_id)
        return self.xml

    def deserialize_object(self):
        """
        Deserialize an XML formatted string based on the model defined.
        @return: True
        """
        logger.debug("Entering deserialize_object for pattern %s" % self.pattern_id)

        # Check pattern
        pattern_model_obj = self.pool.get('tk.json.pattern')
        if not self.pattern_id:
            raise PatternNotFoundException("Pattern with id %s was not found" % self.pattern_id)
        pattern = pattern_model_obj.browse(self.cr, self.uid, self.pattern_id)
        if not self.model_name:
            self.model_name = pattern.model_id and pattern.model_id.model or False

        # Load the JSON pattern
        json_pattern = simplejson.loads(pattern.json_pattern)

        # Before deserialize hook
        hook_res = self._call_hook(self.model_name, "before_deserialize",
                                   xml=self.xml)
        if isinstance(hook_res, dict):
            self.additional_values.update(hook_res)
        else:
            logger.warn("before_deserialize result is not a dictionary")

        if not self.xml:
            raise Exception("No XML defined")

        if not self.model_name:
            raise Exception("No model defined")

        # Prepare XML
        tree = etree.parse(StringIO(self.xml))
        root = tree.getroot()

        # TODO: is it ok to replace self.xml (string) by the parsed XML?
        self.xml = root

        # This is where we begin
        values = self._deserialize_object(model_name=json_pattern.get('model'), json_pattern_part=json_pattern, current_el=root)  # Start looping on the XML to get values
        logger.debug("Final values : %s" % values)

        if not self.multi_documents and values:
            created_entity_id = self._create_entity(self.model_name, values)
            self.created_ids.append(created_entity_id)
            return created_entity_id

        elif not self.multi_documents:
            logger.debug("No values, cannot create entity for %s" % self.model_name)
            return False

        else:
            return self.created_ids

    def _deserialize_object(self, model_name=None, json_pattern_part=None, current_el=None, current_absolute_position=None, only_key=None, only_xpaths=None):
        logger.debug("---------- Get values at %s for %s" % (current_absolute_position, current_el))

        # Get the pattern
        if not json_pattern_part:
            raise Exception("No pattern part.")

        if not model_name:
            raise Exception("No model specified.")

        model_obj = self.pool.get(model_name)
        if not model_obj:
            raise Exception("Cannot get pooler for the model %s" % model_name)

        if not only_xpaths:
            only_xpaths = []

        additional_values_for_model = {}
        model_values = {}
        self._stack_push(current_absolute_position, current_el)

        def _check_value(value, field):
            """
            Checks the value of a specified field.
            Tries to cast if needed
            @param value: the value found in the XML
            @param field: the associated field
            @return: the correct value
            """
            if not value:
                return False

            if field.get('date', False):
                # Get date format
                date_format = field.get('date_format', False) or json_pattern_part.get('date_format', False) or self.master_json_pattern.get('date_format', False)
                if date_format:
                    value = datetime.strptime(value, date_format)

            if field.get('name'):
                field_name = field.get('name')
                # Get the type of the column and cast if necessary
                field_type = model_obj._columns[field_name]._type
                if field_type == 'integer':
                    try:
                        value = int(value)
                    except (TypeError, ValueError), e:
                        logger.warning("Cannot convert value of integer field to int : %s for field %s" % (value, field_name))
                        logger.warning(e)
                        logger.warn("Cannot convert value of integer field to int : %s for field %s" % (value, field_name))
                elif field_type == 'float':
                    try:
                        value = float(value)
                    except (TypeError, ValueError), e:
                        logger.warning("Cannot convert value of float field to float : %s for field %s" % (value, field_name))
                        logger.warning(e)
                        logger.warn("Cannot convert value of float field to float : %s for field %s" % (value, field_name))
            return value

        for field in json_pattern_part.get('fields', []):
            # TODO Check dict structure
            field_name = field.get("name", False)
            field_xpath = field.get('xpath', False)
            logger.debug("Field %s - %s" % (field_name, field_xpath))

            # TODO check only xpath
            # TODO check only key

            if current_absolute_position and field_xpath and field_xpath.find(current_absolute_position) == -1:
                # The xpath of the field does not correspond to the current absolute path,
                # meaning the field is not in the sub_root, but elsewhere.
                logger.debug("Field %s not in current xml part" % field_xpath)
                if not field_name:
                    continue
                only_xpaths.append(field_xpath)
                # Get the absolute_paths in the stack (keys) and sort them by reversed length.
                # The goal is to find the nearest xml part containing this field
                # keys = self.deserialize_stack.keys()
                # keys.sort(cmp=sort_by_length, reverse=True)
                # for key in keys:
                # if key in field.xml_xpath:
                # logger.debug("%s found in %s" % (key, field.xml_xpath))
                # in_tree = self.deserialize_stack.get(key) # The xml part containing the field
                # values = get_values(in_tree, current_absolute_position=key, pattern_model_id=field.pattern_model_id.id, only_xpaths=only_xpaths)
                # if values:
                # model_values.update(values) # Updating the values with the values found
                # return model_values
                # logger.debug("%s not found anywhere in the stack" % field.xml_xpath)
                # continue

            xml_xpath = self.strip_root_from_xpath(self.xml, field_xpath)  # Removes the root tag

            if current_absolute_position:
                # Remove the current_absolute_position from the xpath, to match the current_el paths
                xml_xpath = xml_xpath[len(self.strip_root_from_xpath(self.xml, current_absolute_position)) + 1:]
            logger.debug("Xpath %s" % xml_xpath)

            # TODO check additional value only if value not found
            if field_name in self.additional_values:
                # Check if we have the value in the additional values
                model_values[field_name] = self.additional_values.get(field_name, False)
                continue

            if field.get('multi', False):
                # This field defines a loop
                # We iterate over all the elements.
                self.multi_documents = True

                logger.debug("Looping on %s" % field_xpath)
                elements = current_el.findall(".//%s" % xml_xpath)
                if elements is not None:
                    for element in elements:
                        values = self._deserialize_object(model_name=model_name, json_pattern_part=field, current_el=element, current_absolute_position=field_xpath,
                                                          only_xpaths=only_xpaths)
                        new_id = self._create_entity(model_name, values)
                        self.created_ids.append(new_id)
                continue

            if field_name and field_name not in model_obj._columns:
                logger.warn("Field %s not found in %s" % (field_name, model_obj._name))
                continue

            field_type = field_name and model_obj._columns[field_name]._type or False
            logger.debug("Field type %s" % field_type)

            if not field_type or field_type not in ['one2many', 'many2many', 'many2one']:
                # Get the value
                value = None
                if not xml_xpath or len(xml_xpath) == 0:
                    # The xpath should not be empty,
                    # but in the case of a many2one, the many2one field could have the same xpath
                    # as the fields in it, so try to get the value anyway
                    if field_xpath == current_absolute_position:
                        try:
                            value = current_el.text
                        except Exception, e:
                            logger.debug(e)
                elif xml_xpath.startswith('@'):
                    # Get attribute from sub_root
                    attribute = current_el.get(xml_xpath[1:], "")
                    value = attribute
                elif '/@' in xml_xpath:
                    # Get attribute from specified xpath
                    splitted_xpath = xml_xpath.split('/@')  # First part is the xpath to the element, second part is the name of the attribute
                    if splitted_xpath and len(splitted_xpath) == 2:
                        attribute = current_el.find(".//%s" % splitted_xpath[0]).get(splitted_xpath[1], "")
                        value = attribute
                else:
                    # We have an xpath, try to get the value
                    element = current_el.find(".//%s" % xml_xpath)
                    if element is not None:
                        # if element.text is None and field.key:
                        # _log("Element (key) %s is empty" % xml_xpath)
                        # elif element.text is None:
                        if element.text is None:
                            logger.debug("Element at %s does not have a value" % xml_xpath)
                        else:
                            value = element.text
                if value:
                    value = _check_value(value, field)
                    if field_name:
                        model_values[field_name] = value
                    else:
                        additional_values_for_model[xml_xpath] = value
                        logger.debug("Element at %s does not have a field name, will be ignored (added to additional_values_for_model)." % xml_xpath)
                    logger.debug("value %s" % value)
                continue

            elif field_type in ['one2many', 'many2many']:
                submodel_name = model_obj._columns[field_name]._obj
                if not model_values.get(field_name, False):
                    model_values[field_name] = []
                elements = current_el.findall(".//%s" % xml_xpath)
                if elements is not None:
                    logger.debug("Found %s" % len(elements))
                    for element in elements:
                        values = self._deserialize_object(model_name=submodel_name, json_pattern_part=field, current_el=element, current_absolute_position=field_xpath,
                                                          only_xpaths=only_xpaths)
                        model_values[field_name].append(values)

            elif field_type in ['many2one']:
                values = None
                element = current_el.find(".//%s" % xml_xpath)
                submodel_name = model_obj._columns.get(field_name)._obj
                if element is not None:
                    values = self._deserialize_object(model_name=submodel_name, json_pattern_part=field, current_el=element, current_absolute_position=field_xpath,
                                                      only_xpaths=only_xpaths)
                    # model_values[field_name] = values

                if not values:
                    logger.warn("Could not find value for many2one at %s" % xml_xpath)
                    continue

                ir_submodel = self.pool.get(submodel_name)
                domain = []
                for k, v in values.iteritems():
                    domain.append((k, '=', v))
                    additional_values_for_model.update({field_xpath + '/' + k: v})  # Put the values found for sub field in addition values with full field.xml_xpath
                logger.debug("Searching %s with domain %s" % (field_name, domain))
                ids = ir_submodel.search(self.cr, self.uid, domain)
                if not ids:
                    logger.warn(message="Cannot find %s with domain %s" % (field_name, domain))
                    continue
                elif len(ids) > 1:
                    logger.warn("Cannot find unique %s with domain %s" % (field_name, domain))
                    continue
                else:
                    logger.debug("Found 1 : %s" % ids[0])
                    model_values[field_name] = ids[0]

        model_values = self._call_hook(model_name, "after_deserialize_model", entity=model_values, additional_values_for_model=additional_values_for_model)
        return model_values
