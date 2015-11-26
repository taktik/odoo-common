# coding=utf-8
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp.osv.orm import browse_record_list, browse_record, browse_null


class tk_worklog_invoice(osv.osv_memory):
    _name = 'tk_worklog_invoice'

    _columns = {
        'worklog_ids': fields.many2many('account.analytic.line', 'tk_worklog_rel', 'wiz_id', 'worklog_id', 'Worklogs'),
        'invoice_id': fields.many2one('account.invoice', 'Invoice', required=True),
        'partner_id': fields.many2one('res.partner', 'Partner'),
        'partner_domain': fields.many2many('res.partner', 'tk_worklog_partner_domain_rel', 'wiz_id', 'partner_id', 'Partner domain for invoice'),
        'create_lines': fields.boolean('Create Invoice Lines'),
        'date': fields.boolean('Date', help='The real date of each work will be displayed on the invoice'),
        'time': fields.boolean('Time spent', help='The time of each work done will be displayed on the invoice'),
        'name': fields.boolean('Description', help='The detail of each work done will be displayed on the invoice'),
        'price': fields.boolean('Cost', help='The cost of each work done will be displayed on the invoice. You probably don\'t want to check this'),
    }

    _defaults = {
        'create_lines': True,
        'date': 1,
        'name': 1,
    }

    views = {
        'default': 'tk.worklog.invoice.view',
        'success': 'tk.worklog.invoice.view.success',
    }

    def default_get(self, cr, uid, fields, context=None):
        """
        In this function, we will check that partner is the same for all worklogs
        :param cr: cursor
        :param uid: user id
        :param fields: fields
        :param context: context
        :return: dict
        """
        res = super(tk_worklog_invoice, self).default_get(cr, uid, fields, context)
        if context and context.get('active_ids', False):
            active_ids = context.get('active_ids')
            supplier = False

            for worklog in self.pool.get('account.analytic.line').browse(cr, uid, active_ids):
                if supplier and worklog.account_id.partner_id.id != supplier or not worklog.account_id.partner_id.id:
                    raise osv.except_osv(_('Error !'), _('The Partner must be the same for all the worklog'))
                elif isinstance(worklog.to_invoice, browse_null):
                    raise osv.except_osv(_('Error !'), _('Some worklog are not invoiceable'))
                elif worklog.invoice_id:
                    raise osv.except_osv(_('Error !'), _('Some worklog are already invoiced'))
                else:
                    supplier = worklog.account_id.partner_id.id

            # Invoice id domain = partner is supplier or child of supplier
            partner_domain = [supplier]
            if supplier:
                child_ids = self.pool.get('res.partner').search(cr, uid, [('parent_id', '=', supplier)])
                partner_domain += child_ids

        res.update({'worklog_ids': context.get('active_ids', False), 'partner_id': supplier, 'partner_domain': partner_domain})
        return res

    def get_view_dict(self, cr, uid, ids, view_name, context=None):
        message_view_id = self.pool.get('ir.ui.view').search(cr, uid,
                                                             [('name', '=', view_name)])
        result_message = {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': self._name,
            'type': 'ir.actions.act_window',
            'context': context,
            'view_id': message_view_id,
            'target': 'new',
            'res_id': ids[0],
        }
        return result_message

    def next(self, cr, uid, ids, context=None):
        invoice_obj = self.pool.get('account.invoice')
        product_obj = self.pool.get('product.product')
        invoice_factor_obj = self.pool.get('hr_timesheet_invoice.factor')
        pro_price_obj = self.pool.get('product.pricelist')
        fiscal_pos_obj = self.pool.get('account.fiscal.position')
        product_uom_obj = self.pool.get('product.uom')
        invoice_line_obj = self.pool.get('account.invoice.line')

        data = self.read(cr, uid, ids, [], context=context)[0]
        if data is None:
            data = {}

        wizard = self.browse(cr, uid, ids[0])
        invoice_id = wizard.invoice_id
        worklogs = wizard.worklog_ids
        worklog_ids = [x.id for x in worklogs]
        partner = wizard.partner_id
        create_lines = wizard.create_lines

        # Check account ids
        account_ids = list(set([worklog.account_id and worklog.account_id.id or False for worklog in worklogs]))
        if len(account_ids) > 1:
            raise osv.except_osv('Error in accounts', 'Some worklogs have different accounts')

        context2 = context.copy()
        context2['lang'] = partner.lang

        # Get analytic lines groupes by product and product UOM
        SQL = '''SELECT product_id, to_invoice, sum(unit_amount), product_uom_id
            FROM account_analytic_line as line
            WHERE account_id = %s
            AND id in %s AND to_invoice IS NOT NULL
            GROUP BY product_id,to_invoice,product_uom_id
            ''' % (account_ids[0], tuple(worklog_ids) if len(worklog_ids) > 1 else "(" + str(worklog_ids[0]) + ")")
        cr.execute(SQL)

        for product_id, factor_id, qty, uom in cr.fetchall():
            product = product_obj.browse(cr, uid, product_id, context2)
            if not product:
                raise osv.except_osv(_('Error'), _('At least one line has no product !'))
            factor = invoice_factor_obj.browse(cr, uid, factor_id, context2)
            if factor.customer_name:
                factor_name = product.name + ' - ' + factor.customer_name
            else:
                factor_name = product.name
            ctx = context.copy()
            ctx.update({'uom': uom})
            if worklog.account_id.pricelist_id:
                pl = worklog.account_id.pricelist_id.id
                price = pro_price_obj.price_get(cr, uid, [pl], product_id, qty or 1.0, worklog.account_id.partner_id.id,
                                                context=ctx)[pl]
            else:
                price = 0.0

            taxes = product.taxes_id
            tax = fiscal_pos_obj.map_tax(cr, uid, worklog.account_id.partner_id.property_account_position, taxes)
            account_id = product.product_tmpl_id.property_account_income.id or product.categ_id.property_account_income_categ.id
            if not account_id:
                raise osv.except_osv(_("Configuration Error"),
                                     _("No income account defined for product '%s'") % product.name)
            curr_line = {
                'price_unit': price,
                'quantity': qty,
                'discount': factor.factor,
                'invoice_line_tax_id': [(6, 0, tax)],
                'invoice_id': invoice_id.id,
                'name': factor_name,
                'product_id': product_id,
                'invoice_line_tax_id': [(6, 0, tax)],
                'uos_id': uom,
                'account_id': account_id,
                'account_analytic_id': worklog.account_id.id,
            }

            #
            # Compute for lines
            #
            cr.execute(
                "SELECT * FROM account_analytic_line WHERE account_id = %s and id in %s AND product_id=%s and to_invoice=%s ORDER BY account_analytic_line.date",
                (account_ids[0], tuple(worklog_ids), product_id, factor_id))

            line_ids = cr.dictfetchall()
            note = []
            for line in line_ids:
                # set invoice_line_note
                details = []
                if data.get('date', False):
                    details.append(line['date'])
                if data.get('time', False):
                    if line['product_uom_id']:
                        details.append("%s %s" % (round(line.get('unit_amount', 0), 2), product_uom_obj.browse(cr, uid, [line['product_uom_id']], context2)[0].name))
                    else:
                        details.append("%s" % (round(line.get('unit_amount', 0), 2), ))
                if data.get('name', False):
                    details.append(line['name'])
                note.append(u' - '.join(map(lambda x: unicode(x) or '', details)))

            if note:
                curr_line['name'] += "\n" + ("\n".join(map(lambda x: unicode(x) or '', note)))

            if create_lines:
                invoice_line_obj.create(cr, uid, curr_line, context=context)
            cr.execute("update account_analytic_line set invoice_id=%s WHERE account_id = %s and id IN %s",
                       (invoice_id.id, account_ids[0], tuple(worklog_ids)))
            self.pool.get('account.analytic.line').write(cr, uid, [worklog.id],
                                                         {'to_invoice': factor.id, 'invoice_id': invoice_id.id})
        invoice_obj.button_reset_taxes(cr, uid, [invoice_id.id], context)

        invoice_obj.button_reset_taxes(cr, uid, [invoice_id.id], context)
        view = self.views['success']
        return self.get_view_dict(cr, uid, ids, view, context)

    def act_destroy(self, *args):
        return {'type': 'ir.actions.act_window_close'}


tk_worklog_invoice()
