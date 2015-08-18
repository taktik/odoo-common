# coding=utf-8
from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning


class TkWorkLogInvoiceConfirmed(models.Model):
    """
    Allows to attach a worklog to an existing invoice.
    """
    _name = 'tk.worklog.invoice.confirmed'

    worklog_ids = fields.Many2many('account.analytic.line',
                                   relation='tk_worklog_confirmed_rel',
                                   column1='wiz_id',
                                   column2='worklog_id',
                                   string='Worklogs')
    invoice_id = fields.Many2one('account.invoice', string='Invoice', required=True)
    partner_domain = fields.Many2many('res.partner',
                                      relation='tk_worklog_partner_confirmed_domain_rel',
                                      column1='wiz_id',
                                      column2='partner_id',
                                      string='Partner domain for invoice')
    partner_id = fields.Many2one('res.partner', string='Partner')

    views = {
        'default': 'tk.worklog.invoice.confirm.view',
        'success': 'tk.worklog.invoice.confirm.view.success',
    }

    def default_get(self, cr, uid, fields_list, context=None):
        """
        In this function, we will check that partner is the same for all worklogs and that no worklog have already
         been invoiced
        :param cr: cursor
        :param uid: user id
        :param fields: fields
        :param context: context
        :return: dict
        """
        res = super(TkWorkLogInvoiceConfirmed, self).default_get(cr, uid, fields_list, context=context)
        if context and context.get('active_ids', False):
            active_ids = context.get('active_ids')
            customer = False

            for worklog in self.pool.get('account.analytic.line').browse(cr, uid, active_ids):
                if customer and worklog.account_id.partner_id.id != customer or not worklog.account_id.partner_id.id:
                    raise except_orm(_('Error !'), _('The Partner must be the same for all the worklog'))
                elif worklog.invoice_id:
                    raise except_orm(_('Error !'), _('Some worklog are already invoiced'))
                else:
                    customer = worklog.account_id.partner_id.id

            # Invoice id domain = partner is supplier or child of supplier
            partner_domain = [customer]
            if customer:
                child_ids = self.pool['res.partner'].search(cr, uid, [('parent_id', '=', customer)])
                partner_domain += child_ids

            res.update({
                'worklog_ids': context.get('active_ids', False),
                'partner_id': customer,
                'partner_domain': partner_domain
            })
        return res

    @api.multi
    def get_view_dict(self, view_name):
        message_view_id = self.env['ir.ui.view'].search([('name', '=', view_name)])
        result_message = {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': self._name,
            'type': 'ir.actions.act_window',
            'context': message_view_id.env.context,
            'view_id': message_view_id.id,
            'target': 'new',
            # 'res_id': ids[0],
        }
        return result_message

    @api.multi
    def next(self):
        self.ensure_one()
        invoice_id = self.invoice_id
        worklog_ids = self.worklog_ids
        self.env['account.analytic.line'].search([('id', 'in', [entry.id for entry in worklog_ids])]).write({'invoice_id': invoice_id.id})
        view = self.views['success']
        return self.get_view_dict(view)

    def act_destroy(self, *args):
        return {'type': 'ir.actions.act_window_close'}
