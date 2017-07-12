# -*- encoding: utf-8 -*-
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
#############################################################################

import logging

import openerp
from openerp.addons.web import http
from openerp.http import request

logger = logging.getLogger(__name__)


class Website(openerp.addons.web.controllers.main.Home):
    @http.route('/website/info', type='http', auth="user", website=True)
    def website_info(self):
        admin_group_id = request.env().ref('base.group_erp_manager')
        is_admin_group = request.env()['res.groups'].search([('id', '=', admin_group_id.id),
                                                             ('users', 'in', request.session._uid)])
        if not is_admin_group:
            return request.registry['ir.http']._handle_exception('Not found', 404)

        try:
            request.website.get_template('website.info').name
        except Exception, e:
            return request.registry['ir.http']._handle_exception(e, 404)
        irm = request.env()['ir.module.module'].sudo()
        apps = irm.search([('state', '=', 'installed'), ('application', '=', True)])
        modules = irm.search([('state', '=', 'installed'), ('application', '=', False)])
        values = {
            'apps': apps,
            'modules': modules,
            'version': openerp.service.common.exp_version()
        }
        return request.render('website.info', values)
