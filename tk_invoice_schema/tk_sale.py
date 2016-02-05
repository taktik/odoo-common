from openerp import models, fields, api, exceptions


class TkSaleOrder(models.Model):
    _inherit = 'sale.order'

    invoice_progress = fields.Float('Invoice Progress')

    @api.cr_uid_ids_context
    def action_button_confirm(self, cr, uid, ids, context=None):
        if not context:
            context = {}
        assert len(ids) == 1, 'This option should only be used for a single id at a time.'
        so = self.browse(cr, uid, ids[0], context=context)
        for line in so.order_line:
            if line.recurring_product and not line.subscription_id:
                raise exceptions.Warning("The line with the recurrent product [%s] %s must have a subscription." % (
                line.product_id.default_code, line.product_id.name))
        self.signal_workflow(cr, uid, ids, 'order_confirm')
        if context.get('send_email'):
            self.force_quotation_send(cr, uid, ids, context=context)
        return True

class TKSaleOrderLine(models.Model):

    _inherit = 'sale.order.line'

    recurring_product = fields.Boolean(related='product_id.recurrence')
    subscription_id = fields.Many2one('subscription.subscription', string="Subscription")