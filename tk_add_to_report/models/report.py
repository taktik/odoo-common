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
from PyPDF2.generic import ArrayObject, NameObject
from PyPDF2.utils import isString, PdfReadError
from io import BytesIO
from StringIO import StringIO


def _buildOutline(self, node):
    """
    Override the method to avoid exception PdfReadError if '/Dest' == '/__WKANCHOR_2'
    :param self:
    :param node:
    :return:
    """
    dest, title, outline = None, None, None

    if "/A" in node and "/Title" in node:
        # Action, section 8.5 (only type GoTo supported)
        title = node["/Title"]
        action = node["/A"]
        if action["/S"] == "/GoTo":
            dest = action["/D"]
    elif "/Dest" in node and "/Title" in node:
        # Destination, section 8.2.1
        title = node["/Title"]
        dest = node["/Dest"]

    if dest == '/__WKANCHOR_2':
        return None

    # if destination found, then create outline
    if dest:
        if isinstance(dest, ArrayObject):
            outline = self._buildDestination(title, dest)
        elif isString(dest) and dest in self._namedDests:
            outline = self._namedDests[dest]
            outline[NameObject("/Title")] = title
        else:
            raise PdfReadError("Unexpected destination %r" % dest)
    return outline

PdfFileReader._buildOutline = _buildOutline


class Report(models.Model):
    """
    Report
    A version of this method exist in ovizio_sale_report.
    It has changed because of the Odoo version.
    """
    _inherit = 'report'

    def get_pdf(self, cr, uid, ids, report_name, html=None, data=None, context=None):
        """
        Check if this report model need to include the 'Term and Condition' (tac) pdf.
        If True, loop on each report and add at the end the tac pdf.
        :param report_name: (string)
        :param html:
        :param data: (dict)
        :return: 'string' with pdf value
        """
        action_report_obj = self.pool.get('ir.actions.report.xml')
        report_id = action_report_obj.search(
            cr,
            uid,
            [('report_name', '=', report_name)]
        )
        report = action_report_obj.browse(
            cr,
            uid,
            report_id[0],
            context
        )
        if report.include_term_and_condition_pdf:
            tac_binary = b64decode(
                self.pool.get('res.users').browse(
                    cr, uid, uid, context).get_sale_term_and_condition()
            )

            if tac_binary:
                tac_pdf = PdfFileReader(BytesIO(tac_binary))
                merger = PdfFileMerger()

                for record in self.browse(cr, uid, ids, context=context):
                    pdf = super(Report, self).get_pdf(
                        cr,
                        uid,
                        record.ids,
                        report_name,
                        html,
                        data,
                        context
                    )
                    merger.append(StringIO(pdf))

                    merger.append(tac_pdf)

                final_pdf = StringIO()
                merger.write(final_pdf)
                return final_pdf.getvalue()
        return super(Report, self).get_pdf(
            cr,
            uid,
            ids,
            report_name,
            html,
            data,
            context
        )
