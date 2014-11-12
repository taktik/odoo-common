# -*- encoding: utf-8 -*-
##############################################################################
#
#    Authors: Lefever David, Rolin Simon
#    Copyright Taktik SA 2013
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    "name": "Taktik Base Reports Module",
    "version": "0.1",
    "author": "Taktik S.A.",
    "category": "Generic Modules/Others",
    "website": "http://www.taktik.be",
    "description": """
Taktik Reports Module
=====================

This module offers some basic reports (invoice, sale order, purchase order, delivery order) in webkit.
""",
    "depends": ["base", 'account', 'sale', 'purchase', 'delivery', 'report_webkit', 'tk_report_parser'],
    "init_xml": [],
    "demo_xml": [],
    "data": [
        "data/tk_base_report_webkit_headers.xml",
        "reports/tk_base_report_view.xml",
        "views/tk_delivery_view.xml",
    ],
    "active": False,
    "installable": True
}