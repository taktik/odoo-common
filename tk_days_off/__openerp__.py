# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Taktik S.A.
#    Copyright (c) 2015 Taktik S.A. (http://www.taktik.be)
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
    'name': 'Days Off',
    'version': '8.0.1.0.1',
    'author': 'Taktik',
    'website': 'http://www.taktik.be',
    'summary': "Hr holidays - improvements",
    'category': 'Other',
    'depends': [
        'base',
        'hr',
        'hr_holidays'
    ],
    'description': """
Days Off allows to :
===============================================================
* generate days off via a wizard for a specific year (BE,FR,US)
* Only federal days off are supported for USA.
* manually change/add/remove the generated days.
* When calculating the days of a leave request, adapted to take into account the days off generated.
* Support multi-companies

    """,
    'data': [
        'data/holidays_ir_config_parameter.xml',
        'views/days_off_view.xml',
        'views/hr_holidays_view.xml',
        'wizard/days_off_wizard_views.xml',
        'security/days_off_security.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'active': False,
}
