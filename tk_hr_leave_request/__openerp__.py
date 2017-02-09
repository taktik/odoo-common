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
    'name': 'Human Resources Leave Request',
    'version': '8.0.1.0.0',
    'author': 'Taktik',
    'website': 'http://www.taktik.be',
    'summary': "Holidays - Email to approve leave request",
    'category': 'Other',
    'depends': [
        'base',
        'hr_holidays',
    ],
    'description': """
Human Resources Leave Request :
===============================================================
* Enhance the process of the leave requests. It allow a user to create requests into 'to submit' state. This allow
the user to modify them before sending them to the 'to approve' state.
* When the request go to the 'to approve' state, an email is sent that contain 3 links : 'Confirm', 'Declline' or one to
see the leave request.

    """,
    "data": [
        "data/tk_hr_leave_request_email_template.xml",
        "views/tk_hr_leave_request_templates_views.xml",
        "views/tk_hr_leave_request_view.xml",
        "workflow/tk_hr_leave_request.xml",
    ],
    "qweb": [],
    "demo": [],
    "test": [],
    "active": False,
    "license": "AGPL-3",
    "installable": True,
    "auto_install": False,
    "application": True,
}
