# coding=utf-8
from openerp import models, fields, api, _


class tk_account_invoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    @api.returns('mail.mail')
    def _generate_emails(self, email_template):
        """ Generate email message using template related to level """
        email_message_obj = self.env['mail.mail']
        # Warning: still using the old-api on 'email.template' because
        # the method generate_email() does not follow the cr, uid, ids
        # convention and the new api wrapper can't translate the call
        email_template_obj = self.pool['email.template']
        att_obj = self.env['ir.attachment']
        emails = email_message_obj.browse()
        required_fields = ['subject',
                           'body_html',
                           'email_from',
                           'email_to']
        cr, uid, context = self.env.cr, self.env.uid, self.env.context
        for invoice in self:
            email_values = email_template_obj.generate_email(cr, uid,
                                                             email_template.id,
                                                             invoice.id,
                                                             context=context)
            email_values['type'] = 'email'

            email = email_message_obj.create(email_values)

            state = 'sent'
            # The mail will not be send, however it will be in the pool, in an
            # error state. So we create it, link it with
            # the credit control line
            # and put this latter in a `email_error` state we not that we have
            # a problem with the email
            if not all(email_values.get(field) for field in required_fields):
                state = 'email_error'

            invoice.sent = True

            attachments = att_obj.browse()
            for att in email_values.get('attachments', []):
                attach_fname = att[0]
                attach_datas = att[1]
                data_attach = {
                    'name': attach_fname,
                    'datas': attach_datas,
                    'datas_fname': attach_fname,
                    'res_model': 'mail.mail',
                    'res_id': email.id,
                    'type': 'binary',
                }
                attachments += att_obj.create(data_attach)
            email.write({'attachment_ids': [(6, 0, attachments.ids)]})
            emails += email
        return emails

    @api.model
    @api.returns('res.partner')
    def _get_contact_address(self, partner_id):
        partner_obj = self.env['res.partner']
        partner = partner_obj.browse(partner_id)
        add_ids = partner.address_get(adr_pref=['invoice']) or {}
        add_id = add_ids['invoice']
        return partner_obj.browse(add_id)
