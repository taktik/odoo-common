# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2004-2014 Apertoso NV (<http://www.apertoso.be>).
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
    'name': 'Point of Sale Limit Amount',
    'version': '1.0',
    'category': 'Point Of Sale',
    'sequence': 6,
    'summary': 'Point of Sale Limit Amount',
    'description': """
Limit Amount
========================

This module allows you to avoid to scan an ean/barcode in the field amount when
a customer pay
    """,
    'author': 'Taktik S.A.',
    'images': [],
    'depends': ['point_of_sale'],
    'data': [
        'views/tk_pos_view.xml',
        'views/templates.xml',
    ],
    'demo': [],
    'test': [],
    'installable': True,
    'application': True,
    'qweb': [],
    'website': 'http://www.taktik.be',
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
