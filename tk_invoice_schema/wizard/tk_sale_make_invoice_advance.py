
from openerp import fields, models, api, exceptions

class taktik_sale_advance_payment_inv(models.TransientModel):

    _inherit = "sale.advance.payment.inv"

    @api.cr_uid_ids_context
    def create_invoices(self, cr, uid, ids, context=None):
        """ create invoices for the active sales orders """
        sale_obj = self.pool.get('sale.order')
        act_window = self.pool.get('ir.actions.act_window')
        wizard = self.browse(cr, uid, ids[0], context)
        sale_ids = context.get('active_ids', [])
        if wizard.advance_payment_method != 'schema':
            for so in sale_obj.browse(cr, uid, sale_ids, context=context):
                for line in so.order_line:
                    if line.recurring_product:
                        raise exceptions.Warning("You must use invoicing schema if you have a recurring product")
        if wizard.advance_payment_method == 'all':
            # create the final invoices of the active sales orders
            res = sale_obj.manual_invoice(cr, uid, sale_ids, context)
            if context.get('open_invoices', False):
                return res
            return {'type': 'ir.actions.act_window_close'}

        if wizard.advance_payment_method == 'lines':
            # open the list view of sales order lines to invoice
            res = act_window.for_xml_id(cr, uid, 'sale', 'action_order_line_tree2', context)
            res['context'] = {
                'search_default_uninvoiced': 1,
                'search_default_order_id': sale_ids and sale_ids[0] or False,
            }
            return res
        assert wizard.advance_payment_method in ('fixed', 'percentage')

        inv_ids = []
        for sale_id, inv_values in self._prepare_advance_invoice_vals(cr, uid, ids, context=context):
            inv_ids.append(self._create_invoices(cr, uid, inv_values, sale_id, context=context))

        if context.get('open_invoices', False):
            return self.open_invoices( cr, uid, ids, inv_ids, context=context)
        return {'type': 'ir.actions.act_window_close'}