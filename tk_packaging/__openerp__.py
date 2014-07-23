# 
# 
# 
{
	"name" : "Taktik Packaging",
	"version" : "0.1",
	"author" : "Taktik S.A.",
	"category" : "Generic Modules/Others",
	"website": "http://www.taktik.be",
	"description": 
	"""
	This module add packaging in purchase order to allow order in packaging and convert it into classic uom
	""",
	"depends" : ["base", "purchase", "stock"],
	"init_xml" : [],
	"demo_xml" : [],
	"data" : [
        "view/tk_purchase_view.xml",
        "view/tk_product_view.xml",
        "view/tk_stock_view.xml",
        "menuitem/tk_packaging_menuitem.xml",
				],
	"active": False,
	"installable": True
}