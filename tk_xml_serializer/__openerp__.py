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

{
    "name": "Taktik XML (de)Serializer",
    "version": "0.1",
    "author": "Taktik S.A.",
    "category": "Tools",
    "website": "http://www.taktik.be",
    "description": """
Taktik XML (de)Serializer
=========================

This modules offers the possibility to serialize any entity into an XML document, through a JSON pattern.
It also allows to deserialize an XML document into an entity.

JSON Patterns
=============

The JSON patterns allow you to define for a specified model the structure of the XML document to be serialized
or deserialized.
""",
    "depends": ['base'],
    "init_xml": [
    ],
    "demo_xml": [],
    "update_xml": [
    ],
    "active": False,
    "installable": True,
    "application": True,
}
