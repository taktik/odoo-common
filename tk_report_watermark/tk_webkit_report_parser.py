# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2010 Camptocamp SA (http://www.camptocamp.com) 
# All Right Reserved
#
# Author : Nicolas Bessi (Camptocamp)
# Contributor(s) : Florent Xicluna (Wingo SA)
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

import base64
from pyPdf import PdfFileWriter, PdfFileReader
import cStringIO
from tk_report_parser.tk_report_parser import tk_WebKitParser


class tk_WatermarkWebKitParser(tk_WebKitParser):
    """
    Inherit tk_WebKitParser to add watermarking possibilities.
    """

    def create_single_pdf(self, cursor, uid, ids, data, report_xml, context=None):
        if not report_xml.use_watermark or (not report_xml.watermark_pdf_first and \
                                                not report_xml.watermark_pdf_inner and \
                                                not report_xml.watermark_pdf_last):
            # No watermark needed, or no watermark attachment found
            return super(tk_WatermarkWebKitParser, self).create_single_pdf(cursor, uid, ids, data, report_xml, context=context)
        context['use_watermark'] = True # So the report parser will know if we are watermarking
        doc, type = super(tk_WatermarkWebKitParser, self).create_single_pdf(cursor, uid, ids, data, report_xml, context=context)
        if context.get('use_watermark'):
            context.pop('use_watermark') # Remove from context

        # TODO : find better way to watermark, use of StringIO with a lot of data can be slow / impossible
        original = cStringIO.StringIO(doc)

        input_pdf = PdfFileReader(original)

        if report_xml.watermark_pdf_first:
            watermark_file_content_first = base64.decodestring(report_xml.watermark_pdf_first.db_datas)
            watermark_file_first = cStringIO.StringIO(watermark_file_content_first)
            wm_first = PdfFileReader(watermark_file_first)
        if report_xml.watermark_pdf_inner:
            watermark_file_content_inner = base64.decodestring(report_xml.watermark_pdf_inner.db_datas)
            watermark_file_inner = cStringIO.StringIO(watermark_file_content_inner)
            wm_inner = PdfFileReader(watermark_file_inner)
        if report_xml.watermark_pdf_last:
            watermark_file_content_last = base64.decodestring(report_xml.watermark_pdf_last.db_datas)
            watermark_file_last = cStringIO.StringIO(watermark_file_content_last)
            wm_last = PdfFileReader(watermark_file_last)

        output = PdfFileWriter()

        for i in range(0, input_pdf.getNumPages()):
            # Watermark all pages from the pdf
            wm = False
            if i == 0:
                if report_xml.watermark_pdf_first and wm_first:
                    wm = wm_first
                elif report_xml.use_same_watermark_on_first_page:
                    wm = wm_inner
            elif i == input_pdf.getNumPages() - 1:
                if report_xml.watermark_pdf_last and wm_last:
                    wm = wm_last
                elif report_xml.use_same_watermark_on_last_page:
                    wm = wm_inner
            else:
                if report_xml.watermark_pdf_inner:
                    wm = wm_inner
            page = input_pdf.getPage(i)
            if wm:
                page.mergePage(wm.getPage(0))
            output.addPage(page)

        ostream = cStringIO.StringIO()
        output.write(ostream)
        ostream.seek(0)

        final_pdf = ostream.read()
        ostream.close()
        original.close()

        return (final_pdf, 'pdf')