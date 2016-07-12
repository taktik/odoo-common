# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Taktik S.A.
#    Copyright (c) 2015 Taktik S.A. (http://www.taktik.com)
#    All Rights Reserved
#
#    WARNING: This program as such is intended to be used by professional
#    programmers who take the whole responsibility of assessing all potential
#    consequences resulting from its eventual inadequacies and bugs.
#    End users who are looking for a ready-to-use solution with commercial
#    guarantees and support are strongly advised to contact a Free Software
#    Service Company.
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
    'name': 'List View Fixed Table Footer',
    'version': '8.0.1.0.0',
    'author': 'TAKTIK SA',
    'maintainer': 'TAKTIK SA',
    'website': 'http://www.taktik.com',
    'category': 'Tools',
    'summary': 'Web List View Fixed Table Footer',
    'description': """
Web List View Fixed Table Footer
=================================
* Fixed list view table footer.
""",
    'depends': [
        'web',
        'base'
    ],
    'data': [
        'views/fixed_footer_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
