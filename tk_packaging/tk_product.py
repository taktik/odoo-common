from openerp.osv import orm, fields

class tk_product_packaging(orm.Model):
    _inherit = 'product.packaging'

    _columns = {
        'base': fields.boolean('Base'),
        'intermediate': fields.boolean('Intermediate'),
        'delivery': fields.boolean('Delivery')
    }

tk_product_packaging()