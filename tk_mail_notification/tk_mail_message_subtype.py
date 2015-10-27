from openerp import models, fields


class tk_mail_notification(models.Model):
    _inherit = 'mail.message.subtype'

    send_by_mail = fields.Boolean('Send by mail')