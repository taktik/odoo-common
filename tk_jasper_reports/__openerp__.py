# coding=utf-8
# #############################################################################
#
# Copyright (c) 2008-2012 NaN Projectes de Programari Lliure, S.L.
# http://www.NaN-tic.com
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
# #############################################################################

{
    'name': 'Jasper Reports 8.0',
    'version': '1.0',
    'author': 'Taktik S.A',
    'category': 'Generic Modules/Jasper Reports',
    'description': """
This module integrates Jasper Reports with OpenERP for version 8.0.
-------------------------------------------------------------------

Settings/Technical/Jasper Reports 8.0 (Jasper Reports for OpenERP version 8.0)

Modified original jasper_reports(OpenERP version 7.0) to work fine in odoo version8.0.

Credits to original Author.

Author: kankaungmalay(https://twitter.com/kankaungmalay)

Modified by :

Taktik S.A./N.V.

    """,
    'website': 'http://www.taktik.be',
    'images': [],
    'depends': ["base"],
    'data': [
        'wizard/create_data_template.xml',
        'jasper_wizard.xml',
        'report_xml_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}
