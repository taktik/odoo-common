from openerp import models, fields, api, _, exceptions


class ResPartner(models.Model):
    _name = "res.partner"
    _inherit = ['res.partner', 'mail.thread']

    def _register_hook(self, cr):
        """
        Adds an option in the notify_email.
        """
        self._columns['notify_email'].selection.append(
            ('never_except_mail_compose', 'Never Except Manual Send By Mail')
        )
        return super(ResPartner, self)._register_hook(cr)
