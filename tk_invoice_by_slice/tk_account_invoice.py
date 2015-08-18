# coding=utf-8
from openerp import fields, models, api


class TkAccountInvoice(models.Model):
    _inherit = 'account.invoice'

    slice_percent = fields.Float('Slice Percent', default=100)

    @api.multi
    def invoice_validate(self):
        self.ensure_one()
        res = super(TkAccountInvoice, self).invoice_validate()
        sale_order = self.env['sale.order'].search([('name', '=', self.origin)])
        if sale_order:
            sale_order.invoice_progress = sale_order.invoice_progress + self.slice_percent
        return res
