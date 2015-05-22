# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Kévin Goris
#    Copyright 2015 Taktik SA
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

from openerp import models, fields, api, _

class TkInvoiceEmailerWizard(models.TransientModel):
    """ Send emails for each selected Invoice. """

    _name = "tk.invoice.emailer.wizard"
    _description = """Mass invoice emailer"""
    _rec_name = 'id'

    @api.model
    def _get_invoice_ids(self):
        context = self.env.context
        if not (context.get('active_model') == 'account.invoice' and
                context.get('active_ids', False)):
            return False
        invoice_obj = self.env['account.invoice']
        invoices = invoice_obj.browse(context['active_ids'])
        return self._filter_invoices(invoices)

    @api.model
    def _get_default_templates(self):
        invoice_model = self.env['ir.model'].search([('model', '=', 'account.invoice')])
        email_templates = self.env['email.template'].search([('model_id', '=', invoice_model.id)])
        return email_templates[0]

    invoice_ids = fields.Many2many('account.invoice',
                                string='Invoices',
                                default=_get_invoice_ids)

    email_template_id = fields.Many2one('email.template', string='Invoices', default=_get_default_templates)

    @api.model
    @api.returns('account.invoice')
    def _filter_invoices(self, invoices):
        """ filter lines to use in the wizard """
        invoice_obj = self.env['account.invoice']
        domain = [('sent', '=', False),
                  ('id', 'in', invoices.ids),
                  ('state', '=', 'open')]
        return invoice_obj.search(domain)

    @api.multi
    def email_invoices(self):
        self.ensure_one()
        if not self.invoice_ids:
            raise api.Warning(_('No Invoice selected.'))

        self.invoice_ids.with_context(active_model='account.invoice',active_ids=self.invoice_ids.ids)._generate_emails(self.email_template_id)
        return {'type': 'ir.actions.act_window_close'}

