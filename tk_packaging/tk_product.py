from openerp.osv import orm, fields

class tk_product_packaging(orm.Model):
    _inherit = 'product.packaging'

    _columns = {
        'sale': fields.boolean('Sale Packaging'),
        'stock': fields.boolean('Stock (inventory) Packaging'),
        'purchase': fields.boolean('Purchase Packaging')
    }

tk_product_packaging()