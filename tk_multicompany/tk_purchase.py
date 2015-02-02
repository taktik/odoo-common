from openerp.osv import orm, osv
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp import SUPERUSER_ID
from datetime import datetime

class tk_purchase_order(orm.Model):
    _inherit = 'purchase.order'

    def _choose_account_from_po_line(self, cr, uid, po_line, context=None):
        """
        Inherited method to manage a hierarchy of company with a parent company which have a chart of accounts
        """
        fiscal_obj = self.pool.get('account.fiscal.position')
        property_obj = self.pool.get('ir.property')
        res_company_obj = self.pool.get('res.company')
        res_users_obj = self.pool.get('res.users')
        po_line_obj = self.pool.get('purchase.order.line')

        user = res_users_obj.browse(cr, uid, uid)
        parent_company_id = res_company_obj.get_parent_company_id(cr, uid, context.get('force_company', False) if context.get('force_company', False) else user.company_id.id)
        context['force_company'] = parent_company_id
        po_line = po_line_obj.browse(cr, SUPERUSER_ID, po_line.id, context=context)
        if po_line.product_id:
            acc_id = po_line.product_id.property_account_expense.id
            if not acc_id:
                acc_id = po_line.product_id.categ_id.property_account_expense_categ.id

            if not acc_id:
                raise osv.except_osv('Error!', 'Define an expense account for this product: "%s" (id:%d).' % (po_line.product_id.name, po_line.product_id.id,))
        else:
            acc_id = property_obj.get(cr, uid, 'property_account_expense_categ', 'product.category', context=context).id
        fpos = po_line.order_id.fiscal_position or False

        return fiscal_obj.map_account(cr, uid, fpos, acc_id)

    def _prepare_invoice(self, cr, uid, order, line_ids, context=None):
        """
        Inherited method to manage a hierarchy of company with a parent company which have a chart of accounts
        """
        res_company_obj = self.pool.get('res.company')
        purchase_order_obj = self.pool.get('purchase.order')
        res_users_obj = self.pool.get('res.users')

        account_id = order.partner_id.property_account_payable.id
        user = res_users_obj.browse(cr, uid, uid)
        parent_company_id = res_company_obj.get_parent_company_id(cr, uid, context.get('force_company', False) if context.get('force_company', False) else user.company_id.id)
        context['force_company'] = parent_company_id
        order = purchase_order_obj.browse(cr, SUPERUSER_ID, order.id, context=context) #Fix this --> for order.partner_id.property_account_payable.id
        company_id = res_company_obj.get_parent_company_id(cr, uid, order.company_id.id)
        journal_ids = self.pool['account.journal'].search(cr, uid, [('type', '=', 'purchase'), ('company_id', '=', company_id)], limit=1)
        if not journal_ids:
            raise osv.except_osv(
                'Error!',
                'Define purchase journal for this company: "%s" (id:%d).' % (order.company_id.name, order.company_id.id))


        return {
            'name': order.partner_ref or order.name,
            'reference': order.partner_ref or order.name,
            'account_id': order.partner_id.property_account_payable.id,
            'type': 'in_invoice',
            'partner_id': order.partner_id.id,
            'currency_id': order.currency_id.id,
            'journal_id': len(journal_ids) and journal_ids[0] or False,
            'invoice_line': [(6, 0, line_ids)],
            'origin': order.name,
            'fiscal_position': order.fiscal_position.id or False,
            'payment_term': order.payment_term_id.id or False,
            'company_id': order.company_id.id,
        }

class tk_procurement_order(orm.Model):

    _inherit = 'procurement.order'

    def _get_po_line_values_from_proc(self, cr, uid, procurement, partner, company, schedule_date, context=None):
        if context is None:
            context = {}
        uom_obj = self.pool.get('product.uom')
        pricelist_obj = self.pool.get('product.pricelist')
        prod_obj = self.pool.get('product.product')
        acc_pos_obj = self.pool.get('account.fiscal.position')
        res_company_obj = self.pool.get('res.company')
        res_users_obj = self.pool.get('res.users')
        res_partner_obj = self.pool.get('res.partner')

        user = res_users_obj.browse(cr, uid, uid)
        parent_company_id = res_company_obj.get_parent_company_id(cr, uid, context.get('force_company', False) if context.get('force_company', False) else user.company_id.id)
        context['force_company'] = parent_company_id

        partner = res_partner_obj.browse(cr, uid, partner.id, context=context)

        seller_qty = procurement.product_id.seller_qty
        pricelist_id = partner.property_product_pricelist_purchase.id
        uom_id = procurement.product_id.uom_po_id.id
        qty = uom_obj._compute_qty(cr, uid, procurement.product_uom.id, procurement.product_qty, uom_id)
        if seller_qty:
            qty = max(qty, seller_qty)
        price = pricelist_obj.price_get(cr, uid, [pricelist_id], procurement.product_id.id, qty, partner.id, {'uom': uom_id})[pricelist_id]
        #Passing partner_id to context for purchase order line integrity of Line name
        new_context = context.copy()
        new_context.update({'lang': partner.lang, 'partner_id': partner.id})
        product = prod_obj.browse(cr, uid, procurement.product_id.id, context=new_context)
        taxes_ids = procurement.product_id.supplier_taxes_id
        taxes = acc_pos_obj.map_tax(cr, uid, partner.property_account_position, taxes_ids)
        name = product.partner_ref
        if product.description_purchase:
            name += '\n' + product.description_purchase

        return {
            'name': name,
            'product_qty': qty,
            'product_id': procurement.product_id.id,
            'product_uom': uom_id,
            'price_unit': price or 0.0,
            'date_planned': schedule_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            'taxes_id': [(6, 0, taxes)],
        }
