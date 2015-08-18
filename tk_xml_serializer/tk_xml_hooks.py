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
from openerp.osv import orm, fields
from openerp.addons.tk_xml_serializer.tk_xml_serializer import serializer


class TkXmlHooks(orm.AbstractModel):
    _name = "tk.xml.hooks"

    def before_serialize(self, cr, uid, model_name, additional_values=None, context=None, **kwargs):
        return {}

    def serialize_before_add_element(self, cr, uid, model_name, xml_xpath=None, value=None, res_id=None, xml=None, pattern_id=None, additional_values=None, **kwargs):
        return value

    def after_serialize_model(self, cr, uid, model_name, xml=None, entity=None, id=None, additional_values=None, **kwargs):
        return xml

    def after_serialize(self, cr, uid, model_name, res_id=None, xml=None, pattern_id=None, context=None, **kwargs):
        return xml

    def serialize(self, cr, uid, pattern_id, document_id, partner_id=None, preview=None, add_tag_if_empty=True, context=None):
        return serializer(cr, uid, self.pool, pattern_id=pattern_id, add_tag_if_empty=add_tag_if_empty).serialize_object(document_id)

    def before_deserialize(self, cr, uid, model_name, xml=None, context=None, **kwargs):
        return {}

    def before_create_entity(self, cr, uid, model_name, entity=None, additional_values=None, **kwargs):
        return entity

    def deserialize(self, cr, uid, pattern_id, xml, strict=None, context=None):
        return serializer(cr, uid, self.pool, pattern_id=pattern_id, xml=xml).deserialize_object()

    def after_deserialize_model(self, cr, uid, model_name, entity=None, additional_values_for_model=None, additional_values=None, **kwargs):
        return entity
