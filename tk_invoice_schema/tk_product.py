from openerp import models, fields, api

class TkProductProduct(models.Model):
    _inherit = 'product.template'

    recurrence = fields.Boolean('Recurring')