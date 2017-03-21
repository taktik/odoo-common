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

from openerp import api, exceptions, fields, models, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.multi
    def return_subscription_partner(self):
        """
        :return:
        """
        self.ensure_one()
        tree_subscription_view = self.env.ref('subscription.view_subscription_tree').id
        form_subscription_view = self.env.ref('subscription.view_subscription_form').id
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'views': [(tree_subscription_view, 'tree'), (form_subscription_view, 'form')],
            'res_model': 'subscription.subscription',
            'domain': ['|', ('partner_id', '=', self.id), ('partner_id', 'in', self.child_ids.ids)],
            'target': 'current',
            'context': {'default_partner_id': self.id}
        }

    @api.multi
    def _count_subscriptions(self):
        """
        Compute the number of subscription linked to the given res.partner

        :return: number of subscription linked to the partner
        """
        for partner in self:
            subscriptions = self.env['subscription.subscription']
            count = subscriptions.sudo().search_count([('partner_id', '=', partner.id)])
            for child in partner.child_ids:
                count += subscriptions.sudo().search_count([('partner_id', '=', child.id)])
            partner.subscriptions_count = count

    subscriptions_count = fields.Integer(compute='_count_subscriptions',
                                         string='Subscriptions')
