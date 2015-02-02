# 
# 
# 
{
	"name" : "Taktik Invoice date check module",
	"version" : "0.1",
	"author" : "Taktik S.A.",
	"category" : "Generic Modules/Others",
	"website": "http://www.taktik.be",
	"description": """
	Taktik Invoice date check module will check that your invoices numbers
	stay coherent with their dates.
	Basically the next invoice cannot have a date prior to the previous one.
	A wizard is accessible in the invoices to be able to interpose an invoice between two others,
	providing the correct sequence number.
	""",
	"depends" : ["account", "base"],
	"init_xml" : [],
	"demo_xml" : [],
	"data" : [
        'workflow/tk_account_workflow.xml',
        'wizard/tk_invoice_interpose_wizard_view.xml',
        'view/tk_account_invoice_view.xml',
                    ],
	"active": False,
	"installable": True
}
