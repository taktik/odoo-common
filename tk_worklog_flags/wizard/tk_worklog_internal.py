from openerp import models, fields, api


class TkTimesheetInternal(models.Model):
    """
    Allows to flag a worklog as internal, when you don't want to invoice it
    """
    _name = 'tk.timesheet.internal'

    internal = fields.Boolean(string="Internal", default=True)

    views = {
        'default': 'timesheet.internal.view',
        'success': 'timesheet.internal.view.success',
    }

    @api.multi
    def get_view_dict(self, view_name):
        message_view_id = self.env['ir.ui.view'].search([('name', '=', view_name)])
        result_message = {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': self._name,
            'type': 'ir.actions.act_window',
            'context': self.env.context,
            'view_id': message_view_id.id,
            'target': 'new',
            'res_id': self[0].id
        }
        return result_message

    @api.multi
    def next(self):
        self.ensure_one()
        context = self.env.context

        line_ids = context['active_ids']
        if not hasattr(line_ids, '__iter__'):
            line_ids = [line_ids]

        self.env['account.analytic.line'].search([('id', 'in', line_ids)]).write({'internal': self.internal})
        view = self.views['success']
        return self.get_view_dict(view)

    def act_destroy(self, *args):
        return {'type': 'ir.actions.act_window_close'}
