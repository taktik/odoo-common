# -*- coding: utf-8 -*-
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
    def replace_links_body(self, template):
        """
        Replace the value of links in the email template with the updated
        values (token, id , ...)
        :param template: email.template
        :return: new email.template
        """
        if template:

            template_copy = template.copy()
            base_url = self.env['ir.config_parameter'].get_param(
                'web.base.url'
            )
            to_partner_id = self.env['ir.config_parameter'].get_param(
                'leave_request_mail_to_partner_id'
            )

            action_id = self.env.ref('hr_holidays.open_ask_holidays').id
            hr_holidays_id = self.id
            menu_id = self.env.ref('hr_holidays.menu_open_ask_holidays_new').id

            accept = '%s/leave_request/accept/%s' % (base_url, self.token)
            decline = '%s/leave_request/refuse/%s' % (base_url, self.token)
            leave_request = '%s/web#id=%s&view_type=form&model=hr.holidays&menu_id=%s&action=%s' % (
                base_url, str(hr_holidays_id), str(menu_id), str(action_id)
            )

            template_copy.body_html = template_copy.body_html.replace(
                '_URL_ACCEPT_', accept
            )
            template_copy.body_html = template_copy.body_html.replace(
                '_URL_DECLINE_', decline
            )

            template_copy.body_html = template_copy.body_html.replace(
                '_URL_LEAVE_REQUEST_', leave_request
            )
            template_copy.partner_to = to_partner_id

            return template_copy

    @api.model
    def create(self, values):

        res = super(HrHoliday, self).create(values)
        data_obj = self.env['ir.model.data']

        template_id = data_obj.xmlid_to_object(
            'tk_hr_approve_request.tk_hr_request_mail_template'
        )

        res.token = random_token()
        new_template = res.replace_links_body(template_id)
        new_template.send_mail(res.id)
        new_template.partner_to = ''

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
