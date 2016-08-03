# -*- encoding: utf-8 -*-
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
from openerp import api, models
from base64 import b64decode
from PyPDF2 import PdfFileMerger, PdfFileReader
from io import BytesIO
from StringIO import StringIO


def _buildOutline(self, node):
    """
    Override the method to avoid exception PdfReadError if '/Dest' == '/__WKANCHOR_2'
    :param self:
    :param node:
    :return:
    """
    if node.get('/Dest', '') == '/__WKANCHOR_2':
        return None
    else:
        return super(PdfFileReader, self)._buildOutline(node)

PdfFileReader._buildOutline = _buildOutline


class Report(models.Model):
    """
    Report
    """
    _inherit = 'report'

    @api.multi
    def get_pdf(self, report_name, html=None, data=None):
        """
        Check if this report model need to include the 'Term and Condition' (tac) pdf.
        If True, loop on each report and add at the end the tac pdf.
        :param report_name: (string)
        :param html:
        :param data: (dict)
        :return: 'string' with pdf value
        """
        report_id = self.env['ir.actions.report.xml'].search([
            ('report_name', '=', report_name)
        ])
        if report_id[0].include_term_and_condition_pdf:
            tac_binary = b64decode(
                self.env['res.users'].browse(self._uid).get_sale_term_and_condition()
            )

            if tac_binary:
                tac_pdf = PdfFileReader(BytesIO(tac_binary))
                merger = PdfFileMerger()

                for record in self:
                    pdf = super(Report, record).get_pdf(
                        record,
                        report_name,
                        html=html,
                        data=data
                    )
                    merger.append(StringIO(pdf))

                    merger.append(tac_pdf)

                final_pdf = StringIO()
                merger.write(final_pdf)
                return final_pdf.getvalue()
        return super(Report, self).get_pdf(
            self,
            report_name,
            html=html,
            data=data
        )
