# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Taktik S.A.
#    Copyright (c) 2015 Taktik S.A. (http://www.taktik.be)
#    All Rights Reserved
#
#    WARNING: This program as such is intended to be used by professional
#    programmers who take the whole responsibility of assessing all potential
#    consequences resulting from its eventual inadequacies and bugs.
#    End users who are looking for a ready-to-use solution with commercial
#    guarantees and support are strongly advised to contact a Free Software
#    Service Company.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import models, fields, api, _, exceptions


class ResPartner(models.Model):
    _name = "res.partner"
    _inherit = ['res.partner', 'mail.thread']

    notify_email = fields.Selection(
        selection_add=[('never_except_mail_compose', 'Never Except Manual Send By Mail')],
        default='never_except_mail_compose'
    )

    @api.multi
    def _notify(self, message, force_send=False, send_after_commit=True, user_signature=True):
        # TDE TODO: model-dependant ? (like customer -> always email ?)
        message_sudo = message.sudo()
        email_channels = message.channel_ids.filtered(lambda channel: channel.email_send)

        if self.env.context.get('from_mail_compose'):
            partner_notify_domain = ('notify_email', '!=', 'none')
        else:
            partner_notify_domain = ('notify_email', 'not in', ['none', 'never_except_mail_compose'])

        self.sudo().search([
            '|',
            ('id', 'in', self.ids),
            ('channel_ids', 'in', email_channels.ids),
            ('email', '!=', message_sudo.author_id and message_sudo.author_id.email or message.email_from),
            partner_notify_domain])._notify_by_email(message, force_send=force_send,
                                                              send_after_commit=send_after_commit,
                                                              user_signature=user_signature)
        self._notify_by_chat(message)
        return True
