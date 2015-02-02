from openerp.osv import fields, osv
from datetime import datetime
import time
from openerp import workflow, exceptions


class tk_invoice_interpose(osv.osv_memory):
    _name = 'tk_invoice_interpose'
    _columns = {
        'invoice_id':   fields.many2one('account.invoice','Invoice', required=True),
        'number':       fields.char('Invoice number', size=64, required=True),
        'date':         fields.date('Invoice date', required=True),
    }

    def next(self, cr, uid, ids, context=None):
        """
        Try to interpose an invoice at a specific number with the specified date.
        The date of the invoice must be between the previous and the next invoice dates.
        """
        if not isinstance(ids, list):
            ids = [ids]

        # Get wizard values
        wizard = self.browse(cr, uid, ids[0])
        invoice_id = wizard.invoice_id.id if wizard.invoice_id else None
        number = wizard.number
        date = wizard.date

        if not invoice_id or not number :
            raise osv.except_osv("Warning","You must set an invoice and a number to continue")
        if not date :
            date = datetime.now()

        invoice_obj = self.pool.get('account.invoice')
        sequence_obj = self.pool.get('ir.sequence')

        invoice = invoice_obj.browse(cr, uid, invoice_id)

        if invoice.state != 'draft' :
            raise osv.except_osv("Warning","The invoice must be in the draft state to continue")

        # Check if this internal_number is not already taken
        invoice_ids = invoice_obj.search(cr, uid, [('internal_number','=',number)])
        if invoice_ids and len(invoice_ids) > 0 :
            raise osv.except_osv("Warning","You cannot interpose an invoice at this number (%s). There is already an invoice with this number." % number)

        sequence_id = invoice.journal_id.sequence_id.id
        sequences = sequence_obj.read(cr, uid, [sequence_id], ['company_id','implementation','number_next','prefix','suffix','padding'])
        if sequences and len(sequences)== 1:
            sequence = sequences[0]
        else :
            raise osv.except_osv("Error","No sequence found for this invoice")

        # Try to get this invoice sequence number by removing prefix and suffix
        # (after interpolation)
        d = sequence_obj._interpolation_dict() # Replacing patterns with actual values (ie date %Y...)
        interpolated_prefix = sequence_obj._interpolate(sequence['prefix'], d)
        interpolated_suffix = sequence_obj._interpolate(sequence['suffix'], d)
        sequence_number = number[len(interpolated_prefix):]
        if len(interpolated_suffix) > 0 :
            sequence_number = sequence_number[:len(interpolated_suffix)]

        sequence_number = int(sequence_number)

        # Try to get the previous invoice, going maximum 5 sequence numbers before
        max_previous = 5 if sequence_number>5 else sequence_number
        previous_invoice = None
        previous_sequence_number = '%%0%sd' % sequence['padding'] % (sequence_number-1) # %%0%s = padding
        for i in range(sequence_number, sequence_number-max_previous, -1):
            previous_sequence_number = '%%0%sd' % sequence['padding'] % i # %%0%s = padding
            previous_invoice_ids = invoice_obj.search(cr, uid, [('number','like','%s%s%%' % (interpolated_prefix, previous_sequence_number))])
            if previous_invoice_ids and len(previous_invoice_ids) == 1 :
                previous_invoice = invoice_obj.browse(cr, uid, previous_invoice_ids[0])
                break

        if not previous_invoice :
            raise osv.except_osv("Error","Cannot determine previous invoice (number beginning with %s%s)" % (interpolated_prefix, previous_sequence_number))

        # Try to get next invoice number, going maximum 5 sequence numbers after
        next_invoice = None
        next_sequence_number = '%%0%sd' % sequence['padding'] % (sequence_number+1) # %%0%s = padding
        for i in range(sequence_number, sequence_number+5):
            next_sequence_number = '%%0%sd' % sequence['padding'] % i
            next_invoice_ids = invoice_obj.search(cr, uid, [('number','like','%s%s%%' % (interpolated_prefix, next_sequence_number))])
            if next_invoice_ids and len(next_invoice_ids) == 1 :
                next_invoice = invoice_obj.browse(cr, uid, next_invoice_ids[0])
                break

        if not next_invoice :
            raise osv.except_osv("Error","Cannot determine next invoice (number beginning with %s%s)" % (interpolated_prefix, next_sequence_number))

        # Check if the previous invoice has an anterior date
        previous_date = previous_invoice.date_invoice
        if date < previous_date :
            raise osv.except_osv("Error","The date must be after the previous invoice (number %s date %s)" % (previous_invoice.number, previous_invoice.date_invoice))

        # Check if the next invoice has a superior date
        next_date = next_invoice.date_invoice
        if date > next_date :
            raise osv.except_osv("Error","The date must be before the next invoice (number %s date %s)" % (next_invoice.number, next_invoice.date_invoice))

        invoice_obj.write(cr, uid, [invoice_id], {'internal_number':number,'date_invoice':date})
        # Call workflow to validate the invoice
        workflow.trg_validate(uid, 'account.invoice', invoice_id, 'invoice_open', cr)
        return {
            'type': 'ir.actions.act_window_close'
        }

    _defaults = {
        'invoice_id': lambda self, cr, uid, context=None: context.get('active_id', False) if context else None,
        'date': lambda self, cr, uid, context=None: time.strftime('%Y-%m-%d'),
    }

tk_invoice_interpose()