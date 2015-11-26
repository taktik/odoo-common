# coding=utf-8
from openerp.osv import orm, fields


class tk_stock_move(orm.Model):
    _inherit = 'stock.move'

    _columns = {
        'qty_packaging': fields.integer('Quantity Packaging'),
        'packaging_id': fields.many2one('product.packaging', 'Packaging'),
    }

tk_stock_move()


