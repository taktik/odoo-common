# coding=utf-8
from openerp import models, fields, api


class TkSale(models.Model):
    _inherit = 'sale.order'

    invoice_progress = fields.Float('Invoice Progress')

