# -*- coding: utf-8 -*-

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
