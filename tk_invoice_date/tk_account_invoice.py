from openerp.osv import fields, osv
from datetime import datetime, date

class tk_account(osv.osv):
    _inherit = 'account.invoice'

    def action_delete_number(self, cr, uid, ids, context=None):
        """
        Normal behavior is that the invoice keep its internal_number
        even after a cancel (so that if you want to validate it again, it keeps its number).
        Removes completely the internal_number of an invoice,
        to be able to interpose another invoice at this number.
        """
        if not isinstance(ids, list):
            ids = [ids]
        self.write(cr, uid, ids, {'internal_number':None})
        return True

    def check_date(self, cr, uid, ids):
        """Workflow method to check if the date is not before the last invoice date.
        We modified the workflow as is :
        Instead of going from draft to open, we are going from draft to check_date,
        then from check_date to open if successful, else back to draft.
        """
        for invoice in self.browse(cr, uid, ids):
            if invoice.type in ('out_invoice', 'out_refund'):
                last_invoice_id = self.search(cr, uid, [('state', 'in', ('open', 'paid')), ('type', '=', invoice.type), ('journal_id','=',invoice.journal_id.id)], limit=1, order='date_invoice DESC')
                if not last_invoice_id:
                    return True
                last_invoice = self.browse(cr, uid, last_invoice_id[0])
                if invoice.date_invoice and invoice.date_invoice < last_invoice.date_invoice and not invoice.internal_number:
                    raise osv.except_osv('Error !', 'The date of the invoice for %s (%s) must be after the last invoice date (%s)' % (invoice.partner_id.name, invoice.date_invoice, str(last_invoice.date_invoice)))
        return True

tk_account()