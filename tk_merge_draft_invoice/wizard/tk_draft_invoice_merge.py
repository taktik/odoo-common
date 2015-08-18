# coding=utf-8
from openerp.osv import fields, osv
from openerp.tools.translate import _


class tk_draft_invoice_merge(osv.osv_memory):
    _name = 'tk_draft_invoice_merge'

    _columns = {
        'invoice_ids': fields.many2many('account.invoice', 'tk_merge_draft_invoice_rel', 'wiz_id', 'invoice_id',
                                        'Invoices'),
        'invoice_id': fields.many2one('account.invoice', 'Invoice', domain="[('id','in',invoice_ids[0][2])]",
                                      required=True),
    }

    views = {
        'default': 'tk.draft.invoice.merge.view',
        'success': 'tk.draft.invoice.merge.view.success',
    }

    def default_get(self, cr, uid, fields, context=None):
        res = super(tk_draft_invoice_merge, self).default_get(cr, uid, fields, context)
        if context and context.get('active_ids', False):
            active_ids = context.get('active_ids')
            supplier = False
            for invoice in self.pool.get('account.invoice').browse(cr, uid, active_ids):
                if invoice.state != 'draft':
                    raise osv.except_osv(_('Error !'), _('You can\'t merge non-draft invoices'))
                if supplier and invoice.partner_id.id != supplier:
                    raise osv.except_osv(_('Error !'), _('The Partner must be the same for all the invoice'))
                else:
                    supplier = invoice.partner_id.id

            res.update({'invoice_ids': context.get('active_ids', False)})
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
        wizard = self.browse(cr, uid, ids[0])
        invoice = wizard.invoice_id
        invoice_ids = wizard.invoice_ids
        for inv in invoice_ids:
            if invoice.id != inv.id:
                self.pool.get('account.invoice.line').write(cr, uid, [line.id for line in inv.invoice_line],
                                                            {'invoice_id': invoice.id})
                account_analytic_line_ids = self.pool.get('account.analytic.line').search(cr, uid,
                                                                                          [('invoice_id', '=', inv.id)])
                if account_analytic_line_ids and len(account_analytic_line_ids) >= 1:
                    self.pool.get('account.analytic.line').write(cr, uid, account_analytic_line_ids,
                                                                 {'invoice_id': invoice.id})
                self.pool.get('account.invoice').unlink(cr, uid, [inv.id])
        self.pool.get('account.invoice').button_compute(cr, uid, [invoice.id])
        view = self.views['success']
        return self.get_view_dict(cr, uid, ids, view, context)

    def act_destroy(self, *args):
        return {'type': 'ir.actions.act_window_close'}


tk_draft_invoice_merge()
