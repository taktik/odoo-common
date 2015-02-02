from openerp.osv import fields, osv
from openerp.tools.translate import _

class tk_worklog_invoice_confirmed(osv.osv_memory):
    _name = 'tk_worklog_invoice_confirmed'

    _columns = {
        'worklog_ids': fields.many2many('account.analytic.line', 'tk_worklog_confirmed_rel', 'wiz_id', 'worklog_id',
            'Worklogs'),
        'invoice_id': fields.many2one('account.invoice', 'Invoice', required=True),
        'partner_domain': fields.many2many('res.partner', 'tk_worklog_partner_confirmed_domain_rel', 'wiz_id', 'partner_id', 'Partner domain for invoice'),
        'partner_id': fields.many2one('res.partner', 'Partner'),
    }

    views = {
        'default': 'tk.worklog.invoice.confirm.view',
        'success': 'tk.worklog.invoice.confirm.view.success',
    }

    def default_get(self, cr, uid, fields, context=None):
        """
        In this function, we will check that partner is the same for all worklogs and that no worklog have already
         been invoiced
        :param cr: cursor
        :param uid: user id
        :param fields: fields
        :param context: context
        :return: dict
        """
        res = super(tk_worklog_invoice_confirmed, self).default_get(cr, uid, fields, context)
        if context and context.get('active_ids', False):
            active_ids = context.get('active_ids')
            customer = False

            for worklog in self.pool.get('account.analytic.line').browse(cr, uid, active_ids):
                if customer and worklog.account_id.partner_id.id != customer or not worklog.account_id.partner_id.id:
                    raise osv.except_osv(_('Error !'), _('The Partner must be the same for all the worklog'))
                elif worklog.invoice_id:
                    raise osv.except_osv(_('Error !'), _('Some worklog are already invoiced'))
                else:
                    customer = worklog.account_id.partner_id.id

            # Invoice id domain = partner is supplier or child of supplier
            partner_domain = [customer]
            if customer:
                child_ids = self.pool.get('res.partner').search(cr, uid, [('parent_id', '=', customer)])
                partner_domain += child_ids

            res.update({'worklog_ids': context.get('active_ids', False), 'partner_id': customer, 'partner_domain': partner_domain})
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
        invoice_id = wizard.invoice_id
        worklog_ids = wizard.worklog_ids
        self.pool.get('account.analytic.line').write(cr, uid, [entry.id for entry in worklog_ids],
            {'invoice_id': invoice_id.id})

        view = self.views['success']
        return self.get_view_dict(cr, uid, ids, view, context)

    def act_destroy(self, *args):
        return {'type': 'ir.actions.act_window_close'}


tk_worklog_invoice_confirmed()