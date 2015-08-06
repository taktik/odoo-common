from openerp.osv import fields, osv


class sale_order(osv.Model):
    _inherit = 'sale.order'
    
    def _product_margin_percent(self, cr, uid, ids, field_name, arg, context=None):
        result = {}
        for sale in self.browse(cr, uid, ids, context=context):
            result[sale.id] = (sale.margin / sale.amount_untaxed) * 100 if sale.amount_untaxed else 100

        return result

    def _get_order(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('sale.order.line').browse(cr, uid, ids, context=context):
            result[line.order_id.id] = True
        return result.keys()

    _columns = {
        'margin_percent': fields.function(_product_margin_percent, string='Margin Percent',
                                          help="It gives profitability by calculating "
                                               "the difference between the Unit Price and the cost price.",
                                          store={
                                              'sale.order.line': (_get_order, ['margin'], 20),
                                              'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 20),
                                              }),
    }

sale_order()