from tk_report_parser.tk_report_parser import tk_report_parser

# Account invoice
tk_report_parser.register('report.tk.account.invoice',
                          'account.invoice',
                          'addons/tk_base_reports/reports/template/account_invoice.html.mako',
                          parser=tk_report_parser)

# Delivery order
tk_report_parser.register('report.tk.stock.picking',
                          'stock.picking',
                          'addons/tk_base_reports/reports/template/delivery_order.html.mako',
                          parser=tk_report_parser)

# Purchase order
tk_report_parser.register('report.tk.purchase.order',
                          'purchase.order',
                          'addons/tk_base_reports/reports/template/purchase_order.html.mako',
                          parser=tk_report_parser)

# Request for quotation
tk_report_parser.register('report.tk.purchase.quotation',
                          'purchase.order',
                          'addons/tk_base_reports/reports/purchase_order.html.mako',
                          parser=tk_report_parser)

# Sale order
tk_report_parser.register('report.tk.sale.order',
                          'sale.order',
                          'addons/tk_base_reports/template/reports/sale_order.html.mako',
                          parser=tk_report_parser)