# coding=utf-8
# ############################################################################
#
# Copyright (C) 2014 Taktik SA <http://taktik.be>
#    @author Adil Houmadi
#
#    This file is a part of profiler
#
#    profiler is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License v3 or later
#    as published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    profiler is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License v3 or later for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    v3 or later along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
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
    'depends': ['base', 'web'],
    'data': [
        'view/remove_sheet_view.xml'
    ],
    'installable': True,
    'application': False,
}
