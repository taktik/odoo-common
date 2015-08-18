# coding=utf-8
from openerp import fields, models
from openerp.osv import osv
from openerp import _


class tk_sale_invoice_slice(models.Model):

    _name = 'tk.sale.invoice.slice'

    invoicing_amount = fields.Float('Invoicing Amount', default=0.0)
    name = fields.Char('Name')
    invoice_date = fields.Date('Invoice Date', default=fields.Date.context_today)


class tk_sale_advance_payment_inv(models.TransientModel):

    _inherit = 'sale.advance.payment.inv'

    slice_ids = fields.Many2many('tk.sale.invoice.slice', string='Slices')
    advance_payment_method = fields.Selection(
        [('all', 'Invoice the whole sales order'),
         ('percentage', 'Percentage'), ('fixed', 'Fixed price (deposit)'),
         ('lines', 'Some order lines'), ('slices', 'Invoice By Slice')],
        'What do you want to invoice?', required=True,
        help="""Use Invoice the whole sale order to create the final invoice.
                Use Percentage to invoice a percentage of the total amount.
                Use Fixed Price to invoice a specific amound in advance.
                Use Some Order Lines to invoice a selection of the sales order lines.),
                Use Invoice By Slice to split the amount in several invoice """)

    def _prepare_advance_invoice_vals(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        sale_obj = self.pool.get('sale.order')
        ir_property_obj = self.pool.get('ir.property')
        fiscal_obj = self.pool.get('account.fiscal.position')
        inv_line_obj = self.pool.get('account.invoice.line')
        wizard = self.browse(cr, uid, ids[0], context)
        sale_ids = context.get('active_ids', [])

        percent_amount = context.get('percent_amount', 0.0)
        name = context.get('name', False)

        result = []
        for sale in sale_obj.browse(cr, uid, sale_ids, context=context):
            val = inv_line_obj.product_id_change(cr, uid, [],
                                                 wizard.product_id.id,
                                                 False,
                                                 partner_id=sale.partner_id.id,
                                                 fposition_id=sale.fiscal_position.id)
            res = val['value']

            # determine and check income account
            if not wizard.product_id.id:
                prop = ir_property_obj.get(cr, uid,
                                           'property_account_income_categ',
                                           'product.category', context=context)
                prop_id = prop and prop.id or False
                account_id = fiscal_obj.map_account(cr, uid, sale.fiscal_position or False, prop_id)
                if not account_id:
                    raise osv.except_osv(_('Configuration Error!'),
                                         _(
                                             'There is no income account defined as global property.'))
                res['account_id'] = account_id
            if not res.get('account_id'):
                raise osv.except_osv(_('Configuration Error!'),
                                     _('There is no income account defined '
                                       'for this product: "%s" (id:%d).') %
                                     (wizard.product_id.name,
                                      wizard.product_id.id,))

            # determine invoice amount
            if wizard.amount <= 0.00 and wizard.advance_payment_method != 'slices':
                raise osv.except_osv(_('Incorrect Data'),
                                     _(
                                         'The value of Advance Amount '
                                         'must be positive.'))
            if wizard.advance_payment_method == 'percentage':
                inv_amount = sale.amount_untaxed * wizard.amount / 100
                if not res.get('name'):
                    res['name'] = self._translate_advance(cr, uid, percentage=True, context=dict(context, lang=sale.partner_id.lang)) % (wizard.amount)
            if wizard.advance_payment_method == 'slices':
                if percent_amount <= 0.00:
                    raise osv.except_osv(_('Incorrect Data'),
                                         _(
                                             'The value of Advance Amount'
                                             ' must be positive.'))
                inv_amount = sale.amount_untaxed * percent_amount / 100.0
                res['name'] = name
            else:
                inv_amount = percent_amount
                if not res.get('name'):
                    # TODO: should find a way to call formatLang() from rml_parse
                    symbol = sale.pricelist_id.currency_id.symbol
                    if sale.pricelist_id.currency_id.position == 'after':
                        symbol_order = (inv_amount, symbol)
                    else:
                        symbol_order = (symbol, inv_amount)
                    res['name'] = self._translate_advance(cr, uid, context=dict(context, lang=sale.partner_id.lang)) % symbol_order

            # determine taxes
            if res.get('invoice_line_tax_id'):
                res['invoice_line_tax_id'] = [(6, 0, res.get('invoice_line_tax_id'))]
            else:
                res['invoice_line_tax_id'] = False

            # create the invoice
            inv_line_values = {
                'name': res.get('name'),
                'origin': sale.name,
                'account_id': res['account_id'],
                'price_unit': inv_amount,
                'quantity': wizard.qtty or 1.0,
                'discount': False,
                'uos_id': res.get('uos_id', False),
                'product_id': wizard.product_id.id,
                'invoice_line_tax_id': res.get('invoice_line_tax_id'),
                'account_analytic_id': sale.project_id.id or False,
            }
            inv_values = {
                'name': sale.client_order_ref or sale.name,
                'origin': sale.name,
                'type': 'out_invoice',
                'reference': False,
                'account_id': sale.partner_id.property_account_receivable.id,
                'partner_id': sale.partner_invoice_id.id,
                'invoice_line': [(0, 0, inv_line_values)],
                'currency_id': sale.pricelist_id.currency_id.id,
                'comment': '',
                'payment_term': sale.payment_term.id,
                'fiscal_position': sale.fiscal_position.id or sale.partner_id.property_account_position.id,
                'section_id': sale.section_id.id,
                'slice_percent': percent_amount or wizard.amount,
                'date_invoice': context.get('date_invoice', False),
                'business_unit': sale.business_unit,
            }
            result.append((sale.id, inv_values))
        return result

    def create_invoices(self, cr, uid, ids, context=None):
        """ create invoices for the active sales orders """
        sale_obj = self.pool.get('sale.order')
        act_window = self.pool.get('ir.actions.act_window')
        wizard = self.browse(cr, uid, ids[0], context)
        sale_ids = context.get('active_ids', [])
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

        inv_ids = []
        if wizard.advance_payment_method == 'slices':
            slices = [(x.name, x.invoicing_amount, x.invoice_date) for x in wizard.slice_ids]
            invoicing_amout_total = sum([x[1] for x in slices])
            if invoicing_amout_total != 100:
                raise osv.except_osv(_('Invalid Amount'),
                                     _(
                                         'The total invoicing amount '
                                         'is different from 100 %%'))
            for name, percent_amount, invoice_date in slices:
                context['name'] = name
                context['percent_amount'] = percent_amount
                context['date_invoice'] = invoice_date
                for sale_id, inv_values in self._prepare_advance_invoice_vals(cr, uid, ids, context=context):
                    inv_ids.append(self._create_invoices(cr, uid, inv_values, sale_id, context=context))
                context['name'] = False
                context['percent_amount'] = False
        else:
            for sale_id, inv_values in self._prepare_advance_invoice_vals(cr, uid, ids, context=context):
                inv_ids.append(self._create_invoices(cr, uid, inv_values, sale_id, context=context))

        if context.get('open_invoices', False):
            return self.open_invoices(cr, uid, ids, inv_ids, context=context)
        return {'type': 'ir.actions.act_window_close'}


