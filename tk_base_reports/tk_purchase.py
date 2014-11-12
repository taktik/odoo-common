from openerp.tools.translate import _
import re
from openerp.osv import fields, osv


def name_with_space(name):
    return name.replace('/', ' ').replace('_', ' ')


class tk_purchase_order(osv.osv):
    _inherit = "purchase.order"

    def _translate_term(self, cr, uid, text, lang):
        _transl_regex = re.compile('(\[\[.+?\]\])')
        if lang and text and not text.isspace():
            transl_obj = self.pool.get('ir.translation')
            piece_list = _transl_regex.split(text)
            for pn in range(len(piece_list)):
                if not _transl_regex.match(piece_list[pn]):
                    source_string = piece_list[pn].replace('\n', ' ').strip()
                    if len(source_string):
                        translated_string = transl_obj._get_source(cr, uid, False, ('selection'), lang, source_string)
                        if translated_string:
                            piece_list[pn] = piece_list[pn].replace(source_string, translated_string)
            text = ''.join(piece_list)
        return text

    def _get_report_name(self, cr, uid, ids, context=None):
        if not isinstance(ids, list):
            ids = [ids]
        po = self.pool.get('purchase.order').browse(cr, uid, ids[0])
        translated_term = self._translate_term(cr, uid, 'Purchase Order', po.partner_id and po.partner_id.lang or False)
        name = (translated_term or '') + ((po.name and ' %s' % po.name) or '') or ((po.origin and ' %s' % po.origin) or '')
        return name

    def print_quotation(self, cr, uid, ids, context=None):
        """
        Inherit the default print_quotation and change the report_name to the palani report.
        @param cr: cursor
        @param uid: user id
        @param ids: ids
        @param context: context
        @return: dictionary containing a ir.actions.report.xml
        """
        res = super(tk_purchase_order, self).print_quotation(cr, uid, ids, context=context)
        res.update({'report_name': 'tk.purchase.order'})
        context.update({'report_name': self._get_report_name(cr, uid, ids)})
        return res


tk_purchase_order()