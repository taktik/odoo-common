# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2010 Camptocamp SA (http://www.camptocamp.com) 
# All Right Reserved
#
# Author : Nicolas Bessi (Camptocamp)
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

from osv import osv, fields
from openerp import netsvc
from openerp.report.report_sxw import rml_parse
from tk_webkit_report_parser import tk_WatermarkWebKitParser
from report_webkit import ir_report

old_register_report_method = ir_report.register_report


def tk_register_report_watermark(name, model, tmpl_path, parser=rml_parse):
    """Register the report into the services.
    Override the original register_report method to pass our webkit parser.
    The tk_WatermarkWebKitParser extends the tk_WebKitParser.
    So in addition to the capabilities of tk_WebKitParser, we will have the watermark possibility.
    """
    name = 'report.%s' % name
    if netsvc.Service._services.get(name, False):
        service = netsvc.Service._services[name]
        if isinstance(service, tk_WatermarkWebKitParser):
            #already instantiated properly, skip it
            return
        if hasattr(service, 'parser'):
            parser = service.parser
        del netsvc.Service._services[name]
    tk_WatermarkWebKitParser(name, model, tmpl_path, parser=parser)


ir_report.register_report = tk_register_report_watermark


class tk_WatermarkReportXML(osv.osv):
    _inherit = 'ir.actions.report.xml'

    _columns = {
        'watermark_pdf_first': fields.many2one('ir.attachment', 'Watermark PDF for first page'),
        'watermark_pdf_inner': fields.many2one('ir.attachment', 'Watermark PDF for inner pages'),
        'watermark_pdf_last': fields.many2one('ir.attachment', 'Watermark PDF for last page'),
        'use_same_watermark_on_first_page': fields.boolean('Use same watermark on first page'),
        'use_same_watermark_on_last_page': fields.boolean('Use same watermark on last page'),
        'use_watermark': fields.boolean('Use watermark PDF'),
    }


tk_WatermarkReportXML()
