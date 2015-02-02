#
#
{
    "name" : "Taktik Worklog Invoice",
    "version" : "1.0",
    "author" : "Taktik S.A.",
    "category" : "Generic Modules/Others",
    "website": "http://www.taktik.be",
    "description": "Taktik Worklog Invoice -- This module allow you to add timesheet entries to a draft invoice.",
    "depends" : ['account', 'project', 'hr_timesheet_invoice'],
    "init_xml" : [],
    "demo_xml" : [],
    "data" : [
                    "wizard/tk_worklog_invoice.xml",
                    ],
    "active": False,
    "installable": True
}
