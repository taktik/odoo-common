# coding=utf-8
from openerp.osv import fields, osv
from openerp.tools.translate import _
import time


class account_analytic_line(osv.osv):
    """
    Inherit account.analytic.line to change the method that creates invoices based on the worklogs.
    We keep the method as in rev <= 9209 (http://bazaar.launchpad.net/~openerp/openobject-addons/7.0/view/9209/hr_timesheet_invoice/hr_timesheet_invoice.py)
    Because changes after this revision do not compute the price based on pricelists.
    """
    _inherit = 'account.analytic.line'

    def invoice_cost_create(self, cr, uid, ids, data=None, context=None):
        analytic_account_obj = self.pool.get('account.analytic.account')
        account_payment_term_obj = self.pool.get('account.payment.term')
        invoice_obj = self.pool.get('account.invoice')
        product_obj = self.pool.get('product.product')
        invoice_factor_obj = self.pool.get('hr_timesheet_invoice.factor')
        fiscal_pos_obj = self.pool.get('account.fiscal.position')
        product_uom_obj = self.pool.get('product.uom')
        invoice_line_obj = self.pool.get('account.invoice.line')
        invoices = []
        if context is None:
            context = {}
        if data is None:
            data = {}

        journal_types = {}
        # for each account analytic line selected, we fill the journal types dictionary. This dictionary have the journal
        # type as key, the value is the account analytic lines which have the key as journal type
        for line in self.pool.get('account.analytic.line').browse(cr, uid, ids, context=context):
            if line.journal_id.type not in journal_types:
                journal_types[line.journal_id.type] = set()
            journal_types[line.journal_id.type].add(line.account_id.id)

        for journal_type, account_ids in journal_types.items():
            # One invoice per analytic account will be created
            for account in analytic_account_obj.browse(cr, uid, list(account_ids), context=context):
                partner = account.partner_id
                if (not partner) or not (account.pricelist_id):
                    raise osv.except_osv(_('Analytic Account Incomplete!'),
                                         _('Contract incomplete. Please fill in the Customer and Pricelist fields.'))

                date_due = False
                if partner.property_payment_term:
                    pterm_list = account_payment_term_obj.compute(cr, uid,
                                                                  partner.property_payment_term.id, value=1,
                                                                  date_ref=time.strftime('%Y-%m-%d'))
                    if pterm_list:
                        pterm_list = [line[0] for line in pterm_list]
                        pterm_list.sort()
                        date_due = pterm_list[-1]

                curr_invoice = {
                    'name': time.strftime('%d/%m/%Y') + ' - ' + account.name,
                    'partner_id': account.partner_id.id,
                    'company_id': account.company_id.id,
                    'payment_term': partner.property_payment_term.id or False,
                    'account_id': partner.property_account_receivable.id,
                    'currency_id': account.pricelist_id.currency_id.id,
                    'date_due': date_due,
                    'fiscal_position': account.partner_id.property_account_position.id
                }

                context2 = context.copy()
                context2['lang'] = partner.lang
                # set company_id in context, so the correct default journal will be selected
                context2['force_company'] = curr_invoice['company_id']
                # set force_company in context so the correct product properties are selected (eg. income account)
                context2['company_id'] = curr_invoice['company_id']

                last_invoice = invoice_obj.create(cr, uid, curr_invoice, context=context2)
                invoices.append(last_invoice)

                cr.execute("""SELECT product_id, to_invoice, sum(unit_amount), product_uom_id
                            FROM account_analytic_line as line LEFT JOIN account_analytic_journal journal ON (line.journal_id = journal.id)
                            WHERE account_id = %s
                                AND line.id IN %s
                                AND journal.type = %s
                                AND to_invoice IS NOT NULL
                            GROUP BY product_id, to_invoice, product_uom_id""",
                           # SELECT product_id, user_id, to_invoice, sum(unit_amount), product_uom_id
                           # GROUP BY product_id, user_id, to_invoice, product_uom_id
                           (account.id, tuple(ids), journal_type))

                # for product_id, user_id, factor_id, qty, uom in cr.fetchall():
                for product_id, factor_id, qty, uom in cr.fetchall():
                    if data.get('product'):
                        product_id = data['product'][0]
                    product = product_obj.browse(cr, uid, product_id, context=context2)
                    if not product:
                        raise osv.except_osv(_('Error!'), _(
                            'There is no product defined. Please select one or force the product through the wizard.'))
                    factor = invoice_factor_obj.browse(cr, uid, factor_id, context=context2)
                    factor_name = product_obj.name_get(cr, uid, [product_id], context=context2)[0][1]
                    if factor.customer_name:
                        factor_name += ' - ' + factor.customer_name

                    ctx = context.copy()
                    ctx.update({'uom': uom})

                    price = self._get_invoice_price(cr, uid, account, product_id, None, qty, ctx)

                    general_account = product.property_account_income or product.categ_id.property_account_income_categ
                    if not general_account:
                        raise osv.except_osv(_("Configuration Error!"),
                                             _("Please define income account for product '%s'.") % product.name)
                    taxes = product.taxes_id or general_account.tax_ids
                    tax = fiscal_pos_obj.map_tax(cr, uid, account.partner_id.property_account_position, taxes)
                    curr_line = {
                        'price_unit': price,
                        'quantity': qty,
                        'discount': factor.factor,
                        'invoice_line_tax_id': [(6, 0, tax)],
                        'invoice_id': last_invoice,
                        'name': factor_name,
                        'product_id': product_id,
                        'invoice_line_tax_id': [(6, 0, tax)],
                        'uos_id': uom,
                        'account_id': general_account.id,
                        'account_analytic_id': account.id,
                    }

                    #
                    # Compute for lines
                    #
                    cr.execute(
                        "SELECT * FROM account_analytic_line WHERE account_id = %s and id IN %s AND product_id=%s and to_invoice=%s ORDER BY account_analytic_line.date",
                        (account.id, tuple(ids), product_id, factor_id))

                    line_ids = cr.dictfetchall()
                    note = []
                    for line in line_ids:
                        # set invoice_line_note
                        details = []
                        if data.get('date', False):
                            details.append(line['date'])
                        if data.get('time', False):
                            if line['product_uom_id']:
                                details.append("%s %s" % (line['unit_amount'],
                                                          product_uom_obj.browse(cr, uid, [line['product_uom_id']],
                                                                                 context2)[0].name))
                            else:
                                details.append("%s" % (line['unit_amount'], ))
                        if data.get('name', False):
                            details.append(line['name'])
                        note.append(u' - '.join(map(lambda x: unicode(x) or '', details)))

                    if note:
                        curr_line['name'] += "\n" + ("\n".join(map(lambda x: unicode(x) or '', note)))
                    invoice_line_obj.create(cr, uid, curr_line, context=context)
                    cr.execute("update account_analytic_line set invoice_id=%s WHERE account_id = %s and id IN %s",
                               (last_invoice, account.id, tuple(ids)))

                invoice_obj.button_reset_taxes(cr, uid, [last_invoice], context)
        return invoices


account_analytic_line()
