<html>
<head>
<style type="text/css"> 
${css} 
table {
	border-collapse:collapse;
}
.bas {
	margin-left: 70%;
	width: 30%;
}
.reception {
	line-height: 150%
}
</style>
</head>
<body>
    %for stock in objects :
	<% setLang(stock.partner_id.lang) %>
	<table width="40%" class="contact">
    	<tr>
        	<td>${stock.partner_id.title and stock.partner_id.title.name or ''|entity}  ${stock.partner_id.name |entity}</td>
        </tr>
        <tr>
        	<td>${stock.address_id.street or ''|entity}</td>
        </tr>
        %if stock.address_id.street2 :
        	${stock.address_id.street2 or ''|entity}
        %endif 
        <tr>
        	<td> ${stock.address_id.zip or ''|entity} ${stock.address_id.city or ''|entity}</td>
        </tr>
        <tr>
        	<td>${stock.address_id and stock.address_id.country_id.name or ''|entity}</td>
        </tr>
        <tr>
        	<td>${_("VAT")}: ${stock.partner_id.vat|entity}  </td>
        </tr>
    </table>
    <br />
	<span class="title">${_('Delivery Order N&deg;')} : ${stock.name| entity}</span>
	<br/>
	<br/>
	<p class="doc_info">${_('Your reference')}: ${stock.partner_id.ref or '' | entity}<br/>
	${_('Order date')}: ${formatLang(stock.date, date=True)}<br/>
	%if stock.partner_id.user_id:
	${_('Our salesman')}: ${stock.partner_id.user_id.name or ''| entity}</p>
	%endif
	<br/>
    <table class="doc_content" width="100%">
    	<thead>
			<tr>
	        	<th width="16%" class="left">${_('Item')}</th>
	        	<th width="8%" class="left">${_('Qty')}</th>
				<th width="62%" class="left">${_('Description')}</th>
				<th width="14%">${_('Gross weight kg')}</th>
	      	</tr>
		</thead>
	<% total_quantity = total_weight = 0 %>
	%for line in stock.move_lines :
	<tbody>
        <tr>
        	<td class="texte">${line.product_id.default_code|entity}</td>
        	<td class="texte">${"%.2f" % line.product_qty}</td>
        	<td class="texte">${line.name}</td>
        	<% total_quantity += line.product_qty %>
        	<% total_weight += line.product_id.product_tmpl_id.weight %>
        	<td class="texte" style="text-align:right;">${line.product_id.product_tmpl_id.weight*line.product_qty|entity}</td>
        </tr>
        %if line.note :
		<tr>
			<td colspan="6" class="note">${line.note |entity}</td>
		</tr>
        %endif
        %endfor
        </tbody>
    </table>
	<table border="0" cellpadding="3" cellspacing="0" class="bas">
		<tr>
	        <td>${_('Total<br/>quantity')}</td>
	        <td class="number bold">${formatLang(total_quantity)}</td>
		</tr>
		<tr>
			<td>${_('Total weight')}</td>
			<td class="number bold">${formatLang(total_weight)}</td>
		</tr>
    </table>
    <br>
<table width="26%" border="0" cellspacing="5">
      <tr>
        <td width="30%" valign="top" class="reception">${_('For reception')} :<br/>
          ${_('Name')} : .............................................................................<br>
          ${_('Date')} : ........../.........../20.........<br>
          ${_('Signature')} :<br>
          ..........................................................................................</td>
      </tr>
</table>
%endfor
</body>
</html>