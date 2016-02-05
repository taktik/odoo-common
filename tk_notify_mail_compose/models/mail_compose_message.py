from openerp.osv import osv
from openerp import tools, SUPERUSER_ID
import threading

class MailComposeMessage(osv.TransientModel):
    _inherit = 'mail.compose.message'

    def send_mail(self, cr, uid, ids, context=None):
        """
        Add from_mail_compose in the context.
        """
        context = dict(context or {})
        ctx = context.copy()
        ctx.update({
            'from_mail_compose': True
        })
        super(MailComposeMessage, self).send_mail(cr, uid, ids, context=ctx)
