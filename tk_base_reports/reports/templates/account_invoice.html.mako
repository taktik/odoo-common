<html>
<head>
    <style type="text/css">
            ${css}
        .due_date {
            text-align: right;
        }
    </style>
</head>
<body>
        %for inv in objects :
        <% setLang(inv.partner_id.lang) %>
        <%
            address_invoice = False
            address_invoice_dict = pool.get('res.partner').address_get(cr, uid, [inv.partner_id.id], ['invoice'])
            if address_invoice_dict and address_invoice_dict.get('invoice', False):
                address_invoice = pool.get('res.partner').browse(cr, uid, address_invoice_dict['invoice'])
        %>
        <table class="contact" width="30%">
            <tr>
                <td>${inv.partner_id.name or ''| entity} ${inv.partner_id.title and inv.partner_id.title.name or ''| entity}</td>
            <tr>
            <tr>
                <td>${address_invoice and address_invoice.title and address_invoice.title.name or ''| entity} ${address_invoice.name}</td>
            </tr>
            <tr>
                <td>${address_invoice and address_invoice.street or ''| entity}</td>
            </tr>
            <tr>
                <td>${address_invoice and address_invoice.street2 or ''| entity}</td>
            </tr>
            <tr>
                <td>${address_invoice and address_invoice.zip or ''| entity} ${address_invoice and address_invoice.city or ''| entity}</td>
            </tr>
            <tr>
                <td>${address_invoice and address_invoice.country_id and address_invoice.country_id.name or ''| entity}</td>
            </tr>
            <tr>
                <td>${address_invoice and inv.partner_id.vat or ''| entity}</td>
            </tr>
        </table>
        <br/>
        <%
            inv_type = _('Invoice')
            if inv.type == 'out_invoice' and inv.state in ['proforma']:
                inv_type = 'PRO-FORMA'
            elif inv.type == 'out_invoice' and inv.state in ['draft']:
                inv_type = _('Draft invoice')
            elif inv.type == 'out_invoice' and inv.state in ['cancel']:
                inv_type = _('Cancelled invoice')
            elif inv.type == 'out_refund':
                inv_type = _('Customer refund')
            elif inv.type == 'in_refund':
                inv_type = _('Supplier refund')
            elif inv.type == 'in_invoice':
                inv_type = _('Supplier invoice')

        %>
        <span class="title">${ '%s %s' % (inv_type, inv.number or '')| entity}</span>
        <br/>
        <br/>

        <p class="doc_info">${_('Document')}: ${inv.origin or ''| entity}<br/>
        ${_('Invoice date')}: ${inv.date_invoice and formatLang(inv.date_invoice, date=True)}<br/>
        ${_('Client ref')}: ${inv.name or inv.partner_id.ref or '/'| entity}</p>
        <br/>
        <table class="doc_content" width="100%">
            <thead>
            <tr>
                <th width="16%" class="left">${_('Item')}</th>
                <th width="8%" class="left">${_('Quantity')}</th>
                <th width="44%" class="left">${_('Description')}</th>
                <th width="14%">${_('List price')}</th>
                <th width="6%">${_('Disc.')}<br/>(%)</th>
                <th width="12%">${_('Price')}</th>
            </tr>
            </thead>
        <tbody>
        <%
            invoice_layout_available = hasattr(inv, 'abstract_line_ids')
            subtotal_htva = 0
        %>
        %for line in inv.abstract_line_ids if invoice_layout_available else inv.invoice_line:
            <%
                subtotal_htva += line.price_subtotal
            %>
            %if invoice_layout_available and line.state and line.state == 'title':
                <tr>
                    <td colspan="6"><span style="font-weight:bold">${line.name or ''}</span></td>
                </tr>
            % elif invoice_layout_available and line.state and line.state == 'text':
                <tr>
                    <td colspan="6" style="text-indent: 25px;">${line.name}</td>
                </tr>
            % elif invoice_layout_available and line.state and line.state == 'subtotal':
                <tr>
                    <td colspan="6" style="text-align: right">${_('Subtotal')}: ${formatLang(subtotal_htva)}</td>
                </tr>
                <% subtotal_htva = 0 %>
            % elif invoice_layout_available and line.state and line.state == 'line':
                <tr>
                    <td colspan="6">
                        <hr style="border:0;height:1px;background-color: #CCC;"/>
                    </td>
                </tr>
            % elif invoice_layout_available and line.state and line.state == 'break':
                </tbody></table>
                ${page_break()}
                <table class="doc_content" width="100%" style="width:100%;margin-top:15px;">
                    <thead>
                    <tr>
                        <th width="16%" class="left">${_('Item')}</th>
                        <th width="8%" class="left">${_('Quantity')}</th>
                        <th width="44%" class="left">${_('Description')}</th>
                        <th width="14%">${_('List price')}</th>
                        <th width="6%">${_('Disc.')}<br/>(%)</th>
                        <th width="12%">${_('Price')}</th>
                    </tr>
                    </thead>
                <tbody>
            % else :
                <tr>
                    <td>${line.product_id and line.product_id.default_code or ''| entity}</td>
                    <td class="number">${formatLang(line.quantity)} ${line.uos_id and line.uos_id.name| entity}</td>
                    <td>${line.product_id and line.product_id.name or line.name| entity}</td>
                    <td class="number">${formatLang(line.price_unit)}</td>
                    <td class="number">${formatLang(line.discount)}</td>
                    <td class="number">${formatLang(line.price_subtotal)}</td>
                </tr>
            %endif
        %endfor
        </tbody>
        </table>
        <br/>
        <table class="container">
        <tr>
        <td class="tax">
        <table class="taxes">
            <thead>
            <tr>
                <th width="40%">${_('Taxes')}</th>
                <th width="30%">${_('Base')}</th>
                <th width="30%">${_('Amount')}</th>
            </tr>
            </thead>
        <tbody>
            %for tax in inv.tax_line:
            <tr>
                <td>${tax.name or ''| entity}</td>
                <td class="number">${formatLang(tax.base or 0.0)}</td>
                <td class="number">${formatLang(tax.amount or 0.0)}</td>
            </tr>
            %endfor
        </tbody>
        </table>
        </td>
        <td class="total">
        <table class="">
            <tr>
                <td>${_('Subtotal')}:</td>
                <td class="number">${formatLang(inv.amount_untaxed or 0.0)} ${inv.currency_id.name | entity}</td>
            </tr>
            <tr>
                <td>${_('Taxes')}:</td>
                <td class="number">${formatLang(inv.amount_tax or 0.0)} ${inv.currency_id.name | entity}</td>
            </tr>
            <tr class="total">
                <td class="bold">${_('Total due')}:</td>
                <td class="number bold">${formatLang(inv.amount_total or 0.0)} ${inv.currency_id.name | entity}</td>
            </tr>
        %if inv.date_due and date_due != 'False':
                <tr>
                    <td colspan="2" class="due_date">${_('To pay before')}: ${formatLang(inv.date_due, date=True)}</td>
                </tr>
        %endif
        </table>
        </td>
        </tr>
        </table>
        %endfor
</body>
</html>