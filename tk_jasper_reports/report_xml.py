# encoding: iso-8859-15
# #############################################################################
#
# Copyright (c) 2008-2012 NaN Projectes de Programari Lliure, S.L.
# http://www.NaN-tic.com
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
import unicodedata
from xml.dom.minidom import getDOMImplementation
import os
import base64

from openerp import report
from openerp.osv import orm, fields, osv
from openerp.tools.translate import _
from openerp.report.report_sxw import rml_parse


import jasper_report


class report_xml_file(osv.osv):
    _name = 'ir.actions.report.xml.file'
    _columns = {
    'file': fields.binary('File', required=True, filters="*.jrxml,*.properties,*.ttf", help=''),
    'filename': fields.char('File Name', size=256, required=False, help=''),
    'report_id': fields.many2one('ir.actions.report.xml', 'Report', required=True, ondelete='cascade', help=''),
    'default': fields.boolean('Default', help=''),
    }

    def create(self, cr, uid, vals, context=None):
        result = super(report_xml_file, self).create(cr, uid, vals, context)
        self.pool.get('ir.actions.report.xml').update(cr, uid, [vals['report_id']], context)
        return result

    def write(self, cr, uid, ids, vals, context=None):
        result = super(report_xml_file, self).write(cr, uid, ids, vals, context)
        for attachment in self.browse(cr, uid, ids, context):
            self.pool.get('ir.actions.report.xml').update(cr, uid, [attachment.report_id.id], context)
        return result


# Inherit ir.actions.report.xml and add an action to be able to store .jrxml and .properties
# files attached to the report so they can be used as reports in the application.

def register_report(name, model, tmpl_path, parser=rml_parse):
    "Register the report into the services"
    name = 'report.%s' % name
    jasper_report.report_jasper(name, model)


class report_xml(osv.osv):
    _name = 'ir.actions.report.xml'
    _inherit = 'ir.actions.report.xml'
    _columns = {
    'jasper_output': fields.selection(
        [('html', 'HTML'), ('csv', 'CSV'), ('xls', 'XLS'), ('rtf', 'RTF'), ('odt', 'ODT'), ('ods', 'ODS'),
         ('txt', 'Text'), ('pdf', 'PDF')], 'Jasper Output'),
    #'jasper_file_ids': fields.one2many('ir.actions.report.xml.file', 'report_id', 'Files', help=''),
    'jasper_model_id': fields.many2one('ir.model', 'Model', help=''),  # We use jas-er_model
    'jasper_report': fields.boolean('Is Jasper Report?', help=''),
    }
    _defaults = {
    'jasper_output': lambda self, cr, uid, context: context.get('jasper_report') and 'pdf',
    }


    #===============================================================================
    #	FIX DONE BY ARIF on 22.02.2011
    #	AUTOMATIC JASPER REPORT REGISTRATION DISABLED TO WORK IT FROM WIZARD
    #===============================================================================
    def x_register_all(self, cursor):
        value = super(report_xml, self).register_all(cursor)
        cursor.execute("SELECT * FROM ir_act_report_xml WHERE report_rml ilike '%.jrxml' ORDER BY id")
        records = cursor.dictfetchall()
        for record in records:
            register_report(record['report_name'], record['model'], record['report_rml'])
        return value

    def create(self, cr, uid, vals, context=None):
        print "CONTEXT: ", context
        print "VALS: ", vals
        if context and context.get('jasper_report'):
            vals['model'] = self.pool.get('ir.model').browse(cr, uid, vals['jasper_model_id'], context).model
            vals['type'] = 'ir.actions.report.xml'
            vals['report_type'] = 'pdf'
            vals['jasper_report'] = True
        return super(report_xml, self).create(cr, uid, vals, context)

    def write(self, cr, uid, ids, vals, context=None):
        if context and context.get('jasper_report'):
            if 'jasper_model_id' in vals:
                vals['model'] = self.pool.get('ir.model').browse(cr, uid, vals['jasper_model_id'], context).model
            vals['type'] = 'ir.actions.report.xml'
            vals['report_type'] = 'pdf'
            vals['jasper_report'] = True
        return super(report_xml, self).write(cr, uid, ids, vals, context)

    def save_file(self, name, value):
        path = os.path.abspath(os.path.dirname(__file__))
        path += '/custom_reports/%s' % name
        f = open(path, 'wb+')
        f.write(base64.decodestring(value))
        f.close()

        path = 'jasper_reports/custom_reports/%s' % name
        return path

