# -*- encoding: utf-8 -*-
##############################################################################
#
#   Author: Taktik S.A.
#   Copyright (c) 2015 Taktik S.A. (http://www.taktik.be)
#   All Rights Reserved
#
#   WARNING: This program as such is intended to be used by professional
#   programmers who take the whole responsibility of assessing all potential
#   consequences resulting from its eventual inadequacies and bugs.
#   End users who are looking for a ready-to-use solution with commercial
#   guarantees and support are strongly advised to contact a Free Software
#   Service Company.
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from openerp import SUPERUSER_ID
from openerp.addons.web import http
from openerp.addons.web.http import request, route
from openerp.http import Controller, route, request, Response


class LeaveRequest(Controller):

    def _get_cr_uid_context(self):
        return request.cr, SUPERUSER_ID, request.context

    def _check_leave_request(self, cr, uid, request, token, context=None):
        """
        Verify that the token is mapped with an leave request.
        """
        holidays_obj = request.registry['hr.holidays']
        holidays_ids = holidays_obj.search(cr, uid, [
            ('token', '=', token)
        ])

        if len(holidays_ids) == 0:
            return request.website.render(
                "tk_hr_approve_request.leave_request_not_found"
            )

        _id = holidays_ids[0] if len(holidays_ids) else None
        if _id:
            leave_request = holidays_obj.browse(
                cr, uid, _id, context=context
            )
            return leave_request

    @route(
        ['/leave_request/accept/<string:token>'],
        type='http',
        auth="none",
        website=True
    )
    def leave_request_accept(self, token, **kwargs):
        """
        Accept the leave request
        """
        cr, uid, context = self._get_cr_uid_context()
        res = self._check_leave_request(
            cr, uid, request, token, context=context
        )
        if isinstance(res, http.Response):
            return res
        if res:
            res.signal_workflow('validate')
            if res.state == 'validate':
                return request.website.render(
                    "tk_hr_approve_request.leave_request_accepted"
                )

    @route(
        ['/leave_request/refuse/<string:token>'],
        type='http',
        auth="none",
        website=True
    )
    def leave_request_decline(self, token, **kwargs):
        """
        Refuse the leave request
        """
        cr, uid, context = self._get_cr_uid_context()
        res = self._check_leave_request(
            cr, uid, request, token, context=context
        )
        if isinstance(res, http.Response):
            return res
        if res:
            res.signal_workflow('refuse')
            if res.state == 'refuse':
                return request.website.render(
                    "tk_hr_approve_request.leave_request_refused"
                )
