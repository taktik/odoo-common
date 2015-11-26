from openerp import tools, SUPERUSER_ID
from openerp import models, fields, api, _, exceptions


class MailNotification(models.Model):
    _inherit = 'mail.notification'

    def get_partners_to_email(self, cr, uid, ids, message, context=None):
        """
        Return the list of partners to notify, based on their preferences.
        Override to get the partner if force_mail is set in the context,
        even if the partner.notify_email is none.
        """
        notify_pids = []
        for notification in self.browse(cr, uid, ids, context=context):
            if notification.is_read:
                continue
            partner = notification.partner_id
            # Do not send to partners without email address defined
            if not partner.email:
                continue
            # Do not send to partners having same email address than the author (can cause loops or bounce effect due to messy database)
            if message.author_id and message.author_id.email == partner.email:
                continue
            # Partner does not want to receive any emails or is opt-out
            if not context.get('force_mail', False) and partner.notify_email == 'none':
                continue
            notify_pids.append(partner.id)
        return notify_pids

    def _notify_email(self, cr, uid, ids, message_id, force_send=False, user_signature=True, context=None):
        """
        Override to pass the context in get_partners_to_email.
        """
        message = self.pool['mail.message'].browse(cr, SUPERUSER_ID, message_id, context=context)

        # compute partners
        email_pids = self.get_partners_to_email(cr, uid, ids, message, context=context)
        if not email_pids:
            return True

        # compute email body (signature, company data)
        body_html = message.body
        # add user signature except for mail groups, where users are usually adding their own signatures already
        user_id = message.author_id and message.author_id.user_ids and message.author_id.user_ids[0] and message.author_id.user_ids[0].id or None
        signature_company = self.get_signature_footer(cr, uid, user_id, res_model=message.model, res_id=message.res_id, context=context, user_signature=(user_signature and message.model != 'mail.group'))
        if signature_company:
            body_html = tools.append_content_to_html(body_html, signature_company, plaintext=False, container_tag='div')

        # compute email references
        references = message.parent_id.message_id if message.parent_id else False

        # custom values
        custom_values = dict()
        if message.model and message.res_id and self.pool.get(message.model) and hasattr(self.pool[message.model], 'message_get_email_values'):
            custom_values = self.pool[message.model].message_get_email_values(cr, uid, message.res_id, message, context=context)

        # create email values
        max_recipients = 50
        chunks = [email_pids[x:x + max_recipients] for x in xrange(0, len(email_pids), max_recipients)]
        email_ids = []
        for chunk in chunks:
            mail_values = {
                'mail_message_id': message.id,
                'auto_delete': (context or {}).get('mail_auto_delete', True),
                'mail_server_id': (context or {}).get('mail_server_id', False),
                'body_html': body_html,
                'recipient_ids': [(4, id) for id in chunk],
                'references': references,
            }
            mail_values.update(custom_values)
            email_ids.append(self.pool.get('mail.mail').create(cr, uid, mail_values, context=context))
        # NOTE:
        #   1. for more than 50 followers, use the queue system
        #   2. do not send emails immediately if the registry is not loaded,
        #      to prevent sending email during a simple update of the database
        #      using the command-line.
        if force_send and len(chunks) < 2 and \
               (not self.pool._init or
                getattr(threading.currentThread(), 'testing', False)):
            self.pool.get('mail.mail').send(cr, uid, email_ids, context=context)
        return True
