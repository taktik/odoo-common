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
# #############################################################################
import base64

from openerp.osv import fields, osv
from openerp.tools.translate import _

class create_data_template(osv.osv_memory):
    _name = 'jasper.create.data.template'
    _description = 'Create data template'

    def action_create_xml(self, cr, uid, ids, context=None):
        for data in self.read(cr, uid, ids, context=context):
            model = self.pool.get('ir.model').browse(cr, uid, data['model'][0], context=context)
            xml = self.pool.get('ir.actions.report.xml').create_xml(cr, uid, model.model, data['depth'], context)
            self.write(cr, uid, ids, {
                'data': base64.encodestring(xml),
                'filename': 'template.xml'
            })

        model_data_obj = self.pool.get('ir.model.data')
        view_rec = model_data_obj.get_object_reference(cr, uid, 'jasper_reports', 'view_pos_box_out')
        view_id = view_rec and view_rec[1] or False

        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'view_id': [view_id],
            'res_id': ids[0],
            'res_model': self._name,
            'target': 'new',
            'context': context,
        }

    _columns = {
        'model': fields.many2one('ir.model', 'Model', required=True),
        'depth': fields.integer("Depth", required=True),
        'filename': fields.char('File Name', size=32),
        'data': fields.binary('XML')
    }

    _defaults = {
        'depth': 1
    }