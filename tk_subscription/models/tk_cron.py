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


class TaktikCron(models.Model):
    _inherit = 'ir.cron'

    @api.multi
    def write(self, values):
        """
        Check if a a record in linked to a recurring document before performing the write.
        If it is already linked, it trigger a warning to prevent the user.

        :return: Write the record
        """
        self.ensure_one()
        if 'nextcall' in values \
            or 'interval_number' in values \
            or 'interval_type' in values \
            or 'numbercall' in values:
            subscription_document = self.env['subscription.subscription'].search([('cron_id', '=', self.id)])
            if subscription_document and (subscription_document.state != 'draft'):
                raise exceptions.Warning("Error! \n"
                                         "This cron job is linked to the recurring document \"{}\" and is in the \"{}\" state\n\n"
                                         "Please set the recurring document to the state \"draft\" before updating the cron job"
                                         .format(subscription_document.name.encode('utf-8'), subscription_document.state.encode('utf-8')))
        res = super(TaktikCron, self).write(values)
        return res


class TaktikSubscriptionSubscription(models.Model):
    _inherit = 'subscription.subscription'

    @property
    def ret_invoice_only(self):
        return self.invoice_only

    @api.onchange('invoice_id')
    def invoice_id_onchange(self):
        if self.invoice_only:
            self.doc_source = 'account.invoice,{0}'.format(self.invoice_id.id)

    invoice_id = fields.Many2one('account.invoice',
                                 string='Invoice')

    invoice_only = fields.Boolean(string='Invoice only ?',
                                  default=False,
                                  help="Sort the invoices on the selected partner.")
