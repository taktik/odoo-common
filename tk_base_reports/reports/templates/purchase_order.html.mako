<html>
<head>
<style type="text/css"> 
${css}
.conditions {
	font-family: Verdana, Geneva, sans-serif; font-size: 8px;
}
</style>
</head>
<body>
    %for order in objects :
    <% setLang(order.partner_id.lang) %>
	<table class="contact contact_left">
        <tr>
        	<td ><b>${order.partner_id.title or ''|entity}  ${order.partner_id.name |entity}</b></td>
        </tr>
        <tr>
        	<td>${order.dest_address_id.street or ''|entity}</td>
        </tr>
        <tr>
        	<td>${order.dest_address_id.street2 or ''|entity}</td>
        </tr>
        <tr>
        	<td>${order.dest_address_id.zip or ''|entity} ${order.dest_address_id.city or ''|entity}</td>
        </tr>
        %if order.dest_address_id.country_id :
        <tr>
        	<td>${order.dest_address_id.country_id.name or ''|entity} </td>
        </tr>
        %endif
        %if order.dest_address_id.phone :
        <tr>
        	<td>${_("Tel")}: ${order.dest_address_id.phone|entity}</td>
        </tr>
        %endif
        %if order.dest_address_id.fax :
        <tr>
        	<td>${_("Fax")}: ${order.dest_address_id.fax|entity}</td>
        </tr>
        %endif
        %if order.dest_address_id.email :
        <tr>
        	<td>${_("E-mail")}: ${order.dest_address_id.email|entity}</td>
        </tr>
        %endif
        %if order.partner_id.vat :
		<tr>
			<td>${_("VAT")}: ${order.partner_id.vat or 'N/A' |entity}</td>
		</tr>
        %endif
    </table>
    <br />
    <% doc_type = _('Purchase Order') %>
    %if order.state == 'draft' or order.state == 'sent':
    	<% doc_type = _('Draft') %>
    %endif
    <span class="title">${doc_type} N&deg; : ${order.name| entity}</span>
	<br/>
    <br/>
    <p class="doc_info">${_('Client ref')} : ${ order.partner_ref or 'N/A' }<br/>
    ${_('Date')} : ${formatLang(order.date_order, date=True)|entity}<br/>
    ${_('Confirmed by')} : ${ order.validator and order.validator.name or 'N/A' }
    </p>
	<br>
	<table  width="100%" class="doc_content">
        <thead>
          <tr>
	          <th width="41%" class="left">${_("Label")}</th>
	          <th width="7%" class="">${_("VAT")}</th>
	          <th width="10%">${_("Date")}</th>
	          <th width="9%">${_("Qty")}</th>
	          <th width="9%">${_("Price")}</th>
	          <th width="10%">${_("Net price")}</th>
   		  </tr>
   		</thead>
        <tbody>
        %for line in order.order_line :
        	<tr>
	        	<td>${line.name|entity}</td>
	        	<td>${ ', '.join(map(lambda x: formatLang(x.amount*100)+' %', line.taxes_id))}</td>
	        	<td><div align="center">${ time.strftime(line.date_planned)}</td>
	        	<td><div align="center">${ line.product_qty and formatLang(line.product_qty) or '' } ${ line.product_uom.name}</td>
	        	<td><div align="center">${formatLang(line.price_unit)}</td>
	        	<td style="text-align:right;"><div align="center">${formatLang(line.price_subtotal)}</td>
	        </tr>

        %endfor
    </table>
    <br/>
    %if order.notes :
	<table width="100%" border="0">
	  <tr>
	    <th scope="col" class="texte"><div align="left">Notes</div></th>
	  </tr>
	  <tr><td class="texte">${order.notes |entity}</td>
	</table>
	%endif
	<table class="container">
		<tr>
			<td class=""></td>
	        <td class="total">
				<table class="">
					<tr>
						<td >${_('Total (HT)')}:</td>
						<td class="number">${formatLang(order.amount_untaxed or 0.0)} ${order.pricelist_id.currency_id.name | entity}</td>
					</tr>
					<tr>
						<td >${_('Taxes')}:</td>
						<td class="number">${formatLang(order.amount_tax or 0.0)} ${order.pricelist_id.currency_id.name | entity}</td>
					</tr>
					<tr class="total">
						<td class="bold">${_('To pay')}:</td>
						<td class="number bold">${formatLang(order.amount_total or 0.0)} ${order.pricelist_id.currency_id.name | entity}</td>
					</tr>
				</table>
			</td>
		</tr>
	</table>
    %endfor   
</body>
</html>