from openerp.osv import fields, osv


def name_with_space(name):
    return name.replace('/', ' ').replace('_', ' ')


class tk_sale_order(osv.osv):
    _inherit = "sale.order"

    def _get_report_name(self, cr, uid, ids, context=None):
        if not isinstance(ids, list):
            ids = [ids]
        if len(ids) > 1:
            return "Multiple"
        name = self.pool.get('sale.order').browse(cr, uid, ids[0]).name
        return name_with_space(name)

    def print_quotation(self, cr, uid, ids, context=None):
        """
        Inherit the default print_quotation and change the report_name to the palani report.
        @param cr: cursor
        @param uid: user id
        @param ids: ids
        @param context: context
        @return: dictionary containing a ir.actions.report.xml
        """
        res = super(tk_sale_order, self).print_quotation(cr, uid, ids, context=context)
        res.update({'report_name': 'tk.sale.order'})
        # Custom name
        if not isinstance(ids, list):
            ids = [ids]
        context.update({'report_name': self._get_report_name(cr, uid, ids[0])})
        return res


tk_sale_order()