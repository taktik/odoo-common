<html>
<head>
<style type="text/css"> 
${css} 
.contact {
	margin-left: 30%;
}
.contact_left {
	margin-left: 0%;
	font-size: 12px;
}
</style>
</head>
<body>
    %for so in objects :
	<% setLang(so.partner_id.lang) %>
	<table class="container">
		<tr>
			<td>
				<table class="contact contact_left">
					<tr>
						<td class="bold">${_('Shipping address')} :</td>
					<tr>
					<tr>
						<td>${so.partner_id.name or ''| entity} ${so.partner_id.title and so.partner_id.title.name or ''| entity}</td>
					<tr>
					<tr>
						<td>${so.partner_shipping_id.title and so.partner_shipping_id.title.name or ''| entity} ${so.partner_shipping_id.name}</td>
					</tr>
					<tr>
						<td>${so.partner_shipping_id.street or ''| entity}</td>
					</tr>
					%if so.partner_shipping_id.street2:
					<tr>
						<td>${so.partner_shipping_id.street2 or ''| entity}</td>
					</tr>
					%endif
					<tr>
						<td>${so.partner_shipping_id.zip or ''| entity} ${so.partner_shipping_id.city or ''| entity}</td>
					</tr>
					<tr>
						<td>${so.partner_shipping_id.country_id and so.partner_shipping_id.country_id.name or ''| entity}</td>
					</tr>
				</table>
			</td>
			<td>
				<table class="contact">
					<tr>
						<td>${so.partner_id.name or ''| entity} ${so.partner_id.title and so.partner_id.title.name or ''| entity}</td>
					<tr>
					<tr>
						<td>${so.partner_id.title and so.partner_id.title.name or ''| entity} ${so.partner_id.name}</td>
					</tr>
					<tr>
						<td>${so.partner_id.street or ''| entity}</td>
					</tr>
					%if so.partner_id.street2:
					<tr>
						<td>${so.partner_id.street2 or ''| entity}</td>
					</tr>
					%endif
					<tr>
						<td>${so.partner_id.zip or ''| entity} ${so.partner_id.city or ''| entity}</td>
					</tr>
					<tr>
						<td>${so.partner_id.country_id and so.partner_id.country_id.name or ''| entity}</td>
					</tr>
					<tr>
						<td>${so.partner_id.vat or ''| entity}</td>
					</tr>
				</table>
			</td>
		</tr>
		<tr>
			<td>
				<table class="contact contact_left">
					<tr>
						<td class="bold">${_('Invoice address')} :</td>
					</tr>
					<tr>
						<td>${so.partner_invoice_id.title and so.partner_invoice_id.title.name or ''| entity} ${so.partner_invoice_id.name}</td>
					</tr>
					<tr>
						<td>${so.partner_invoice_id.street or ''| entity}</td>
					</tr>
					%if so.partner_invoice_id.street2:
					<tr>
						<td>${so.partner_invoice_id.street2 or ''| entity}</td>
					</tr>
					%endif
					<tr>
						<td>${so.partner_invoice_id.zip or ''| entity} ${so.partner_invoice_id.city or ''| entity}</td>
					</tr>
					<tr>
						<td>${so.partner_invoice_id.country_id and so.partner_invoice_id.country_id.name or ''| entity}</td>
					</tr>
				</table>
			</td>
		</tr>
	</table>
	
	<br/>
    <% doc_type = _('Sale order') %>
    %if so.state in ['draft', 'sent']:
		<% inv_type = _('Quotation') %>    	
    %endif
	<span class="title">${doc_type} N&deg; : ${so.name| entity}</span>
	<br/>
	<br/>
	<p class="doc_info">${_('Your reference')}: ${so.client_order_ref or '/' | entity}<br/>
	${_('Order date')}: ${so.date_order and formatLang(so.date_order, date=True)}<br/>
	${_('Our salesman')}: ${so.user_id.name or ''| entity}</p>
	<br/>
	<table class="doc_content" width="100%">
		<thead>
			<tr>
				<th width="16%" class="left">${_('Item')}</th>
				<th width="8%" class="left">${_('Quantity')}</th>
				<th width="44%" class="left">${_('Description')}</th>
				<th width="14%">${_('List price')}</th>
				<th width="6%">${_('Disc<br/>%')}</th>
				<th width="12%">${_('Price')}</th>
			</tr>
		</thead>
		<tbody>
        <%
            sale_layout_available = hasattr(so, 'abstract_line_ids')
            subtotal_htva = 0
        %>
            %for line in so.abstract_line_ids if sale_layout_available else so.order_line:
                <%
                    subtotal_htva += line.price_subtotal
                %>
                %if sale_layout_available and line.layout_type and line.layout_type == 'title':
                    <tr>
                        <td colspan="6"><span style="font-weight:bold">${line.name or ''}</span> </td>
                    </tr>
                % elif sale_layout_available and line.layout_type and line.layout_type == 'text':
                    <tr>
                        <td colspan="6" style="padding-left: 25px;">${nl2br(line.name)}</td>
                    </tr>
                % elif sale_layout_available and line.layout_type and line.layout_type == 'subtotal':
                    <tr>
                        <td colspan="6" style="text-align: right">${_('Subtotal')}: ${formatLang(subtotal_htva)}</td>
                    </tr>
                    <% subtotal_htva = 0 %>
                % elif sale_layout_available and line.layout_type and line.layout_type == 'line':
                    <tr>
                        <td colspan="6"><hr style="border:0;height:1px;background-color: #CCC;" /></td>
                    </tr>
                % elif sale_layout_available and line.layout_type and line.layout_type == 'break':
                    </tbody></table>
                    ${page_break()}
                    <table class="doc_content" width="100%" style="width:100%;margin-top:15px;">
                        <thead>
                        <tr>
                            <th width="16%" class="left">${_('Item')}</th>
                            <th width="8%" class="left">${_('Quantity')}</th>
                            <th width="44%" class="left">${_('Description')}</th>
                            <th width="14%">${_('List price')}</th>
                            <th width="6%">${_('Disc<br/>%')}</th>
                            <th width="12%">${_('Price')}</th>
                        </tr>
                        </thead>
                    <tbody>
                    % else :
                <tr>
                    <td>${line.product_id and line.product_id.default_code or ''| entity}</td>
                    <td class="number">${formatLang(line.product_uos_qty and line.product_uos_qty or line.product_uom_qty)} ${line.product_uos and line.product_uos.name or line.product_uom.name| entity}</td>
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
			<td class=""></td>
			<td class="total">
				<table class="">
					<tr>
						<td >${_('Total ex VAT')}:</td>
						<td class="number">${formatLang(so.amount_untaxed or 0.0)} ${so.pricelist_id.currency_id.name | entity}</td>
					</tr>
					<tr>
						<td >${_('Taxes')}:</td>
						<td class="number">${formatLang(so.amount_tax or 0.0)} ${so.pricelist_id.currency_id.name | entity}</td>
					</tr>
					<tr class="total">
						<td class="bold">${_('To pay')} :</td>
						<td class="number bold">${formatLang(so.amount_total or 0.0)} ${so.pricelist_id.currency_id.name | entity}</td>
					</tr>
					<tr>
						<td colspan="2">${so.payment_term and so.payment_term.note| entity}</td>
					</tr>
				</table>
			</td>
		</tr>
	</table>
	%endfor
</body>
</html>