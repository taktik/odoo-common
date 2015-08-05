from openerp import fields, models, api, exceptions
from openerp.osv import osv
from openerp import _


class tk_sale_invoice_slice(models.Model):
    _name = 'tk.sale.invoice.slice'

    invoicing_amount = fields.Float('Invoicing Amount', default=0.0)
    invoicing_percent = fields.Float('Invoicing Percent (%)')
    name = fields.Char('Name')
    invoice_date = fields.Date('Invoice Date', default=fields.Date.context_today)
    total_amount = fields.Float('Total Amount')

    @api.onchange('invoicing_percent')
    def onchange_percent(self):

        initial_invoicing_amount = self.env.context['total_amount'] or 1

        self.invoicing_amount = initial_invoicing_amount * self.invoicing_percent /100


    @api.onchange('invoicing_amount')
    def onchange_amount(self):
        initial_invoicing_amount = self.env.context['total_amount'] or 1

        self.invoicing_percent = self.invoicing_amount / initial_invoicing_amount * 100


class TkAmountInvoiceSelector(models.TransientModel):
    _name = 'tk.amount.invoice.selector'

    total_amount = fields.Float('Total Amount')
    slice_ids = fields.Many2many('tk.sale.invoice.slice', string='Slices')

    @api.cr_uid_ids_context
    def _prepare_advance_invoice_vals(self, cr, uid, ids, slice, slice_name, context=None):
        if context is None:
            context = {}
        sale_obj = self.pool.get('sale.order')
        ir_property_obj = self.pool.get('ir.property')
        fiscal_obj = self.pool.get('account.fiscal.position')
        inv_line_obj = self.pool.get('account.invoice.line')
        sale_id = context.get('active_id', [])
        sale = sale_obj.browse(cr, uid, sale_id, context=context)
        percent_amount = slice.invoicing_percent
        res = {}

        # determine and check income account
        prop = ir_property_obj.get(cr, uid,
                                   'property_account_income_categ',
                                   'product.category', context=context)
        prop_id = prop and prop.id or False
        account_id = fiscal_obj.map_account(cr, uid,
                                            sale.fiscal_position or False,
                                            prop_id)
        if not account_id:
            raise osv.except_osv(_('Configuration Error!'),
                                 _(
                                     'There is no income account defined as global property.'))
        res['account_id'] = account_id

        if percent_amount <= 0.00 and not slice.invoicing_amount:
            raise osv.except_osv(_('Incorrect Data'),
                                 _(
                                     'The value of Advance Amount must be positive.'))
        if not slice.invoicing_amount:
            inv_amount = sale.amount_untaxed * percent_amount / 100.0
        else:
            inv_amount = slice.invoicing_amount

        # determine taxes
        if res.get('invoice_line_tax_id'):
            res['invoice_line_tax_id'] = [
                (6, 0, res.get('invoice_line_tax_id'))]
        else:
            res['invoice_line_tax_id'] = False

        # create the invoice
        inv_line_values = {
            'name': slice_name,
            'origin': sale.name,
            'account_id': res.get('account_id', False),
            'price_unit': inv_amount,
            'quantity': 1.0,
            'discount': False,
            'uos_id': res.get('uos_id', False),
            'invoice_line_tax_id': [(6, 0, sale.order_line[0].tax_id.ids)],
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
            'slice_percent': percent_amount,
            'date_invoice': slice.invoice_date,
            'business_unit': sale.business_unit,
        }
        return [(sale.id, inv_values)]

    @api.multi
    def create_invoices(self):
        total_percent = 0.0
        concatenated_sol_names = ''
        inv_ids = []
        sale_order = False
        so_line_ids = []
        so_lines = self.env['sale.order.line'].browse(self.env.context['sol_to_treat'])
        total_so_lines = 0

        for sol in so_lines:
            if sol.recurring_product and len(self.slice_ids) > 1:
                raise exceptions.Warning('The recurring product must be invoiced in one slice')
            concatenated_sol_names += "%s \n" % sol.name
            sale_order = sol.order_id
            so_line_ids.append(sol.id)
            total_so_lines += sol.price_subtotal

        total_percent = sum([x.invoicing_percent for x in self.slice_ids])
        total_amount = sum(x.invoicing_amount for x in self.slice_ids)
        if total_percent != 100.0 and total_amount != total_so_lines:
            raise exceptions.Warning('Total must match 100%')

        for slice_id in self.slice_ids:
            #Complete the description name
            slice_name = "%s \n%s" % (slice_id.name, concatenated_sol_names)

            #Create invoices
            for sale_id, inv_values in self._prepare_advance_invoice_vals(slice_id, slice_name):
                inv_ids.append(
                    self.env['sale.advance.payment.inv']._create_invoices(inv_values, sale_id))
            invoice_lines = self.env['account.invoice.line'].search([('invoice_id', 'in', inv_ids)])

            #Update so lines
            self.env['sale.order.line'].browse(so_line_ids).write({'invoice_line': [(4, invoice_lines.ids)]})

        for sol in so_lines:
            if sol.recurring_product and inv_ids:
                sol.subscription_id.doc_source = 'account.invoice,%s' % inv_ids[0]

        sale_order.state = 'progress'
        return True


class TkSaleOrderLineInvoicePartially(models.TransientModel):
    _name = "sale.order.line.invoice.partially"

    name = fields.Char('Name')
    line_ids = fields.One2many('sale.order.line.invoice.partially.line', 'wizard_id', string="Lines")

    @api.multi
    def show_slices(self):
        views = self.env['ir.ui.view'].search([('name', '=', 'tk.amount.invoice.selector.slides.form')])
        sol_to_treat = []
        total_amount = 0
        for line in self.line_ids:
            if line.chosen_line:
                sol_to_treat.append(line.sale_order_line_id.id)
                total_amount += line.sale_order_line_id.price_subtotal
        context = self.env.context
        copy_context = {}
        if 'active_id' in context:
            copy_context['active_id'] = context['active_id']
        if 'active_model' in context:
            copy_context['active_model'] = context['active_model']
        if 'lang' in context:
            copy_context['lang'] = context['lang']
        if 'params' in context:
            copy_context['params'] = context['params']
        if 'search_disable_custom_filters' in context:
            copy_context['search_disable_custom_filters'] = context['search_disable_custom_filters']
        if 'tz' in context:
            copy_context['tz'] = context['tz']
        if 'uid' in context:
            copy_context['uid'] = context['uid']
        copy_context['sol_to_treat'] = sol_to_treat
        copy_context['total_amount'] = total_amount
        res_id = self.env['tk.amount.invoice.selector'].create({'total_amount': total_amount})
        result_message = {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'tk.amount.invoice.selector',
            'type': 'ir.actions.act_window',
            'context': copy_context,
            'view_id': views[0].id,
            'target': 'new',
            'res_id': res_id.id
        }
        return result_message


class TkSaleOrderLineInvoicePartiallyLine(models.TransientModel):
    _name = "sale.order.line.invoice.partially.line"

    wizard_id = fields.Many2one('sale.order.line.invoice.partially', string='Wizard')
    sale_order_line_id = fields.Many2one('sale.order.line', string='Sale Order Line')
    chosen_line = fields.Boolean('Chosen Line')
    price_subtotal = fields.Float(related='sale_order_line_id.price_subtotal', string="Price Subtotal")
    recurring_product = fields.Boolean(related='sale_order_line_id.product_id.recurrence', string="Recurrence")
    name = fields.Text(related='sale_order_line_id.name', string="Line")


class tk_sale_advance_payment_inv(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'

    advance_payment_method = fields.Selection(
        [('all', 'Invoice the whole sales order'), ('percentage', 'Percentage'),
         ('fixed', 'Fixed price (deposit)'),
         ('lines', 'Some order lines'), ('schema', 'Invoice with a schema')],
        'What do you want to invoice?', required=True,
        help="""Use Invoice the whole sale order to create the final invoice.
                Use Percentage to invoice a percentage of the total amount.
                Use Fixed Price to invoice a specific amound in advance.
                Use Some Order Lines to invoice a selection of the sales order lines.),
                Use Invoice By Slice to split the amount in several invoice """)


    def create_sale_order_partially_inv(self, so):
        line_values = []
        for line in so.order_line:
            line_val = {
                'sale_order_line_id': line.id
            }
            line_values.append((0, 0, line_val))
        vals = {'line_ids': line_values}
        return self.env['sale.order.line.invoice.partially'].create(vals)

    @api.multi
    def show_lines(self):
        if not self.env.context.get('active_ids', False):
            return False
        so_id = self.env.context['active_ids'][0]
        so = self.env['sale.order'].browse(so_id)

        partial_inv = self.create_sale_order_partially_inv(so)
        views = self.env['ir.ui.view'].search([('name', '=', 'sale.order.line.invoice.partially.form')])
        result_message = {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sale.order.line.invoice.partially',
            'type': 'ir.actions.act_window',
            'context': self.env.context,
            'view_id': views[0].id,
            'target': 'new',
            'res_id': partial_inv.id,
        }
        return result_message

