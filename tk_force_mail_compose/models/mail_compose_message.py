from openerp.osv import osv
from openerp import tools, SUPERUSER_ID
import threading

class MailComposeMessage(osv.TransientModel):
    _inherit = 'mail.compose.message'

    def send_mail(self, cr, uid, ids, context=None):
        """
        Add force_mail in the context.
        """
        context = dict(context or {})
        ctx = context.copy()
        ctx.update({
            'force_mail': True
        })
        super(tk_mail_compose_message, self).send_mail(cr, uid, ids, context=ctx)
