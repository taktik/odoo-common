# -*- coding: utf-8 -*-
import re
from openerp.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from datetime import datetime, timedelta
import random
from openerp import models, api, fields



def random_token():
    """
    Compute a random token
    :return: string
    """
    # the token has an entropy of about 120 bits (6 bits/char * 20 chars)
    chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
    return ''.join(random.SystemRandom().choice(chars) for i in xrange(20))


class HrHoliday(models.Model):
    _inherit = 'hr.holidays'

    @api.multi
    def replace_links_body(self, mail_values):
        """
        Replace the value of links in the email template with the updated
        values (token, id , ...)
        """
        action_id = self.env.ref('hr_holidays.open_ask_holidays').id

        hr_holidays_id = self.id

        menu_id = self.env.ref('hr_holidays.menu_open_ask_holidays_new').id

        accept = 'leave_request/accept/%s' % self.token
        decline = 'leave_request/refuse/%s' % self.token
        leave_request = 'web#id=%s&view_type=form&model=hr.holidays&menu_id=%s&action=%s' % (
            str(hr_holidays_id),
            str(menu_id),
            str(action_id)
        )

        mail_body = mail_values.get('body', '')
        mail_body_html = mail_values.get('body_html', '')

        rdict = {
            '_URL_ACCEPT_': accept,
            '_URL_DECLINE_': decline,
            '_URL_LEAVE_REQUEST_': leave_request,
        }

        robj = re.compile('|'.join(rdict.keys()))
        result_body = robj.sub(
            lambda m: rdict[m.group(0)],
            mail_body
        )
        result_body_html = robj.sub(
            lambda m: rdict[m.group(0)],
            mail_body_html
        )

        mail_values.update({
            'body': result_body,
            'body_html': result_body_html
        })

        return mail_values

    @api.model
    def create(self, values):

        res = super(HrHoliday, self).create(values)
        mail_obj = self.env['mail.mail']
        template_id = self.env.ref(
            'tk_hr_approve_request.tk_hr_request_mail_template'
        )
        recipient_id = res.employee_id.parent_id.user_id.partner_id.id
        res.token = random_token()
        mail_values = template_id.generate_email(template_id.id, res.id)
        mail_values['recipient_ids'] = [(4, recipient_id)]
        mail_values = res.replace_links_body(mail_values)
        msg_id = mail_obj.create(mail_values)
        return res

    def format_date(self, date):
        if date:
            return datetime.strptime(
                date,
                DEFAULT_SERVER_DATETIME_FORMAT
            ).strftime("%H:%M:%S %d-%m-%Y")
        else:
            return ''

    token = fields.Char(
        string="Token",
        required=False
    )
