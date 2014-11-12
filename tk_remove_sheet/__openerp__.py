# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2010-Today OpenERP S.A. (<http://www.openerp.com>).
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
    'name': 'Taktik Remove Sheet',
    'version': '1.0',
    'category': 'Others',
    'sequence': 2,
    'summary': 'Remove sheet CSS',
    'description': """
Remove Sheet from views
===================================
Remove the sheet CSS on sale orders, invoices, ...
    """,
    'author': 'Taktik SA',
    'website': 'http://www.taktik.be',
    'depends': ['base'],
    'data': [

    ],
    'installable': True,
    'application': False,
    'css': [
        'static/src/css/tk_remove_sheet.css',
        ],
    }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
