from openerp.osv import orm, fields
from openerp import SUPERUSER_ID


class tk_sale_order_line(orm.Model):
    _inherit = 'sale.order.line'

    def product_id_change_with_wh(self, cr, uid, ids, pricelist, product, qty=0,
                                  uom=False, qty_uos=0, uos=False, name='', partner_id=False,
                                  lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False, flag=False,
                                  warehouse_id=False, context=None):
        """
        Inherited from sale_stock to compute get the packagings of the selected product
        """
        packaging_obj = self.pool.get('product.packaging')
        product_product_obj = self.pool.get('product.product')
        res = super(tk_sale_order_line, self).product_id_change_with_wh(cr, uid, ids, pricelist, product, qty=qty, uom=uom, qty_uos=qty_uos,
                                                                uos=uos, name=name, partner_id=partner_id,
                                                                lang=lang, update_tax=update_tax, date_order=date_order,
                                                                packaging=packaging, fiscal_position=fiscal_position, flag=flag,
                                                                warehouse_id=warehouse_id, context=context)
        if not res:
            res = {}
        if not 'value' in res:
            res['value'] = {}
        if not 'domain' in res:
            res['domain'] = {}

        if not product:
            res['value'].update({'packaging_domain_ids': False})

        if product:
            product_record = product_product_obj.read(cr, uid, product, ['product_tmpl_id'])
            product_tmpl_id = product_record.get('product_tmpl_id', False)
            if product_tmpl_id:
                # TODO: check if we take only base, intermediate or delivery or add another (sale)?
                packaging_ids = packaging_obj.search(cr, uid, [('product_tmpl_id', '=', product_tmpl_id[0])])
                res['value'].update({'packaging_domain_ids': packaging_ids}) # Update packaging_domain_ids values
                if packaging_ids and len(packaging_ids) == 1:
                    # If only one packaging, put it directly in packaging_id
                    res['value'].update({'packaging_id': packaging_ids[0]})
                    res['domain'].update({'packaging_id': [('product_tmpl_id', '=', product_tmpl_id[0])]})

        return res

    def _get_product_qty(self, cr, uid, packaging_id, qty_packaging=0, context=None):
        """
        Internal method. Called in on_change, write and create method. This method compute the packaging qty * qty in purchase order line
        """
        # Objects
        packaging_obj = self.pool.get('product.packaging')

        packaging_record = packaging_obj.read(cr, uid, packaging_id, ['qty'], context=context)
        return packaging_record.get('qty', 0) * qty_packaging

    def onchange_qty_packaging(self, cr, uid, ids, qty_packaging, packaging_id, context=None):
        """
        Recompute the product quantity when the packaging or its quantity is changed (packaging qty * packaging coefficient (qty))
        """
        res = {}
        if packaging_id:
            res['value'] = {'product_uom_qty': self._get_product_qty(cr, uid, packaging_id, qty_packaging, context)}
        return res

    def create(self, cr, uid, vals, context=None):
        if 'qty_packaging' in vals and 'packaging_id' in vals:
            vals['product_uom_qty'] = self._get_product_qty(cr, uid, vals['packaging_id'], vals['qty_packaging'], context)
        return super(tk_sale_order_line, self).create(cr, uid, vals, context)

    _columns = {
        'qty_packaging': fields.integer('Quantity Packaging', required=False),
        'packaging_id': fields.many2one('product.packaging', 'Packaging', required=False),
        'packaging_domain_ids': fields.function(lambda self, *args, **kwargs: {}, type='many2many', obj='product.packaging', store=False),

    }


tk_sale_order_line()
